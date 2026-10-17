# R098 — Independent Audit of CameraHoloOverlay, MediaPipe Runtime, and KYC Lifecycle

**Date:** 2026-10-17  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Branch inspected:** `main`  
**Inspected HEAD:** `631a5e8055851880c752406945aac4f0cbfaaa4d`  
**Scope:** Read-only review of `frontend/src/components/CameraHoloOverlay.tsx`, `frontend/src/components/KycPanel.tsx`, and `frontend/package.json`. No application source, deployment, configuration, or runtime logs were modified.

## Expertise Activated

- React and TypeScript lifecycle auditing
- Browser media capture and permission handling
- MediaPipe Tasks Vision / WASM runtime compatibility
- Frontend reliability and main-thread performance
- KYC security boundaries and biometric claim accuracy
- Evidence provenance and validation methodology

## Executive Finding

The component and its KYC-panel integration are present in the inspected source. The source supports several implementation claims made in the supplied R098 draft, including five camera states, explicit stopping of stream tracks, a cleanup effect, lazy MediaPipe initialization, a canvas overlay, and a separate animation-frame loop.

However, source inspection does **not** establish successful operation with a physical camera or certify biometric identity. This independent review also identifies lifecycle and compatibility risks that should be tested before describing the feature as operationally complete.

**Certification remains false:** `CERTIFIED_100=false` and `unique_human_proven=false`.

## 1. Repository State and Evidence Boundary

The inspected remote HEAD is `631a5e8055851880c752406945aac4f0cbfaaa4d`, whose commit message identifies R097. The reports directory contained R095, R096, and R097; no R098 report file was present when this review began. This document records R098 in the reports directory.

Source review is not a browser execution test. No claim is made here that the production bundle was built, a physical camera was opened, or browser behavior was exercised during this audit.

## 2. Findings

### F-098-01 — P1: Camera stream may remain active after an activation failure or unmount race

**Process — how it works:** `startCamera()` awaits `navigator.mediaDevices.getUserMedia()`, stores the returned stream in `streamRef.current`, assigns it to the video element, and awaits `video.play()`. The error handler changes the UI state but does not itself stop any stream already acquired. The unmount cleanup stops the stream currently held by the ref.

**Problem — what can go wrong:** If `getUserMedia()` succeeds but `video.play()` rejects, control enters the catch branch while the acquired stream remains stored and its tracks are not explicitly stopped there. A second lifecycle edge case exists if the component unmounts while the permission request is pending: cleanup may run before the promise resolves, after which the resolved stream can be assigned to the ref without a subsequent cleanup. These paths can leave the camera active longer than intended.

**Solution — recommended correction:**
1. Track cancellation/unmount while awaiting permission and stop any stream that resolves after cancellation.
2. In the activation catch path, stop every track from any locally acquired stream and clear `srcObject`.
3. Use a single idempotent cleanup routine for activation failure, explicit stop, and unmount.
4. Add tests for rejected `play()`, permission resolution after unmount, repeated start/stop, and camera-track termination.

**Acceptance criterion:** every failed or cancelled activation ends with all acquired tracks stopped and `video.srcObject` cleared; tests verify this rather than relying only on the displayed state.

### F-098-02 — P1: The MediaPipe package and WASM runtime use different explicit versions

**Process — how it works:** `frontend/package.json` declares `@mediapipe/tasks-vision: ^1.1.1`, while `loadFaceLandmarker()` explicitly loads WASM assets from `@mediapipe/tasks-vision@0.10.22/wasm`.

**Problem — what can go wrong:** the JavaScript API and WASM runtime are not pinned to the same release. This is a compatibility risk, not proof that the combination necessarily fails. It also makes a future dependency update capable of changing the JavaScript package without updating the separately pinned runtime.

**Solution — recommended correction:**
1. Prefer a single explicitly pinned MediaPipe release for both the npm package and WASM asset path, or use the package's matching WASM directory.
2. If an intentionally mixed version is required, document the reason and add an automated compatibility test.
3. Validate cold-cache loading, WASM fetch failures, model fetch failures, and initialization on supported browsers.
4. Record the resolved package version from the lockfile in the release evidence.

The official package documentation demonstrates resolving vision WASM assets from the matching package CDN path. See the [MediaPipe Tasks Vision package documentation](https://www.npmjs.com/package/@mediapipe/tasks-vision) and [FilesetResolver reference](https://developers.google.com/edge/api/mediapipe/js/tasks-vision.filesetresolver).

**Acceptance criterion:** the production build and a real browser test load the selected JS, WASM, and model assets successfully from a documented compatible release.

### F-098-03 — P1: GPU-only delegate has no explicit CPU retry

**Process — how it works:** FaceLandmarker initialization requests `delegate: 'GPU'`. Initialization failures are caught and converted to a `null` result; the UI can continue with the scan-only animation.

**Problem — what can go wrong:** a browser/device that cannot initialize the GPU delegate will not attempt a CPU delegate. The graceful visual fallback avoids crashing the overlay, but it does not provide face landmark detection on that device.

**Solution — recommended correction:**
1. Attempt GPU initialization first.
2. On an initialization failure, close any partially created resources and retry with `delegate: 'CPU'`.
3. If both attempts fail, report the actual capability state distinctly from camera availability.
4. Test GPU success, GPU failure with CPU success, and failure of both delegates.

**Acceptance criterion:** the UI distinguishes camera-active/model-unavailable from camera-active/face-landmarker-ready, and a forced GPU failure demonstrates the CPU retry.

### F-098-04 — P1: Synchronous frame inference can block the browser main thread

**Process — how it works:** the animation-frame loop invokes `landmarkerRef.current.detectForVideo(video, performance.now())` directly from the component's browser-side animation loop.

**Problem — what can go wrong:** synchronous inference consumes main-thread time. On slower devices or high-latency frames, it can delay rendering and user interactions. The source does not include measurements proving that this impact is acceptable for the supported device range.

**Solution — recommended correction:**
1. Measure inference duration and frame-to-frame latency on representative low-, mid-, and high-performance devices.
2. Consider moving inference to a worker/OffscreenCanvas architecture if measurements show main-thread contention and the supported browser matrix allows it.
3. Avoid processing duplicate frames; record dropped/late-frame metrics.
4. Ensure KYC decision and defensive processing never depend on the animation loop completing.

**Acceptance criterion:** publish measured p50/p95 inference duration, dropped-frame rate, and UI responsiveness for the supported test matrix. Do not claim real-time performance without these measurements.

### F-098-05 — P2: MediaPipe task lifetime is not explicitly closed

**Process — how it works:** the component stores the created FaceLandmarker in `landmarkerRef.current`. The shown `stopCamera()` cleanup cancels the animation frame and stops media tracks, but does not explicitly close the FaceLandmarker task.

**Problem — what can go wrong:** stopping and restarting the camera, or repeatedly mounting/unmounting the component, may retain native/WASM task resources longer than intended depending on the library lifecycle.

**Solution — recommended correction:** define explicit ownership of the FaceLandmarker instance; call its documented close/dispose method when the owning component is finished with it, and reset the reference. If the instance is deliberately shared, use a managed singleton lifecycle with clear ownership and tests.

**Acceptance criterion:** repeated mount/start/stop/unmount cycles do not show growing memory or retained task resources in a browser profiling run.

### F-098-06 — P2: KYC busy state prevents starting the camera but does not stop an already-active camera

**Process — how it works:** the camera activation button is disabled when `kycRunning` is true. When the camera is already active, the rendered control is the stop-camera button, which is not disabled by the same condition.

**Problem — what can go wrong:** the implementation prevents starting a new camera session during KYC but does not automatically stop an existing camera session when KYC begins. This may be intentional because the camera and KYC stream are independent, but the behavior must be explicit; the current prop name alone does not enforce a mutual exclusion policy.

**Solution — recommended correction:** document the intended policy. If concurrent operation is permitted, add a test and visible status showing that camera capture and KYC processing can run simultaneously. If mutual exclusion is required, implement and test a deliberate state transition rather than relying only on disabling the start button.

**Acceptance criterion:** product behavior and tests explicitly define whether camera capture may continue during a KYC run.

## 3. Biometric Claims and Security Boundary

Face landmarks indicate that the model localized facial features in an image. They do not prove:
- that the person is unique;
- that the person is the claimed identity;
- that the input is live rather than a replay or presentation attack;
- that the camera feed has not been manipulated upstream.

The holographic canvas is a visualization layer, not a liveness detector or cryptographic proof. Keep `unique_human_proven=false` and `CERTIFIED_100=false` until independent evidence supports stronger claims.

If the camera is not an authoritative KYC input, its status must not be treated as a KYC pass/fail signal. If it is intended to contribute to identity verification, define the threat model, consent flow, presentation-attack controls, measured FAR/FRR, and independent validation protocol first.

## 4. Validation Plan

| Test | Required result | Status in this audit |
|---|---|---|
| TypeScript/Vite production build | Build succeeds with the committed lockfile | Not executed |
| Physical camera permission granted | Video starts and all states update correctly | Not executed |
| Permission denied / device missing | Clear error state, no retained stream | Not executed |
| `video.play()` rejects | All acquired tracks are stopped | Source risk identified; test not executed |
| Unmount while permission is pending | Late-resolving stream is stopped | Source risk identified; test not executed |
| GPU initialization fails | CPU retry succeeds or explicit unavailable state appears | No CPU retry in inspected source |
| WASM/model download fails | Clear model-unavailable state and retry behavior | Not executed |
| Repeated start/stop/unmount | No retained tracks or task-resource growth | Not executed |
| KYC starts while camera active | Matches documented concurrency policy | Not executed |
| Biometric claims | No uniqueness/liveness claim without separate evidence | Claim flags remain false |

## 5. Prioritized Remediation

1. **P1:** guarantee stream cleanup for all failure and unmount races.
2. **P1:** align and pin the MediaPipe JS/WASM release; validate the actual deployed assets.
3. **P1:** add explicit GPU-to-CPU initialization fallback.
4. **P1:** benchmark synchronous inference and isolate it if measured performance requires it.
5. **P2:** define FaceLandmarker resource ownership and disposal.
6. **P2:** document and test camera/KYC concurrency behavior.
7. Preserve the existing false certification flags until all acceptance criteria have independent evidence.

## 6. Change Boundary

This report is the only intended repository change for this audit. No application code, test files, deployment settings, credentials, or runtime logs were changed. No logs were added to Git. The historical `vgactech/artcb` repository was not modified.

## Final Status

**Source review: completed for the three listed files.**  
**Browser/device validation: not performed.**  
**Biometric uniqueness: not proven.**  
**Certification: false.**

The next step is to implement and test the lifecycle and runtime-compatibility corrections in the authorized TERMINATOR project, then update the audit only with results that can be reproduced.
