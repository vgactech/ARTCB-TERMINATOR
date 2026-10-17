# R075 — Critical Review of R074 DNS Cutover and OVH2 / OVH4 / AWS Isolation Claims

**Date:** 2026-10-17  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Scope:** Evidence-based review of the user-provided R074 status summary concerning `artcb.me`, `www.artcb.me`, `n4.artcb.me`, and `n3.artcb.me`.  
**Change policy:** Report-only. No DNS, application, server, firewall, TLS, cloud resource, secret, log, or other repository was modified.

## 1. Executive assessment

**The proposed separation is technically plausible; the supplied status is not independently verified.**

The supplied summary states:
- `artcb.me` → `151.80.107.29` (OVH2 TERMINATOR), propagating;
- `www.artcb.me` → `151.80.107.29`, propagated;
- `n4.artcb.me` → `91.134.45.8` (OVH4 blockchain), unchanged;
- `n3.artcb.me` → `13.38.209.25` (AWS3 blockchain), unchanged;
- OVH4 and AWS3 will never again receive traffic for `artcb.me` within 24 hours.

The R074 path supplied in the status message could not be retrieved from the connected repository's `main` branch at `rapports/R074_dns_artcb_me_ovh2_uniquement_isolation_finale_2026-10-17.md` (GitHub Contents API returned 404). This does not prove the report does not exist on another branch or in another location; it means the exact claimed path was not available for this review.

A web retrieval of `https://artcb.me/` returned a page title/snippet, but did not expose response headers or the resolved destination IP. The web retrieval for `https://www.artcb.me/` failed with a cache-miss fetch error. The available environment could not perform a direct DNS lookup or direct TLS/HTTP test. Therefore no live DNS, TLS, routing, or traffic-isolation claim is certified by this report.

## 2. Expertise activated

- DNS records, authoritative nameservers, recursive resolver caching, and TTL semantics.
- HTTP routing, virtual hosts, reverse proxies, and TLS certificate validation.
- Cloud network segmentation and traffic-path verification across OVH and AWS.
- Blockchain node discovery and separation of peer traffic from web traffic.
- Operational verification, acceptance testing, and rollback design.
- GitHub repository evidence review and controlled documentation changes.

## 3. Process / problem / solution

### 3.1 DNS changes select a destination for new name resolutions

**Process:** An A record maps a hostname to an IPv4 address. A browser or client typically resolves the hostname and then connects to the returned address. Recursive resolvers cache answers according to TTL; clients and network components may also retain connections or cache data.

**Problem:** Saying that OVH4 and AWS3 will “never receive traffic for `artcb.me`” is stronger than a DNS change alone can prove. During a transition, resolvers may still return cached prior answers. Existing connections, direct-IP clients, alternate A/AAAA records, a CDN/proxy, or a separate hostname can also send traffic to other infrastructure. DNS changes cannot recall requests already in flight.

**Solution:** Verify authoritative records and compare multiple public recursive resolvers. Inspect A, AAAA, CNAME/alias, and any relevant proxy/CDN configuration. Wait for the previously published TTLs to expire before asserting convergence. Describe the result precisely as “public DNS currently resolves to OVH2 from the tested resolvers,” not as a universal guarantee that no traffic can ever reach other servers.

### 3.2 “24 hours maximum” is not a universal DNS guarantee

**Process:** Propagation behavior is influenced by the authoritative zone, the TTL values previously published, resolver caching, negative caching, and provider behavior.

**Problem:** A fixed “24 hours max” cannot be validated without the old and new TTLs, authoritative responses, and resolver observations. A resolver may retain an old cached answer until its TTL expires; some systems behave differently, and DNS alone does not control existing connections or hard-coded addresses.

**Solution:** Record the prior TTL, the authoritative answer, and timestamped results from multiple resolvers. Set a realistic transition window based on evidence. Do not treat elapsed time alone as proof of propagation.

### 3.3 DNS separation does not itself prove network isolation

**Process:** DNS controls hostname-to-address resolution. Firewalls, routing tables, listeners, reverse proxies, and application configuration determine which traffic a server can actually receive and serve.

**Problem:** Pointing the apex domain at OVH2 does not prove OVH4 or AWS3 cannot receive requests for that Host header, direct-IP requests, node-to-node traffic, or requests through another hostname. Conversely, the nodes may need to continue exchanging blockchain peer traffic.

**Solution:** Define the exact isolation goal. If the intended requirement is “public web requests using Host: artcb.me should terminate at OVH2,” test that host routing and the destination. If the requirement is “OVH4 and AWS3 must not serve the public TERMINATOR website,” validate their virtual-host configuration and network controls without blocking required blockchain peer ports. Preserve and test `n4.artcb.me` and `n3.artcb.me` as separate node endpoints.

### 3.4 A DNS result is not an end-to-end demo acceptance test

**Process:** After DNS resolution, the client must complete TCP connectivity, TLS negotiation, HTTP routing, frontend asset loading, and the required backend/API or live-event calls.

**Problem:** A correct A record can still lead to a broken pitch interface due to a missing certificate, wrong virtual host, redirect loop, unavailable frontend service, mixed-content API URLs, CORS failures, or broken SSE/WebSocket proxying.

**Solution:** From an external network, test the exact URLs `https://artcb.me/` and `https://www.artcb.me/`; record DNS answers, certificate hostname/expiry, HTTP status and redirect chain, loaded frontend version, API health, and a successful end-to-end demo flow. Do not include credentials or secret-bearing logs in evidence.

## 4. Claim-by-claim status

| Claim in supplied summary | Review status | Evidence required |
|---|---|---|
| `artcb.me` A record is `151.80.107.29` | **NOT VERIFIED** | Authoritative answer plus timestamped public-resolver lookups |
| `www.artcb.me` A record is `151.80.107.29` | **NOT VERIFIED** | Authoritative and public-resolver answers; inspect CNAME/AAAA too |
| `n4.artcb.me` remains `91.134.45.8` | **NOT VERIFIED** | Current A/AAAA/CNAME results and node health |
| `n3.artcb.me` remains `13.38.209.25` | **NOT VERIFIED** | Current A/AAAA/CNAME results and node health |
| DNS will fully propagate within 24 hours | **UNPROVEN AS A GUARANTEE** | Previous TTLs, authoritative data, resolver observations |
| OVH4 and AWS3 will never receive any `artcb.me` traffic | **OVERSTATED / NOT PROVEN** | Define traffic scope; inspect DNS, IPv6, caches, proxy routes, host routing, and traffic telemetry |
| The apex serves TERMINATOR from OVH2 over valid HTTPS | **NOT VERIFIED** | External HTTP/TLS and frontend end-to-end test |
| Blockchain peer traffic remains healthy after the DNS change | **NOT VERIFIED** | Peer reachability and consensus/replication checks independent of the website |

## 5. Prioritized verification plan

### P0 — Verify public name resolution
1. Query the authoritative nameservers for A, AAAA, CNAME/alias, and relevant DNSSEC data for `artcb.me` and `www.artcb.me`.
2. Query at least Google Public DNS and Cloudflare DNS for both names, record TTLs and timestamps, and compare results.
3. Confirm that `n4.artcb.me` and `n3.artcb.me` still resolve to their intended node endpoints.
4. Confirm whether any CDN, proxy, load balancer, or IPv6 record changes the actual traffic path.

### P0 — Verify the website externally
1. Fetch `https://artcb.me/` and `https://www.artcb.me/` from an external network.
2. Record the full HTTP status/redirect chain and validate certificate name, expiry, and trust chain.
3. Verify the actual TERMINATOR frontend and the required API/live-demo path, not just a successful HTTP response.
4. Confirm no localhost, private-only, or development-only API endpoints are embedded in the public frontend.

### P0 — Verify isolation without breaking the blockchain
1. State whether isolation means “website Host header routed only to OVH2” or “no packets at all reach OVH4/AWS3”; these are different requirements.
2. Test public web routing to OVH2 using the intended hostname.
3. Inspect OVH4/AWS3 web virtual hosts and firewall rules to ensure they do not accidentally serve the TERMINATOR public site, while preserving explicitly required blockchain peer traffic.
4. Check node-to-node health and consensus/replication after the DNS change.
5. Use time-bounded traffic telemetry to support any claim that no matching requests reached OVH4/AWS3; DNS results alone cannot establish that fact.

## 6. Safe wording for the operational status

Until the checks above are completed, use wording such as:

“DNS cutover to OVH2 is reported as configured. Public propagation and HTTPS/frontend behavior remain under verification. The OVH4 and AWS3 blockchain node hostnames are reported unchanged. We have not yet independently demonstrated that all public resolvers converge or that no requests using the apex hostname can reach OVH4/AWS3.”

After evidence is collected, report the exact resolver set, time window, observed IPs, HTTP/TLS result, and traffic scope. Avoid the absolute phrase “never receive traffic” unless the scope is narrowly defined and supported by network-level evidence.

## 7. Change-control statement

This review is documentation-only. It does not change DNS records, infrastructure, source code, deployment configuration, secrets, logs, or the separate `vgactech/artcb` repository. The claimed R074 file was not found at the exact path supplied in the connected repository view, so this report evaluates only the user-provided summary and the limited public retrieval observations above.

## 8. Final verdict

**Architecture: plausible. DNS cutover: not independently verified. Public demo readiness: not certified. Absolute OVH4/AWS3 traffic-isolation claim: unsupported by DNS evidence alone.**

The immediate next action is to collect authoritative and multi-resolver DNS evidence, validate HTTPS and the live frontend from outside OVH2, and separately test blockchain peer health. This is an evidence gap, not proof that the cutover failed.
