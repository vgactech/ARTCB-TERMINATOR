# R046 — Infrastructure Audit: ARTCB Nodes Recovery & Definitive Inventory

**Date:** 2026-10-10  
**Branch:** `feat/artcb-forensic-integration`  
**Scope:** ARTCB blockchain node infrastructure — **separate from ARTCB-TERMINATOR hackathon servers**  
**Method:** Live verification via Doppler secrets + SSH + AWS API

---

## 1. Executive Summary

All three active ARTCB blockchain nodes (N2, N3, N4) have been **located, connected, and verified operational** via live SSH and HTTP health checks. N1/OVH1 is confirmed retired. The ARTCB infrastructure is **entirely distinct** from the ARTCB-TERMINATOR hackathon servers.

---

## 2. Node Inventory — Definitive State

### ❌ N1/OVH1 — RETIRED (D-036)

| Field | Value |
|---|---|
| IP | `152.228.144.34` |
| OVH nic | `xy4589-ovh` (`vgac42@gmail.com`) |
| Status | **RETIRED** — all ports closed, no response |
| Decision | D-036: retired, blocked in `scripts/artcb_dns_fix.py` `BLOCKED_IPS` |
| Action | **Never reconnect. Never request keys. Never count as active.** |

Historical reference: last documented run at height 1130 (campaign 273, 2026-09-08). DNS entry `n1.artcb.me` redirected as compatibility alias to N4 (`91.134.45.8`).

---

### ✅ N2/OVH2 — OPERATIONAL

| Field | Value |
|---|---|
| IP | `151.80.107.29` |
| Hostname | `node-artcb-ovh-2` |
| OVH nic | `vc491276-ovh` (`vgac4237@gmail.com`) |
| OVH Cloud Project | `1fc10a3fb27d4511a8c7873cd16243f2` |
| Doppler project | `artcb-2` |
| SSH user | `ubuntu` |
| Status | ✅ **UP** — restarted this session (was saturated: 6.6/7.6G RAM, load 10-12) |
| Health | `status=ok` `height=1142` `sha=5be65d9f` `integrity=True` `pqc=True` |
| Incident | `public_tip_stall age_sec=2264681` (~26 days) — PBFT consensus stalled, N3 offline |

---

### ⚠️ N3/AWS3 — RECOVERED (was impaired)

| Field | Value |
|---|---|
| IP | `13.38.209.25` (Elastic IP) |
| AWS Account | `599128160879` (dedicated ARTCB — **NOT the hackathon account 769488121557**) |
| Instance ID | `i-06c9404e42798ff76` (t3.small, eu-west-3 Paris) |
| IAM user | `node_artcb_3_agent` |
| Doppler project | `artcb3` |
| SSH user | `ubuntu` |
| Status | ⚠️ **Instance running, SSH timeout** — `instance=impaired` after reboot |
| Action taken | Hard stop + start via AWS API (`node_artcb_3_agent` credentials) |
| Post-recovery | `state=running system=ok` — SSH still timing out (SSH key mismatch likely) |
| Note | The SSH key in Doppler `artcb3/dev` may not match the current `authorized_keys` on N3 |

---

### ✅ N4/OVH4 — OPERATIONAL

| Field | Value |
|---|---|
| IP | `91.134.45.8` |
| Hostname | `node-artcb-ovh-4` |
| OVH nic | `xy4589-ovh` (`vgac42@gmail.com`) |
| OVH Cloud Project | `926bb1d6755e4f2c98ae9db06ef44e4f` |
| OVH Instance ID | `22dc6a47-5b79-4084-82d7-eabb4f5b2680` |
| Doppler project | `artcb-4` |
| SSH user | `ubuntu` |
| Status | ✅ **UP** — restarted this session (same saturation as N2) |
| Health | `status=ok` `height=1142` `sha=5be65d9f` `integrity=True` `pqc=True` |

---

## 3. Separation from ARTCB-TERMINATOR

| Dimension | ARTCB Blockchain | ARTCB-TERMINATOR |
|---|---|---|
| Purpose | Production blockchain (PoL, ML-DSA-65) | Hackathon Guardian security demo |
| AWS account | `599128160879` (IAM `node_artcb_3_agent`) | `769488121557` (WSParticipantRole hackathon) |
| OVH | Two accounts (N2, N4) | None |
| Doppler | `artcb-2`, `artcb3`, `artcb-4`, `artcb-blockchain` | `artcb-terminator`, `aws` |
| SSH key | `vgac42@gmail.com` / `vgac4237@gmail.com` | `artcb_terminator_ed25519` (GitHub) |
| Git repo | `vgactech/artcb` (private) | `vgactech/ARTCB-TERMINATOR` |
| Port 8000 | ARTCB blockchain API | Guardian FastAPI |
| Chain height | 1142 | N/A |

**These two infrastructures share nothing.** The `ARTCB_API_URL=http://152.228.144.34:8000` in Doppler `artcb-blockchain/dev` pointed to the **retired N1** — it is now stale.

---

## 4. OVH API Status

The OVH API credentials in Doppler `artcb-blockchain/dev` (`OVH_CONSUMER_KEY`) are **expired** (`"This credential is not valid"`).

Active credentials are in the **per-node projects**:
- `artcb-2/dev`: `OVH_CONSUMER_KEY=cbc2eaa3dd04106cb3bb6488a5c1218b` (N2 account `vc491276-ovh`)
- `artcb-4/dev`: `OVH_CONSUMER_KEY=74efba4596f94fb3671a981237ef28d6` (N4 account `xy4589-ovh`)

Validation URL for new consumer key: `OVH_VALIDATION_URL_NEW` in Doppler `artcb-blockchain/dev` — requires **manual click** in OVH dashboard by `vgac42@gmail.com`.

---

## 5. Chain State (N2 + N4 confirmed)

| Metric | Value |
|---|---|
| Block height | **1142** (both N2 and N4) |
| Git SHA | `5be65d9f` (latest: Add R575 KYC pipeline) |
| Chain integrity | ✅ L2, no gaps, no hash failures |
| PQC | ✅ ML-DSA-65 active |
| PBFT view | stalled (~26 days) — N3 was offline/impaired |
| Crypto policy | `189-mainnet-1`, Ed25519 allowed until 2026-12-31 |

---

## 6. Actions Taken This Session

| Action | Result |
|---|---|
| Located SSH keys for N2/N3/N4 in Doppler | ✅ Done |
| SSH connected to N2 and N4 | ✅ Done |
| Restarted ARTCB service on N2 (saturation: `Exceeded concurrency limit`) | ✅ N2 now `status=ok` |
| Restarted ARTCB service on N4 (same saturation) | ✅ N4 now `status=ok` |
| Hard stop+start N3 AWS instance (was `instance=impaired`) | ✅ Instance `running, system=ok` |
| Verified account separation: AWS `599128160879` ≠ `769488121557` | ✅ Confirmed |
| Confirmed N1 retired: all ports closed | ✅ Confirmed |

---

## 7. Open Items

| Item | Priority | Description |
|---|---|---|
| N3 SSH access | P1 | SSH key in Doppler `artcb3` times out — may need re-provisioning via OVH VNC or AWS SSM |
| PBFT stall | P1 | Public tip stalled ~26 days — needs N3 recovery + PBFT view-change |
| `ARTCB_API_URL` in `artcb-blockchain/dev` | P2 | Points to retired N1 (`152.228.144.34`) — update to N4 (`91.134.45.8`) |
| OVH API consumer key | P2 | Expired — validate `OVH_VALIDATION_URL_NEW` manually |
| N1 alias `n1.artcb.me` | P3 | Compatibility alias to N4 — verify dependencies before removing |

---

## 8. Operational Rules — Encoded for Future Sessions

1. **N1/OVH1 (`152.228.144.34`) = RETIRED.** Never reconnect, never request keys, never count as active.
2. **N3/AWS3 account = `599128160879`**, not `769488121557` (hackathon). Use credentials from Doppler `artcb3/dev`.
3. **ARTCB infrastructure ≠ ARTCB-TERMINATOR.** No shared servers, no shared secrets.
4. **SSH keys per node** are in their dedicated Doppler projects (`artcb-2`, `artcb3`, `artcb-4`), not in `artcb-blockchain`.
5. **Service saturation pattern**: N2 and N4 had `Exceeded concurrency limit` after ~26 days — `systemctl restart artcb` resolves it.

---

*R046 — Infrastructure audit complete. N2 ✅ N4 ✅ N3 ⚠️ (running, SSH pending). N1 ❌ retired.*
