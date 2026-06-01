//! Rust-owned crew consensus protocol for Nova CommsOps.
//!
//! The service consumes proposal and vote envelopes on NATS, keeps only
//! short-lived coordination state in memory, and publishes a binding resolution
//! when quorum is reached, quorum becomes impossible, or the vote times out.

use async_nats::Client;
use futures_util::StreamExt;
use serde::de::{Error as DeError, Visitor};
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use std::future::Future;
use std::pin::Pin;
use std::time::{Duration, Instant};
use thiserror::Error;
use time::format_description::well_known::Rfc3339;
use time::OffsetDateTime;
use tokio::sync::oneshot;
use tokio::time::interval;
use tracing::{debug, info, warn};

/// Default crew members eligible to vote on consensus proposals.
pub const DEFAULT_VOTERS: &[&str] = &[
    "skipper", "echo", "iris", "zap", "forge", "synergy", "tecton",
];

/// A proposal vote decision.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub enum VoteDecision {
    /// The voter supports binding the proposal.
    Yes,
    /// The voter rejects binding the proposal.
    No,
    /// The voter is present but does not count toward quorum.
    #[default]
    Abstain,
}

impl VoteDecision {
    /// Parses a user or JSON supplied decision.
    ///
    /// Unknown values intentionally normalize to `ABSTAIN` so malformed votes
    /// cannot accidentally count toward either binding or rejection.
    pub fn parse_lossy(value: &str) -> Self {
        match value.trim().to_ascii_uppercase().as_str() {
            "YES" => Self::Yes,
            "NO" => Self::No,
            "ABSTAIN" => Self::Abstain,
            _ => Self::Abstain,
        }
    }

    /// Returns the protocol string form used in JSON envelopes.
    pub fn as_protocol_str(self) -> &'static str {
        match self {
            Self::Yes => "YES",
            Self::No => "NO",
            Self::Abstain => "ABSTAIN",
        }
    }
}

impl Serialize for VoteDecision {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(self.as_protocol_str())
    }
}

impl<'de> Deserialize<'de> for VoteDecision {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        struct DecisionVisitor;

        impl Visitor<'_> for DecisionVisitor {
            type Value = VoteDecision;

            fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
                formatter.write_str("YES, NO, or ABSTAIN")
            }

            fn visit_str<E>(self, value: &str) -> Result<Self::Value, E>
            where
                E: DeError,
            {
                Ok(VoteDecision::parse_lossy(value))
            }
        }

        deserializer.deserialize_str(DecisionVisitor)
    }
}

/// A published consensus resolution decision.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ResolutionDecision {
    /// Quorum was reached and the proposal is binding.
    Bind,
    /// Quorum became impossible before timeout.
    NoBind,
    /// Timeout elapsed before quorum was reached.
    NoQuorum,
}

impl ResolutionDecision {
    /// Returns the protocol string form used in JSON envelopes.
    pub fn as_protocol_str(self) -> &'static str {
        match self {
            Self::Bind => "BIND",
            Self::NoBind => "NO_BIND",
            Self::NoQuorum => "NO_QUORUM",
        }
    }
}

impl Serialize for ResolutionDecision {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(self.as_protocol_str())
    }
}

/// Proposal envelope consumed from `nova.crew.consensus.propose`.
#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
pub struct ProposalPayload {
    /// NATS-safe topic used in the bind subject suffix.
    pub topic: String,
    /// Nova or service proposing the decision.
    pub proposer: String,
    /// Stable proposal identifier used by votes.
    pub proposal_id: Option<String>,
    /// Human or machine readable evidence summary.
    #[serde(default)]
    pub evidence: String,
    /// Minimum number of YES votes required to bind.
    #[serde(default = "default_quorum")]
    pub quorum: usize,
    /// Seconds before unresolved proposals publish `NO_QUORUM`.
    #[serde(default = "default_timeout_seconds")]
    pub timeout_seconds: u64,
}

/// Vote envelope consumed from `nova.crew.consensus.vote.*`.
#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize)]
pub struct VotePayload {
    /// Proposal identifier being voted on.
    pub proposal_id: Option<String>,
    /// Optional topic fallback for proposal lookup.
    pub topic: Option<String>,
    /// Nova or service casting the vote.
    pub voter: Option<String>,
    /// YES, NO, or ABSTAIN.
    #[serde(default)]
    pub decision: VoteDecision,
    /// Short reasoning string retained in active state for diagnostics.
    #[serde(default)]
    pub reasoning: String,
}

/// Resolution envelope published to `nova.crew.consensus.bind.<topic>`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ResolutionPayload {
    /// Proposal identifier that resolved.
    pub proposal_id: String,
    /// Topic that resolved.
    pub topic: String,
    /// BIND, NO_BIND, or NO_QUORUM.
    pub decision: ResolutionDecisionWire,
    /// Minimum YES votes required.
    pub quorum: usize,
    /// Current YES vote count.
    pub yes_votes: usize,
    /// Current NO vote count.
    pub no_votes: usize,
    /// Current ABSTAIN vote count.
    pub abstain_votes: usize,
    /// Total accepted vote count.
    pub votes_received: usize,
    /// Sorted accepted voter names.
    pub voters: Vec<String>,
    /// Duplicate state string for simple downstream routing.
    pub state: ResolutionDecisionWire,
    /// RFC3339 UTC timestamp.
    pub bound_at: String,
    /// Optional resolution reason.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reason: Option<String>,
}

/// Serializable wire representation of a resolution decision.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(transparent)]
pub struct ResolutionDecisionWire(String);

impl ResolutionDecisionWire {
    /// Creates a wire decision from the internal enum.
    pub fn new(decision: ResolutionDecision) -> Self {
        Self(decision.as_protocol_str().to_string())
    }

    /// Returns the underlying protocol value.
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

/// Runtime configuration for a consensus service instance.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ConsensusConfig {
    namespace: String,
    voters: BTreeSet<String>,
    poll_interval: Duration,
}

impl ConsensusConfig {
    /// Creates a config using the default `nova` namespace and crew roster.
    pub fn default_nova() -> Self {
        Self {
            namespace: "nova".to_string(),
            voters: DEFAULT_VOTERS
                .iter()
                .map(|voter| (*voter).to_string())
                .collect(),
            poll_interval: Duration::from_millis(250),
        }
    }

    /// Creates a config with explicit namespace and voters.
    ///
    /// # Errors
    ///
    /// Returns an error when the namespace is not NATS-safe or the voter list is
    /// empty after normalization.
    pub fn new(
        namespace: impl Into<String>,
        voters: impl IntoIterator<Item = String>,
    ) -> Result<Self, ConsensusError> {
        let namespace = namespace.into();
        validate_namespace(&namespace)?;
        let voters = normalize_voters(voters);
        if voters.is_empty() {
            return Err(ConsensusError::NoVoters);
        }
        Ok(Self {
            namespace,
            voters,
            poll_interval: Duration::from_millis(250),
        })
    }

    /// Returns a clone with a different timeout polling interval.
    pub fn with_poll_interval(mut self, poll_interval: Duration) -> Self {
        self.poll_interval = poll_interval.max(Duration::from_millis(1));
        self
    }

    /// Returns the configured namespace.
    pub fn namespace(&self) -> &str {
        &self.namespace
    }

    /// Returns the sorted eligible voter set.
    pub fn voters(&self) -> &BTreeSet<String> {
        &self.voters
    }

    /// Returns the timeout polling interval.
    pub fn poll_interval(&self) -> Duration {
        self.poll_interval
    }

    /// Returns the proposal subject.
    pub fn propose_subject(&self) -> String {
        format!("{}.crew.consensus.propose", self.namespace)
    }

    /// Returns the wildcard vote subject.
    pub fn vote_subject_wildcard(&self) -> String {
        format!("{}.crew.consensus.vote.*", self.namespace)
    }

    /// Returns the bind subject for a topic.
    pub fn bind_subject(&self, topic: &str) -> String {
        format!("{}.crew.consensus.bind.{topic}", self.namespace)
    }
}

/// Consensus protocol errors.
#[derive(Debug, Error)]
pub enum ConsensusError {
    /// The namespace is not safe for use as a NATS subject prefix.
    #[error("invalid NATS namespace: {0}")]
    InvalidNamespace(String),
    /// The topic is empty or not safe for use as a subject suffix.
    #[error("invalid consensus topic: {0}")]
    InvalidTopic(String),
    /// No eligible voters were configured.
    #[error("consensus voter roster is empty")]
    NoVoters,
    /// The proposal omitted a required topic.
    #[error("proposal missing topic")]
    MissingTopic,
    /// The requested quorum is invalid for the configured voter roster.
    #[error("quorum {requested} is invalid for {available} eligible voters")]
    InvalidQuorum {
        /// Requested quorum.
        requested: usize,
        /// Available voters.
        available: usize,
    },
    /// The timeout value is zero.
    #[error("timeout_seconds must be >= 1")]
    InvalidTimeout,
    /// JSON parsing or encoding failed.
    #[error("json error: {0}")]
    Json(#[from] serde_json::Error),
    /// NATS subscription failed.
    #[error("nats subscribe failed: {0}")]
    NatsSubscribe(String),
    /// NATS publish failed.
    #[error("nats publish failed: {0}")]
    NatsPublish(String),
    /// NATS flush failed.
    #[error("nats flush failed: {0}")]
    NatsFlush(String),
    /// A required NATS subscription closed unexpectedly.
    #[error("nats subscription closed: {0}")]
    NatsSubscriptionClosed(&'static str),
}

/// In-memory protocol engine.
#[derive(Debug, Clone)]
pub struct ConsensusEngine {
    config: ConsensusConfig,
    proposals: BTreeMap<String, PendingProposal>,
    decided: BTreeMap<String, ResolutionPayload>,
}

impl ConsensusEngine {
    /// Creates an empty engine from config.
    pub fn new(config: ConsensusConfig) -> Self {
        Self {
            config,
            proposals: BTreeMap::new(),
            decided: BTreeMap::new(),
        }
    }

    /// Returns the active proposal count.
    pub fn active_count(&self) -> usize {
        self.proposals.len()
    }

    /// Returns previously decided proposals by id.
    pub fn decided(&self) -> &BTreeMap<String, ResolutionPayload> {
        &self.decided
    }

    /// Handles a raw proposal JSON payload.
    ///
    /// # Errors
    ///
    /// Returns JSON or validation errors; callers running a long-lived service
    /// should log these and continue.
    pub fn handle_proposal_bytes(&mut self, bytes: &[u8]) -> Result<(), ConsensusError> {
        let payload = serde_json::from_slice::<ProposalPayload>(bytes)?;
        self.handle_proposal(payload)
    }

    /// Handles a typed proposal payload.
    ///
    /// # Errors
    ///
    /// Returns an error if topic, quorum, or timeout values are invalid.
    pub fn handle_proposal(&mut self, payload: ProposalPayload) -> Result<(), ConsensusError> {
        let topic = payload.topic.trim().to_ascii_lowercase();
        if topic.is_empty() {
            return Err(ConsensusError::MissingTopic);
        }
        validate_subject_token(&topic)?;
        if payload.quorum == 0 || payload.quorum > self.config.voters.len() {
            return Err(ConsensusError::InvalidQuorum {
                requested: payload.quorum,
                available: self.config.voters.len(),
            });
        }
        if payload.timeout_seconds == 0 {
            return Err(ConsensusError::InvalidTimeout);
        }

        let proposer = normalize_name(&payload.proposer).unwrap_or_else(|| "unknown".to_string());
        let proposal_id = payload
            .proposal_id
            .as_deref()
            .map(str::trim)
            .filter(|id| !id.is_empty())
            .map(ToOwned::to_owned)
            .unwrap_or_else(|| format!("{topic}:{proposer}"));

        if self.decided.contains_key(&proposal_id) {
            debug!(proposal_id, "ignoring already decided proposal");
            return Ok(());
        }
        if self.proposals.contains_key(&proposal_id) {
            debug!(proposal_id, "ignoring duplicate active proposal");
            return Ok(());
        }

        let proposal = PendingProposal {
            topic,
            proposal_id: proposal_id.clone(),
            quorum: payload.quorum,
            timeout: Duration::from_secs(payload.timeout_seconds),
            created_at: Instant::now(),
            votes: BTreeMap::new(),
        };
        info!(
            proposal_id,
            proposer,
            topic = proposal.topic,
            quorum = proposal.quorum,
            evidence_len = payload.evidence.len(),
            "proposal accepted"
        );
        self.proposals.insert(proposal_id, proposal);
        Ok(())
    }

    /// Handles a raw vote JSON payload.
    ///
    /// # Errors
    ///
    /// Returns JSON or validation errors; unknown proposals/voters are ignored
    /// and return `Ok(None)`.
    pub fn handle_vote_bytes(
        &mut self,
        subject: &str,
        bytes: &[u8],
    ) -> Result<Option<ResolutionPayload>, ConsensusError> {
        let payload = serde_json::from_slice::<VotePayload>(bytes)?;
        self.handle_vote(subject, payload)
    }

    /// Handles a typed vote payload.
    ///
    /// # Errors
    ///
    /// Returns an error if a referenced topic is not NATS-safe.
    pub fn handle_vote(
        &mut self,
        subject: &str,
        payload: VotePayload,
    ) -> Result<Option<ResolutionPayload>, ConsensusError> {
        let Some(proposal_id) = self.resolve_proposal_id(&payload) else {
            debug!("vote ignored without active proposal");
            return Ok(None);
        };
        let voter = payload
            .voter
            .as_deref()
            .and_then(normalize_name)
            .or_else(|| normalize_name(&vote_subject_suffix(&self.config, subject)));
        let Some(voter) = voter else {
            warn!(proposal_id, "vote ignored without voter");
            return Ok(None);
        };
        if !self.config.voters.contains(&voter) {
            warn!(proposal_id, voter, "vote ignored from unknown voter");
            return Ok(None);
        }

        let Some(proposal) = self.proposals.get_mut(&proposal_id) else {
            debug!(proposal_id, "vote ignored for inactive proposal");
            return Ok(None);
        };
        if proposal.votes.contains_key(&voter) {
            debug!(proposal_id, voter, "duplicate vote ignored");
            return Ok(None);
        }

        proposal.votes.insert(
            voter,
            VoteRecord {
                decision: payload.decision,
            },
        );

        if proposal.yes_count() >= proposal.quorum {
            return Ok(Some(self.resolve(
                &proposal_id,
                ResolutionDecision::Bind,
                None,
            )));
        }
        if proposal.max_possible_yes(self.config.voters.len()) < proposal.quorum {
            return Ok(Some(self.resolve(
                &proposal_id,
                ResolutionDecision::NoBind,
                Some("quorum can no longer be reached with remaining eligible voters"),
            )));
        }
        Ok(None)
    }

    /// Resolves timed-out proposals and returns payloads that should be published.
    pub fn expire_due(&mut self) -> Vec<ResolutionPayload> {
        let now = Instant::now();
        let expired: Vec<String> = self
            .proposals
            .iter()
            .filter(|(_, proposal)| now.duration_since(proposal.created_at) >= proposal.timeout)
            .map(|(proposal_id, _)| proposal_id.clone())
            .collect();

        expired
            .into_iter()
            .map(|proposal_id| {
                self.resolve(
                    &proposal_id,
                    ResolutionDecision::NoQuorum,
                    Some("timeout expired without quorum"),
                )
            })
            .collect()
    }

    fn resolve_proposal_id(&self, payload: &VotePayload) -> Option<String> {
        if let Some(proposal_id) = payload.proposal_id.as_deref().map(str::trim) {
            if self.proposals.contains_key(proposal_id) {
                return Some(proposal_id.to_string());
            }
        }
        if let Some(topic) = payload.topic.as_deref().map(str::trim) {
            if validate_subject_token(topic).is_err() {
                return None;
            }
            return self.proposals.iter().find_map(|(proposal_id, proposal)| {
                (proposal.topic == topic).then(|| proposal_id.clone())
            });
        }
        None
    }

    fn resolve(
        &mut self,
        proposal_id: &str,
        decision: ResolutionDecision,
        reason: Option<&str>,
    ) -> ResolutionPayload {
        let proposal = self
            .proposals
            .remove(proposal_id)
            .expect("resolve is only called for active proposals");
        let payload = proposal.to_resolution(decision, reason);
        self.decided
            .insert(payload.proposal_id.clone(), payload.clone());
        payload
    }
}

/// Runs the NATS consensus service until the supplied shutdown future resolves.
///
/// # Errors
///
/// Returns an error when NATS subscriptions or publishes fail, or when a
/// subscription closes unexpectedly.
pub async fn run_consensus_service<F>(
    client: Client,
    config: ConsensusConfig,
    shutdown: F,
) -> Result<(), ConsensusError>
where
    F: Future<Output = ()>,
{
    run_consensus_service_inner(client, config, None, shutdown).await
}

/// Runs the NATS consensus service and signals when subscriptions are active.
///
/// # Errors
///
/// Returns an error when NATS subscriptions, subscription flush, or publishes
/// fail, or when a subscription closes unexpectedly.
pub async fn run_consensus_service_with_ready<F>(
    client: Client,
    config: ConsensusConfig,
    ready: oneshot::Sender<()>,
    shutdown: F,
) -> Result<(), ConsensusError>
where
    F: Future<Output = ()>,
{
    run_consensus_service_inner(client, config, Some(ready), shutdown).await
}

async fn run_consensus_service_inner<F>(
    client: Client,
    config: ConsensusConfig,
    ready: Option<oneshot::Sender<()>>,
    shutdown: F,
) -> Result<(), ConsensusError>
where
    F: Future<Output = ()>,
{
    let mut proposal_sub = client
        .subscribe(config.propose_subject())
        .await
        .map_err(|err| ConsensusError::NatsSubscribe(err.to_string()))?;
    let mut vote_sub = client
        .subscribe(config.vote_subject_wildcard())
        .await
        .map_err(|err| ConsensusError::NatsSubscribe(err.to_string()))?;
    client
        .flush()
        .await
        .map_err(|err| ConsensusError::NatsFlush(err.to_string()))?;
    if let Some(ready) = ready {
        let _ = ready.send(());
    }
    let mut shutdown: Pin<Box<F>> = Box::pin(shutdown);
    let mut ticker = interval(config.poll_interval());
    let mut engine = ConsensusEngine::new(config.clone());

    loop {
        tokio::select! {
            _ = &mut shutdown => return Ok(()),
            _ = ticker.tick() => {
                for resolution in engine.expire_due() {
                    publish_resolution(&client, &config, &resolution).await?;
                }
            }
            maybe_msg = proposal_sub.next() => {
                let msg = maybe_msg.ok_or(ConsensusError::NatsSubscriptionClosed("proposal"))?;
                if let Err(err) = engine.handle_proposal_bytes(&msg.payload) {
                    warn!(error = %err, subject = msg.subject.as_str(), "proposal ignored");
                }
            }
            maybe_msg = vote_sub.next() => {
                let msg = maybe_msg.ok_or(ConsensusError::NatsSubscriptionClosed("vote"))?;
                match engine.handle_vote_bytes(msg.subject.as_str(), &msg.payload) {
                    Ok(Some(resolution)) => publish_resolution(&client, &config, &resolution).await?,
                    Ok(None) => {}
                    Err(err) => warn!(error = %err, subject = msg.subject.as_str(), "vote ignored"),
                }
            }
        }
    }
}

/// Publishes a consensus resolution to its bind subject.
///
/// # Errors
///
/// Returns a NATS publish error if the message cannot be sent.
pub async fn publish_resolution(
    client: &Client,
    config: &ConsensusConfig,
    resolution: &ResolutionPayload,
) -> Result<(), ConsensusError> {
    let subject = config.bind_subject(&resolution.topic);
    let payload = serde_json::to_vec(resolution)?;
    client
        .publish(subject, payload.into())
        .await
        .map_err(|err| ConsensusError::NatsPublish(err.to_string()))?;
    info!(
        proposal_id = resolution.proposal_id,
        topic = resolution.topic,
        decision = resolution.decision.as_str(),
        "resolution published"
    );
    Ok(())
}

fn default_quorum() -> usize {
    3
}

fn default_timeout_seconds() -> u64 {
    120
}

fn normalize_voters(voters: impl IntoIterator<Item = String>) -> BTreeSet<String> {
    voters
        .into_iter()
        .filter_map(|voter| normalize_name(&voter))
        .collect()
}

fn normalize_name(value: &str) -> Option<String> {
    let normalized = value.trim().to_ascii_lowercase();
    (!normalized.is_empty()).then_some(normalized)
}

fn validate_namespace(namespace: &str) -> Result<(), ConsensusError> {
    let valid = namespace
        .split('.')
        .all(|segment| !segment.is_empty() && is_subject_token(segment));
    if valid {
        Ok(())
    } else {
        Err(ConsensusError::InvalidNamespace(namespace.to_string()))
    }
}

fn validate_subject_token(token: &str) -> Result<(), ConsensusError> {
    if is_subject_token(token) {
        Ok(())
    } else {
        Err(ConsensusError::InvalidTopic(token.to_string()))
    }
}

fn is_subject_token(token: &str) -> bool {
    !token.is_empty()
        && token
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b':'))
}

fn vote_subject_suffix(config: &ConsensusConfig, subject: &str) -> String {
    let prefix = format!("{}.crew.consensus.vote.", config.namespace());
    subject
        .strip_prefix(&prefix)
        .unwrap_or_default()
        .to_string()
}

fn now_rfc3339() -> String {
    OffsetDateTime::now_utc()
        .format(&Rfc3339)
        .unwrap_or_else(|_| "1970-01-01T00:00:00Z".to_string())
}

#[derive(Debug, Clone)]
struct PendingProposal {
    topic: String,
    proposal_id: String,
    quorum: usize,
    timeout: Duration,
    created_at: Instant,
    votes: BTreeMap<String, VoteRecord>,
}

impl PendingProposal {
    fn yes_count(&self) -> usize {
        self.count(VoteDecision::Yes)
    }

    fn no_count(&self) -> usize {
        self.count(VoteDecision::No)
    }

    fn abstain_count(&self) -> usize {
        self.count(VoteDecision::Abstain)
    }

    fn count(&self, decision: VoteDecision) -> usize {
        self.votes
            .values()
            .filter(|record| record.decision == decision)
            .count()
    }

    fn max_possible_yes(&self, eligible_voters: usize) -> usize {
        self.yes_count() + eligible_voters.saturating_sub(self.votes.len())
    }

    fn to_resolution(
        &self,
        decision: ResolutionDecision,
        reason: Option<&str>,
    ) -> ResolutionPayload {
        let wire = ResolutionDecisionWire::new(decision);
        ResolutionPayload {
            proposal_id: self.proposal_id.clone(),
            topic: self.topic.clone(),
            decision: wire.clone(),
            quorum: self.quorum,
            yes_votes: self.yes_count(),
            no_votes: self.no_count(),
            abstain_votes: self.abstain_count(),
            votes_received: self.votes.len(),
            voters: self.votes.keys().cloned().collect(),
            state: wire,
            bound_at: now_rfc3339(),
            reason: reason.map(ToOwned::to_owned),
        }
    }
}

#[derive(Debug, Clone)]
struct VoteRecord {
    decision: VoteDecision,
}

#[cfg(test)]
mod tests {
    use super::*;

    fn config() -> ConsensusConfig {
        ConsensusConfig::new(
            "testnova",
            ["iris", "zap", "forge", "synergy"]
                .into_iter()
                .map(ToOwned::to_owned),
        )
        .expect("test config should be valid")
        .with_poll_interval(Duration::from_millis(5))
    }

    fn proposal(quorum: usize, timeout_seconds: u64) -> ProposalPayload {
        ProposalPayload {
            topic: "deploy-rust-bridge-v1".to_string(),
            proposer: "synergy".to_string(),
            proposal_id: Some("prop-001".to_string()),
            evidence: "proof".to_string(),
            quorum,
            timeout_seconds,
        }
    }

    fn vote(voter: &str, decision: VoteDecision) -> VotePayload {
        VotePayload {
            proposal_id: Some("prop-001".to_string()),
            topic: None,
            voter: Some(voter.to_string()),
            decision,
            reasoning: "aligned".to_string(),
        }
    }

    #[test]
    fn binds_when_quorum_is_reached() {
        let mut engine = ConsensusEngine::new(config());
        engine
            .handle_proposal(proposal(2, 5))
            .expect("proposal should be accepted");
        assert!(engine
            .handle_vote(
                "testnova.crew.consensus.vote.iris",
                vote("iris", VoteDecision::Yes)
            )
            .expect("vote should be valid")
            .is_none());
        let resolution = engine
            .handle_vote(
                "testnova.crew.consensus.vote.zap",
                vote("zap", VoteDecision::Yes),
            )
            .expect("vote should be valid")
            .expect("quorum should bind");

        assert_eq!(resolution.decision.as_str(), "BIND");
        assert_eq!(resolution.yes_votes, 2);
        assert_eq!(
            resolution.voters,
            vec!["iris".to_string(), "zap".to_string()]
        );
        assert_eq!(engine.active_count(), 0);
        assert!(engine.decided().contains_key("prop-001"));
    }

    #[test]
    fn no_bind_when_quorum_becomes_impossible() {
        let mut engine = ConsensusEngine::new(config());
        engine
            .handle_proposal(proposal(3, 5))
            .expect("proposal should be accepted");
        assert!(engine
            .handle_vote(
                "testnova.crew.consensus.vote.iris",
                vote("iris", VoteDecision::No),
            )
            .expect("vote should be valid")
            .is_none());
        let resolution = engine
            .handle_vote(
                "testnova.crew.consensus.vote.zap",
                vote("zap", VoteDecision::No),
            )
            .expect("vote should be valid")
            .expect("quorum should be impossible");

        assert_eq!(resolution.decision.as_str(), "NO_BIND");
        assert_eq!(resolution.no_votes, 2);
        assert_eq!(resolution.abstain_votes, 0);
    }

    #[test]
    fn timeout_yields_no_quorum() {
        let mut engine = ConsensusEngine::new(config());
        engine
            .handle_proposal(proposal(3, 1))
            .expect("proposal should be accepted");
        engine
            .handle_vote(
                "testnova.crew.consensus.vote.iris",
                vote("iris", VoteDecision::Yes),
            )
            .expect("vote should be valid");

        std::thread::sleep(Duration::from_millis(1_050));
        let resolutions = engine.expire_due();

        assert_eq!(resolutions.len(), 1);
        assert_eq!(resolutions[0].decision.as_str(), "NO_QUORUM");
        assert_eq!(resolutions[0].yes_votes, 1);
    }

    #[test]
    fn rejects_invalid_quorum() {
        let mut engine = ConsensusEngine::new(config());
        let err = engine
            .handle_proposal(proposal(9, 5))
            .expect_err("quorum above voter count should fail");

        assert!(matches!(err, ConsensusError::InvalidQuorum { .. }));
    }

    #[test]
    fn ignores_unknown_and_duplicate_voters() {
        let mut engine = ConsensusEngine::new(config());
        engine
            .handle_proposal(proposal(2, 5))
            .expect("proposal should be accepted");
        assert!(engine
            .handle_vote(
                "testnova.crew.consensus.vote.unknown",
                vote("unknown", VoteDecision::Yes),
            )
            .expect("unknown voter should be ignored")
            .is_none());
        assert!(engine
            .handle_vote(
                "testnova.crew.consensus.vote.iris",
                vote("iris", VoteDecision::Yes)
            )
            .expect("vote should be valid")
            .is_none());
        assert!(engine
            .handle_vote(
                "testnova.crew.consensus.vote.iris",
                vote("iris", VoteDecision::No)
            )
            .expect("duplicate vote should be ignored")
            .is_none());
    }

    #[test]
    fn accepts_voter_from_subject_suffix() {
        let mut engine = ConsensusEngine::new(config());
        engine
            .handle_proposal(proposal(1, 5))
            .expect("proposal should be accepted");
        let mut payload = vote("", VoteDecision::Yes);
        payload.voter = None;
        let resolution = engine
            .handle_vote("testnova.crew.consensus.vote.iris", payload)
            .expect("vote should be valid")
            .expect("subject voter should bind");

        assert_eq!(resolution.decision.as_str(), "BIND");
        assert_eq!(resolution.voters, vec!["iris".to_string()]);
    }
}
