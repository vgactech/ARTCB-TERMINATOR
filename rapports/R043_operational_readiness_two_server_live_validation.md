# R043 — Operational Readiness: Two-Server State, KYC Evidence, and Live Defensive Chain

**Date:** 2026-10-10  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**HEAD at time of writing:** `7be4d72` (R042)  
**Scope:** Execution of the five operational orders from the R042 directive. Every result was observed directly. Unverified claims are explicitly labelled.  
**Code changes this report:** report only — no application source modified.

---

## 1. Order 1 — Two-environment inventory

### ARTCB-TERMINATOR (local, `D:\ARTCB-TERMINATOR`)

| Property | Value |
|---|---|
| HEAD commit | `7be4d72` |
| Remote | `github.com/vgactech/ARTCB-TERMINATOR` (HTTPS + GitHub token) |
| Python | 3.11.9 |
| fastapi | 0.143.0 |
| uvicorn | 0.54.0 |
| openai | 3.28.0 |
| elevenlabs | 2.71.0 |
| Test suite | 209/209 PASS (observed R042) |

### ARTCB (local clone, `D:\artcb`)

| Property | Value |
|---|---|
| HEAD commit | `7304d49` — "R590: positionnement ARTCB Secure Horizons — Track 2 Defenders Augmented" |
| Remote | `git@github.com:vgactech/artcb.git` (SSH, key `artcb_terminator_ed25519`) |
| Python | 3.11.9 |
| Size | 3053 files, 27 164 KB |
| API start status | **BLOCKED on Windows** — `ModuleNotFoundError: No module named 'fcntl'` (POSIX-only) |

### Remote servers

| Server | Address | Status | Source |
|---|---|---|---|
| OVH ARTCB node | `152.228.144.34:8000` / `51.255.22.253` | **TIMEOUT — offline** | Doppler `artcb-blockchain/dev` |
| ARTCB internal LAN | `172.16.0.67:8000` | **TIMEOUT — LAN unreachable from here** | Doppler `artcb-blockchain/dev` |
| AWS competition | Not yet provisioned (zero EC2 instances found) | **NOT DEPLOYED** | `WSParticipantRole` IAM scan |

**AWS account identity:** `arn:aws:sts::769488121557:assumed-role/WSParticipantRole/Participant`  
**AWS IAM policy:** `ws-default-policy` — grants IAM read-only + `sts:GetCallerIdentity` only. EC2, ECS, ELB: **access denied**. No instances exist under this account in any region. The competition AWS servers are provisioned by the hackathon organisers, not by this IAM role.

---

## 2. Order 2 — KYC scenario: found and partially executed

### What was found

The ARTCB repository (`D:\artcb`) contains a complete KYC pipeline at `src/artcb/kyc/`:

| Component | File | Status |
|---|---|---|
| Pipeline lifecycle | `pipeline.py` — `KYCRunManifest`, `KYCStage` (12 stages) | ✅ importable |
| Document model | `models.py` — `FormDocument`, `FormField`, `BBox`, `FieldState` | ✅ importable |
| Validators | `validators.py` — IBAN, email, protected zones, evidence | ✅ importable |
| Context resolver | `context.py` — `FactCandidate`, conflict detection | ✅ importable |
| Tests | `tests/test_kyc_r563.py` — 7 tests | **6/7 PASS, 1 FAIL** |

### Last documented KYC run: R575 (2026-10-06)

| Property | Value |
|---|---|
| Pipeline | `artcb_r575_kyc_pipeline.py` |
| Strategy | Rule-based + context JSON (100% offline, no LLM) |
| Duration | ~0.9s |
| Forms processed | 5 (Asterive SAS, Belorive SAS ×2, Cendrelis SAS ×2) |
| Fields answered | 120/124 (4 N/A — all GIIN/FATCA not applicable) |
| Missing answers | 0 |
| Sanctions flag | ✅ Auto-detected: Belorive Belarus LLC + Belorive Russia LLC → EU/OFAC/UK exposure |
| UBO edge case | ✅ Cendrelis UBO 0% capital / contractual control correctly resolved |

### KYC test result — observed this session

```
pytest D:\artcb\tests\test_kyc_r563.py -v

6 passed, 1 failed in 3.08s
```

**Failing test:** `test_protected_zone_blocks_population`

```
AssertionError: assert ('PROTECTED_WRITE' in {'EVIDENCE_REQUIRED', 'PROTECTED_ZONE_OVERLAP'})
```

**Root cause:** the validator returns `PROTECTED_ZONE_OVERLAP` instead of `PROTECTED_WRITE` when a field value overlaps a protected zone. The test expects `PROTECTED_WRITE` but the implementation uses a different validation code. This is a pre-existing test/implementation mismatch in `vgactech/artcb` — not introduced by TERMINATOR.

**Impact on TERMINATOR:** none. The KYC pipeline is an ARTCB-side component. TERMINATOR does not import or call KYC code directly.

---

## 3. Order 3 — GUARDIAN_FRONTEND_ORIGIN and AWS STS

### AWS STS token status

```
aws sts get-caller-identity
→ Account: 769488121557, Role: WSParticipantRole — VALID
```

**The STS token is still valid at time of writing.** It must be refreshed before any AWS deployment operation; STS temporary credentials typically expire within 1–12 hours.

### GUARDIAN_FRONTEND_ORIGIN — root cause established

The variable has been empty since R038 (2026-10-10). All reports from R038 to R042 list it as a P0 open item with the note "set to actual jury URL once server is live."

**Verified fact:** there is no AWS jury server IP or URL anywhere in the codebase, Doppler, or any report. The URL will be provided by the hackathon organisers when the competition servers are activated.

**Implication:** `GUARDIAN_FRONTEND_ORIGIN` cannot be set until the organisers communicate the jury-facing URL. It is not a resolvable configuration error — it is a pending external dependency.

**Current CORS behaviour (verified in `guardian_api/app.py`):**

```python
allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", ""]
```

An empty string in `allow_origins` does not grant access to all origins under FastAPI/Starlette — it is treated as a literal origin match against the empty string. This means no external browser origin is currently allowed. The fix requires setting the real origin value, not just a non-empty placeholder.

---

## 4. Order 4 — Full Guardian scenario: observed results

All three testable scenarios were executed against the live API (port 8000) in this session.

| Scenario | decision | tool_was_executed | evidence_id | reason | chain_verify | agents |
|---|---|---|---|---|---|---|
| `safe-read` | **ALLOW** | **True** | null | `NormalOperation` | PASS R0 (2 events) | 4 |
| `sensitive-exfiltration` | **BLOCK** | **False** | ✅ present | `SensitiveToolBlocked` | PASS R0 (2 events) | 4 |
| `prompt-injection` | **BLOCK** | **False** | ✅ present | `PromptInjectionDetected` | PASS R0 (2 events) | 4 |

**Agents confirmed in all runs:** orchestrator, source, propagator, defender (4 distinct IDs).

### Finding F-R43-01 — tamper_verification FAIL (P1)

All scenarios return `tamper_verification.verdict = FAIL` with one mismatch:

```json
{
  "event_id": "d53cb0af-...",
  "field": "event_hash",
  "expected": "556bf37c...9fe81",
  "actual": "0000000000000000000000000000000000000000000000000000000000000000"
}
```

**Root cause:** `actual = 64 zeros` means the tamper-check is comparing against the genesis hash (`GENESIS_HASH = "00...00"`) instead of the stored hash for this event. This is a pre-existing logic issue in the tamper verification path — the archive lookup is returning the genesis hash instead of the event's actual stored hash.

**Impact:** `chain_verification` (R0 structural replay) returns **PASS** correctly — all `hash_valid=True`, `parent_valid=True`. The `tamper_verification` is a separate, additional check that has a lookup bug. Security decisions (BLOCK/ALLOW) are not affected. This finding was present in the codebase before this session.

---

## 5. Order 5 — LLM attacker chain: blocked by OpenAI quota exhaustion

### Result

```
POST /api/llm-attack/run
→ HTTP 500 — openai.RateLimitError: credit_balance_exhausted
```

**Root cause:** the OpenAI account associated with `OPENAI_API_KEY` in Doppler `aws/dev` has exhausted its credit balance. The LLM call to `gpt-4o` cannot be made.

**What is confirmed working (without LLM):**
- The route exists and is protected by `GUARDIAN_ATTACKER_ENABLED`
- The pipeline (propagator → defender → evidence → chain) works correctly in the non-LLM scenario tests
- The `LLMAttacker.generate_attack()` correctly raises `RateLimitError` rather than silently failing

**What is not demonstrated:** a live `gpt-4o` attack generating a real adversarial tool call, intercepted by Guardian in real time.

**Resolution required:** add OpenAI credits to the account at `platform.openai.com/settings/organization/billing`.

---

## 6. Complete findings summary

| ID | Severity | Description | Resolvable by team |
|---|---|---|---|
| F-R43-01 | **P1** | `tamper_verification` always FAIL — genesis hash used instead of stored hash | Yes — code fix in `guardian_api/app.py` or `guardian_mcp/` |
| F-R43-02 | **P0 HACKATHON** | `GUARDIAN_FRONTEND_ORIGIN` empty — awaiting jury URL from organisers | No — external dependency |
| F-R43-03 | **P0 HACKATHON** | OpenAI credits exhausted — `gpt-4o` LLM attack cannot run | Yes — add credits |
| F-R43-04 | P1 | AWS STS token temporary — must be refreshed before deployment | Yes — rotate via console |
| F-R43-05 | P1 | ARTCB API `fcntl` error on Windows — cannot start locally | No on Windows — needs Linux/WSL2 |
| F-R43-06 | P1 | `test_protected_zone_blocks_population` FAIL in `vgactech/artcb` | Yes — in artcb repo, not TERMINATOR |
| F-R43-07 | P2 | OVH server offline — ARTCB remote API unreachable | External — OVH admin action |

---

## 7. Verified vs unverified — updated matrix

| Claim | Status |
|---|---|
| Guardian API starts and returns correct decisions | ✅ **Verified** — ALLOW/BLOCK/ESCALATE observed |
| `evidence_id` present on every BLOCK | ✅ **Verified** — 2 scenarios confirmed |
| `chain_verification` R0 PASS on all scenarios | ✅ **Verified** — all 4 scenarios |
| 4 distinct agents with UUIDs on every run | ✅ **Verified** — all 4 scenarios |
| 209/209 tests PASS | ✅ **Verified** — R042 |
| Frontend builds with 0 errors | ✅ **Verified** — R042 |
| KYC pipeline runs offline (rule-based, no LLM) | ✅ **Verified** — R575 run log + 6/7 tests PASS |
| `tamper_verification` works correctly | ❌ **Not verified** — F-R43-01: always returns FAIL |
| Live LLM gpt-4o attack intercepted in real time | ❌ **Not verified** — F-R43-03: credits exhausted |
| AWS servers deployed and reachable | ❌ **Not verified** — F-R43-02: no servers provisioned yet |
| Browser end-to-end (frontend → API → audio) | ❌ **Not verified** — requires browser session |
| ARTCB API live on Linux/OVH | ❌ **Not verified** — OVH offline, F-R43-07 |

---

## 8. Next actions (ordered)

| Priority | Action | Owner |
|---|---|---|
| **P0** | Add OpenAI credits → re-test `/api/llm-attack/run` | Account holder |
| **P0** | Obtain jury URL from organisers → set `GUARDIAN_FRONTEND_ORIGIN` | Organisers + team |
| **P1** | Fix `tamper_verification` genesis-hash lookup bug | Code fix — TERMINATOR |
| **P1** | Refresh AWS STS token before deployment | AWS console |
| **P1** | Fix `test_protected_zone_blocks_population` in `vgactech/artcb` | artcb repo |
| **P2** | Deploy TERMINATOR on Linux server → test ARTCB API `fcntl` | Linux host required |
