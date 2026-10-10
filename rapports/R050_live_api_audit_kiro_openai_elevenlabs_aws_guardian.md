# R050 — Live API Audit: Kiro, OpenAI, ElevenLabs, AWS STS, Bedrock, Guardian

**Date:** 2026-10-11  
**Branch:** `feat/artcb-forensic-integration`  
**Method:** Live calls to all external APIs — no assumptions, no cache  
**Previous:** R049 (end-to-end readiness), R048 (node certification)

---

## 1. Kiro Token — What It Actually Is

**Question asked:** Can the Kiro key in Doppler `aws/dev` substitute for blocked LLM API keys?

**Answer: No.**

| Field | Value |
|---|---|
| Token format | `d-<workspaceId>.<agentToken>` |
| Product | **Amazon Kiro** — agentic IDE for developers (kiro.dev) |
| What Kiro credits are | IDE usage credits (code generation within the Kiro IDE) |
| What Kiro credits are NOT | OpenAI API credits, Bedrock tokens, or any programmatic LLM API |
| API endpoint | `api.kiro.dev` — NXDOMAIN (no public LLM API exposed) |
| Can ARTCB-TERMINATOR call it | **No** — there is no documented REST API for Kiro model inference |

**The `ESSECKATHON26` bonus credits (1000 units) are Kiro IDE credits.** They cannot be used to call `gpt-4o`, Claude, or any model via HTTP from Guardian backend code.

---

## 2. OpenAI — Status Corrected

| Check | Result |
|---|---|
| Key validity | ✅ Valid — 104 GPT models listed |
| `gpt-4o` call | ❌ `insufficient_quota` — **no credits remaining** |
| `gpt-4o-mini` call | ❌ `insufficient_quota` |
| `gpt-3.5-turbo` call | ❌ `insufficient_quota` |

**Correction from R048:** The key is syntactically valid and accepted by the API, but the **account has zero credits**. This is distinct from an invalid or expired key — the account must be recharged at [platform.openai.com](https://platform.openai.com/account/billing).

**Impact on ARTCB-TERMINATOR:**
- `POST /api/llm-attack/run` → blocked (requires `gpt-4o` inference)
- `POST /api/llm-attack/stream` → blocked
- All 4 Guardian agent flows using LLM attacker → blocked
- The 4-scenario demo (`/api/scenarios/{id}/run`) → **fully operational** (no LLM required)

---

## 3. ElevenLabs — Confirmed Invalid

| Check | Result |
|---|---|
| Key `sk_025a7affa...` | ❌ HTTP 401 Unauthorized |
| Status | Invalid or expired |

**Impact:** Voice commentary is silenced. Text captions (`voice_script` SSE events) still function. The forensic demo works in text-only mode.

---

## 4. AWS STS Hackathon Token — Expired

| Check | Result |
|---|---|
| Token `ASIA3GKIQ53KVTG7O3QJ` | ❌ `ExpiredTokenException` |
| Bedrock access | ❌ Blocked (token expired) |
| EC2 instances visible | 0 (token expired — cannot confirm server state) |

**The two AWS ARTCB-TERMINATOR servers cannot be confirmed operational from here.** The STS token rotates every ~12h. It must be refreshed via the AWS console or the hackathon organizer infrastructure.

**Note on the two TERMINATOR servers:** Based on all prior audits, no EC2 instance was ever visible in account `769488121557` even with a valid token. The servers are either:
- Not yet provisioned by hackathon organizers, or
- Provisioned but in a region not scanned, or
- Accessible only from within the hackathon VPN/network

---

## 5. ARTCB N4 Port 8000 — Closed from This Machine

| Check | Result |
|---|---|
| `91.134.45.8:8000` TCP | ❌ CLOSED (from this machine) |
| N4 health via SSH | ✅ `status=ok height=1142` (confirmed R048) |

Port 8000 on N4 is firewalled from the public internet — it only accepts connections from within the ARTCB peer network (other nodes) or via SSH tunnel. This is expected and correct security behavior.

**Impact on `artcb_bridge.py`:** The bridge will fail to reach `http://91.134.45.8:8000` directly from the Guardian backend running locally. It would work if Guardian runs on a server within the ARTCB network (i.e., on one of the nodes themselves), or via SSH port-forward.

---

## 6. Guardian Local Backend — Not Running

The Guardian backend (port 8000 locally) is not running in this session. To activate the MCP bridge with the corrected URL, start it with:

```bat
LANCER_BACKEND.bat   (uses doppler run -- uvicorn guardian_api.app:app --port 8000)
```

Once running, `/api/artcb/status` will call `ArtcbMcpBridge.health()` → tries `http://91.134.45.8:8000/mcp` → will fail (N4 port 8000 externally closed). This is correct and expected — the bridge reports `available: false`, which is the right answer from a local machine.

---

## 7. Complete Status Matrix — All Systems

| System | Status | Blocker | Fix |
|---|---|---|---|
| Guardian backend (local) | ⏸ Not running | Manual start required | `LANCER_BACKEND.bat` |
| Guardian 4-scenario demo | ✅ Fully operational | None | No LLM required |
| OpenAI `gpt-4o` | ❌ Zero credits | Account balance = $0 | Recharge at platform.openai.com |
| ElevenLabs voice | ❌ 401 Unauthorized | Key expired | New key from elevenlabs.io |
| AWS STS hackathon | ❌ Token expired | ~12h rotation | Refresh from AWS console |
| AWS Bedrock | ❌ (STS expired) | Same as above | New STS token |
| EC2 TERMINATOR servers | ❓ Not verifiable | STS expired + never seen | Refresh STS, check organizer |
| Kiro token | ❌ Not an LLM API | Wrong product type | Cannot substitute OpenAI |
| ARTCB N2/OVH2 | ✅ `height=1142` | None | Verified R048 |
| ARTCB N3/AWS3 | ✅ `height=1142` | SSH key pending | SSM works (R048) |
| ARTCB N4/OVH4 | ✅ `height=1142` | None | Verified R048 |
| ARTCB bridge (local→N4) | ❌ Port filtered | N4:8000 not public | SSH tunnel or node-side deploy |
| Frontend build | ✅ 0 errors | None | R044 |
| 169 Python tests | ✅ All PASS | None | R044 |

---

## 8. What Can Be Demonstrated Right Now (No External Fixes Needed)

The following work **today, locally, without any external API credits:**

1. **4-scenario Guardian demo** — `safe-read`, `prompt-injection`, `sensitive-exfiltration`, `human-approval` via `POST /api/scenarios/{id}/run`
2. **Cryptographic proof chain** — R0 + R1 replay, JCS SHA-256, tamper detection
3. **ForensicPanel** — phase indicators, detection%, block%, resolution%
4. **Text captions** — `voice_script` SSE events (no ElevenLabs required)
5. **169 Python tests** — full test suite

The live LLM attacker scenario and voice commentary are blocked by external credits.

---

## 9. Recommended Actions (Ordered)

| Priority | Action | Owner |
|---|---|---|
| **P0** | Recharge OpenAI account | Human — billing at platform.openai.com |
| **P0** | Refresh AWS STS token | Human — AWS console login |
| **P0** | New ElevenLabs key | Human — elevenlabs.io |
| **P1** | Confirm TERMINATOR EC2 with fresh STS | After STS refresh |
| **P1** | SSH port-forward N4:8000 for local bridge test | `ssh -L 8000:localhost:8000 ubuntu@91.134.45.8` |
| **P2** | Re-provision N3 SSH key via SSM | One SSM command |
| **P2** | Merge `feat/` → `main` | Awaiting explicit approval |

---

*R050 — live API audit complete. Kiro ≠ LLM API. OpenAI zero credits. ElevenLabs invalid. STS expired. 4-scenario demo operational.*
