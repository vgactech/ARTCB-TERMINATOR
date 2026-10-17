# R093 — Independent Critical Audit of R092

**Project:** ARTCB-TERMINATOR  
**Review date:** 2026-10-17  
**Reviewed remote HEAD:** `74cc9aa009e7e17b907112e3a8d45c295d31f845`  
**Scope:** Read-only review of R092's future-date guard, Blob URL ownership, claimed test coverage, and previously outstanding SSE parsing issue.  
**Change policy:** This audit changes no application code. The only deliverable is this report under `rapports/`.

## Executive assessment

**Assessment: PARTIALLY ACCEPTED — one previously identified P1 remains open.**

The R092 commit is present on `main`. Its commit message reports six new tests and 80/80 passing. The R092 report is also present on the remote branch. This review inspected the remote commit diff, the current KYC date-validation code, the relevant React component code, and the test additions. It did not execute the test suite or independently verify the reported runtime result.

R092 improves the KYC date check by rejecting dates on or after the server's current date, and it moves Blob URL revocation out of React state updater functions. However, the frontend still dispatches a pending SSE event at EOF without requiring the blank-line delimiter. The new Python tests do not directly exercise React's Blob URL lifecycle.

## Expertise activated

- Python date parsing and KYC validation
- React state purity, refs, and component resource cleanup
- WHATWG Server-Sent Events parsing and streaming boundaries
- Test design and evidence quality
- GitHub commit and report-scope verification

## Findings

### R093-01 — P1: Incomplete SSE events are still dispatched at EOF

**Process — what happens:** In `frontend/src/components/KycPanel.tsx`, the stream reader dispatches an event when it encounters a blank line. After the read loop, it additionally calls `handleEvent(curEvent, curData)` whenever `curData` is non-empty. The code comment describes this as flushing an event when the stream ends without a trailing blank line.

**Problem — why it matters:** EOF is not interchangeable with the blank-line event delimiter in the EventSource parsing model. A connection interrupted after a partial `data:` payload can therefore be treated as if it contained a complete event. Since the handler parses JSON and updates visible KYC state, this can make a truncated stream appear to have delivered a valid event. The reader also does not visibly flush the `TextDecoder` with a final no-argument `decode()` call or process the remaining unterminated `buf` at EOF. CRLF pairs split between decoded chunks also require explicit stateful handling.

**Solution:** Replace the hand-written parsing loop with a maintained, tested SSE parser compatible with a POST response body, or implement a small state machine that preserves CR/LF and decoder state across chunks. At EOF, flush the decoder and process residual text according to the line parser, but do not dispatch a pending event unless the required blank-line delimiter was received. Add deterministic tests that split CRLF, UTF-8 multibyte sequences, the final line, and the event delimiter at every relevant chunk boundary.

**Acceptance criteria:**
- A complete event is dispatched exactly once.
- A pending event without its blank-line delimiter is not dispatched at EOF.
- No characters or lines are lost or duplicated across chunk boundaries.
- Malformed or truncated JSON cannot be mistaken for a successful terminal event.

**Status:** OPEN — the inspected R092 diff does not change this parser behavior.

### R093-02 — P2: Date parsing still does not enforce a canonical wire format

**Process — what happens:** The backend parses the input with `datetime.strptime(dob.strip(), "%Y-%m-%d")`, checks the year range, and rejects the parsed date when it is greater than or equal to `date.today()`.

**Problem — why it matters:** The new future-date guard addresses the main R091 finding. However, trimming whitespace and relying on `strptime` does not itself guarantee that the input was supplied in the exact canonical ASCII `YYYY-MM-DD` form. Non-zero-padded representations may be accepted by Python's parser. Also, `date.today()` uses the server's local date; the policy timezone should be explicit if deployments can run in different timezones.

**Solution:** First require an exact ASCII shape of four digits, hyphen, two digits, hyphen, two digits; then parse and validate the calendar date; then compare it with the current date in the explicitly chosen business timezone. Keep minimum-age and maximum-age checks separate from calendar validity. Add tests for `2000-1-1`, surrounding whitespace, malformed Unicode digits, leap days, year boundaries, today, and future dates.

**Acceptance criteria:** Only the agreed canonical representation is accepted, impossible calendar dates are rejected, and the definition of “today” is stable across deployment timezones.

**Status:** PARTIALLY ADDRESSED — future dates are now rejected; strict canonical format and timezone policy remain unproven.

### R093-03 — P2: The six added Python tests do not directly verify React Blob URL lifecycle behavior

**Process — what happens:** The R092 additions in `guardian_api/test_app.py` exercise the backend SSE response contract, including whether `done.pdf_b64` is absent for a rejected KYC flow and whether a valid flow ends with a `done` event. The report itself describes the Blob URL checks as indirect.

**Problem — why it matters:** These tests can verify the backend payload that the frontend consumes, but they cannot prove that `KycPanel` revokes the old URL exactly once, keeps the active URL valid, clears the ref on reset, or cleans up correctly on unmount and under React Strict Mode. The reported 80 passing pytest tests therefore do not establish frontend lifecycle correctness.

**Solution:** Add frontend unit/component tests using the project's existing test framework, with `URL.createObjectURL` and `URL.revokeObjectURL` mocked. Cover replacement by a second PDF, reset, unmount, a rejected flow with no PDF, and repeated effect lifecycle behavior in Strict Mode. Assert the active URL is not revoked before replacement and every created URL is eventually revoked once when no longer owned.

**Acceptance criteria:** Frontend tests directly demonstrate URL ownership and cleanup; backend SSE contract tests remain separate.

**Status:** OPEN — source code shows the ref-based lifecycle change, but direct frontend test evidence was not present in the inspected R092 diff.

## Positive changes verified in the remote diff

- `guardian_api/kyc_stream.py` now rejects a parsed date of birth when `parsed_dob.date() >= date.today()`.
- `KycPanel.tsx` stores the current Blob URL in `pdfUrlRef`, revokes it during reset and unmount cleanup, and performs replacement outside a state updater.
- The R092 report and commit are present on `main`.

These source-level observations do not independently reproduce the reported pytest result or establish frontend test coverage.

## Recommended next actions

1. Fix the SSE EOF/delimiter behavior first; it remains the highest-priority unresolved issue from R091.
2. Enforce canonical date format and define the business timezone for the date comparison.
3. Add direct frontend tests for Blob URL replacement, reset, unmount, and Strict Mode.
4. Capture a CI run tied to the exact commit and report Python and frontend test results separately.
5. Revisit the outstanding Dependabot alerts through the repository's GitHub security interface; the alerts endpoint was not available through the read interface used for this review, so their current count and package details are **not independently verified here**.

## Evidence and limitations

- Reviewed commit: [`74cc9aa`](https://github.com/vgactech/ARTCB-TERMINATOR/commit/74cc9aa009e7e17b907112e3a8d45c295d31f845)
- R092 report: [`R092_dob_future_blob_url_lifecycle_2026-10-17.md`](https://github.com/vgactech/ARTCB-TERMINATOR/blob/main/rapports/R092_dob_future_blob_url_lifecycle_2026-10-17.md)
- Source reviewed: `guardian_api/kyc_stream.py`, `frontend/src/components/KycPanel.tsx`, and the R092 test additions in `guardian_api/test_app.py`.
- No tests were executed by this audit. The reported `80 passed in 8.14s` is attributed to the R092 report and commit message, not to an independent run by this reviewer.
- No application code, configuration, or log files were modified. This report is the sole intended repository change.

**Final status: PARTIALLY ACCEPTED — R092 improves date and Blob URL handling, but SSE EOF parsing remains open and frontend lifecycle tests are still required.**
