# R014 — AWS-Only Execution Architecture for the Competition

## 1. Decision and scope

**Mandatory requirement:** every ARTCB Guardian execution used for the competition demonstration and jury testing must run on the two AWS servers provided for the competition. A juror's local computer is a browser client only. The juror must not need to clone the repository, install runtimes or dependencies, compile Rust, install Python packages, start a local API, or run the agents locally.

This report documents the deployment target and acceptance criteria. It does not modify application code, the existing README, AWS resources, credentials, or any other repository files.

## 2. Repository baseline and discrepancy

The repository README currently describes a local development workflow that starts FastAPI and the frontend on the developer's machine. That workflow is useful for development but does not satisfy the competition requirement that jury tests execute on AWS without local installation.

The README also describes the current integrated scenario as four agent roles orchestrated within one Python process, rather than four separately deployed microservices. The AWS design must preserve this distinction unless a later, separately approved report documents an architectural change.

The competition-provided server addresses, operating systems, CPU/RAM limits, network rules, and access method have not been supplied in this request. They must be inventoried before deployment; this report does not invent hostnames, IP addresses, ports, or instance sizes.

## 3. Target topology

### AWS Server 1 — Public web entry point and API

Responsibilities:

- Serve the Guardian web console over HTTPS.
- Expose the minimum API required to submit an approved test scenario and retrieve its execution status and results.
- Validate request schemas, scenario identifiers, input sizes, authentication where required, and rate limits.
- Assign a unique run ID and correlate API requests with execution events.
- Forward approved jobs to Server 2 over a restricted private channel.
- Return the run status, Guardian decision, event trace, evidence references, replay result, and integrity-verification result.
- Avoid executing attacker-controlled scenario logic inside the public-facing web process.

The public server must not expose administrative interfaces, internal service ports, credentials, or arbitrary shell/command execution to jurors.

### AWS Server 2 — Guardian execution and evidence

Responsibilities:

- Run the Guardian API-side worker or execution service and the existing Python multi-agent scenario orchestration.
- Run the Rust Security Core and its supported Python bindings where the current code and build artifacts permit.
- Execute only predefined, bounded, competition-approved scenarios.
- Produce correlated events, causal relationships, policy decisions, evidence, replay data, and tamper-verification results.
- Persist run records and evidence according to the available storage capacity and competition retention requirements.
- Return structured results to Server 1 through an authenticated, restricted service interface.

Attacker simulations must remain inside an explicitly bounded test environment. They must not receive unrestricted host privileges, access to cloud metadata credentials, or general-purpose access to unrelated AWS resources.

### Network boundaries

- Jurors connect to Server 1 through HTTPS.
- Server 1 communicates with Server 2 only over the necessary service port and an authenticated channel.
- Server 2 should not expose its execution service directly to the public internet unless the competition infrastructure makes this unavoidable and a documented compensating control is approved.
- Administrative access is separate from the jury-facing path and must use the access method authorized by the competition.
- No additional cloud host, third-party execution platform, or developer PC is part of the production execution path.

## 4. Jury experience

The expected flow is:

1. The juror opens one published HTTPS URL in a standard browser.
2. The console loads without requiring a local package manager, runtime, plugin, extension, or repository checkout.
3. The juror selects a documented scenario and submits it.
4. Server 1 validates the request and creates a run ID.
5. Server 2 executes the scenario and emits events as the run progresses.
6. The console displays live status and the execution trace as events become available.
7. The juror can inspect the final decision, evidence, provenance, and replay/integrity results.
8. The juror can run another scenario without resetting or installing the application.

A browser is a presentation and control client only. No scenario, agent, policy engine, evidence-generation process, or Rust/Python application component may silently fall back to local execution.

## 5. Process — how the two-server model works

The browser sends a scenario request to the public API. The API validates the request, assigns a run ID, and forwards a constrained job to the execution server. The execution server runs the scenario, instruments the agents and security components, records correlated events, and returns structured status and evidence. The public API streams or polls the results for the browser.

In other words, the local computer requests and displays a run; AWS performs the run.

## 6. Problem — why a local fallback is unacceptable

If a juror must install Python, Rust, Node.js, dependencies, or launch a local API, the demonstration becomes dependent on the juror's operating system, local configuration, and setup time. It also becomes difficult to prove which environment actually executed a scenario. A browser UI that runs locally while the security decisions are computed locally would violate the stated requirement even if the interface looked identical.

## 7. Solution — deployment and operational controls

### Build and release

- Build and test the application before deployment; do not require jurors to compile source code.
- Deploy versioned artifacts to the two authorized AWS servers.
- Record the source commit, artifact hashes, dependency versions, build result, and deployment timestamp.
- Keep credentials out of source files, frontend bundles, logs, and jury-visible responses.
- Use the competition-approved secret-management method. Do not print or commit secrets.

### Service resilience

- Configure both services to start through the approved process manager or container runtime available on the supplied hosts.
- Add health checks for the public API, execution worker, and inter-server connection.
- Apply bounded request sizes, execution timeouts, concurrency limits, and a maximum run duration.
- Return a clear failure status when Server 2 is unavailable; never pretend a scenario ran successfully or silently run it on the juror's PC.
- Prevent duplicate submissions from creating uncontrolled duplicate jobs; use a run ID and an idempotency mechanism where practical.

### Security and evidence

- Keep the public interface separate from the execution environment.
- Restrict inter-server communication to the required ports and authenticated identities.
- Treat scenario inputs as untrusted data and allow only enumerated test scenarios or explicitly bounded parameters.
- Correlate each run's request, agent actions, policy decisions, and evidence using a unique run ID.
- Distinguish observed events from inferred findings and confirmed outcomes.
- Record dropped telemetry and execution failures; do not represent missing telemetry as proof that no activity occurred.
- Do not write raw secrets or unnecessary sensitive data to logs.
- Keep logs and artifacts off the Git repository unless a report explicitly requires sanitized, non-sensitive evidence.

## 8. Acceptance tests

The AWS-only requirement is not complete until the following tests pass on the actual competition servers:

1. **Clean-client test:** from a computer with no project dependencies installed, a juror can open the public URL and run a scenario using only a browser.
2. **Remote-execution proof:** each run has server-side records identifying the execution host/service and run ID.
3. **No-local-fallback test:** stopping Server 2 makes a new run fail visibly; it does not execute on the browser computer or Server 1.
4. **End-to-end test:** a scenario returns a real Guardian decision, correlated events, evidence, and integrity/replay results from the deployed services.
5. **Live trace test:** events appear while the scenario runs, not only after a precomputed result is returned.
6. **Security-boundary test:** the public API cannot invoke arbitrary shell commands, access the host filesystem without authorization, or reach unrelated services.
7. **Recovery test:** restarting the execution service produces an explicit unavailable/recovered state without falsely reporting success for interrupted runs.
8. **Reproducibility test:** the deployed version and artifact hashes are recorded and can be matched to the release.
9. **Resource test:** concurrent requests and deliberately slow scenarios remain within defined CPU, memory, and time limits.
10. **Secret/log hygiene test:** no credentials, API keys, or private keys appear in frontend assets, API responses, committed files, or routine logs.

For every test, retain the test result, timestamp, deployed version, and sanitized evidence needed to substantiate the claim.

## 9. Deployment sequence

1. Inventory both competition AWS servers and confirm permitted access, operating systems, capacity, networking, and competition restrictions.
2. Decide which server hosts the public web/API entry point and which hosts Guardian execution, based on the actual supplied constraints.
3. Build and test the release artifacts without changing the historical ARTCB repository.
4. Configure the restricted inter-server channel, service identities, health checks, and approved secret handling.
5. Deploy the backend/execution service to Server 2 and verify its health.
6. Deploy the public API and web console to Server 1 and verify the end-to-end request path.
7. Execute all acceptance tests from a clean external browser client.
8. Publish the single jury URL and concise usage instructions only after the end-to-end test succeeds.

If the two supplied servers cannot support this separation due to a documented competition constraint, record the limitation and propose the smallest compliant alternative before changing the topology.

## 10. Out of scope

- No application-code changes are authorized by this report.
- No changes to the historical `vgactech/artcb` repository.
- No integration or migration into VLC&ARTCB.
- No creation, rotation, or disclosure of AWS credentials.
- No deployment claim is made: this report specifies the target and validation plan; it does not establish that either AWS server has already been configured.

## 11. Definition of done

The requirement is satisfied only when a juror can use a normal browser, with no local installation, to trigger a new scenario whose execution is demonstrably performed by the competition's AWS infrastructure, observe the live trace, and inspect the actual Guardian decision and verifiable evidence. The execution path must use only the two authorized competition servers.

**Governing rule: the juror's PC is a browser terminal, not an ARTCB runtime.**
