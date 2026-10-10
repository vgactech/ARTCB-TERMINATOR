# R041 — Critical Audit of R040 Voice Commentary, SSE Delivery, and Enforcement Isolation

**Date:** 2026-10-10  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Branch reviewed:** `main`  
**Reviewed HEAD:** `44e4087e799fad0ffb2cc625010097fadb7ba7e7`  
**Previous implementation report:** R040 — Real-Time Voice Commentary and Live Execution Observability  
**Scope:** Read-only review of commit R040 and the current repository tree. This report is the only repository change authorized by the project directive. No application source, tests, deployment configuration, secrets, or runtime logs are modified. No logs are pushed.

---

## 1. Executive decision

**Verdict: PARTIAL DELIVERY — backend prototype present; end-to-end real-time voice integration is not yet demonstrated.**

Commit `44e4087` is the current `main` HEAD. The commit adds `guardian_mcp/voice_commentary.py`, adds an SSE generator and voice-status endpoint in `guardian_api/app.py`, and adds tests in `guardian_api/test_app.py`. The commit metadata confirms those three changed paths. The reported result of 154/154 passing tests is accepted as user-provided status, not independently reproduced in this read-only audit.

The implementation establishes a useful backend path, but several requirements documented in R040 are not yet met:

1. **Voice synthesis can delay Guardian enforcement.** The synchronous SSE generator invokes blocking ElevenLabs HTTP requests between pipeline stages. The 15-second per-call timeout means a slow provider can delay later stages and the defender decision; a sequence of calls can multiply that delay.
2. **The frontend is not wired to the new stream by this commit.** The commit changes no frontend files. Therefore the claim that the browser updates the graph and plays the audio from these SSE events is not established by the diff.
3. **The chain-verification narration overstates its scope.** The stream verifies the defender's event list, not a single merged ledger containing every agent and every inter-agent event. Yet the narration says the audit trail is cryptographically sound without qualifying the verified scope.
4. **The endpoint can trigger costly work without an application-level caller authorization check.** When the feature flag is enabled, the stream endpoint can start an LLM call and several TTS requests. CORS is not authentication or authorization.
5. **The stream is event-by-event SSE, not progressive audio streaming.** Each synthesized MP3 is read in full, base64-encoded, and emitted only after synthesis completes. There is no audio-chunk stream from ElevenLabs in this implementation.

These are implementation and assurance gaps, not evidence that the entire feature is unusable. The correct status is **backend prototype implemented; production-grade, non-blocking, end-to-end real-time delivery remains unverified**.

---

## 2. Expertise activated

- Python and FastAPI execution semantics.
- Server-Sent Events (SSE), HTTP streaming, and browser integration.
- Text-to-speech integration and provider failure modes.
- Security control-plane isolation and fail-open/fail-safe design.
- Distributed tracing, event provenance, and cryptographic chain verification.
- API authorization, abuse resistance, and cloud cost exposure.
- Test coverage analysis and acceptance criteria.
- Forensic evidence integrity and truthful security narration.

---

## 3. Verified repository facts

The remote `main` reference resolves to commit `44e4087e799fad0ffb2cc625010097fadb7ba7e7`.

The commit changes exactly these three paths:

- `guardian_api/app.py`
- `guardian_api/test_app.py`
- `guardian_mcp/voice_commentary.py`

No frontend path changes in this commit. The API adds:

- `POST /api/llm-attack/stream`
- `GET /api/voice/status`

The stream uses a synchronous generator, and the ElevenLabs adapter uses `urllib.request.urlopen(..., timeout=15)` followed by `resp.read()`. The voice adapter catches provider HTTP errors and operating-system/network errors and returns empty bytes. This is graceful error fallback, but it does not eliminate latency while a request is in progress.

The stream emits session, attack, propagation, decision, chain-verification, script, audio, and final-result events. The audio payload is a complete MP3 represented as base64 rather than a sequence of audio chunks.

---

## 4. Finding R041-001 — Voice synthesis is on the enforcement critical path

**Severity: HIGH**

### Process — what the code does

The SSE generator emits an event and a narration script, calls the synchronous TTS method, waits for the provider response, emits the completed audio payload, and only then advances to the next pipeline stage. The TTS method has a 15-second network timeout.

### Problem — why this is material

The voice system is intended to be an observational side channel. R040 explicitly requires that voice failure never blocks or delays a security decision. Returning empty bytes on an error is not enough: a timeout is only handled after the request has already waited.

For example, if several narration calls each reach their timeout, the cumulative delay can be many tens of seconds before the defender decision or final verification event is emitted. The exact duration depends on the number of calls and provider behavior; it was not measured in this audit.

### Solution — required correction

1. Move TTS out of the enforcement execution path.
2. Publish canonical security events immediately, without awaiting audio generation.
3. Submit narration work to a bounded background queue or task group that cannot block policy evaluation.
4. Give narration a strict deadline and cancellation policy; when the deadline expires, preserve the text event and mark audio as unavailable.
5. Keep enforcement results authoritative even if the queue is full, the provider is unavailable, or the client disconnects.
6. Add a regression test in which the TTS adapter deliberately blocks or times out and assert that the defender decision is emitted without waiting for TTS completion.

**Acceptance criterion:** with TTS delayed by 15 seconds or made unavailable, the security decision and its event are emitted independently of the TTS delay. Measure and publish the decision latency separately from narration latency.

---

## 5. Finding R041-002 — End-to-end frontend delivery is not in the commit

**Severity: HIGH for the claimed live user experience**

### Process

The backend returns SSE events and full MP3 payloads. For a user to hear and see them live, the frontend must open the stream, parse named SSE events, correlate them to the current run, update the graph and timeline, decode or enqueue the audio, and handle completion, failure, and reconnection.

### Problem

The R040 implementation commit contains no frontend file changes. A backend endpoint alone does not prove that the browser consumes it. The implementation report's description of what the frontend receives must therefore be treated as an intended interface, not as verified end-to-end behavior.

### Solution

1. Add a dedicated frontend SSE client for `POST /api/llm-attack/stream` (the standard browser `EventSource` API does not support POST bodies; use `fetch()` with a streaming reader or change the protocol deliberately).
2. Parse each SSE frame according to the SSE format, including multi-line `data:` fields and incomplete frames split across network chunks.
3. Correlate events by `session_id`, `run_id`, sequence, and stable event ID; do not rely on arrival order alone.
4. Update the graph from received events, not from a timer that simulates activity after a completed response.
5. Queue audio sequentially and expose text narration when audio is disabled or fails.
6. Add frontend integration tests covering delayed events, stream termination, duplicate events, malformed payloads, and a failed audio item.

**Acceptance criterion:** a browser test demonstrates that the graph changes before the final `done` event, and that audio/text playback follows received event provenance rather than a precomputed animation.

---

## 6. Finding R041-003 — The chain-verification narration overstates the verified scope

**Severity: HIGH for forensic trust**

### Process

The stream obtains events from `defender.get_all_events()`, checks their stored hashes and parent links, and emits an R0 verdict. The narration template for a PASS verdict says that the chain integrity is verified and that the audit trail is cryptographically sound.

### Problem

The verified collection is the defender's event list. It is not evidence that the orchestrator, attacker, propagator, defender, transport, TTS calls, and all cross-agent transfers have been merged into one complete, independently verifiable ledger. Earlier R039/R040 material already identifies separate instrumentation instances and the absence of a merged cross-agent chain as a limitation.

A valid hash chain proves integrity only for the events and links actually included in the check. It does not prove that all relevant events were recorded, that no event was omitted before ingestion, or that every agent shares one global chain.

### Solution

1. Include explicit scope metadata in the result, for example: `verified_scope = "defender_event_chain"`.
2. Rename or qualify the spoken result: “The defender event-chain checks passed for N recorded events; cross-agent ledger completeness has not been verified.”
3. Do not use “the audit trail is cryptographically sound” as an unqualified global statement.
4. Preserve separate chain IDs and agent provenance until a merged ledger is implemented and validated.
5. Add negative tests that verify narration remains scoped when the defender chain passes but cross-agent events are missing.

**Acceptance criterion:** every PASS statement identifies the exact ledger, event count, and checks performed; it never implies completeness beyond the data verified.

---

## 7. Finding R041-004 — An enabled stream can trigger expensive provider work without a caller authorization check

**Severity: HIGH if exposed beyond a trusted local environment**

### Process

The route checks whether `GUARDIAN_ATTACKER_ENABLED` is set to true. If so, it returns the stream generator, which can invoke the configured LLM and multiple TTS requests.

### Problem

The feature flag is an operational enablement control, not caller identity or permission. CORS limits which browsers can read cross-origin responses; it is not an access-control boundary for direct HTTP clients. If the route is reachable by untrusted callers while enabled, it may be abused to consume model/TTS quota or repeatedly run the attack pipeline.

This audit did not verify the actual AWS ingress, authentication middleware, or deployed exposure. The risk is conditional on deployment reachability.

### Solution

1. Verify the deployed network exposure before enabling the endpoint publicly.
2. Require the application's established authentication and authorization mechanism for this route; do not rely on CORS or the feature flag.
3. Apply per-user and per-session rate limits, concurrency limits, request budgets, and provider-spend alerts.
4. Reject unauthorized calls before creating an LLM or TTS client.
5. Add tests for unauthenticated access, authorization failure, and rate-limit exhaustion.

**Acceptance criterion:** unauthorized requests cannot trigger an LLM or TTS call, and authorized usage is bounded by explicit quotas.

---

## 8. Finding R041-005 — The implementation does not stream audio progressively

**Severity: MEDIUM**

### Process

The adapter reads the complete HTTP response into memory. The stream then base64-encodes the complete MP3 and emits it as one SSE event.

### Problem

This adds buffering and approximately one-third encoding overhead for the audio payload. The browser cannot begin consuming the audio until synthesis and the complete response have finished. The event is a completed audio object, not a progressive audio stream.

### Solution

1. If progressive playback is required, use an ElevenLabs streaming endpoint and relay bounded audio chunks through a transport suited to binary media, such as a dedicated streaming response or WebSocket.
2. If retaining SSE, treat it as the control/event channel and send audio through a separate media channel; avoid repeated large base64 payloads in JSON events.
3. Add sequence and completion metadata so the client can detect missing chunks.
4. Keep the text script available independently of audio transport.

**Acceptance criterion:** measure time-to-first-audio and end-to-end audio latency; document whether the target is progressive streaming or complete-clip delivery.

---

## 9. Finding R041-006 — Narration templates contain claims that must be evidence-gated

**Severity: MEDIUM**

### Process

The script builder uses fixed sentences for event types and interpolates values from the pipeline result.

### Problem

Some phrases imply more than the event itself necessarily proves. For example, the propagation narration says a causal link is established and the hash is preserved; the block narration says the tool was never executed; the chain narration says the audit trail is sound. Those claims are appropriate only if the relevant execution and evidence fields actually support them. The session narration also calls one agent “Source” even though the stream's role list uses “llm-attacker”, which can confuse users about identity.

The attack commentary also speaks text returned by the attacker model. It is not an authority-bearing instruction to Guardian, but it can still produce misleading, abusive, or distracting speech if used without output controls.

### Solution

1. Map narration templates to explicit typed facts and verification outcomes, not merely to an event name.
2. Derive “tool not executed” from the authoritative executor status, and avoid saying this for unknown or inconsistent statuses.
3. Derive “hash preserved” from the relevant hash comparison result.
4. Keep the speaker label consistent with the canonical agent identity.
5. Label attacker-generated text as untrusted quoted content, bound its length, and apply text/audio moderation appropriate to the product.
6. Use “unknown” or “not verified” when evidence is incomplete.

**Acceptance criterion:** tests cover BLOCK, ALLOW, ESCALATE, unknown status, missing evidence ID, invalid chain, and absent propagation verification; no template may upgrade an unknown result to a confirmed fact.

---

## 10. Finding R041-007 — The SSE contract lacks durable replay and delivery semantics

**Severity: MEDIUM**

### Process

The generator sends named SSE events with JSON data. The event payload includes sequence numbers for narration scripts, but the transport does not assign standard SSE event IDs or define reconnect/replay behavior.

### Problem

If a browser disconnects or receives a partial response, it has no durable event cursor to request the missed section. There is also no heartbeat event or explicit contract for duplicate delivery, event ordering, or a client reconnect. The final `done` event includes the final data, but this is not equivalent to a replayable live history.

### Solution

1. Give each event a stable ID derived from the canonical run/event identity.
2. Define replay and reconnect behavior, or explicitly document that the current demo stream is non-resumable.
3. Add keep-alive comments or heartbeat events for long-running stages.
4. Make frontend event processing idempotent and deduplicate by event ID.
5. Persist canonical events independently of the live connection; never treat SSE delivery as the audit archive.

**Acceptance criterion:** a test disconnects the client between two events and verifies either deterministic replay without loss or a clear, documented non-resumable failure state.

---

## 11. Finding R041-008 — The voice status endpoint reports configuration, not provider health

**Severity: LOW**

### Process

`GET /api/voice/status` reports whether the environment variable exists and returns the configured voice IDs.

### Problem

A configured key may be invalid, revoked, quota-limited, or unable to reach ElevenLabs. The response currently calls the feature enabled when a non-empty key is present, which can be mistaken for a successful end-to-end provider check. A live provider probe on every status request would also be undesirable because it adds cost and latency.

### Solution

Expose separate states such as:

- `configured`: a key is present, without returning it;
- `last_provider_result`: result and timestamp of a bounded health check, if implemented;
- `last_error_class`: sanitized error category, never the secret or full request headers;
- `audio_delivery_available`: whether the latest synthesis operation returned audio.

Do not make status checks synthesize speech on every request. Protect the endpoint if operational metadata is not intended to be public.

**Acceptance criterion:** status clearly distinguishes configuration from successful provider operation and never returns secret material.

---

## 12. Prioritized correction plan

| Priority | Action | Reason |
|---|---|---|
| P0 | Decouple TTS latency from the Guardian enforcement path | Prevent narration from delaying a security decision |
| P0 | Scope all chain-verification claims to the ledger actually checked | Prevent false forensic assurance |
| P0 | Verify route exposure and enforce caller authorization/rate limits | Prevent untrusted, costly pipeline invocation |
| P1 | Wire the frontend to SSE and audio events | Deliver the actual live user experience |
| P1 | Add evidence-gated narration templates and consistent agent identity | Prevent narration from overstating observed facts |
| P1 | Define stable event IDs, replay, and disconnect semantics | Preserve live-to-forensic continuity |
| P2 | Decide between complete MP3 clips and progressive audio streaming | Set accurate latency expectations |
| P2 | Distinguish configured credentials from actual provider health | Improve operations without leaking secrets |

---

## 13. Required validation matrix

The 154/154 PASS result reported for the commit is useful but is not, by itself, evidence of these additional properties. The following checks should be added or explicitly demonstrated:

1. **Enforcement isolation:** make TTS sleep for 15 seconds; confirm the policy decision is emitted independently.
2. **Provider failure:** simulate timeout, HTTP 401, HTTP 429, and connection reset; confirm Guardian decisions and canonical events remain intact.
3. **Frontend integration:** run a browser test proving graph updates precede the final result and the audio queue consumes the correct event sequence.
4. **Chain scope:** remove or omit a cross-agent event while the defender chain remains valid; confirm narration does not claim a globally complete ledger.
5. **Authorization:** call the endpoint without valid credentials and confirm no LLM/TTS invocation occurs.
6. **Rate limits:** test concurrent and repeated calls and confirm bounded work.
7. **SSE robustness:** split frames across transport chunks, disconnect and reconnect, deliver duplicates, and terminate before `done`.
8. **Narration correctness:** test all policy outcomes and unknown evidence; assert that claims match the structured result.
9. **Secrets and logs:** verify that API keys, authorization headers, and raw provider credentials never enter the response, event archive, or application logs.
10. **Deployment:** separately verify AWS environment configuration, real frontend origin, TLS, provider authentication, and measured latency. Repository state alone cannot prove those runtime properties.

---

## 14. Process / problem / solution summary

### Process

R040 introduces a backend SSE route that yields pipeline events and narration scripts, calls ElevenLabs for complete MP3 responses, and returns a final result. A status route reports whether a credential is configured.

### Problem

The synchronous TTS calls are interleaved with execution and can delay the defender; the frontend is unchanged in this commit; chain verification covers a narrower event set than the narration implies; and an enabled endpoint can trigger expensive work without route-level caller authorization visible in the reviewed code.

### Solution

First isolate voice from enforcement, then make all evidence claims scope-aware, establish access controls and resource limits, and complete the browser SSE/audio integration. Add tests for latency isolation, missing evidence, authorization, provider failures, and stream reconnection before declaring the experience production-ready.

---

## 15. Final verdict

**R040 is a meaningful backend increment, but not yet a verified end-to-end real-time voice feature.** The most urgent correction is to make TTS fully non-blocking with respect to security enforcement. The most important trust correction is to narrow chain-integrity narration to the precise event set verified. The most important product correction is to implement and test the frontend consumer rather than infer it from the existence of an SSE endpoint.

**Repository scope respected:** this report is the only intended repository change for R041. No application files, test files, deployment settings, secrets, or logs were changed by this audit.
