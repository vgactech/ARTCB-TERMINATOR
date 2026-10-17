# R100 — P0 Frontend Recovery Audit and OVH2 Deployment Blocker

**Date:** 2026-10-17  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Scope:** This report only; no application files, deployment scripts, configuration, secrets, or runtime logs were modified.  
**Debug mode:** active  
**CERTIFIED_100=false** | **unique_human_proven=false**

## Executive decision

**P0 remains OPEN: the current production frontend has not been redeployed or independently verified during this session.**

The remote `deploy_terminator_ovh2.sh` is unsafe for the requested frontend-only recovery. Its source copies a legacy standalone `index.html` from a hard-coded macOS path instead of the complete Vite artifact in `frontend/dist/`. It also copies `guardian_api`, installs Python dependencies, writes a new Nginx configuration, and reloads Nginx. These actions exceed a static frontend deployment and could disturb a live service.

The repository's R099 report documents a successful local TypeScript/Vite build but explicitly records that deployment of the generated `dist/` was not performed. A successful build is not proof that the same artifact is serving production.

## Expertise activated

- Linux and Nginx deployment diagnosis
- SSH/rsync transport and host access
- React, TypeScript, and Vite production builds
- Static asset routing, cache behavior, and browser delivery
- Change control and production blast-radius reduction
- HTTP/HTTPS verification and deployment acceptance testing
- GitHub repository provenance and report-only change discipline

## 1. Confirmed repository evidence

### 1.1 Deployment script has the wrong artifact source

The current `main` version of `deploy_terminator_ovh2.sh` defines:

- `FRONTEND_SRC="/Users/deyi/.bob/artcb_TERMINATOR_FRONTEND/index.html"`
- `/tmp/index_terminator.html` as the transfer staging file
- `/var/www/terminator/index.html` as the target HTML file

It transfers only one HTML file. A Vite build normally emits an HTML entry point plus hashed JavaScript, CSS, and potentially other assets. Copying only the HTML entry point can leave asset URLs pointing to files that do not exist on the server, resulting in a blank page or failed module/style requests.

### 1.2 Script changes unrelated production components

The same script also copies `guardian_api`, copies `start_guardian.sh`, installs Python dependencies, writes `/etc/nginx/conf.d/artcb-terminator.conf`, and reloads Nginx. None of those operations is required to publish an already-built static frontend. Do not run this script for the immediate frontend-only recovery.

### 1.3 Production document root must be confirmed before writing

R069 documents an OVH2 Nginx configuration with `root /var/www/terminator` and a successful historical response containing the TERMINATOR HTML document. The current deploy script also targets `/var/www/terminator`. However, these are historical repository records, not a live configuration read performed during this session. Do not assume the live configuration is unchanged; inspect the active Nginx virtual host before transferring files.

### 1.4 Build status is not deployment status

R099 records:
- TypeScript check: PASS
- Vite production build: PASS
- Output includes `dist/index.html`, hashed JS, CSS, and an ExecutionGraphOverlay chunk
- OVH2 `dist/` deployment: NOT DONE
- Real browser camera/MediaPipe and simultaneous SSE/camera end-to-end behavior: NOT CERTIFIED

The R099 report is evidence of the earlier build, not proof that the currently checked-out artifact has been rebuilt or uploaded in this session.

## 2. Process, problem, and correction

### Process

A frontend-only deployment must publish the entire contents of `frontend/dist/` to the exact active Nginx document root, preserve the existing API proxy and TLS configuration, then verify that the HTML and every referenced static asset are served successfully.

### Problem

The existing script copies one stale HTML file and changes unrelated services/configuration. Its hard-coded local source path is not portable and does not use the build output. Running it could report success while the actual Vite application remains unavailable or incomplete.

### Safe correction

1. From a trusted checkout of the current `main`, inspect the current commit and working-tree state.
2. Install dependencies from the lockfile and rebuild `frontend/dist/` using the repository's documented build command.
3. Over SSH, read the active Nginx configuration and confirm the exact `root` for the intended host. R069 historically reports `/var/www/terminator`, but the live value must be confirmed.
4. Confirm that the destination is dedicated to this application and that a rollback copy or equivalent recovery path exists.
5. Transfer **the entire contents** of `frontend/dist/` to that confirmed root. Do not copy `guardian_api`, install Python packages, rewrite Nginx configuration, restart Guardian, or touch unrelated services.
6. Run `nginx -t` before any reload. A static-file replacement normally does not require an Nginx reload; reload only if a separately justified configuration change is made.
7. Verify the intended HTTP/HTTPS host, the returned HTML, all referenced JS/CSS chunks, and browser console/network behavior. Confirm that the API health endpoint and SSE route still work.
8. Record the exact deployed Git commit, artifact hashes, HTTP results, and rollback outcome. Never claim success without observed results.

## 3. Current-session execution limitation

The current execution environment does not expose the private SSH key referenced in the earlier session summary. The repository's deploy script expects a local key at `/tmp/artcb_ssh/ovh2_key`, while the previous notes refer to a Doppler-managed `SSH_PRIVATE_KEY`. Neither key material nor a connected remote-shell action was available to this audit. No attempt was made to access OVH1, and no credentials were printed or copied into this report.

Therefore, this session could inspect the GitHub repository and diagnose the deployment script, but **could not execute a safe transfer to OVH2 or independently probe the live server**. Production recovery is not represented as completed.

## 4. Immediate acceptance checklist

- [ ] Authorized SSH access to OVH2 is available in the deployment environment.
- [ ] Active Nginx virtual host and document root confirmed over SSH.
- [ ] Current `main` checked out; frontend dependencies installed from lockfile.
- [ ] Fresh `frontend/dist/` build succeeds.
- [ ] Complete `dist/` uploaded to the confirmed document root.
- [ ] HTML, JS, CSS, and other referenced assets return successful HTTP responses.
- [ ] Correct HTTPS hostname and TLS behavior verified.
- [ ] Guardian health and SSE paths remain functional.
- [ ] Rollback path and deployed artifact hashes recorded.

## 5. Remaining queued work

The deployment takes precedence. Once P0 is verified, continue without overwriting earlier reports:

1. **Dependabot:** re-fetch the live alert list and remediate the currently open alerts by severity and affected dependency; the historical count of three alerts must not be treated as current without a fresh query.
2. **OVH4:** diagnose the reported HTTP 503 separately; do not infer that the OVH2 frontend fix repairs OVH4.
3. **Frontend runtime acceptance:** test the actual browser camera permission flow, MediaPipe model/WASM loading, and concurrent camera/SSE operation. Build success alone does not certify these behaviors.

## Final status

**Diagnosis: CONFIRMED — deployment script is unsuitable for a frontend-only recovery.**  
**Production redeployment: NOT EXECUTED — remote SSH access unavailable in this session.**  
**Report-only policy: COMPLIED WITH — only this report is added.**  
**No runtime logs were committed. No ARTCB principal repository or VLC&ARTCB project was modified.**
