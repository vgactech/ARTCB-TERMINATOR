# R046 — Global Read-Only Audit of AWS API Gateway HTTP API h2wftxtbtb

**Date:** 2026-10-11  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Branch:** `experiment/artcb-api-mcp-integration`  
**Target:** API Gateway HTTP API `h2wftxtbtb`, `us-west-2`  
**Previous numbered report:** R045 — Operational Delta Audit, Live Execution Evidence, and Integration Acceptance Gate  
**Scope:** Read-only review of the supplied API Gateway configuration snapshot, repository evidence, and public AWS documentation. Report creation is the only permitted repository write.  
**Change boundary:** This report only is added under `rapports/`. No application code, tests, cloud configuration, deployment, credentials, or external repository is modified. No execution logs are committed.

---

## 1. Executive decision

**Verdict: NOT READY FOR LIVE-TRAFFIC ACCEPTANCE — deployment attachment is not demonstrated and the security configuration remains unverified.**

The supplied AWS console snapshot identifies an HTTP API in `us-west-2` with ID `h2wftxtbtb`, a default endpoint enabled, and a `$default` stage. The same snapshot says the stage has no attached deployment, automatic deployment is disabled, and no last-update value is shown.

That combination is the primary blocker. AWS documents that an HTTP API needs at least one route, integration, stage, and deployment to be functional; the `$default` stage serves from the API base URL, but the stage must point to a deployed configuration. With automatic deployment disabled and no deployment attached in the supplied snapshot, there is no evidence that a usable API configuration has been published. This is a **configuration-based high-confidence concern**, not a live AWS control-plane verification: the snapshot was supplied in chat and could not be independently refreshed through an authenticated AWS API in this audit.

The public invoke URL is `https://h2wftxtbtb.execute-api.us-west-2.amazonaws.com`. A public-looking URL does not prove that routes exist, an integration is configured, authorization is enabled, the backend is healthy, or the service is safe to expose.

**Current acceptance status: NOT CERTIFIED.** Do not send production or sensitive requests to this endpoint until the deployment, routes, integrations, authorization, and backend health are verified.

## 2. Expertise activated

- AWS API Gateway v2 / HTTP API architecture and deployment lifecycle.
- Cloud configuration assurance and read-only evidence validation.
- API route, integration, authentication, and authorization security.
- Network reachability and interpretation of failed connectivity probes.
- Secure cloud operations, least-privilege evidence collection, and secret hygiene.
- Distributed-service readiness, backend health, and failure-mode analysis.
- Audit traceability, evidence confidence, and acceptance-gate design.

## 3. Evidence and limits

### 3.1 Supplied configuration snapshot

The following are treated as **operator-supplied observations**, not independently confirmed live control-plane values:

| Property | Supplied value | Audit interpretation |
|---|---|---|
| API ID | `h2wftxtbtb` | Identifies the API to inspect |
| Protocol | HTTP | Expected API Gateway HTTP API / v2 configuration |
| Region | `us-west-2` | All control-plane inspection must target this region |
| Default endpoint | Enabled | The `execute-api` URL may be used if the stage and route are deployed |
| Stage | `$default` | Uses the base invoke URL without a stage path |
| Attached deployment | Empty | No active deployment is evidenced by the supplied snapshot |
| Auto deploy | Disabled | Configuration changes are not automatically released |
| Last updated | Empty | No recent stage/deployment update is evidenced in the supplied snapshot |
| IPv4 | Enabled/reported | Does not establish backend reachability or application security |

### 3.2 Repository state synchronized before review

The GitHub connector was used to read the remote repository before drafting this report.

- Default branch `main`: HEAD `3ae0b9653be8fab8c6d51c4942407bfbbbd6e844`, whose commit message records R043.
- Experiment branch: `experiment/artcb-api-mcp-integration`; R045 is present on this branch at the time of inspection.
- R045 identifies R044 as its preceding report. R046 is therefore the next report number, preserving the existing numbering sequence.
- This report is written to the same experiment branch as R045 to preserve report continuity. No branch merge, rebase, deployment, or source-code change is performed.

The repository's prior reports contain unresolved operational items, including a separately reported tamper-verification mismatch, unproven cross-host API/MCP connectivity, incomplete live LLM validation, and unverified browser end-to-end behavior. Those are historical findings, not freshly reproduced in this AWS-only inspection, and must remain open until separately revalidated.

### 3.3 Live network probe limitation

A single read-only HTTPS GET of the root invoke URL was attempted from the available execution environment. The probe failed before an HTTP response was received because the environment could not resolve the hostname (`Temporary failure in name resolution`). No HTTP status, API Gateway request ID, route result, or backend response was obtained.

**Interpretation:** this is a limitation of the probe environment's DNS/network access. It is **not** evidence that the AWS endpoint itself is down, misconfigured, or secure. The endpoint's live behavior remains unverified.

### 3.4 AWS control-plane access limitation

No authenticated AWS control-plane connector or usable AWS CLI credentials were available to this audit execution. Accordingly, the following could not be independently queried: routes, integrations, stage deployment ID, authorizers, resource policy, CORS, throttling, access logging, CloudWatch metrics/log groups, custom domains, VPC links, backend health, or recent configuration changes.

No credentials were requested, displayed, stored, or included in this report.

## 4. Finding R046-001 — No attached deployment is evidenced for the default stage

**Severity: HIGH — deployment/readiness blocker**  
**Confidence:** High for the supplied snapshot; not independently confirmed against the live AWS control plane.

### Process — what this means

An HTTP API configuration defines routes (the path and HTTP method clients call), integrations (the backend destination or service invoked by a route), and a stage. A deployment is the published snapshot that makes the configured API available to clients. The `$default` stage is served at the root of the invoke URL.

### Problem — why it matters

The supplied snapshot shows a `$default` stage but an empty deployment attachment, with automatic deployment disabled. Therefore the presence of the stage and invoke URL alone does not establish that a published route can execute. The API may return an API Gateway error, or there may be no usable route at all. The precise response cannot be asserted without a valid live request and control-plane inspection.

### Solution and acceptance test

1. In the AWS console, select API Gateway → APIs → `h2wftxtbtb` in `us-west-2`.
2. Inspect Routes and confirm each intended route has the correct method and a valid integration.
3. Inspect Integrations and verify the destination, protocol, timeout, network path, and invocation permissions.
4. Inspect Stages → `$default`; confirm whether a deployment ID is attached and whether auto-deploy is intentionally off.
5. If deployment is required, prepare the intended configuration and deployment description, review the diff, and have the authorized operator deploy it. This audit does not deploy or change settings.
6. After deployment, run one harmless request against a documented read-only health route and record only status, latency, and non-secret correlation/request IDs in the approved operational system—not in this repository.
7. Confirm that a deliberately unknown route returns the expected non-sensitive error and does not fall through to an unintended backend.

**Acceptance criterion:** an active deployment is explicitly attached or the stage's documented auto-deploy behavior is verified; at least one intended route returns the expected result from its configured integration.

## 5. Finding R046-002 — Routes and integrations are unknown

**Severity: HIGH — functional and exposure uncertainty**  
**Confidence:** Confirmed evidence gap.

### Process

A client request is matched to a configured route, then API Gateway dispatches it to that route's integration. An API ID and stage do not describe which paths are exposed or what each path invokes.

### Problem

No route or integration inventory was supplied, and authenticated read access was unavailable. It is therefore unknown whether the API has a health route, application routes, catch-all routing, a Lambda integration, an HTTP backend, or no usable route. It is also unknown whether the integration points to the intended ARTCB-TERMINATOR service.

### Solution and acceptance test

- Export or inspect the route inventory and map each route to its integration.
- Document each route's purpose, allowed methods, payload schema, authentication mode, backend target class, timeout, and expected status codes.
- Remove unintended routes and avoid broad catch-all routes unless explicitly required and tested.
- For every route, verify the integration's invocation permissions and backend reachability.
- Prove that the intended TERMINATOR backend—not an unrelated service—is called using a harmless synthetic request with a correlation ID.
- Treat an absent route, an unavailable integration, and an application-level error as distinct outcomes.

**Acceptance criterion:** every deployed route has an identified owner, purpose, integration, access policy, and passing non-destructive smoke test.

## 6. Finding R046-003 — Authentication and authorization have not been verified

**Severity: CRITICAL if sensitive or state-changing routes are exposed without access control**  
**Confidence:** Unknown configuration; do not interpret unknown as absent or present.

### Process

API Gateway can use authorizers and/or IAM-based authorization, while the backend should still enforce operation-level permissions appropriate to the application. Authentication establishes who is calling; authorization determines what that caller may do.

### Problem

The supplied snapshot does not show authorizers, route authorization types, IAM policies, JWT issuer/audience constraints, identity-provider settings, or backend authorization. The enabled default endpoint means the standard hostname is available as an ingress option, but it does **not** by itself prove that requests are unauthenticated. The actual authorization posture is unknown.

### Solution and acceptance test

1. Inspect authorization settings for every route, not just the API-level summary.
2. Verify token issuer, audience, signature validation, expiry, and required claims where JWT authorization is used.
3. For IAM authorization, confirm the signing model and least-privilege identity policies.
4. Ensure sensitive operations have server-side authorization even if a gateway authorizer is present.
5. Test missing credentials, malformed tokens, expired tokens, wrong audience, insufficient permissions, and valid authorized access.
6. Confirm rejected requests do not invoke the backend; use backend-side counters or safe test instrumentation to prove this.
7. Never use CORS as an authentication control. CORS is a browser policy and does not prevent direct HTTP clients from making requests.

**Acceptance criterion:** unauthorized and underprivileged requests are denied before sensitive work begins, while authorized requests succeed only for their permitted operations.

## 7. Finding R046-004 — The default execute-api endpoint is enabled

**Severity: MEDIUM until the intended exposure model is established; HIGH if it bypasses a required private/custom-domain boundary**  
**Confidence:** Supplied snapshot.

### Process

API Gateway can accept traffic through its default `execute-api` hostname or, where configured, through a custom domain. Enabling the default endpoint makes the standard invoke hostname available, subject to route, authorization, and other configured controls.

### Problem

The intended exposure model is not documented in the supplied evidence. If the architecture requires clients to use a controlled custom domain or a private ingress path, an enabled default endpoint may provide an unintended alternate entry point. Conversely, if the public default hostname is intentional, it still requires verified route-level controls.

### Solution and acceptance test

- Establish whether the API is intended to be public, private, or reachable only through a defined gateway/domain boundary.
- If a custom domain is mandatory, verify its TLS certificate, DNS, API mapping, and equivalent authorization controls.
- If the default endpoint is not required, evaluate disabling it through the approved change process after confirming clients do not depend on it.
- Test both the intended hostname and the default hostname; verify that the unintended path is unavailable or protected as designed.
- Do not disable the endpoint during this audit; that would be a live configuration change.

**Acceptance criterion:** the actual reachable ingress paths match an approved architecture and every exposed path enforces the same required security posture.

## 8. Finding R046-005 — Observability and abuse controls are unverified

**Severity: HIGH for a security-sensitive API; exact operational impact unknown**

### Process

Access logs, metrics, alarms, throttling, quotas, and request identifiers help operators distinguish normal traffic from failures or abuse. Logging must capture enough evidence to investigate without recording credentials or sensitive request bodies.

### Problem

The snapshot does not establish whether access logging, metrics, alarms, throttling, quotas, or alert routing are configured. Without these controls, repeated failures or abusive traffic may be difficult to detect, and incident reconstruction may be incomplete. This is an evidence gap, not proof that monitoring is absent.

### Solution and acceptance test

- Verify access logging for the stage and identify the destination log group and retention policy.
- Ensure logs omit authorization headers, API keys, cookies, tokens, and unnecessary sensitive payloads.
- Verify metrics and alarms for request count, 4xx/5xx rates, latency, integration errors, throttling, and backend failures.
- Configure bounded request rates and burst limits appropriate to the workload and backend capacity.
- Confirm alarms reach an actively monitored destination and that a test alert can be acknowledged.
- Keep operational logs in the approved logging platform. **Do not commit logs or diagnostic dumps to GitHub.**

**Acceptance criterion:** a controlled test failure is observable through metrics/logs without exposing secrets, and the relevant alarm reaches the responsible operator.

## 9. Finding R046-006 — CORS and browser policy are unknown

**Severity: MEDIUM for browser-based clients; not an API authentication boundary**

### Process

CORS controls whether browser JavaScript may read cross-origin responses. It does not prevent command-line tools, backend services, or other non-browser clients from sending requests.

### Problem

No allowed origins, methods, headers, or credential settings were provided. The correct configuration depends on the actual frontend origin. An overly broad configuration can expose responses to unintended browser origins; a too-restrictive one can break the frontend. Neither state can be concluded from the API ID or endpoint URL.

### Solution and acceptance test

- Inventory the exact production and development frontend origins.
- Allow only required origins, methods, and headers.
- Avoid wildcard origins when credentialed browser requests are required.
- Verify preflight behavior for the actual methods and headers.
- Test from an approved origin and an unapproved origin.
- Enforce authentication and authorization independently of CORS.

**Acceptance criterion:** approved browser origins work as intended, unapproved origins cannot read protected responses, and non-browser requests remain protected by real authorization controls.

## 10. Finding R046-007 — Backend identity, health, and network path are unverified

**Severity: HIGH for integration readiness**

### Process

API Gateway forwards requests to its configured integration. Successful gateway DNS resolution or a reachable stage does not prove that the backend is reachable, healthy, correctly authenticated, or the intended ARTCB-TERMINATOR service.

### Problem

No integration target, backend health result, VPC link, Lambda permission, TLS setting, or service identity was available for inspection. Earlier TERMINATOR reports recorded historical cross-host connectivity and API/MCP acceptance gaps; those earlier observations are not fresh proof about this gateway.

### Solution and acceptance test

1. Identify the integration target and service owner.
2. Verify backend network reachability from the integration's actual network context.
3. Validate TLS and backend identity where HTTP integration is used.
4. Verify Lambda invocation permissions or other backend service permissions where applicable.
5. Run a read-only synthetic request and correlate gateway request ID with backend correlation ID.
6. Test backend timeout and failure responses; ensure no sensitive internal details are returned to callers.
7. Confirm that a failed remote integration cannot bypass local Guardian enforcement or be falsely reported as a successful ARTCB operation.

**Acceptance criterion:** a request is correlated end to end to the intended backend, with a tested failure path and no false success status.

## 11. Prioritized remediation and verification plan

| Priority | Action | Owner / dependency | Completion evidence |
|---|---|---|---|
| P0 | Confirm active deployment attachment and intended auto-deploy policy | Authorized AWS operator | Stage details plus deployment identifier |
| P0 | Inventory routes and integrations | API owner | Route-to-integration map and smoke-test results |
| P0 | Verify route authorization and backend permission model | Security/API owner | Positive and negative authorization tests |
| P1 | Establish intended ingress: public default endpoint, custom domain, or private access | Architecture owner | Approved exposure model and tested ingress paths |
| P1 | Verify backend target, network path, TLS, and health | Backend/network owner | Correlated synthetic request and failure test |
| P1 | Verify logs, metrics, alarms, throttling, and secret redaction | Operations/security owner | Sanitized log sample, alarm test, and limit configuration |
| P1 | Verify CORS against actual frontend origins | Frontend/API owner | Allowed/disallowed origin test matrix |
| P2 | Define deployment/change-control and rollback procedure | Release owner | Reviewed deployment plan and rollback evidence |
| P2 | Re-run the earlier TERMINATOR integration acceptance gate after AWS checks | TERMINATOR and ARTCB service owners | Updated R046/R045 follow-up evidence; no assumptions carried forward |

No action above was executed as part of this read-only audit. The table describes validation work required before the API can be accepted.

## 12. Minimum read-only AWS inspection checklist

Using an authorized identity with read-only permissions in `us-west-2`, inspect the following resources for API ID `h2wftxtbtb`:

1. API metadata: protocol type, API endpoint configuration, CORS, and API-level policy where applicable.
2. Routes: route keys, authorization type, authorizer ID, and integration ID.
3. Integrations: target URI or function identity, integration type, connection type, timeout, and credentials/permissions references. Do not export secret values.
4. Stages: `$default`, auto-deploy flag, deployment ID, access-log settings, route settings, and throttling.
5. Authorizers: type, identity source, issuer/audience settings, and configuration references with secrets redacted.
6. CloudWatch: available metrics, log-group configuration, retention, alarms, and recent error/latency trends.
7. Domain and ingress configuration: custom domains, API mappings, certificate state, and whether the default endpoint is intentionally enabled.
8. Backend target: health/readiness, network path, TLS, and invocation permission.
9. Resource tags and ownership metadata, if present.
10. CloudTrail or equivalent change history for recent API/stage/route/integration changes, where the authorized role permits access.

Read-only inspection should not create deployments, change authorizers, alter route configuration, invoke state-changing application routes, or change logging. Keep evidence sanitized and outside the repository unless an approved report needs a non-secret summary.

## 13. Process / problem / solution summary

### Process

API Gateway receives a request, matches a route, checks the configured authorization path, invokes an integration, and returns the backend result. A stage publishes a deployment snapshot. Logs and metrics provide operational evidence about this sequence.

### Problem

The supplied snapshot contains a deployment-readiness concern: a `$default` stage with no deployment attached, automatic deployment disabled, and no last-update value. The available evidence does not establish routes, integrations, authorization, ingress intent, backend health, CORS, or observability. The live network probe did not obtain an HTTP response because DNS resolution failed in the audit environment.

### Solution

First independently inspect the API's current control-plane state with an authorized read-only identity. Confirm or correct the deployment state through a separately authorized change process. Then validate route-to-integration mapping, route-level authorization, intended ingress, backend health, and monitoring with harmless requests and negative tests. Keep all changes outside this report-only audit, and do not claim readiness until each gate has evidence.

## 14. Final verdict

**R046 status: NOT CERTIFIED — AWS configuration and runtime behavior remain partially unverified.**

The strongest actionable signal is the supplied empty deployment attachment combined with disabled automatic deployment. Confirm this directly in API Gateway before attempting application-level debugging. Even after a deployment is confirmed, do not treat a successful HTTP response as security certification: route authorization, backend identity, logging, throttling, CORS, and intended ingress must be checked separately.

**Repository and operational boundary:** this report is the only intended repository change. No application source, tests, cloud settings, deployment, secrets, or external ARTCB repository were modified. No logs were committed. The public endpoint probe yielded no HTTP response and is not presented as a successful service test.

## 15. References

- AWS, *Develop HTTP APIs in API Gateway*: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop.html
- AWS, *Stages for HTTP APIs in API Gateway*: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-stages.html
- AWS, *Publish HTTP APIs for customers to invoke*: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-publish.html
- AWS, *API Gateway HTTP API reference*: https://docs.aws.amazon.com/apigatewayv2/latest/api-reference/
