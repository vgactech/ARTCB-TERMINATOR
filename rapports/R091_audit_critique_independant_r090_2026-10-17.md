# R091 — Independent Critical Review of R090

**Project:** ARTCB-TERMINATOR  
**Review date:** 2026-10-17  
**Reviewed remote HEAD:** `6f035d2b551d523fc7740b2bd41a09b9322d8b63`  
**Scope:** Read-only review of R090 changes in KYC validation, Server-Sent Events (SSE), Blob URL lifecycle, rate-limit test isolation, and repository hygiene. No application code was modified during this review.

## Executive assessment

R090 contains useful security and correctness improvements, but the supplied “100%” completion status is not equivalent to independent acceptance. The commit is present on `main`; its commit metadata reports 185 passing tests, but this review did not execute the test suite independently.

**Assessment: PARTIALLY ACCEPTED — follow-up required.** The most important remaining concerns are: (1) date-of-birth validation still accepts future dates through year 2100 and Python's `strptime` is not by itself an exact-format validator; (2) the SSE reader still dispatches an incomplete event at EOF and does not visibly flush the decoder or process the final unterminated buffer; (3) `URL.revokeObjectURL` and `URL.createObjectURL` are side effects inside a React state updater; and (4) the broad autouse rate-limiter reset can weaken the realism of tests that need to verify rate-limit state across requests or concurrent tests.

## Expertise activated

- Python date/time parsing and KYC validation logic
- Frontend React state lifecycle and browser Blob URL resource management
- WHATWG Server-Sent Events parsing and streaming boundary behavior
- API rate-limiting and automated-test isolation
- Git commit and repository-hygiene review

## Findings

### R091-01 — P1: A birth date in the future can pass validation

**Process — what happens:** R090 parses the supplied value using `datetime.strptime(dob.strip(), "%Y-%m-%d")` and accepts any parsed year from 1900 through 2100.

**Problem — why it matters:** This rejects impossible calendar dates such as February 31, but it does not reject a date of birth that is in the future. For example, a valid calendar date in 2029 can pass the year-range check even though the current review date is in 2026. In addition, `strptime` accepts some non-zero-padded month/day representations on common Python implementations, so it should not be treated as a strict enforcement of the literal `YYYY-MM-DD` wire format.

**Solution:** Require an exact ASCII date shape first (four digits, hyphen, two digits, hyphen, two digits), then parse it as a calendar date, then reject dates later than the current date in the agreed business timezone. Keep any minimum-age or maximum-age policy as a separate, explicit business rule rather than conflating it with calendar validity. Add tests for `2999-02-31`, `2029-01-01`, `2000-1-1`, leap days, year boundaries, whitespace, and malformed Unicode digits.

**Acceptance criteria:** Invalid calendar dates, non-canonical date strings, and future birth dates produce a hard rejection before downstream fraud simulation or approval logic runs.

### R091-02 — P1: The SSE EOF handling still treats an incomplete event as dispatchable

**Process — what happens:** The frontend accumulates `data:` lines and calls `handleEvent` when it sees a blank line. After the read loop, it also calls `handleEvent` if `curData` remains non-empty.

**Problem — why it matters:** Under the EventSource parsing algorithm, a blank line dispatches an event. EOF alone is not a substitute for that blank-line delimiter. Dispatching a truncated event can cause partial JSON to be parsed or silently discarded, and can make the client appear to have received a complete terminal event when the stream was cut off.

The reviewed loop also does not visibly call `decoder.decode()` without arguments to flush any buffered decoder state, nor does it process the remaining `buf` after EOF. A final unterminated line can therefore be lost. The CRLF normalization is performed independently on each decoded chunk; a CRLF pair split across chunks needs explicit handling to avoid producing an unintended extra line boundary.

**Solution:** Use a tested SSE parser or implement a state machine that preserves delimiter state across chunks. At EOF, flush the TextDecoder and process any remaining text according to the parser's line rules, but do not dispatch a pending event unless a valid blank-line delimiter was received. Add deterministic tests where CRLF, UTF-8 multibyte characters, the final line, and the event delimiter are split at every possible chunk boundary.

**Acceptance criteria:** Complete events are dispatched exactly once; incomplete events at EOF are not dispatched; no line or character is lost or duplicated at chunk boundaries.

### R091-03 — P2: Blob URL creation and revocation are side effects inside a React state updater

**Process — what happens:** R090 uses a functional `setPdfUrl(prev => ...)` updater that revokes the previous URL and creates a new URL.

**Problem — why it matters:** React state updater functions should be pure. In development Strict Mode, React may invoke updater functions more than once to detect impure logic. Performing resource allocation and revocation inside the updater can therefore create URLs that are never stored, or revoke a URL as part of an updater invocation whose result is not committed. The previous cleanup-on-unmount behavior should also be checked against the current URL ownership model.

**Solution:** Move URL creation and revocation into the imperative stream-handling path or a dedicated effect with a clearly defined owner. Keep the current URL in a ref if necessary; revoke the prior URL exactly once when replacing it and revoke the final URL on unmount. Do not call `setState` from an unmount cleanup merely to clear state that is no longer observable.

**Acceptance criteria:** Repeated KYC runs and component unmounts do not leak URLs, double-revoke active URLs, or allocate untracked URLs under React Strict Mode.

### R091-04 — P2: An autouse limiter reset can mask rate-limit integration behavior

**Process — what happens:** The new pytest autouse fixture resets the shared limiter storage before each test.

**Problem — why it matters:** This is a reasonable isolation technique for tests that should be independent, but it is global test behavior. It can hide cross-request or cross-test state interactions, and it is not a substitute for dedicated tests proving that a single client is throttled after the configured number of requests. Concurrent tests can also interfere with shared limiter state if they run in parallel.

**Solution:** Keep unit-test isolation, but add explicit rate-limit tests that make multiple requests within one test and assert the expected 429 boundary. Where parallel execution is supported, use isolated limiter storage per test/client or mark the shared-state tests as non-parallel. Confirm that the reset fixture is not used to neutralize the very behavior under test.

**Acceptance criteria:** The suite passes both isolated unit tests and explicit end-to-end rate-limit tests, including the configured threshold and recovery/window behavior.

### R091-05 — P2: The reported 185/185 test result is not independently reproduced by this review

**Process — what happens:** The R090 commit message and supplied summary state that 185 tests passed.

**Problem — why it matters:** A commit message is evidence of a reported result, not independent proof that the current remote tree passes in a clean environment. This review only inspected the remote commit and relevant source excerpts; it did not run the suite or inspect a successful CI run.

**Solution:** Link the exact CI run for commit `6f035d2b551d523fc7740b2bd41a09b9322d8b63`, or rerun the test suite from a clean checkout and preserve the test command, environment, exit code, and report as a report artifact—not as a committed runtime log.

**Acceptance criteria:** A successful CI run or reproducible clean-checkout run is tied to the reviewed commit SHA.

## Positive changes verified in the remote diff

- KYC date parsing now rejects impossible calendar dates that passed the former length-and-hyphen check.
- A validation failure now emits a `REJECTED` result and returns before the later fraud-simulation stages.
- SSE `data:` parsing strips at most one optional U+0020 space after the colon instead of applying `trim()` to the payload.
- The `.gitignore` now includes `logs/`.
- The R090 commit removes six previously tracked JSON files under `logs/` (R083, R084, R085, R087, R088, and R089), consistent with the stated repository-hygiene goal.

## Recommended order for R092

1. Close R091-01 and R091-02 first: KYC future-date rejection and SSE parser conformance.
2. Refactor Blob URL ownership so React state updater functions remain pure.
3. Add explicit rate-limit boundary tests and validate the fixture under the project's supported test execution modes.
4. Attach clean, commit-specific CI evidence for the claimed 185/185 pass result.
5. Recheck the three Dependabot alerts from GitHub's alert view; do not infer their package names or severity details from `npm audit` alone.

## Change boundary

This report is the only proposed artifact from this review. No application source, configuration, lockfile, test file, or runtime log was modified by the reviewer.
