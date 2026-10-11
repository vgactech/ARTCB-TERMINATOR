# Soumission Hackathon — ARTCB TERMINATOR FORENSIC
## Secure Horizons 2026 — Round 1

> **Fichier de préparation** — À remplir puis coller dans le formulaire Google Forms  
> Lien formulaire : https://forms.gle/a1FqDZueuUKX3Tz26  
> **Deadline : Dimanche 12h30 (HARD FREEZE)**

---

## CHAMPS DU FORMULAIRE GOOGLE

### Team number
```
N/A
```
*(si vous n'avez pas reçu de numéro d'équipe)*

---

### Team contact full name
```
[TON NOM COMPLET ICI]
```
*Exemple : Paul NOEL*

---

### Team contact email
```
vgac4237@gmail.com
```
*(compte Google que tu utiliseras pour uploader les fichiers)*

---

### Team members, emails and schools
*(Un membre par ligne, format exact : Prénom NOM | email | école)*
```
[PRÉNOM NOM] | vgac4237@gmail.com | [TON ÉCOLE / UNIVERSITÉ]
```
*Exemple si tu es seul :*
```
Paul NOEL | vgac4237@gmail.com | ESSEC Business School
```
*Si plusieurs membres, ajoute une ligne par personne :*
```
Paul NOEL | vgac4237@gmail.com | ESSEC Business School
[Membre 2] | [email2@example.com] | [École 2]
```

---

### Track / challenge name
```
Secure Horizons
```

---

### Project name
```
ARTCB TERMINATOR FORENSIC
```

---

### Project pitch (maximum 2 sentences)
```
AI agents handling financial and legal tasks — KYC, transactions, contract 
generation — are blind attack vectors: no standard today traces or proves 
what an AI decided, when, and why. ARTCB TERMINATOR FORENSIC is a Guardian 
Engine that intercepts every AI agent tool call before execution, blocks 
attacks with cryptographic proof (SHA-256 R0 chain), and generates a 
court-admissible forensic PDF report — demonstrated live with a KYC 
scenario where a Bedrock LLM attacker is blocked in real time.
```

*(Si la limite est vraiment 2 phrases courtes, version condensée :)*
```
Banks and law firms deploying AI agents face an invisible threat: no 
standard traces or proves what an AI decided before a fraud or injection 
occurs. ARTCB TERMINATOR FORENSIC is a Guardian Engine that intercepts 
every agent tool call in real time, blocks attacks with SHA-256 forensic 
proof, and generates a downloadable audit PDF — live KYC demo included.
```

---

### GitHub repository URL
```
https://github.com/vgactech/ARTCB-TERMINATOR
```
⚠️ **ACTION REQUISE** : Rendre le dépôt **PUBLIC** avant la soumission  
`GitHub → Settings → Danger Zone → Change repository visibility → Public`

---

### Setup instructions of your github repository and notes for judges
```
## Quick Start (judges)

Live demo (no install needed):
  Frontend: http://35.90.101.61
  API health: http://54.203.22.158:8000/api/health

Branch: feat/artcb-forensic-integration

Local install:
  git clone https://github.com/vgactech/ARTCB-TERMINATOR.git
  cd ARTCB-TERMINATOR
  git checkout feat/artcb-forensic-integration

  # Backend (Python 3.11+)
  pip install -r guardian_api/requirements.txt
  pip install boto3
  uvicorn guardian_api.app:app --host 0.0.0.0 --port 8000

  # Frontend (Node 20+)
  cd frontend && npm install && npm run dev
  # Open http://localhost:5173

Known limitations:
  - LLM attacker uses static fallback when AWS Bedrock token expires (~12h)
  - ElevenLabs voice commentary disabled (API key expired)
  - ARTCB blockchain N3 node SSH provisioning pending (SSM access OK)
```

---

## CHECKLIST FICHIERS À UPLOADER (avant 12h30)

| Fichier | Statut | À faire |
|---|---|---|
| **Pitch deck** (OBLIGATOIRE, ≤8 slides) | ⏳ À créer | Voir structure ci-dessous |
| **Demo video** (2-3 min) | ⏳ Optionnel | Enregistrer écran sur http://35.90.101.61 |
| **Defense sheet** (1 page) | ⏳ Optionnel | Voir structure ci-dessous |
| **Track deliverable** | ✅ GitHub + live | http://35.90.101.61 |

---

## STRUCTURE PITCH DECK (8 slides max)

### Slide 1 — Titre
- **ARTCB TERMINATOR FORENSIC**
- Guardian Security Console for AI Agents
- Team : [Nom équipe] | ESSEC Hackathon 2026

### Slide 2 — Le problème
- Les agents IA gèrent des actes financiers/juridiques à la place de l'humain
- Aucune traçabilité = aucune preuve en cas de fraude ou de litige
- Réglementations (DORA, AI Act, LCB-FT) n'ont pas de standard pour les agents IA
- **Chiffre choc** : fraude IA en hausse de 300% depuis 2023

### Slide 3 — Les cibles
- **Banques** : KYC, signature électronique, conformité AML
- **Juristes** : due diligence, contrats IA, responsabilité civile
- **Fintechs** : différenciation réglementaire, certifications

### Slide 4 — La solution
- Guardian Engine : intercepte chaque appel d'outil AVANT exécution
- 4 agents : Orchestrator → Attacker → Propagator → Defender
- Preuve R0 : SHA-256 chaîné, immuable, vérifiable indépendamment
- Rapport PDF forensique téléchargeable

### Slide 5 — Architecture
```
[LLM Attacker (Bedrock)] → [Orchestrator] → [Propagator] → [Guardian]
                                                                 ↓
                                                          BLOCK + SHA-256
                                                                 ↓
                                                          PDF Report
```
- AWS Bedrock Claude Sonnet 4.5 (attaquant + fallback LLM)
- FastAPI + Python Guardian Engine
- React + Vite frontend
- ARTCB Blockchain (3 nœuds, height=1142)

### Slide 6 — Démo live
- Scénario KYC : formulaire → attaque → BLOCK → PDF
- Timeline forensic en temps réel (SSE)
- HUD Graph animé (4 nœuds Guardian)
- **URL jury** : http://35.90.101.61

### Slide 7 — Résultats / Tests
- 169 tests Python PASS
- 27 tests Rust PASS (Guardian Core C-01→C-08)
- CORS ouvert : accessible depuis tout réseau
- 7 événements SSE vérifiés (session→identity→attack→block→chain→KYC→PDF)

### Slide 8 — Limitations & Roadmap
**Limitations connues :**
- Voice commentary désactivé (ElevenLabs key expirée)
- STS token AWS hackathon ~12h (se renouvelle manuellement)
- ARTCB blockchain consensus PBFT en stall (26j, N3 offline temporaire)

**Roadmap :**
- SaaS Guardian API pour banques
- ARTCB on-chain anchoring des preuves
- Intégration DORA compliance reporting automatique

---

## STRUCTURE DEFENSE SHEET (1 page)

```
ARTCB TERMINATOR FORENSIC — Defense Sheet

PROBLEM / THREAT
AI agents executing financial and legal operations (KYC, transactions, 
contracts) have no forensic traceability. An attacker can inject malicious 
instructions, trigger unauthorized transactions, or manipulate agent 
memory — with zero audit trail under current standards.

OUR SOLUTION
Guardian Engine: a policy interceptor placed between the AI orchestrator 
and sensitive tools. Every tool call is evaluated BEFORE execution.
Blocked calls produce a SHA-256 cryptographic proof (R0 chain) stored 
in an immutable archive. A forensic PDF report is auto-generated.

WHAT WE TESTED
- 169 Python unit tests (PASS) covering all 4 Guardian agents
- 27 Rust unit tests (PASS) for Guardian Core components C-01→C-08  
- Live KYC scenario: identity → LLM fraud attack → BLOCK → PDF (verified)
- 7 SSE events streamed in correct order (session/identity/attack/
  propagation/decision/chain/result)
- CORS validated across multiple networks and devices

RESULTS
- 100% of test attacks blocked before tool execution
- Cryptographic chain integrity: PASS on all runs
- Tamper detection: PASS (modified archive detected)
- Live demo accessible: http://35.90.101.61

KNOWN LIMITATIONS
- Voice commentary disabled (ElevenLabs API key expired)
- AWS STS token requires manual refresh every ~12 hours
- ARTCB blockchain PBFT consensus stalled (N3 node was offline 26 days,
  now recovered; view-change relay pending)
- LLM attacker uses static fallback when Bedrock token expires

REGULATORY RELEVANCE
DORA (Art. 9), AI Act (2024), LCB-FT, RGPD Art. 22, eIDAS, MiFID II
```

---

## NOTES IMPORTANTES

1. **Rendre le repo PUBLIC** sur GitHub avant de soumettre
2. **Sauvegarder le lien "Edit your response"** après soumission (pour mettre à jour le GitHub link)
3. **URL démo jury** : http://35.90.101.61 (port 80, accessible partout)
4. **Deadline HARD FREEZE** : Dimanche 12h30
5. Le dossier Google Drive sera créé automatiquement après soumission du formulaire
