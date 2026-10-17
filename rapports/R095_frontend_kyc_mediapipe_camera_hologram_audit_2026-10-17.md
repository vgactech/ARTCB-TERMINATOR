# R095 — Frontend KYC Demo Audit: MediaPipe, Camera Activation, and 3D Hologram

**Project:** ARTCB-TERMINATOR  
**Review date:** 2026-10-17  
**Reviewed remote HEAD:** `f6bcee34dac4235e3f514bd2e2ffd71047124379`  
**Branch:** `main`  
**Scope:** Frontend-only source audit of the KYC demonstration flow, browser camera permission UX, MediaPipe integration readiness, and holographic visualization.  
**Change policy:** Read-only application audit. This commit adds only this report under `rapports/`. No application source, dependency manifest, tests, configuration, secrets, or runtime logs are changed.

## Executive assessment

**Status: NOT READY for a camera-enabled MediaPipe KYC demonstration.**

The current frontend has a KYC panel, a backend POST/SSE flow, a forensic timeline, and an animated SVG agent graph. However, the reviewed frontend does not implement camera activation or rendering, and the frontend dependency manifest does not declare MediaPipe or a 3D rendering engine. The existing “Lancer KYC complet” button starts the backend KYC stream; it does not request camera permission or initialize a face-processing pipeline.

This is a source-level audit of the current remote files, not a browser run. The findings below are directly supported by the reviewed source and dependency manifest. No claim is made that the camera or MediaPipe path was tested at runtime: that path is currently absent from the reviewed implementation.

## Expertise activated

- React 19 / TypeScript frontend architecture and component lifecycle
- Browser camera permissions, MediaDevices, MediaStream, and secure-context requirements
- MediaPipe Tasks Vision and live face-landmark processing
- 2D SVG animation versus genuine 3D/WebGL rendering
- KYC demonstration UX, consent, privacy, and separation of biometric signals from identity proof
- POST-based Server-Sent Events (SSE), cancellation, and UI state synchronization
- Frontend dependency review and browser end-to-end acceptance testing

## Reviewed evidence

- `frontend/package.json`: React, React DOM, Framer Motion, Lucide, XYFlow, Vite, TypeScript; no declared MediaPipe, Three.js, or React Three Fiber dependency.
- `frontend/src/components/KycPanel.tsx`: KYC form, “Lancer KYC complet” action, POST to `/api/kyc/stream`, manual SSE reader, timeline, and PDF handling. No `navigator.mediaDevices.getUserMedia`, video element, camera state, MediaPipe import, or face-landmark processing is present in the reviewed file.
- `frontend/src/App.tsx`: the KYC tab renders `<KycPanel apiBase={API_BASE} />`; the live Guardian overlay is driven by custom KYC SSE events.
- `frontend/src/components/LiveGuardianGraph.tsx`: animated SVG nodes and edges for Orchestrator, LLM Attacker, Propagator, and Guardian. This is a 2D SVG graph, not a 3D face hologram.
- `frontend/src/components/AnimatedArchitectureGraph.tsx`: animated SVG architecture graph for the pitch page; also 2D.
- `frontend/src/api/guardian.ts`: types and HTTP helpers for Guardian/KYC-related backend calls; no camera or MediaPipe API.
- Latest remote commit reviewed: [R094](https://github.com/vgactech/ARTCB-TERMINATOR/commit/f6bcee34dac4235e3f514bd2e2ffd71047124379).

## Findings

### R095-01 — P0: Camera permission request and camera action are missing

**Process — what should happen:** The user explicitly presses a camera action. The browser then displays its own permission prompt when needed. If permission is granted, the frontend receives a `MediaStream`, attaches it to a `<video>` element, and displays a clear “camera active” state. The user must retain a visible way to stop the camera.

**Problem — what the source currently does:** The KYC panel has a single primary action, “Lancer KYC complet”. Its handler validates the text fields and immediately sends a POST request to `/api/kyc/stream`. There is no separate camera activation action and no camera permission request in the reviewed component. Consequently, the browser cannot ask for camera permission through this flow, and the demo cannot show live camera input.

**Solution:** Add a separate, clearly labelled **“Activer la caméra”** button. Call `navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false })` only from that explicit click handler. Attach the returned stream to a video element through a ref and call `play()` after metadata is ready. Add a separate **“Arrêter la caméra”** action that stops every stream track and clears the video element. Handle permission denied, no camera, camera busy/unreadable, unsupported browser, and insecure-origin errors with visible, actionable messages.

**Acceptance criteria:**
- The browser permission prompt is triggered by the explicit camera button when required.
- A granted stream is visible and the UI reports camera state accurately.
- Denied permission does not crash the KYC panel or falsely claim that the camera is active.
- Stop, unmount, tab change, and camera failure stop all owned tracks.
- No camera access is initiated automatically on page load.

**Status:** OPEN — camera flow absent from the reviewed frontend.

### R095-02 — P0: MediaPipe is not integrated into the frontend dependency or execution path

**Process — what should happen:** After camera permission succeeds, the frontend initializes a MediaPipe Vision task, supplies live video frames in video/live-stream mode, and receives face landmarks and (if enabled) the facial transformation matrix needed to align an overlay. Initialization and per-frame processing must be lifecycle-managed and must not block the KYC SSE stream.

**Problem — what the source currently does:** `frontend/package.json` does not declare `@mediapipe/tasks-vision`; the reviewed KYC component has no MediaPipe import, model initialization, video-frame loop, landmark callback, or processing status. A camera preview alone would therefore not constitute MediaPipe integration.

**Solution:** Use Google's supported JavaScript package `@mediapipe/tasks-vision` and the Face Landmarker task, with a pinned dependency and a documented model asset location. Initialize the task after camera activation, use the live-video execution mode and a throttled frame scheduler, and render only from fresh, valid results. Dispose of task resources and cancel scheduled frame work on stop/unmount. Keep the face-processing loop independent from the Guardian API request and SSE reader.

**Acceptance criteria:**
- The task and model initialize successfully on the target demo browser.
- UI distinguishes “camera ready”, “loading face model”, “face detected”, “no face”, and “processing error”.
- A missing model asset, WASM load failure, or unsupported browser produces a visible error and a recoverable retry path.
- Face processing can be stopped without leaving a camera track or scheduled frame loop alive.
- Camera/landmark failure is never presented as a successful KYC or Guardian verification.

**Status:** OPEN — MediaPipe is not present in the reviewed manifest or KYC source.

### R095-03 — P1: The existing holographic visuals are 2D animated graphs, not a 3D face hologram

**Process — what should happen:** A real-time face-landmark result drives a visual layer aligned to the face, while the interface presents the result as a clearly labelled visualization. A genuine 3D overlay needs a 3D rendering pipeline or another explicitly defined 3D implementation.

**Problem — what the source currently does:** `LiveGuardianGraph.tsx` and `AnimatedArchitectureGraph.tsx` draw animated SVG nodes, lines, glows, and particles. The package manifest has no Three.js or React Three Fiber dependency. These visuals can be described as animated 2D/SVG dashboards, but the reviewed code does not establish a 3D holographic face demonstration or camera-aligned 3D landmarks.

**Solution:** For the deadline, separate the two visual layers:
1. Keep the current Guardian execution graph as the forensic/agent-flow view.
2. Add a camera stage with a face-aligned landmark overlay driven by MediaPipe.
3. If true 3D is a hard requirement, introduce a small, isolated Three.js scene (or React Three Fiber if its dependency and integration cost are acceptable) that uses MediaPipe's facial transformation matrix and a defined canonical face geometry. If that cannot be completed and tested in time, label the effect honestly as a “2D face-landmark holographic overlay” rather than claiming a true 3D reconstruction.

**Acceptance criteria:**
- The camera-aligned overlay follows head movement and does not drift substantially from the face.
- Camera loss or missing landmarks hides/clears the tracking overlay rather than leaving a misleading frozen result.
- 2D SVG graph state and face tracking state are distinct.
- UI and presentation wording accurately distinguishes 2D visualization, 3D rendering, liveness signal, and KYC verdict.

**Status:** OPEN — current source proves animated 2D SVG graphs only.

### R095-04 — P1: The KYC action does not coordinate camera readiness and the backend KYC stream

**Process — what should happen:** The UI should have explicit, independent states for camera permission, MediaPipe initialization, face tracking, and the Guardian KYC stream. The operator should be able to see which subsystem is ready and which failed.

**Problem — what the source currently does:** `runKyc()` begins the POST/SSE flow as soon as the text fields are non-empty. It has no camera or MediaPipe readiness precondition and no visible cross-state model. The app-level HUD sets `kycRunning` to true when it receives `session_opened`, and sets it false on `done`; it does not represent camera or model status. The visual graph is therefore driven by Guardian events, not by camera/face-processing events.

**Solution:** Use a small explicit frontend state model with independent statuses such as `cameraStatus`, `visionStatus`, and `kycStatus`. Make the action sequence clear: activate camera → initialize MediaPipe → verify that the demo has the required input state → launch KYC. If the demonstration is intentionally allowed to run without a camera, provide a clearly labelled “Continue without camera” path; never silently treat it as camera-verified. Keep backend SSE cancellation and camera shutdown separate, with a single coordinated cleanup path on unmount.

**Acceptance criteria:**
- The “Lancer la démonstration KYC” action reports which prerequisites are met.
- A camera/model failure cannot be mistaken for a successful identity or Guardian result.
- KYC backend events continue to be handled even if the camera visualization fails.
- Repeated start/stop cycles do not create duplicate streams, duplicate frame loops, or duplicate SSE requests.

**Status:** OPEN — the current flow has no camera/MediaPipe coordination.

### R095-05 — P1: Camera lifecycle, errors, and secure-context deployment requirements are not implemented

**Process — what should happen:** The frontend requests only the necessary media, starts on a user gesture, reports permission and device errors, and always releases its media tracks. Browser camera access requires a secure context (HTTPS, or localhost for development) and user permission.

**Problem — what the source currently does:** No camera lifecycle or camera error handling exists in the reviewed KYC component. The frontend can currently display a KYC form without any indication that the camera requirement is not implemented. The deployed demo's HTTPS and camera Permissions Policy configuration were not independently verified during this source review.

**Solution:** Add a dedicated camera hook or component with explicit `idle/requesting/active/denied/unavailable/error/stopped` states. Use `try/catch/finally`-style cleanup, stop every `MediaStreamTrack`, clear `video.srcObject`, and handle `NotAllowedError`, `NotFoundError`, `NotReadableError`, and unsupported/insecure contexts. Verify the actual demo URL uses HTTPS and that any response `Permissions-Policy` allows camera access for the app origin. Do not use an iframe unless its camera permissions are intentionally configured.

**Acceptance criteria:**
- HTTPS production/demo URL and localhost development path are tested.
- Denial, no device, device busy, browser reload, and component unmount all produce correct UI states.
- Camera tracks are stopped on explicit stop, unmount, and fatal processing failure.
- The browser's camera indicator is consistent with the UI's state.

**Status:** OPEN — no camera lifecycle exists; deployment policy not checked in this source audit.

### R095-06 — P1: The demo's seeded identity fields can be mistaken for real identity verification

**Process — what should happen:** Demo data, camera-based face tracking, document-field validation, liveness checks, and a KYC verdict must be represented as separate evidence classes. A face landmark detector is not proof of a unique human, legal identity, or liveness by itself.

**Problem — what the source currently does:** The KYC form initializes with fixed example values (“Alice Dupont”, a sample document number, and a fixed date of birth). The UI then launches a backend KYC stream using those fields. Without explicit “demo data” and evidence-status labels, a jury may interpret a visually convincing face overlay or an APPROVED backend verdict as proof of camera-based biometric verification even though that integration is absent from the reviewed source.

**Solution:** Label seeded values as synthetic demonstration data, provide a clear reset-to-demo-data action, and label the current backend result as the Guardian/KYC pipeline verdict. Add separate status indicators for camera access, face detected, liveness (only if a validated liveness method exists), document validation, and backend verdict. Do not claim unique-human proof or biometric certification unless a specific, tested mechanism supports the claim.

**Acceptance criteria:**
- Synthetic identity data is visibly marked as demo-only.
- A face detection event does not automatically approve identity or imply liveness.
- The final verdict lists which checks actually ran, passed, failed, or were not tested.
- The demo remains truthful when camera permission is denied or no face is detected.

**Status:** OPEN — fixed demo values are present; camera-derived identity evidence is not integrated.

## Recommended implementation order for the deadline

1. **P0 — Camera activation button and visible preview:** implement and verify the explicit permission request, active/error states, and stop-camera cleanup.
2. **P0 — MediaPipe Face Landmarker:** add the dependency/model asset, initialize after camera start, and show live landmark status.
3. **P1 — Holographic overlay:** align a lightweight overlay to MediaPipe results; use true 3D only if it can be completed and validated within the remaining time.
4. **P1 — Explicit demo sequence:** coordinate camera, vision, and Guardian KYC states without coupling camera failure to backend security decisions.
5. **P1 — Browser acceptance pass:** test HTTPS, permission grant/deny, no camera, busy camera, no face, face movement, stop/restart, SSE success, SSE failure, and mobile layout.
6. **P1 — Demo integrity labels:** mark seeded identity as synthetic and clearly distinguish face detection from identity verification.

## Suggested target interaction

1. Open the KYC tab; camera remains off.
2. User clicks **“Activer la caméra”**.
3. Browser asks for permission if needed.
4. Preview appears; MediaPipe model loads and reports its status.
5. The face-landmark overlay follows the user's face, without claiming identity proof.
6. User clicks **“Lancer la démonstration KYC”**.
7. Guardian POST/SSE events populate the existing forensic timeline and graph.
8. The final screen separately reports camera/vision status, Guardian decision, chain verification, and PDF availability.
9. User can stop the camera at any point; tracks and processing loops are released.

## External technical references checked

- MDN, `MediaDevices.getUserMedia()`: secure-context requirement, user permission, returned `MediaStream`, and common error conditions — https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
- Google AI for Developers, MediaPipe Face Landmarker options: live-stream mode and facial transformation matrices for face-effect alignment — https://ai.google.dev/edge/api/mediapipe/python/mp/tasks/vision/FaceLandmarkerOptions

These references support the recommended browser and MediaPipe integration approach; they do not prove that the feature is already implemented in this repository.

## Audit limitations

- Remote source files and the latest commit were inspected through GitHub.
- No application code was changed.
- No frontend build, browser session, camera device, MediaPipe model download, or end-to-end test was run as part of this audit.
- No runtime claims are made for camera or MediaPipe behavior because those paths are absent from the reviewed frontend source.
- No logs or secrets were added to the repository.

**Final status: NOT READY for a camera-enabled MediaPipe KYC demo until R095-01 and R095-02 are implemented and tested. The existing backend KYC/SSE UI and 2D SVG Guardian graphs are useful foundations, but they do not currently constitute a camera-enabled 3D holographic KYC flow.**
