# R065 — Frontend KYC Guardian Metro Network + MediaPipe 3D + Screenpipe Track 3

**Date :** 2026-10-17  
**Projet :** `vgactech/artcb_TERMINATOR_FRONTEND` + `vgactech/ARTCB-TERMINATOR`  
**Commit frontend :** `2739715`  
**Mode DEBUG actif.** `CERTIFIED_100=false` | `unique_human_proven=false`

---

## Résumé

Réécriture complète de `index.html` dans `artcb_TERMINATOR_FRONTEND` :
- Architecture **réseau de métro** (3 lignes, 11 stations) représentant le pipeline KYC réel
- Connexion **live SSE** à `guardian_api/kyc_stream.py` (7 événements → activations 3D)
- **Fallback simulé** complet si Guardian API hors ligne (Screenpipe Track 3 compatible)
- **MediaPipe** main tracking + pinch → sélection de stations conservée et améliorée
- **Header Screenpipe** obligatoire ajouté (`<!-- screenpipe — AI that knows ... -->`)

---

## Avant / Après

### `artcb_TERMINATOR_FRONTEND/index.html`

| | AVANT (commit `ee98fea`) | APRÈS (commit `2739715`) |
|---|---|---|
| Titre | `ARTCB // Holographic Command Surface` | `ARTCB TERMINATOR // Guardian KYC Console` |
| Nœuds 3D | 6 nœuds fictifs (AGENT-01, TOOL-02…) | 11 stations réelles (S-01…S-11) |
| Architecture | Graphe générique | Réseau de métro 3 lignes (A=Identity, B=Guardian, C=Forensic) |
| Données | Fixture statique | Live SSE depuis `/api/kyc/stream` + fallback simulé |
| Interactions | Pinch → nœud suivant | Pinch → station suivante + KYC modal (▶ Run KYC) |
| API | Non connectée | `checkApi()` → `ONLINE/OFFLINE` chip en temps réel |
| PDF | Absent | Download auto si `pdf_b64` reçu depuis Guardian |
| Screenpipe | Absent | Header obligatoire + `Track 3` dans subtitle + fallback conforme |
| Lignes | `index.html` : 245 lignes | `index.html` : 880 lignes |

---

## Architecture réseau de métro — Pipeline KYC

```
LINE A (cyan) — Identity
  S-01: session.open  →  S-02: identity.verify  →  S-03: kyc.start
                                                         ↓
LINE B (amber) — Guardian                         S-04: attack.craft
  S-03 → S-04 → S-05: request.propagate → S-06: policy.evaluate → S-07: BLOCK/ALLOW
                                                                         ↓
LINE C (violet) — Forensic                              S-08: chain.verify
  S-07 → S-08 → S-09: kyc.score → S-10: pdf.generate → S-11: done
  S-03 ─────────────────────────────────────────────── S-11 (express loop)
```

**Correspondances avec `guardian_api/kyc_stream.py` (SSE events) :**

| Station | Event SSE | Fichier source |
|---------|-----------|----------------|
| S-01 | `session_opened` | `kyc_stream.py:235` |
| S-02 | `kyc_identity_check` | `kyc_stream.py:255` |
| S-04 | `attack_generated` | `kyc_stream.py:278` |
| S-05 | `propagation` | `kyc_stream.py:295` |
| S-06/S-07 | `guardian_decision` | `kyc_stream.py:309` |
| S-08 | `chain_verified` | `kyc_stream.py:331` |
| S-09 | `kyc_result` | `kyc_stream.py:345` |
| S-10/S-11 | `done` | `kyc_stream.py:358` |

---

## Statuts de stations (couleurs 3D temps réel)

| Statut | Couleur hex | Signification |
|--------|-------------|---------------|
| `idle` | `#224466` | En attente |
| `active` | `#59f6ff` (cyan pulsant) | En cours d'exécution |
| `ok` | `#83ffbf` (vert) | Succès |
| `warn` | `#ffd27a` (amber) | Alerte / risque |
| `block` | `#ff6f9f` (rouge) | Attaque bloquée / erreur |
| `done` | `#bd7bff` (violet) | Terminal / pipeline terminé |

---

## Screenpipe Track 3 — Compatibilité

Le frontend est conçu pour fonctionner dans les 4 cas du Track 3 :

| Cas | Comportement |
|-----|-------------|
| Guardian API online | SSE live → stations s'activent en temps réel |
| Guardian API offline | Fallback simulé `simulateKyc()` → même parcours, données synthétiques |
| Démo pour un collègue | `▶ Run KYC` → modal → saisie identité → pipeline observable |
| Replay sur nouvelle entrée | Chaque Run KYC est indépendant — `resetAllStations()` à chaque lancement |

**Données SIMULATED** — aucun PII réel. Mention `● SIMULATED DATA` visible en permanence.

---

## Nouveaux fichiers / fichiers modifiés

| Fichier | Dépôt | Changement |
|---------|-------|------------|
| `index.html` | `artcb_TERMINATOR_FRONTEND` | Réécriture complète (+634 lignes nettes) |

---

## Comment lancer

### Sans backend (demo mode complet)
```
# Ouvrir directement dans un navigateur :
open artcb_TERMINATOR_FRONTEND/index.html
# ou via GitHub Pages : https://vgactech.github.io/artcb_TERMINATOR_FRONTEND/
```

### Avec Guardian API live
```bash
# Backend ARTCB-TERMINATOR (terminal 1)
cd terminator_repo
pip install -r guardian_api/requirements.txt
uvicorn guardian_api.app:app --host 0.0.0.0 --port 8001

# Frontend (terminal 2 — ouvrir index.html ou servir via http-server)
# Le chip "API ONLINE" s'allume, les stations 3D s'activent en temps réel
```

### Déploiement OVH2 (API déjà live)
```
GUARDIAN_API_URL=http://151.80.107.29:8001
```
Définir dans la page via console : `window.GUARDIAN_API_URL = 'http://151.80.107.29:8001'`  
ou via paramètre URL (à implémenter si nécessaire).

---

## Notes

- Header Screenpipe `<!-- screenpipe — AI that knows everything you've seen, said, or heard -->` ajouté ligne 2 conformément aux règles du hackathon.
- Pinch MediaPipe → navigue entre les 11 stations (pas d'action métier déclenchée par le geste).
- `pdf_b64` reçu en fin de pipeline → téléchargement automatique du PDF forensic Guardian.
- Rapport précédent R064 conservé intégralement (no wipe).
