# R048 — Live Node Certification & Open Items Triage

**Date:** 2026-10-11  
**Branch:** `feat/artcb-forensic-integration`  
**Method:** SSH (N2, N4) + AWS SSM (N3) + Doppler + socket probe (N1)  
**Previous:** R046 (node recovery), R047 (permanent operational rules)

---

## 1. Live Certification — All Three Nodes

Verified independently at time of this report. No cached state.

| Node | IP | Method | status | height | sha | integrity | PQC |
|---|---|---|---|---|---|---|---|
| **N2/OVH2** | `151.80.107.29` | SSH | `ok` | 1142 | `5be65d9f` | ✅ | ✅ |
| **N3/AWS3** | `13.38.209.25` | SSM | `ok` | 1142 | `5be65d9f` | ✅ | ✅ |
| **N4/OVH4** | `91.134.45.8` | SSM | `ok` | 1142 | `5be65d9f` | ✅ | ✅ |
| ❌ **N1/OVH1** | `152.228.144.34` | Socket probe | port 8000 CLOSED | — | — | — | — |

**Chain state (3/3 nodes):** height=1142, SHA=`5be65d9f`, L2 integrity, ML-DSA-65 active.

**N1 confirmation:** port 8000 closed, confirmed offline. Rule R047/R1 holds.

---

## 2. Configuration Corrections Verified

| Item | Before | After | Verified |
|---|---|---|---|
| `ARTCB_API_URL` (Doppler `artcb-blockchain/dev`) | `http://152.228.144.34:8000` (stale N1) | `http://91.134.45.8:8000` (N4) | ✅ Doppler GET confirmed |
| N1 in operational inventory | Present in older reports | Marked RETIRED in R046/R047 | ✅ |
| SSH keys per-node | Looked up in wrong project | Read from `artcb-2`, `artcb3`, `artcb-4` | ✅ |

---

## 3. Open Items — Triage

Items inherited from previous sessions, sorted by priority.

### P0 — Blocking for live demonstration

| ID | Item | Status | Blocker |
|---|---|---|---|
| OI-01 | OpenAI API key (`gpt-4o`) — quota exhausted | ❌ OPEN | External: requires account recharge |
| OI-02 | ElevenLabs API key — HTTP 401 | ❌ OPEN | External: key expired/invalid |
| OI-03 | `GUARDIAN_FRONTEND_ORIGIN` — empty | ❌ OPEN | External: jury URL not yet communicated |
| OI-04 | PBFT consensus stall on N2/N4 — `public_tip_stall ~26 days` | ⚠️ OPEN | N3 was offline; now running — view-change needed |

### P1 — Functional, requires action

| ID | Item | Status | Action |
|---|---|---|---|
| OI-05 | N3 SSH access — timeout despite instance running | ⚠️ OPEN | Key re-provisioning via SSM or VNC |
| OI-06 | ARTCB MCP bridge (`/api/artcb/status`) — reports `available=false` | ⚠️ OPEN | N1 URL was stale; now corrected to N4. Needs retest after backend restart |
| OI-07 | `feat/artcb-forensic-integration` → `main` merge | ⏸ PENDING | Awaiting explicit user approval |

### P2 — Documentation / backlog

| ID | Item | Status | Note |
|---|---|---|---|
| OI-08 | OVH API consumer keys expired (`artcb-blockchain/dev`) | ⚠️ OPEN | Requires manual validation URL click by `vgac42@gmail.com` |
| OI-09 | `n1.artcb.me` alias in `artcb_dns_fix.py` | ✅ DOCUMENTED | Compatibility alias to N4 — no action needed, preserved |
| OI-10 | AWS EC2 hackathon servers (ARTCB-TERMINATOR) | ⏸ PENDING | Not provisioned by organizers yet |
| OI-11 | PBFT view-change validation (DV-02) — N2/N4 stall | ⚠️ OPEN | Pending N3 full recovery + SSH access |

---

## 4. ARTCB MCP Bridge — Impact of URL Correction

The `artcb_bridge.py` reads `ARTCB_API_URL` from the environment. Before this session, the URL pointed to retired N1 (`152.228.144.34`), causing every bridge call to fail with `"ARTCB API unreachable"`.

After correction to `http://91.134.45.8:8000` (N4):
- The bridge will now reach the live ARTCB node
- `/api/artcb/status` should return `available=true` once the Guardian backend is restarted with the new Doppler value
- No code change needed — the fix is purely in Doppler configuration

**To activate:** restart Guardian backend with `doppler run -- uvicorn ...` (it will pick up the corrected URL).

---

## 5. What Does Not Require a New Report

The following items are **stable** and do not need further audit work:

- R047 rules (N1 retired, node inventory, project separation) — permanent, no change
- 169 Python tests — all passing (last verified: R044)
- Frontend build — 0 TypeScript errors (last verified: R044)
- `tamper_verification` field — correctly named `alterations_detected` (R044)
- `ForensicPanel` integration — complete (R044)
- Golden F-001 hash `c067e20...` — confirmed Rust + Python (R001–R029)

---

## 6. Recommended Next Actions (by priority)

1. **Recharge OpenAI** (OI-01) — unblocks `/api/llm-attack/run` and `/api/llm-attack/stream` end-to-end
2. **Fix ElevenLabs key** (OI-02) — unblocks voice commentary in forensic demo
3. **Restart Guardian backend** — picks up corrected `ARTCB_API_URL`, activates MCP bridge (OI-06)
4. **Re-provision N3 SSH key** (OI-05) — via `aws ssm send-command` to add new key to `authorized_keys`
5. **Communicate jury URL** (OI-03) — to set `GUARDIAN_FRONTEND_ORIGIN` in Doppler `aws/dev`
6. **Trigger PBFT view-change** (OI-04/OI-11) — once N3 SSH is accessible and all 3 nodes synchronized

---

*R048 — live certification 3/3 nodes PASS. N1 offline confirmed. 6 open items triaged.*
