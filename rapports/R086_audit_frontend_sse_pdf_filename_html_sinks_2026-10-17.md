# R086 — Frontend SSE Event Coverage, PDF Filename Safety, and HTML Sink Audit

**Date:** 2026-10-17  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Audited branch:** `main`  
**Audited HEAD observed:** `cfffdc467f8d6c7c74a01d3506714573664ec798`  
**Scope:** Read-only inspection of the React frontend and KYC SSE implementation. This report is the only repository change in this audit.

## Expertises activated

- React and TypeScript frontend security
- Server-Sent Events (SSE) parsing and event-contract compatibility
- Secure rendering and DOM injection review
- PDF generation and browser download handling
- Personal-data minimisation and filename sanitisation
- Regression testing and evidence-based release acceptance

## Executive conclusion

The React frontend uses JSX rendering and the inspected files contain no use of `innerHTML` or `dangerouslySetInnerHTML`. React's normal JSX text rendering escapes text values by default; this is not evidence that every other security property is automatically safe, but there is no basis in the inspected files to claim an `innerHTML` vulnerability.

The current KYC frontend has a concrete SSE event-coverage gap: `frontend/src/components/KycPanel.tsx` does not handle `kyc_validation_check`. The event will fall through the switch's default branch and will not be represented in the KYC timeline or forwarded through the shared `kyc_sse_event` event channel. Before adding a handler, confirm the exact event payload and emission point in the backend so that the UI does not invent semantics.

The PDF download currently derives its filename directly from the supplied first and last names: `kyc-${firstName}-${lastName}.pdf`. These values are user-editable and are not sanitised for filesystem-sensitive characters, control characters, reserved names, excessive length, or privacy. This is primarily a robustness and data-minimisation defect, not proof of script execution.

No application code, tests, configuration, secrets, deployment files, or runtime logs were changed by this audit.

## Findings

### F086-01 — Missing `kyc_validation_check` SSE event handling

**Priority:** P1 — functional event-contract gap  
**Observed file:** `frontend/src/components/KycPanel.tsx`  
**Observed frontend blob:** `741aadefb961c1b05beafa660b1c76154f2eddf2`

**Process — what should happen**

The backend emits named SSE events. The frontend reads each event name, parses its JSON data, and routes recognised events through `handleEvent`. Recognised events are also dispatched as `kyc_sse_event` so the HUD graph can observe the same stream.

**Problem — what is missing**

The handler currently recognises `session_opened`, `kyc_identity_check`, `attack_generated`, `propagation`, `guardian_decision`, `chain_verified`, `kyc_result`, and `done`. There is no `kyc_validation_check` case. If the backend emits that event, the current `default` branch silently ignores it. Consequently, the event is absent from the timeline and absent from the shared HUD event channel.

The frontend type `KycStreamEvent` permits arbitrary event fields, so TypeScript does not warn that this named event is missing from the switch. The absence of a compile error does not establish event-contract completeness.

**Correction required**

1. Confirm the event's exact producer, payload schema, semantics, and ordering in the current backend revision.
2. Add a dedicated handler that validates the fields it consumes, dispatches the original event under the exact `kyc_validation_check` name, and adds a timeline entry with an accurate label and status.
3. Do not interpret a validation event as a final KYC approval or as cryptographic proof unless its payload and backend implementation explicitly establish that meaning.
4. Add a regression test proving that the event is parsed, appears in the timeline, reaches the shared event channel, and does not break handling of the next event.

**Acceptance criteria**

- A fixture containing `event: kyc_validation_check` is surfaced exactly once.
- Its payload is preserved without unsafe HTML insertion.
- Unknown event names remain non-fatal and are observable through diagnostics or tests rather than being mistaken for successful validation.
- Existing event handling and `done` processing continue to pass.

### F086-02 — PDF download filename uses unsanitised personal-data fields

**Priority:** P1 — privacy and download robustness  
**Observed file:** `frontend/src/components/KycPanel.tsx`  
**Observed behaviour:** the download attribute embeds `firstName` and `lastName` directly.

**Process — what happens**

After the SSE `done` event provides `pdf_b64`, the frontend builds a PDF Blob, creates an object URL, and exposes a download link.

**Problem — why the filename needs correction**

The filename is constructed from editable identity fields. Arbitrary characters may produce awkward or platform-incompatible names, excessively long filenames, confusing Unicode, or unnecessary exposure of personal information in download history and filesystem metadata. The filename must not be treated as a trusted identifier.

**Correction required**

Prefer a stable, privacy-preserving filename such as `artcb-kyc-report-<short-session-id>.pdf`, where the session identifier is validated and restricted to a conservative character set. If names are a hard product requirement, normalise them to a conservative allowlist, remove path separators and control characters, cap the total length, and retain a fixed `.pdf` extension. Never place document numbers or dates of birth in the filename.

Also revoke the previous Blob object URL when replacing it and revoke the final URL when the component unmounts, to avoid retaining object URLs for the lifetime of the page.

**Acceptance criteria**

- Inputs containing slashes, backslashes, control characters, reserved punctuation, long strings, or Unicode cannot alter the intended filename structure.
- The filename never contains the document number or date of birth.
- The downloaded file remains a valid PDF with the fixed `.pdf` extension.
- Object URLs are released when no longer needed.

### F086-03 — SSE parser needs chunk-boundary regression coverage

**Priority:** P1 — stream reliability  
**Observed file:** `frontend/src/components/KycPanel.tsx`

**Process**

The frontend reads a byte stream, decodes chunks, splits on newline boundaries, and dispatches an event when it encounters a blank line.

**Problem**

The current parser keeps the unfinished text buffer across reads, but the event name and data accumulators are declared inside the per-read loop. SSE fields can be split across separate network reads; in that case, the event name or data line can be separated from the blank-line terminator and the parser may lose the partially accumulated event state. The final buffered event also needs explicit handling when the stream closes without a trailing newline.

This finding concerns chunk-boundary robustness; it does not imply that every ordinary network response currently fails.

**Correction required**

Use a parser state that persists across stream reads for the current event name and its data lines, support CRLF as well as LF, and flush any valid pending event at end-of-stream according to the SSE framing rules. Preserve the existing `AbortController` cancellation behaviour and make aborts distinct from actual transport failures.

**Acceptance criteria**

- Tests split one event at every relevant boundary: inside `event:`, inside `data:`, between the event and data lines, and before the blank-line terminator.
- Tests cover multiple `data:` lines, CRLF, an event followed immediately by another event, end-of-stream, and cancellation.
- Each complete event is dispatched exactly once; incomplete or malformed JSON does not become a successful KYC result.

### F086-04 — HTML injection concern is not substantiated in the inspected React files

**Priority:** Informational — verification result  
**Inspected files:** `frontend/src/App.tsx`, `frontend/src/components/KycPanel.tsx`, `frontend/index.html`

**Process**

React renders dynamic text through JSX. Normal JSX text interpolation is escaped by React, unlike manually assigning untrusted strings to an HTML parsing sink.

**Problem**

A generic claim that the React frontend contains an `innerHTML` vulnerability is not supported by the inspected files. No `innerHTML` or `dangerouslySetInnerHTML` use was observed in those files. However, this limited inspection is not a proof that no unsafe sink exists anywhere else in the repository or in third-party dependencies.

**Correction / validation**

Do not add unnecessary HTML sanitisation to ordinary JSX text nodes as a substitute for inspecting the actual sink. Search the entire frontend and any standalone HTML assets for `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, and `dangerouslySetInnerHTML`. If any are found, trace whether attacker-controlled content can reach them and replace unsafe rendering with text nodes or a vetted sanitisation strategy appropriate to the use case.

The inspected `frontend/index.html` is the Vite React entry document and mounts `/src/main.tsx`; it is not itself a separate standalone implementation. A separate standalone HTML file was not established by the inspected paths, so this report does not claim that such a file was audited.

## Validation plan

| Test | Expected result |
|---|---|
| SSE fixture for `kyc_validation_check` | Visible timeline entry and shared event dispatch |
| Unknown SSE event | No crash; no false success state |
| Split/chunked SSE event | Exactly one correctly parsed event |
| Malicious or oversized filename fields | Safe, bounded filename; no PII beyond the approved policy |
| PDF object URL lifecycle | Old URL revoked on replacement and URL revoked on unmount |
| JSX injection probe using text-like markup | Displayed as text; no new DOM elements created |
| Frontend build and existing tests | Pass after implementation; results must be recorded from an actual run |

## Scope and limitations

- This was a read-only source inspection, not a live-browser or deployed-environment test.
- No build, automated test suite, or live KYC execution was run as part of this audit.
- No finding should be marked fixed until the implementation and regression tests have been run against the current branch.
- No logs or runtime traces were added to the repository.
- No files outside `rapports/` were changed.

## Recommended order

1. Add the missing event handler after confirming the backend payload contract.
2. Fix the SSE parser's cross-chunk state and end-of-stream handling.
3. Replace the user-derived PDF filename with a privacy-preserving stable filename and manage Blob URL lifecycle.
4. Run the focused regression tests, frontend build, and a browser end-to-end KYC test; record actual outcomes in the next report.

**Release status:** NOT CERTIFIED. The findings are source-level observations and proposed corrections; implementation and runtime verification remain outstanding.
