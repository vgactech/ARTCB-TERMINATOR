# R051 — Bedrock Integration & EC2 Provisioning

**Date:** 2026-10-10  
**Branch:** feat/artcb-forensic-integration  
**Status:** ✅ COMPLETE

---

## Summary

This report documents the successful activation of AWS Bedrock as LLM fallback
and the provisioning of two EC2 instances on the hackathon account `769488121557`.

---

## 1. STS Credentials Refresh

| Field | Value |
|---|---|
| Account | `769488121557` |
| Role | `WSParticipantRole/Participant` |
| Region | `us-west-2` |
| Token refreshed via | AWS CloudShell IMDS |
| Stored in | Doppler `aws/dev` |

---

## 2. AWS Bedrock — Verified PASS

| Model | Profile ID | Status |
|---|---|---|
| Claude Sonnet 4.5 | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` | ✅ PASS |
| Claude Sonnet 4 | `us.anthropic.claude-sonnet-4-20250514-v1:0` | Available |
| Claude Opus 4.5 | `us.anthropic.claude-opus-4-5-20251101-v1:0` | Available |

**Test result:** Live invoke confirmed — model responded correctly.  
**Note:** On-demand model IDs require cross-region inference profile prefix `us.*`

---

## 3. Bedrock Fallback Integration — guardian_mcp/llm_attacker.py

- **Architecture:** OpenAI primary → Bedrock automatic fallback
- **Trigger:** Any OpenAI exception (quota, auth, network)
- **Bedrock call:** Messages API with JSON tool-call prompt (no native tool_choice)
- **Model:** `us.anthropic.claude-sonnet-4-5-20250929-v1:0`
- **New field in result:** `backend: "openai" | "bedrock"`
- **Tests:** 169/169 PASS (no regression)

---

## 4. EC2 Infrastructure — Provisioned

| Instance | ID | IP | DNS | Role |
|---|---|---|---|---|
| artcb-terminator-api | `i-0b6a5a8f173666d50` | `54.203.22.158` | `ec2-54-203-22-158.us-west-2.compute.amazonaws.com` | Guardian API :8000 |
| artcb-terminator-frontend | `i-0afd05ce87a7e6bf2` | `35.90.101.61` | `ec2-35-90-101-61.us-west-2.compute.amazonaws.com` | React Frontend :3000 |

- **AMI:** `ami-00e236d9d38e7c625` (Amazon Linux 2023, x86_64)
- **Type:** `t3.medium`
- **Region:** `us-west-2`
- **Key pair:** `artcb-terminator-key` (stored: `%TEMP%\artcb-terminator-key.pem`)
- **Security group:** `sg-032633fda3d582f15` (ports 22/80/443/3000/8000 open)
- **All values stored:** Doppler `aws/dev` (9 new secrets)

---

## 5. Deployment Script

Created: `scripts/deploy_ec2.sh`  
- Clones repo on both nodes
- Installs Python 3.11 + boto3 + uvicorn on API node
- Builds React frontend on frontend node
- Starts Guardian API via Doppler run
- Starts frontend via PM2 serve

---

## 6. Pending

| Task | Status |
|---|---|
| SSH key to EC2 nodes (push + run deploy_ec2.sh) | ⏳ Next |
| DNS `terminator.artcb.me` → `35.90.101.61` | ⏳ Next |
| Re-provision SSH N3 via SSM | ⏳ Pending |
| PBFT view-change relay (stall ~26 days) | ⏳ Pending |
| New ElevenLabs key | ⏳ Pending |

---

## Checklist

- [x] STS refreshed and validated
- [x] Bedrock list-foundation-models PASS (16 Claude models)
- [x] Bedrock invoke-model PASS (claude-sonnet-4-5)
- [x] llm_attacker.py updated with Bedrock fallback
- [x] 169 tests PASS
- [x] EC2 key pair created
- [x] Security group created (5 ports)
- [x] 2 EC2 instances running
- [x] All IDs/IPs stored in Doppler aws/dev
- [x] deploy_ec2.sh created
