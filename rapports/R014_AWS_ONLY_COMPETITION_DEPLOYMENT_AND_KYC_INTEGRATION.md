# R014 — AWS-Only Competition Deployment and KYC Repository Integration Audit

**Status:** Architecture and deployment-readiness report; no AWS host was modified during this audit.  
**Target repository:** `vgactech/ARTCB-TERMINATOR`  
**Target branch:** `main`  
**Report directory:** `rapports/`  
**Scope restriction:** This change adds this report only. No application source, workflow, infrastructure, configuration, or historical ARTCB repository was modified.

## 1. Executive decision

The final competition build must execute on the two designated AWS servers only. Attack simulations, adversarial-agent runs, demonstrations, and the jury-facing runtime must not execute on a developer's PC, Mac, or another host. The jury should be able to reach the deployed application through a browser or documented HTTPS API without installing project software.

The intended deployment is a two-node, active/standby arrangement:

- **AWS Node A — preferred active node:** serves the jury-facing application and runs authorized competition scenarios.
- **AWS Node B — standby/recovery node:** contains the same pinned application and approved model inventory, receives the required state, and becomes active when Node A fails health checks.
- **A single externally documented HTTPS entry point:** directs jury traffic to the active healthy node. The deployment must avoid requiring the jury to know which instance is active.
- **Doppler-managed runtime secrets:** secrets are retrieved on the AWS hosts at runtime and are never committed to Git, embedded in images, copied into reports, or exposed in browser-delivered configuration.
- **A separately versioned KYC dependency:** the KYC repository should be referenced as a Git submodule (preferred where repository access permits) or integrated through an explicitly pinned subtree/import. It must not be manually copy-pasted or silently diverge from its source repository.

**Critical blocker:** GitHub metadata currently reports `vgactech/artcb_kyc` as an empty repository (size 0). Therefore there is no KYC source content confirmed to clone into ARTCB-TERMINATOR at this time. Repository metadata and README content do not prove that either AWS server is configured or that deployment has succeeded.

## 2. Remote-state observations

The following were checked through the connected GitHub account during this audit:

| Repository | Observed state | Consequence |
|---|---|---|
| `vgactech/ARTCB-TERMINATOR` | Public repository, default branch `main`, reported size 539 KB | Existing Guardian code and reports are present. |
| `vgactech/artcb_kyc` | Public repository, default branch `main`, reported size 0 KB | No KYC source tree was available to import. |
| `vgactech/artcb` | Private repository, separate from TERMINATOR | Do not modify it as part of this task. |

The current TERMINATOR README describes a Rust security core, Python instrumentation/API components, a React/TypeScript console, and a local development launch procedure. It also describes a four-role multi-agent scenario orchestrated inside one Python process. This is useful baseline documentation, but it is not evidence of a two-server AWS deployment, automatic failover, remote jury access, Doppler injection, or AWS-only attack execution.

## 3. Requirement A — AWS-only runtime and attack execution

### Process

The jury connects to a hosted HTTPS endpoint. The active AWS node runs the application, agents, policy engine, event ledger, evidence generation, and authorized test scenarios. The second AWS node is ready to take over. Developers may inspect source and review logs, but the final runtime and any attack/adversarial execution are confined to the two designated AWS hosts.

### Problem to prevent

A demo that launches agents or attack scenarios on a local workstation violates the stated competition constraint, even if the UI itself is hosted on AWS. A second failure mode is exposing a general-purpose attack endpoint that can be pointed at arbitrary external targets.

### Required solution

1. Make the AWS deployment the only supported runtime entry point for the competition profile.
2. Configure scenario targets from a strict allowlist containing only the competition lab resources and the two designated AWS nodes where appropriate.
3. Reject arbitrary target URLs, IP addresses, cloud metadata addresses, and destinations outside the authorized lab. Enforce this at both the application policy layer and AWS network egress layer.
4. Tag every scenario with a run ID, initiating identity, declared target, authorization scope, start/end time, and final outcome.
5. Keep attack simulation separate from production credentials and production data. Use synthetic fixtures and explicitly authorized test accounts.
6. Make the UI identify the active AWS node and display the scenario scope before a run starts.
7. Preserve the complete event/evidence record, including blocked attempts, failed scenarios, timeouts, and missing telemetry.

**Acceptance evidence:** a demo run record showing that the request reached the public AWS endpoint, executed on the active AWS host, targeted only the allowlisted lab, and produced a persistent Guardian event/evidence trail. A local run must not be required for the jury to reproduce the demonstration.

## 4. Requirement B — two-node availability and failover

### Recommended operating model

Use an active/standby model unless the event ledger and all shared state are proven safe for concurrent writers. Running both nodes as independent active writers without coordination can produce duplicated events, split-brain decisions, inconsistent policy state, or conflicting scenario ownership.

### Minimum controls

- Deploy the same immutable application release and model manifest to both hosts.
- Record the Git commit SHA, image/artifact digest, configuration version, and model versions on each node.
- Add health checks for process liveness, readiness, model availability, storage connectivity, and Guardian policy-engine operation. A process responding to TCP alone is not sufficient.
- Use an AWS-supported routing/failover mechanism, such as a load balancer with target health checks, or an equivalent controlled failover endpoint.
- Use a lease, fencing token, or equivalent single-writer mechanism for scenario execution and mutable ledger operations.
- Persist event/evidence data outside ephemeral instance storage or replicate it with a documented consistency guarantee.
- Ensure that Node B can start from the last verified checkpoint and continue without silently discarding events.
- Test failover by terminating or isolating Node A during a synthetic, authorized scenario. Verify that Node B becomes active, the jury endpoint remains usable, and the event history remains verifiable.
- Define recovery-time and recovery-point objectives, then measure them. Do not claim zero data loss or instantaneous failover without test evidence.

### Failure cases to test

1. Node A process crash.
2. Node A host loss or network isolation.
3. One approved model failing to load.
4. Doppler or an upstream secret service temporarily unavailable during restart.
5. Shared event storage unavailable or read-only.
6. Node A returning after Node B has taken over.
7. A long-running scenario interrupted during failover.

The system must not automatically replay a potentially state-changing scenario after failover unless the scenario is explicitly idempotent or its last durable state can be established. Prefer to mark an interrupted run as interrupted and preserve its evidence.

## 5. Requirement C — Doppler and runtime secret delivery

Doppler should provide the runtime secrets required by both AWS hosts, including the relevant Avalanche `AVA_API_KEY` if it is still required by the approved design. The secret value must never appear in this report, Git history, CI logs, shell history, frontend bundles, or ordinary application logs.

### Recommended configuration

1. Create or verify the dedicated Doppler project and configuration for the TERMINATOR competition environment.
2. Use separate service identities/configurations for the two AWS nodes where practical, with access limited to the exact environment and secret set each node needs.
3. Prefer short-lived workload identity or AWS IAM-based access where supported by the selected Doppler integration. If a Doppler service token is required, inject it through a protected host bootstrap mechanism such as AWS Systems Manager Parameter Store/Secrets Manager and restrict its retrieval to the relevant instance role.
4. Install and pin the official Doppler CLI on both hosts, verify its origin/version, and avoid downloading unverified binaries.
5. Retrieve secrets at service startup or through the approved runtime integration. Do not bake secret values into AMIs, Docker layers, deployment artifacts, or configuration files committed to Git.
6. Use least-privilege secret scopes, rotate tokens, and audit access. Do not grant blanket administrator access merely to simplify secret injection.
7. Redact secrets from exception messages and telemetry; test redaction with a synthetic canary value.
8. Define behavior for Doppler unavailability: a node should not print secrets or fall back to an unsafe local file. It may continue only if its already-authorized runtime state and policy explicitly allow that behavior.

**Acceptance evidence:** a successful secret-read health check on each host that records only the secret key names and success/failure status—not the values. Validate that neither repository history nor logs contain secret values.

## 6. Requirement D — approved model inventory and standby readiness

The request is to install all previously approved models on both AWS hosts so that Node B can take over if Node A or a model fails. The exact approved model list was not established by the repository metadata available in this audit; do not guess model names or silently substitute a different model.

Create a signed or otherwise integrity-checked model manifest containing, for every approved model:

- canonical model identifier and provider;
- exact model/version or immutable artifact digest;
- deployment mode (local inference, hosted API, or hybrid);
- runtime requirements, memory/accelerator requirements, and license constraints;
- required secret names (never secret values);
- startup and readiness checks;
- expected fallback model, if one was explicitly approved;
- timeout, retry, and circuit-breaker policy;
- validation results and the test dataset/version used.

If models are hosted by an external provider, they cannot be described as “installed on both AWS servers”; document them as external dependencies and test provider/API failover separately. For local model artifacts, verify that both hosts have the exact approved artifact and sufficient capacity. Avoid downloading large model files during a live jury demonstration.

### Runtime fallback

A model failure should trigger a bounded, observable recovery sequence: mark the model unhealthy, stop assigning new work to it, retry only under the documented policy, route eligible work to an explicitly approved fallback, and emit a Guardian event describing the decision. Never silently change model versions or disable security checks to keep the demo running.

**Acceptance evidence:** the same manifest and artifact digests are verified on both nodes; all required readiness checks pass; each approved failure case is exercised on AWS; the event trail records the failed model and the fallback decision.

## 7. Requirement E — integrate `artcb_kyc` without copy-paste

### Current blocker

GitHub currently reports `vgactech/artcb_kyc` as an empty repository. An empty repository cannot provide source files, tests, dependencies, or build metadata for integration. Do not fabricate files or declare the integration complete.

### Preferred integration when source becomes available

Use a Git submodule at a clearly documented path such as `vendor/artcb_kyc`, pinned to an exact commit. This preserves the source repository's independent history and makes the dependency revision explicit. A submodule is a Git reference, not a copy of every file into the parent repository; jury/deployment instructions must therefore fetch submodules recursively and the KYC repository must remain accessible to the build/deployment identity.

If the final distribution must contain the KYC files directly in the TERMINATOR repository, use a documented, pinned subtree/import workflow instead. Do not use manual copy-paste: it loses a reliable link to upstream changes and makes provenance harder to audit.

### Integration gates

1. Verify that the KYC repository has a real default-branch commit and source tree.
2. Identify its license, supported runtime, dependencies, tests, secret requirements, and security boundaries.
3. Review whether KYC code handles identity documents or sensitive personal information. Use synthetic competition data unless a separately approved data-handling design exists.
4. Pin the exact upstream commit; record its repository URL and commit SHA in the integration report.
5. Add dependency scanning, secret scanning, and relevant tests before deployment.
6. Ensure the KYC service cannot bypass Guardian policy, write arbitrary ledger events, or access secrets outside its declared scope.
7. Build and test the integrated artifact on AWS; do not make the jury install the KYC repository separately.
8. Keep the historical `vgactech/artcb` repository untouched.

**Acceptance evidence:** a non-empty upstream KYC commit is pinned, the submodule/subtree resolves in a clean deployment checkout, the integrated test suite passes, and the deployed build records the exact KYC revision.

## 8. Jury access with no local installation

The jury-facing experience should consist of:

- one stable HTTPS URL;
- a browser-accessible dashboard;
- documented, authenticated API endpoints where direct API testing is part of the judging process;
- a small set of preconfigured synthetic scenarios and an explicit authorization boundary;
- visible health and active-node status;
- event/evidence export or inspection suitable for verification;
- a clear error state when a dependency is unavailable.

The jury should not need Git, Python, Rust, Node.js, Docker, Doppler, or local model runtimes installed. Those are build/deployment concerns handled before the judging session. Avoid exposing SSH, the Doppler token, database credentials, raw model-provider credentials, or unrestricted administrative endpoints to the public internet.

## 9. Network and host security baseline

- Permit public inbound traffic only on the required HTTPS port; restrict administrative access to AWS Systems Manager Session Manager or a similarly controlled management path.
- Do not expose SSH or internal service ports publicly unless there is a documented, narrowly scoped requirement.
- Restrict outbound traffic to required model/API endpoints, package registries during deployment, and explicitly authorized lab targets.
- Separate the jury-facing service role from host administration and secret-management roles.
- Keep operating system packages and deployment artifacts patched and pinned.
- Run services under dedicated OS identities; grant privileged access only to the specific deployment operation that requires it.
- Use immutable or reproducible deployment artifacts and record their hashes.
- Store audit logs durably, restrict write/delete permissions, and alert on log loss or integrity-check failures.
- Back up the event ledger and model manifest; test restoration rather than assuming a backup is usable.
- Ensure security controls remain enabled during attack simulations. The competition objective does not justify disabling containment, access checks, or evidence integrity.

## 10. Deployment sequence

1. **Inventory:** confirm both AWS instance IDs, regions, operating systems, capacity, network boundaries, IAM roles, and current deployed commit.
2. **Repository integrity:** identify the current report numbering and deployment artifact source; keep this change limited to `rapports/`.
3. **Secret readiness:** configure Doppler access for both nodes without putting secret values in Git.
4. **Model readiness:** establish the approved model manifest and verify capacity on both nodes.
5. **Artifact build:** create one immutable, versioned artifact from a known commit; record its digest.
6. **Node B staging:** deploy and validate the standby first without making it the active writer.
7. **Node A deployment:** deploy the same artifact and configuration, then run health checks.
8. **Traffic switch:** expose the stable HTTPS entry point only after readiness and access-control checks pass.
9. **AWS-only scenario tests:** execute synthetic, authorized scenarios on AWS and verify the full event/evidence chain.
10. **Failover rehearsal:** stop or isolate Node A, confirm controlled takeover by Node B, then verify ledger integrity and jury endpoint continuity.
11. **KYC integration:** proceed only after the upstream repository contains real source and its revision is pinned.
12. **Release gate:** publish the URL and jury instructions only after the acceptance criteria below are evidenced.

## 11. Acceptance checklist

- [ ] The final runtime and all attack/adversarial scenarios execute only on the two designated AWS hosts.
- [ ] A jury member can run the approved demonstration through HTTPS without installing software.
- [ ] Only authorized lab targets are reachable by attack-simulation components.
- [ ] Node A and Node B run the same pinned release and model manifest.
- [ ] Failover is demonstrated and measured; the active writer is fenced to prevent split-brain.
- [ ] Event/evidence records survive the tested failure and remain verifiable.
- [ ] Doppler delivers required secrets to both nodes without exposing values in source, logs, images, or frontend assets.
- [ ] Every approved model is inventoried and validated on both nodes, or documented accurately as an external dependency.
- [ ] No model or security policy is silently downgraded on failure.
- [ ] The KYC upstream repository is non-empty, reviewed, pinned, and integrated through a reproducible Git mechanism.
- [ ] The historical `vgactech/artcb` repository remains unchanged.
- [ ] No credentials, attack logs, or secret-bearing runtime logs are committed to the repository.
- [ ] All claims in the jury instructions are backed by test evidence.

## 12. Execution limitations and immediate blockers

This audit used the connected GitHub integration to inspect repository metadata and the TERMINATOR README. No AWS/EC2/SSM/SSH or Doppler administration tool is available in the current execution context. Consequently, this report does **not** claim that Doppler was installed, secrets were injected, models were installed, either server was configured, attacks were run, failover was tested, or the KYC source was cloned.

The KYC repository currently has no reported content. Before source integration can be completed, the repository owner must populate it or identify the correct non-empty upstream repository. AWS deployment work requires an authorized AWS execution path to the two designated instances. Do not paste API keys, Doppler tokens, private keys, or other secret values into this conversation or GitHub.

## 13. Final recommendation

Treat the AWS-only deployment as a release requirement, not a presentation convention. The required proof is an end-to-end AWS test: browser/API request → active AWS node → authorized scenario → Guardian policy and event capture → durable evidence → verified failover to the second AWS node. In parallel, keep the KYC integration blocked until its upstream source exists. This avoids claiming capabilities that have not yet been deployed or measured.

**Change performed for this task:** this report only. No application code or historical ARTCB repository was changed.
