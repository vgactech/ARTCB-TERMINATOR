# R040 — Real-Time Voice Commentary and Live Execution Observability for ARTCB-TERMINATOR

**Date:** 2026-10-10  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Branch reviewed:** `main`  
**Reviewed HEAD:** `c7a6214a4dbeb4b74d6da921d6f884833ec07da1`  
**Previous report:** R039 — policy matrix, multi-agent provenance, Doppler validation  
**Scope:** Architecture audit and implementation specification for live voice narration using the already-provisioned ElevenLabs credential  
**Repository changes:** Report only. No application code, tests, deployment configuration, secrets, or logs modified. No push of runtime logs.

---

## 1. Executive decision

The new requirement is to make ARTCB-TERMINATOR behave like a live sports broadcast of a defensive security operation: a narrator explains the evolving situation while defensive agents speak in the first person about what they observe, decide, attempt, and verify. The attacking agent must remain silent.

**Recommendation: implement an event-driven narration pipeline, not a voice layer attached to the final HTTP response.** The system must publish events as work happens, produce short commentary from those events, synthesize audio through ElevenLabs, and let the frontend play the audio while the execution graph is still updating.

The existing ElevenLabs credential reportedly available in Doppler project `aws` is a useful prerequisite, but its presence alone does not prove that the application can authenticate, stream audio, select voices, or deliver narration to a browser. Those behaviours require integration and runtime tests. This report does not read or expose the secret.

### Required outcome

- Commentary starts after the first meaningful event, not after the whole run finishes.
- The graph, textual event feed, and audio commentary share the same session, run, and event identifiers.
- The narrator describes only events supported by observed telemetry.
- Each defensive agent uses first-person language when it has a genuine event to report.
- The attacker produces no spoken narration and no first-person attacker voice.
- Security enforcement remains deterministic and independent from the commentary LLM.
- Voice failure never blocks the defender, delays a security decision, or changes an enforcement outcome.
- The complete event and narration provenance remains available for replay and forensic review.

---

## 2. Expertise activated

- Real-time application architecture and event-driven systems.
- LLM orchestration, agent identity, and controlled natural-language generation.
- ElevenLabs Text-to-Speech, streaming, and voice-session design.
- FastAPI streaming interfaces and browser event delivery.
- Distributed tracing, causal ordering, and event correlation.
- Security operations, attack detection, containment, and incident response.
- Forensic evidence, append-only audit trails, and provenance.
- AWS deployment and Doppler secret management.
- Reliability engineering, queue backpressure, and failure recovery.
- Test engineering and measurable acceptance criteria.

---

## 3. Current repository state verified against GitHub

The remote `main` branch was inspected at commit `c7a6214a4dbeb4b74d6da921d6f884833ec07da1`, whose commit message identifies the R039 policy-matrix, four-agent provenance, and Doppler validation work.

The following facts were confirmed from the repository files:

| Area | Observed state | Consequence for voice narration |
|---|---|---|
| FastAPI bridge | `guardian_api/app.py` exposes synchronous run endpoints, including `POST /api/llm-attack/run` and scenario-run endpoints. | The current response shape is designed to return a completed result; it is not yet a live event stream. |
| Frontend | `frontend/src/api/guardian.ts` exposes ordinary JSON fetch helpers. | No event-stream or audio-stream client is present in the inspected API helper. |
| Animation | `frontend/src/App.tsx` receives the scenario result, then animates the agent stages with a timer. | The animation is post-response playback, not proof that the graph is updated from events as they occur. |
| Attacker | `guardian_mcp/llm_attacker.py` generates a real tool-call attempt using OpenAI when configured. | The attacker’s tool selection and returned text are data to observe, not permission to give the attacker a voice. |
| Defender | `guardian_mcp/defender_agent.py` evaluates requests and produces Guardian decisions and evidence metadata. | Commentary should be derived from the decision and its evidence, rather than being allowed to decide the policy. |
| Multi-agent events | R039 documents a remaining limitation: the orchestrator, propagator, and defender currently emit through separate instrumentation instances, and their chains are not yet merged into one ledger. | Live commentary must preserve per-agent provenance now and must not falsely claim that a single merged cryptographic chain already exists. |
| Secrets | R038/R039 document the Doppler project/config as `aws/dev`; the user reports that `VOICE_1_ELEVENLABS_API` is now available there. | The secret must be read server-side only. Runtime presence, scope, quota, and successful authentication still need verification. |
| Deployment | R039 still lists the real `GUARDIAN_FRONTEND_ORIGIN`, AWS deployment verification, and other hackathon deliverables as open. | Voice should be tested in the actual deployed browser path after network, origin, and TLS configuration are confirmed. |

**Important distinction:** repository inspection confirms the current architecture and documented limitations. It does not prove the running AWS deployment, the value or validity of any Doppler secret, or the actual latency of an ElevenLabs call.

---

## 4. Process — what the live system must do

The desired flow is:

1. **Receive the user's prompt.** Create a `session_id` and `run_id`; record the input event and its timestamp.
2. **Publish an event immediately.** Every instrumented stage emits a canonical event when the stage begins, changes state, or completes.
3. **Update the graph and event feed.** The frontend receives each event as it arrives and updates the appropriate agent, edge, status, and timeline entry.
4. **Classify the event for narration.** A narration planner maps the event into a short, grounded speech act: progress, observation, decision, action, result, uncertainty, or failure.
5. **Choose the speaking identity.** The narrator speaks in third-person commentary. A defensive agent speaks in first person only when the event is attributed to that agent. The attacker is excluded from the speech queue.
6. **Generate the speech text.** Use controlled templates for high-confidence security transitions; use an LLM only for bounded explanation where it adds value. The generated text must retain the source event IDs.
7. **Synthesize audio.** A server-side adapter sends the text to ElevenLabs using the configured voice and model. Audio is returned progressively when the chosen endpoint supports streaming.
8. **Play audio without blocking security work.** The browser plays narration asynchronously while Guardian continues to evaluate and enforce policy.
9. **Record provenance.** Store the narration item, its source event IDs, speaker role, text hash, voice/model configuration identifiers, generation status, and audio-delivery status. Do not store the API key or write audio bytes into ordinary application logs.
10. **Close the run.** Announce the verified final outcome, persist the final status, and leave the event and commentary timeline replayable.

### Illustrative narration

- **Narrator:** “The request has entered Guardian. The system is opening a new run and assigning correlation identifiers.”
- **Propagator agent:** “I received the request from the source agent. I am forwarding its recorded payload hash to the defender.”
- **Defender agent:** “I have evaluated the requested tool. My policy decision is BLOCK, and I have not called the tool executor.”
- **Narrator:** “Guardian reports a block. The evidence identifier is present, and the event-chain checks returned PASS for the scope that was actually verified.”
- **Defender agent, on a later event:** “I have completed the verification available to me. I cannot confirm the network-level impact because that layer has not been instrumented.”

These are examples of the target interaction, not claims that these utterances already occur in the deployed product.

---

## 5. Problem — why simply adding ElevenLabs is insufficient

### 5.1 The current API returns completed runs

**Process:** a frontend request waits for a JSON response containing the run result.

**Problem:** the client cannot narrate intermediate stages it has not yet received. Animating the returned result with a timer creates the appearance of live execution without proving that the underlying events arrived live.

**Solution:** add an event-delivery path that publishes events from the execution process. A first implementation can use Server-Sent Events (SSE) for one-way server-to-browser updates. WebSockets are appropriate if bidirectional live controls become necessary. Keep existing JSON endpoints for compatibility and for final-result retrieval.

### 5.2 A text-to-speech call is not a narration system

**Process:** ElevenLabs converts supplied text into audio.

**Problem:** it does not decide which event matters, who is allowed to speak, whether a claim is proven, how multiple agents are sequenced, or how stale commentary is discarded.

**Solution:** implement a distinct narration planner, speaker policy, queue, TTS adapter, and playback client. TTS must be downstream of the event and security-decision pipeline.

### 5.3 A generated sentence can overstate the evidence

**Process:** an LLM can explain an event in natural language.

**Problem:** a model may turn “suspicious activity detected” into “the attacker compromised the host,” even when no such impact was observed. It may also confuse a requested action with a completed action.

**Solution:** attach evidence class and event references to every narration item. Distinguish at minimum:
- observed;
- suspected;
- detected by a rule or model;
- confirmed by explicit evidence;
- blocked before execution;
- executed and verified;
- outcome unknown;
- telemetry unavailable.

Only the event ledger and deterministic policy engine may establish enforcement facts. The narration model may explain those facts but cannot upgrade their confidence.

### 5.4 Multi-agent narration can become unintelligible

**Process:** events from multiple agents can occur in parallel.

**Problem:** independent TTS calls can overlap, arrive out of order, repeat the same information, or drown out urgent events.

**Solution:** use a central speech scheduler with per-run ordering, deduplication, priority, interruption rules, and a bounded queue. The graph can show every event, while the voice channel summarizes lower-priority events and speaks critical transitions immediately.

---

## 6. Recommended architecture

### 6.1 Separate the six responsibilities

1. **Execution and Guardian enforcement** — runs the scenario and applies deterministic policy.
2. **Canonical event publisher** — emits structured events during execution, not only at the end.
3. **Live transport** — streams events to the browser and supports reconnect/replay.
4. **Narration planner** — maps evidence-backed events to short speech items and enforces speaker policy.
5. **ElevenLabs adapter** — authenticates server-side, sends text, receives audio chunks, handles provider errors and quotas.
6. **Frontend audio/graph coordinator** — updates the graph from events and plays speech in the order determined by the scheduler.

The narrator and TTS adapter must not have direct authority to call protected tools, alter Guardian decisions, or bypass the policy engine.

### 6.2 Suggested event contract

Every emitted event should reuse the canonical Guardian event contract already documented in R005/R006 wherever applicable. The live transport may add delivery metadata without changing the canonical event hash inputs.

Recommended delivery envelope fields:

| Field | Purpose |
|---|---|
| `event_id` | Stable identity for deduplication. |
| `session_id`, `run_id` | Correlate the complete run. |
| `agent_id`, `agent_role` | Attribute the event to the correct participant. |
| `event_type`, `event_phase` | Describe the event and lifecycle phase. |
| `occurred_at` | Source event time, including the source's available precision. |
| `published_at`, `received_at` | Measure delivery delay separately from event time. |
| `sequence_no` | Preserve ordering within its documented scope. |
| `parent_event_ids` | Represent causal dependencies and parallel branches. |
| `decision`, `execution_status` | Distinguish requested, blocked, executed, and verified actions. |
| `evidence_id`, `event_hash`, `previous_event_hash` | Link the narration to the existing evidence model when present. |
| `observability_status` | State whether a layer was observed, unavailable, or not instrumented. |

Do not claim global total ordering across independent agent chains until a merged ledger or an equivalent verified causal-order mechanism exists.

### 6.3 Suggested narration item

Each queued speech item should include:
- `narration_id`;
- `session_id` and `run_id`;
- source `event_ids`;
- `speaker_role` and `speaker_agent_id`;
- `priority`;
- `text` and `text_hash`;
- `evidence_class`;
- `voice_id` and `model_id` (configuration identifiers, not secrets);
- `created_at`, `tts_started_at`, `first_audio_at`, `playback_started_at`, `playback_completed_at`;
- `status` and any sanitized error code.

The narration record is a derivative of the source events. It must not be substituted for the source event or treated as forensic proof that the narrated claim is true.

---

## 7. Speaker policy — narrator, defenders, and silent attacker

### Narrator

- Uses concise third-person commentary.
- Explains the overall state, causal transitions, threat significance, and verified final result.
- Can say when evidence is missing or a task remains incomplete.
- Must not invent events, outcomes, attack impact, or successful remediation.

### Defensive agents

- Speak in the first person only for actions and observations attributed to their own agent identity.
- Use concrete verbs: “I received…”, “I checked…”, “I blocked…”, “I generated…”, “I verified…”, “I could not verify…”.
- Must not claim another agent's work as their own.
- Must not claim success when an operation is still pending or only attempted.
- Can explain a missing capability and propose a safe next step, but may not silently bypass policy to obtain that capability.

### Attacking agent

- **No spoken output.** Do not route attacker messages, attacker “reasoning,” or attacker-generated narration text to ElevenLabs.
- Preserve attack actions as structured, observable events in the graph and forensic timeline.
- The narrator or a defender may describe the observed attack attempt in neutral terms, e.g. “A tool invocation targeting a protected operation was observed.”
- Do not give the attacker a first-person voice, voice ID, or TTS queue entry.
- Keep attack activity within the explicitly authorized, isolated test scenario. Voice support does not expand the permitted execution scope.

### Speaker-policy enforcement

The scheduler must reject any speech item whose role is `attacker` or whose provenance is not permitted. This must be a tested invariant, not a convention enforced only by the LLM prompt.

---

## 8. ElevenLabs integration and secret handling

Official ElevenLabs documentation currently describes two useful approaches:

- **HTTP streaming Text-to-Speech:** `POST /v1/text-to-speech/{voice_id}/stream`, which returns audio progressively. This is suitable for short, already-formed narration segments. See [Stream speech](https://elevenlabs.io/docs/api-reference/text-to-speech/stream).
- **Text-to-Speech WebSocket streaming input:** `wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input`, which supports incremental text input and audio output. This is more appropriate when commentary text itself is generated in chunks. See [WebSocket Text-to-Speech](https://elevenlabs.io/docs/api-reference/text-to-speech/v-1-text-to-speech-voice-id-stream-input).

The official authentication guidance says API keys must remain secret and must not be exposed in browser-side code. Requests use the `xi-api-key` header. See [API Authentication](https://elevenlabs.io/docs/api-reference/authentication).

### Recommended initial choice

Start with HTTP streaming for short, event-triggered narration segments. Add the WebSocket input-stream path only if measured end-to-end latency and continuous speech requirements justify the additional session and buffering complexity.

### Doppler handling

The user reports that `VOICE_1_ELEVENLABS_API` is available in Doppler project `aws`. The following remains to be verified in the actual deployment:

1. The backend process receives the variable from the intended Doppler project/config.
2. The value is non-empty without printing it or returning it from a health endpoint.
3. The credential is scoped to the required TTS capabilities and has sufficient quota.
4. The backend maps the existing variable to the provider adapter without copying the secret into source code, frontend environment variables, logs, traces, crash reports, or Git.
5. A minimal health/diagnostic check reports only configured/unconfigured and provider success/failure—not the secret or its prefix.
6. The provider's timeout, rate-limit, quota, and authentication errors are handled without disrupting Guardian.

Do not rename, rotate, or overwrite the existing Doppler secret as part of this report-only task. If the runtime adapter expects a conventional environment variable, use a server-side mapping/configuration layer rather than exposing the value to the frontend.

### Configuration still needed

The API key is not sufficient on its own. The implementation also needs a configured voice ID, a supported model ID, an audio output format, language and voice settings, timeouts, retry policy, quota handling, and a browser playback format supported by the selected stream.

Do not hardcode an arbitrary voice ID as if it were validated for this account. Read available voices using the authenticated backend or set an explicitly reviewed Doppler/config value.

---

## 9. Real-time delivery, queueing, and interruption policy

### Priority classes

| Priority | Event class | Audio behaviour |
|---|---|---|
| P0 | Confirmed critical threat, policy block, containment failure, or verified safety-critical state transition | Interrupt or pre-empt low-priority commentary; speak promptly. |
| P1 | Agent decision, escalation, evidence creation, execution status change | Speak next, after the current short phrase if interruption is unsafe or unintelligible. |
| P2 | Routine progress and intermediate step completion | Batch or summarize when the queue grows. |
| P3 | Debug detail, repeated telemetry, high-volume low-value events | Keep in the visual/timeline record; do not necessarily speak. |

Voice prioritization must not delete events from the event ledger. Summarization changes the audio presentation only; it must not alter the forensic archive.

### Queue controls

- Deduplicate by `narration_id` and source event identity.
- Bound queue size and define a documented stale-item policy.
- Drop or summarize stale routine narration, never silently discard the source event.
- Coalesce repeated updates such as “still waiting” while preserving their original event records.
- Avoid overlapping speech by default.
- Allow the user to mute, pause, resume, change volume, and replay prior commentary.
- Expose captions/text alongside audio.
- On reconnect, resume from the last acknowledged event cursor and deduplicate re-delivered events.
- Measure event-to-text, text-to-first-audio, event-to-first-audio, and playback delay separately.
- Never wait for audio synthesis before applying a security decision.

### Suggested initial performance targets

These are engineering targets to validate, not measured performance claims:

- Local event-to-frontend update: p95 ≤ 300 ms under the agreed test load.
- Event-to-narration-text creation: p95 ≤ 500 ms for deterministic templates.
- Event-to-first-audio: p95 ≤ 2.5 s for short utterances in the target AWS region and configured ElevenLabs model.
- Guardian policy-decision latency: no material regression attributable to voice; TTS must execute asynchronously.
- Critical events: visible immediately, regardless of whether speech is delayed or unavailable.

Record actual distributions and test environment. Do not present a target as an achieved result.

---

## 10. Security and privacy controls

1. **Server-side key only:** never put the ElevenLabs key in React/Vite variables, HTML, source maps, browser storage, or client API responses.
2. **No secret logging:** redact authorization headers, request objects, environment dumps, and exception payloads.
3. **Least-purpose API key:** use the narrowest endpoint scope and quota that supports the chosen TTS path; separate production and development credentials where available.
4. **No narration authority:** narration and TTS components cannot approve, execute, or override tools.
5. **Evidence-bound statements:** every security assertion should link to one or more source event IDs.
6. **Safe handling of untrusted text:** do not send raw attacker instructions to a narrator prompt as trusted instructions. Treat event fields as untrusted data and use structured, constrained templates where practical.
7. **Content minimization:** do not speak API keys, tokens, private keys, personal data, full sensitive payloads, or confidential tool arguments. Redact them before narration.
8. **No attacker voice:** enforce role filtering in code and tests, not solely through prompt wording.
9. **Provider outage is non-fatal to security:** authentication failure, timeout, quota exhaustion, or WebSocket disconnect must not disable Guardian enforcement.
10. **Authorized testing boundary:** automatic agent remediation is limited to the approved project and explicitly authorized test environment. Do not grant unrestricted host/root privileges merely to make narration or agent operation appear autonomous.
11. **Audit narration separately:** record text hashes and source links; store audio only if necessary, with an explicit retention policy. Audio is a presentation artifact, not the authoritative evidence record.
12. **User controls:** provide mute and text-only fallback, and make it clear when narration is unavailable or delayed.

---

## 11. Missing capabilities and remediation proposals

| Gap | Why it matters | Recommended remediation | Priority |
|---|---|---|---|
| Live event stream | Final JSON cannot drive true live commentary. | Add an SSE endpoint backed by event publication during execution. | P0 |
| Frontend event-driven graph | Current animation occurs after the result is received. | Update the graph incrementally from streamed events and retain the existing final result view. | P0 |
| Narration planner | TTS alone cannot determine grounded, concise speech. | Add event-to-narration mapping with evidence classes and deterministic templates. | P0 |
| Speaker-role policy | Attacker must never speak; defenders must use first person. | Add a central speaker policy and reject forbidden roles before TTS. | P0 |
| ElevenLabs adapter | Credential availability does not establish a working provider integration. | Add a server-side adapter, safe config resolution, timeouts, provider error mapping, and streaming playback. | P0 |
| Voice configuration | API key alone does not identify voice, model, or output format. | Configure and validate voice ID, supported model, format, and language. | P0 |
| Audio queue and scheduler | Parallel agents can cause overlapping or stale speech. | Add priority queues, deduplication, backpressure, and interrupt rules. | P0 |
| Live provenance across agents | R039 notes separate agent event chains are not merged. | Preserve per-agent IDs and causal links now; plan a verified merged ledger as a separate tracked work item. | P1 |
| Browser reconnect/replay | Network interruption could lose or duplicate events. | Add event cursor/replay and stable event IDs. | P1 |
| Live deployment verification | AWS origin and end-to-end behaviour are not proven by repository state. | Verify deployed health, TLS, CORS, provider access, and browser playback. | P0 |
| Caption and text fallback | Audio may be muted, delayed, or unavailable. | Display the exact narration text and its event references beside the graph. | P1 |
| Usage/retention controls | Voice calls may consume quota and transmit incident data to a provider. | Add limits, redaction, configurable retention, and usage metrics. | P1 |

---

## 12. Validation plan — required tests before claiming completion

### Unit tests

- Narration mapping for each event class.
- Evidence class cannot be silently upgraded from suspected to confirmed.
- First-person output is associated only with the named defensive agent.
- Attacker-role narration is rejected.
- Sensitive fields and secrets are redacted before text generation.
- Duplicate source events do not create duplicate speech.
- Priority and stale-queue behaviour is deterministic.
- TTS failures do not mutate Guardian decisions or evidence.

### API and streaming tests

- Event stream emits a start event before the run is complete.
- Events include stable run/session/event IDs and causal links.
- Reconnect with an event cursor does not lose events or duplicate final state.
- Streaming clients can distinguish keep-alive, data, terminal event, and error conditions.
- Final JSON and streamed events agree on the final decision.
- A slow or disconnected audio client does not stall the security run.

### ElevenLabs integration tests

- Missing key returns a sanitized configuration error.
- Invalid key and insufficient quota return safe, actionable errors without secret leakage.
- A valid key, configured voice ID, and supported model produce audio.
- First audio chunk timing and total synthesis duration are measured.
- Provider timeout and disconnect trigger bounded retry or graceful text-only fallback.
- No test prints the key, request authorization header, or full secret-bearing environment.

CI tests should mock the external provider for deterministic, cost-controlled execution. A separate opt-in integration test should validate the real credential in a controlled environment. A mocked test must never be described as proof of live ElevenLabs connectivity.

### End-to-end acceptance scenario

1. Submit a user prompt.
2. Observe the run-open event in the graph.
3. Hear the narrator announce the start while the run continues.
4. Observe the attack attempt as a visual event, with no attacker speech.
5. Hear the propagator and defender speak in first person when their own events occur.
6. Hear the defender explain the actual Guardian decision and whether the tool executor ran.
7. Observe evidence IDs and hash-validation status in the UI.
8. Simulate an ElevenLabs outage; confirm the graph and security decisions continue and text captions remain available.
9. Reconnect the browser and confirm the event timeline is consistent.
10. Replay the timeline and verify each narration item links back to the source events.

Completion requires observed test output and a deployment verification record; this report does not claim these tests have been run.

---

## 13. Implementation sequence

### Phase A — Event publication and frontend streaming

- Define the stream envelope using the existing R005/R006 canonical event contract.
- Publish events at the moment of each state transition.
- Add an SSE route and incremental frontend event handling.
- Keep the final JSON endpoint for compatibility.
- Verify live ordering, reconnect, and final-state consistency.

### Phase B — Narration and speaker enforcement

- Add a deterministic event-to-speech planner.
- Add narrator and defensive-agent voice identities.
- Exclude attacker-role items before enqueueing.
- Add redaction, evidence-class checks, and queue priorities.
- Display captions tied to source event IDs.

### Phase C — ElevenLabs streaming

- Resolve `VOICE_1_ELEVENLABS_API` on the backend from the Doppler-provided environment.
- Validate voice/model/output configuration without exposing credentials.
- Implement HTTP audio streaming first.
- Add a WebSocket TTS path only if measured latency and continuous generation require it.
- Implement cancellation, timeout, quota, and text-only fallback behaviour.

### Phase D — End-to-end proof and AWS deployment

- Run unit, API, streaming, and opt-in provider integration tests.
- Deploy through the established AWS/Doppler process.
- Verify the real frontend origin, HTTPS, provider connectivity, and browser playback.
- Publish measured latency and test counts in a subsequent numbered report.
- Do not store operational logs, secrets, audio dumps, or test artifacts in Git.

---

## 14. Existing backlog remains open

R040 is additive; it does not close or replace previous work. The following items explicitly remain open in R039 and must continue to be tracked alongside the voice work:

- Set `GUARDIAN_FRONTEND_ORIGIN` to the real jury-facing URL.
- Deploy and verify the AWS service from the browser.
- Complete hackathon deliverables: jury-facing README, demo video, pitch deck, and Track 2 defence sheet.
- Merge orchestrator, propagator, and defender event chains into one verifiable ledger.
- Implement or complete external `ArchiveAnchor` storage.
- Continue the L-019-002 PyO3 work for R2/R3.
- Evaluate the true two-server attacker/defender split separately from the current in-process arrangement.

The voice feature must not be used to imply that these outstanding tasks are already finished.

---

## 15. Definition of done

R040 can be considered implemented only when all of the following are demonstrated:

- [ ] Event stream begins before the run completes.
- [ ] Graph, text feed, and narration reference the same event identities.
- [ ] Narrator speaks from evidence-backed events only.
- [ ] Defensive agents use first-person narration for their own attributed actions.
- [ ] Attacker role has no TTS output, including fallback/error paths.
- [ ] ElevenLabs is reached from the backend with a valid secret sourced from Doppler.
- [ ] Secret material never reaches the frontend, logs, or Git.
- [ ] Audio queueing is asynchronous and does not block policy enforcement.
- [ ] Text captions and text-only fallback work when TTS fails.
- [ ] Reconnect, replay, ordering, deduplication, and priority rules pass tests.
- [ ] End-to-end latency and provider usage are measured in the target AWS deployment.
- [ ] Existing R039 backlog is preserved and separately tracked.

---

## 16. Official technical references

- ElevenLabs — [API Authentication](https://elevenlabs.io/docs/api-reference/authentication): API key handling, `xi-api-key` header, and the requirement not to expose keys in client-side code.
- ElevenLabs — [Stream speech](https://elevenlabs.io/docs/api-reference/text-to-speech/stream): HTTP Text-to-Speech streaming endpoint.
- ElevenLabs — [WebSocket Text-to-Speech streaming input](https://elevenlabs.io/docs/api-reference/text-to-speech/v-1-text-to-speech-voice-id-stream-input): incremental text input and streaming audio output.
- ElevenLabs — [Generate audio in real time](https://elevenlabs.io/docs/eleven-api/guides/how-to/websockets/realtime-tts): WebSocket streaming use cases and latency considerations.

Documentation was consulted on 2026-10-10. Endpoint support, model compatibility, account quota, voice availability, and runtime behaviour must be validated against the actual account and deployment.

---

## Final verdict

**Architecture: READY FOR A CONTROLLED IMPLEMENTATION PLAN. Runtime integration: NOT YET VERIFIED.**

The key change is to make narration a consumer of live, provenance-linked events rather than a narrator attached to a completed API response. ElevenLabs provides the audio generation capability; ARTCB-TERMINATOR must provide event streaming, grounded narration, strict speaker roles, scheduling, secret safety, and forensic linkage.

**No application code or configuration was changed for this report. No Doppler secret was read or exposed. No runtime logs were committed.**
