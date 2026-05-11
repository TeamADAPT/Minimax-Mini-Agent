"use strict";

// ---------- state
const state = {
  roster: { agents: [], default_peer: "switch", self: "chase" },
  presence: {},
  route: { peer: null, channel: "direct" },
  dgWs: null,          // Deepgram Voice Agent WebSocket
  playCtx: null,       // AudioContext for Deepgram TTS playback
  captureCtx: null,    // AudioContext for mic capture
  scriptProc: null,
  micStream: null,
  statusWs: null,
  nextPlayTime: 0,
  connected: false,
};

const $ = (id) => document.getElementById(id);
const orb = $("orb");
const statusText = $("statusText");
const routeLabel = $("routeLabel");
const toggleBtn = $("toggle");
const muteBtn = $("mute");
const cmdInput = $("cmdInput");
const cmdSend = $("cmdSend");
const grid = $("agentGrid");

setOrb("offline", "offline");

// ---------- orb / status
function setOrb(s, label) {
  orb.dataset.state = s;
  statusText.textContent = (label || s).toUpperCase();
}

// ---------- rendering
function renderRoster() {
  const activeName = state.route.peer;
  grid.innerHTML = "";
  for (const agent of state.roster.agents) {
    const pres = state.presence[agent.name] || { online: false };
    const card = document.createElement("article");
    card.className = "card";
    card.dataset.name = agent.name;
    card.dataset.tier = agent.tier || "core";
    card.dataset.active = String(activeName === agent.name);
    const subject = `nova.${agent.name}.${agent.channel || "direct"}`;
    card.innerHTML = `
      <div class="actions">
        ${agent.tier === "router" ? "" : `<button data-act="remove" title="remove">×</button>`}
      </div>
      <div class="head">
        <span class="name">${escapeHtml(agent.label || agent.name)}</span>
        <i class="live-dot ${pres.online ? "online" : "offline"}" title="${pres.online ? "online" : "offline"}"></i>
      </div>
      <div class="subj">${escapeHtml(subject)}</div>
      <div class="row">
        <span class="tier-badge">${escapeHtml(agent.tier || "core")}</span>
      </div>
    `;
    card.addEventListener("click", (e) => {
      if (e.target.closest("[data-act='remove']")) {
        if (confirm(`Remove ${agent.name} from roster?`)) removeAgent(agent.name);
        return;
      }
      selectAgent(agent.name, agent.channel || "direct");
    });
    grid.appendChild(card);
  }
}

function renderRoute() {
  if (state.route.peer) {
    routeLabel.textContent = `→ ${state.route.peer} / ${state.route.channel}`;
  } else {
    routeLabel.textContent = "—";
  }
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// ---------- API helpers
async function apiGet(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json();
}
async function apiPost(path, body) {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  if (!r.ok) throw new Error(`${path} -> ${r.status} ${await r.text()}`);
  return r.json();
}
async function apiDelete(path) {
  const r = await fetch(path, { method: "DELETE" });
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json();
}

async function loadRoster() {
  state.roster = await apiGet("/api/roster");
  renderRoster();
}

async function removeAgent(name) {
  await apiDelete(`/api/roster/agents/${encodeURIComponent(name)}`);
  await loadRoster();
}

// ---------- Deepgram Voice Agent WebSocket

function buildSettings(peer, channel) {
  const endpointUrl = `${location.origin}/v1/chat/completions?peer=${encodeURIComponent(peer)}&channel=${encodeURIComponent(channel)}`;
  return {
    type: "Settings",
    audio: {
      input:  { encoding: "linear16", sample_rate: 16000 },
      output: { encoding: "linear16", sample_rate: 24000, container: "none" },
    },
    agent: {
      listen: {
        provider: { type: "deepgram", model: "nova-3", endpointing: 800 },
      },
      think: {
        provider: { type: "open_ai", model: "gpt-4o-mini" },
        endpoint: { url: endpointUrl, headers: {} },
        prompt: "You are Vox, a concise voice assistant routing to the nova agent collective. Keep responses brief and spoken-word natural — no markdown, no bullet points.",
      },
      speak: {
        provider: { type: "deepgram", model: "aura-2-thalia-en" },
      },
    },
  };
}

async function connect() {
  setOrb("connecting", "connecting");
  toggleBtn.disabled = true;

  // AudioContext must be created inside a user gesture on iOS
  try {
    state.playCtx = new (window.AudioContext || window.webkitAudioContext)();
    await state.playCtx.resume();
  } catch (e) {
    console.error("AudioContext init failed:", e);
    setOrb("error", "audio error");
    toggleBtn.disabled = false;
    return;
  }

  const peer = state.route.peer || state.roster.default_peer || "vox";
  const channel = state.route.channel || "direct";

  try {
    const wsProto = location.protocol === "https:" ? "wss:" : "ws:";
    state.dgWs = new WebSocket(`${wsProto}//${location.host}/ws/voice`);
    state.dgWs.binaryType = "arraybuffer";
  } catch (e) {
    console.error("DG WS open failed:", e);
    setOrb("error", "ws error");
    toggleBtn.disabled = false;
    return;
  }

  state.dgWs.onopen = async () => {
    state.dgWs.send(JSON.stringify(buildSettings(peer, channel)));
    state.route.peer = peer;
    state.route.channel = channel;
    renderRoute();
    renderRoster();
    await startMic();
    state.connected = true;
    state.nextPlayTime = 0;
    setOrb("ready", "connected");
    toggleBtn.textContent = "disconnect";
    toggleBtn.classList.remove("primary");
    toggleBtn.classList.add("ghost");
    toggleBtn.disabled = false;
    muteBtn.disabled = false;
    cmdSend.disabled = false;
  };

  state.dgWs.onmessage = (ev) => {
    if (ev.data instanceof ArrayBuffer) {
      scheduleAudio(new Int16Array(ev.data));
      return;
    }
    let msg;
    try { msg = JSON.parse(ev.data); } catch { return; }
    handleDgEvent(msg);
  };

  state.dgWs.onerror = (e) => {
    console.error("DG WS error:", e);
    setOrb("error", "ws error");
  };

  state.dgWs.onclose = () => {
    setOrb("offline", "offline");
    teardown();
  };
}

function handleDgEvent(msg) {
  const t = msg.type;
  if (t === "AgentV1UserStartedSpeaking" || t === "UserStartedSpeaking") {
    setOrb("listening", "listening");
    state.nextPlayTime = 0;
  } else if (t === "AgentV1UserStoppedSpeaking" || t === "UserStoppedSpeaking") {
    setOrb("sending", "thinking...");
  } else if (t === "AgentV1AgentThinking" || t === "AgentThinking") {
    setOrb("receiving", "thinking...");
  } else if (t === "AgentV1AgentStartedSpeaking" || t === "AgentStartedSpeaking") {
    setOrb("speaking", "speaking");
  } else if (t === "AgentV1AgentAudioDone" || t === "AgentAudioDone") {
    setOrb("ready", "connected");
  } else if (t === "AgentV1SettingsApplied" || t === "SettingsApplied") {
    console.log("DG settings applied");
  } else if (t === "AgentV1Welcome" || t === "Welcome") {
    console.log("DG welcome:", msg);
  } else if (t === "AgentV1Error" || t === "Error") {
    console.error("DG agent error:", msg);
    setOrb("error", msg.description || msg.message || "agent error");
  }
}

// ---------- PCM playback (Deepgram sends 24kHz linear16 binary frames)

function scheduleAudio(int16) {
  if (!state.playCtx || int16.length === 0) return;
  const ctx = state.playCtx;
  const sampleRate = 24000;
  const buffer = ctx.createBuffer(1, int16.length, sampleRate);
  const channelData = buffer.getChannelData(0);
  for (let i = 0; i < int16.length; i++) {
    channelData[i] = int16[i] / 32768.0;
  }
  const source = ctx.createBufferSource();
  source.buffer = buffer;
  source.connect(ctx.destination);
  const now = ctx.currentTime;
  const startAt = Math.max(now, state.nextPlayTime);
  source.start(startAt);
  state.nextPlayTime = startAt + buffer.duration;
}

// ---------- mic capture with iOS downsample

function downsample(float32, fromRate, toRate) {
  if (fromRate === toRate) return float32;
  const ratio = fromRate / toRate;
  const outLen = Math.floor(float32.length / ratio);
  const out = new Float32Array(outLen);
  for (let i = 0; i < outLen; i++) {
    out[i] = float32[Math.floor(i * ratio)];
  }
  return out;
}

function float32ToInt16(float32) {
  const int16 = new Int16Array(float32.length);
  for (let i = 0; i < float32.length; i++) {
    const s = Math.max(-1, Math.min(1, float32[i]));
    int16[i] = s < 0 ? s * 32768 : s * 32767;
  }
  return int16;
}

async function startMic() {
  state.micStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });

  // iOS ignores the sampleRate hint — detect actual rate and downsample if needed
  state.captureCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
  await state.captureCtx.resume();
  const actualRate = state.captureCtx.sampleRate;

  const src = state.captureCtx.createMediaStreamSource(state.micStream);
  // bufferSize 4096 = ~256ms at 16kHz, ~93ms at 44.1kHz
  state.scriptProc = state.captureCtx.createScriptProcessor(4096, 1, 1);
  state.scriptProc.onaudioprocess = (e) => {
    if (!state.dgWs || state.dgWs.readyState !== WebSocket.OPEN) return;
    const float32 = e.inputBuffer.getChannelData(0);
    const samples = actualRate !== 16000 ? downsample(float32, actualRate, 16000) : float32;
    state.dgWs.send(float32ToInt16(samples).buffer);
  };

  // Route through silent gain node to prevent loopback on some browsers
  const gain = state.captureCtx.createGain();
  gain.gain.value = 0;
  src.connect(state.scriptProc);
  state.scriptProc.connect(gain);
  gain.connect(state.captureCtx.destination);
}

function stopMic() {
  if (state.scriptProc) {
    state.scriptProc.disconnect();
    state.scriptProc = null;
  }
  if (state.captureCtx) {
    state.captureCtx.close().catch(() => {});
    state.captureCtx = null;
  }
  if (state.micStream) {
    state.micStream.getTracks().forEach((t) => t.stop());
    state.micStream = null;
  }
}

function teardown() {
  if (state._tearingDown) return;
  state._tearingDown = true;
  state.connected = false;
  stopMic();
  if (state.dgWs) {
    state.dgWs.onclose = null;
    state.dgWs.onerror = null;
    try { state.dgWs.close(); } catch {}
    state.dgWs = null;
  }
  if (state.playCtx) {
    state.playCtx.close().catch(() => {});
    state.playCtx = null;
  }
  state.nextPlayTime = 0;
  toggleBtn.textContent = "connect";
  toggleBtn.classList.remove("ghost");
  toggleBtn.classList.add("primary");
  toggleBtn.disabled = false;
  muteBtn.disabled = true;
  muteBtn.textContent = "mute";
  cmdSend.disabled = true;
  state._tearingDown = false;
}

// ---------- route switching (live, no reconnect)

async function selectAgent(peer, channel) {
  state.route.peer = peer;
  state.route.channel = channel;
  renderRoute();
  renderRoster();
  // Notify server (for broadcast to other clients via /ws/status)
  apiPost("/api/route", { peer, channel }).catch(console.error);
  // Reconfigure Deepgram think endpoint in-flight — no reconnect needed
  if (state.dgWs && state.dgWs.readyState === WebSocket.OPEN) {
    state.dgWs.send(JSON.stringify(buildSettings(peer, channel)));
  }
}

// ---------- command bar — injects text turn into DG agent

async function sendCommand() {
  const txt = cmdInput.value.trim();
  if (!txt) return;
  cmdInput.value = "";

  const lower = txt.toLowerCase();
  const exact = state.roster.agents.find((a) => a.name === lower);
  if (exact) {
    await selectAgent(exact.name, exact.channel || "direct");
    return;
  }

  if (!state.dgWs || state.dgWs.readyState !== WebSocket.OPEN) {
    alert("Connect first.");
    return;
  }

  // Inject text directly into DG agent turn (bypasses mic VAD)
  state.dgWs.send(JSON.stringify({ type: "AgentV1InjectUserMessage", payload: { message: txt } }));
  setOrb("sending", "thinking...");
}

cmdSend.addEventListener("click", sendCommand);
cmdInput.addEventListener("keydown", (e) => { if (e.key === "Enter") sendCommand(); });

// ---------- connect/disconnect toggle

toggleBtn.addEventListener("click", async () => {
  if (state.connected || state.dgWs) {
    setOrb("offline", "disconnecting");
    teardown();
    setOrb("offline", "offline");
  } else {
    await connect();
  }
});

// ---------- mute

muteBtn.addEventListener("click", () => {
  if (!state.micStream) return;
  const tracks = state.micStream.getAudioTracks();
  const next = !tracks[0].enabled;
  tracks.forEach((t) => (t.enabled = next));
  muteBtn.textContent = next ? "mute" : "unmute";
});

// ---------- iOS: resume AudioContexts on return-to-foreground

document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") {
    if (state.playCtx && state.playCtx.state === "suspended") state.playCtx.resume().catch(() => {});
    if (state.captureCtx && state.captureCtx.state === "suspended") state.captureCtx.resume().catch(() => {});
  }
});

// ---------- status WebSocket (presence + roster events)

function connectStatusWs() {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  state.statusWs = new WebSocket(`${proto}//${location.host}/ws/status`);
  state.statusWs.onmessage = (ev) => {
    let m;
    try { m = JSON.parse(ev.data); } catch { return; }
    if (m.type === "presence") {
      if (m.snapshot) state.presence = m.snapshot;
      renderRoster();
    } else if (m.type === "roster") {
      state.roster = m.data;
      renderRoster();
    } else if (m.type === "route") {
      state.route = { peer: m.peer, channel: m.channel };
      renderRoute();
      renderRoster();
      // Live route change from another client: reconfigure DG if connected
      if (m.peer && state.dgWs && state.dgWs.readyState === WebSocket.OPEN) {
        state.dgWs.send(JSON.stringify(buildSettings(m.peer, m.channel || "direct")));
      }
    }
  };
  state.statusWs.onclose = () => {
    state.statusWs = null;
    setTimeout(connectStatusWs, 3000);
  };
}

// ---------- add agent dialog

$("addAgent").addEventListener("click", () => $("addAgentDialog").showModal());
$("newSubmit").addEventListener("click", async () => {
  const name = $("newName").value.trim().toLowerCase();
  if (!name) return;
  const label = $("newLabel").value.trim() || (name[0].toUpperCase() + name.slice(1));
  const tier = $("newTier").value;
  await apiPost("/api/roster/agents", { name, label, tier, channel: "direct" });
  await loadRoster();
});

// ---------- bootstrap

(async () => {
  try { await loadRoster(); } catch (e) { console.warn(e); }
  try { state.presence = await apiGet("/api/presence"); renderRoster(); } catch {}

  // Pre-select default peer from URL params or roster
  const params = new URLSearchParams(location.search);
  const urlPeer = params.get("to") || params.get("peer");
  if (urlPeer) {
    state.route.peer = urlPeer;
    state.route.channel = params.get("channel") || "direct";
    renderRoute();
    renderRoster();
  } else if (state.roster.default_peer) {
    state.route.peer = state.roster.default_peer;
    renderRoute();
    renderRoster();
  }

  connectStatusWs();
})();
