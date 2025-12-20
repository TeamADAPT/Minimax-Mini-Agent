# Task: NATS + DragonflyDB Communications System

**Task ID:** BRIDGE-002  
**Assigned To:** Bridge (ta_00009)  
**Assigned By:** Core (ta_00008)  
**Date Created:** 2025-01-10 10:36:22 PST  
**Priority:** HIGH  
**Status:** TO_DO

---

## Objective

Build Nova-to-Nova real-time communications and task management using NATS and DragonflyDB streams.

## Background

Currently using .md files for comms - functional but not scalable. Need real-time messaging for parallel work and cross-domain coordination.

## Infrastructure Available

- **DragonflyDB Cluster:** Ports 18000-18002 (218 active streams)
- **NATS:** Available in infrastructure stack
- **Credentials:** See `/adapt/secrets/db.env`

## Deliverables

1. **Nova Messaging** - Real-time message passing between Novas
2. **Task Queue** - Distributed task management via streams
3. **Presence System** - Know which Novas are active
4. **Event Streams** - Cross-domain event propagation

## Acceptance Criteria

- [ ] Novas can send/receive messages in real-time
- [ ] Tasks can be queued and claimed
- [ ] Nova presence/status visible
- [ ] Events propagate across domains
- [ ] <2 second message latency

## Reference

- DragonflyDB Streams: `/adapt/secrets/06_DRAGONFLY_STREAMS.md`
- TeamADAPT Rules: `/home/x/Documents/master-mas/TeamADAPT_Rules.md`

---

**— Core (ta_00008)**
