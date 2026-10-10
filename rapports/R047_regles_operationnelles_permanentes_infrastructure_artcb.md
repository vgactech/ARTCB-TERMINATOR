# R047 — Règles opérationnelles permanentes : Infrastructure ARTCB

**Date :** 2026-10-10  
**Statut :** RÈGLE PERMANENTE — ne pas supprimer, ne pas modifier les interdits  
**Portée :** Toutes les futures sessions travaillant sur ARTCB ou ARTCB-TERMINATOR  
**Source :** R046 (audit live SSH + AWS + Doppler, 2026-10-10)

---

## Règle absolue R1 — N1/OVH1 est retiré

```
IP  : 152.228.144.34
NIC : xy4589-ovh (vgac42@gmail.com)
```

**N1/OVH1 est un nœud blockchain ARTCB retiré depuis la décision D-036.**

Interdits permanents sur N1 :
- Ne **jamais** cibler `152.228.144.34` comme serveur actif
- Ne **jamais** demander ou chercher les clés SSH de N1
- Ne **jamais** compter N1 parmi les nœuds actifs du consensus PBFT
- Ne **jamais** tenter de le relancer, le reconfigurer ou le reconnecter
- Ne **jamais** interpréter un ancien rapport mentionnant N1 comme preuve qu'il est opérationnel

Mention historique autorisée : N1 peut apparaître **dans les rapports d'audit historiques** avec la mention explicite `[RETIRÉ — D-036]`. C'est la seule forme de référence acceptable.

---

## Règle R2 — Inventaire actif des nœuds (vérifié live 2026-10-10)

| Nœud | IP active | Hébergeur | Doppler | SSH user | État |
|---|---|---|---|---|---|
| **N2/OVH2** | `151.80.107.29` | OVH GRA11, nic `vc491276-ovh` | `artcb-2/dev` | `ubuntu` | ✅ UP — height 1142 |
| **N3/AWS3** | `13.38.209.25` (EIP) | AWS `599128160879`, eu-west-3 | `artcb3/dev` | `ubuntu` | ⚠️ Running, SSH à re-provisionner |
| **N4/OVH4** | `91.134.45.8` | OVH GRA11, nic `xy4589-ovh` | `artcb-4/dev` | `ubuntu` | ✅ UP — height 1142 |

**Règle** : tout état d'un nœud cité sans vérification live récente doit être qualifié d'**historique non confirmé**.

---

## Règle R3 — Séparation ARTCB blockchain ≠ ARTCB-TERMINATOR

Ces deux projets ne partagent **aucun serveur, aucune clé, aucun compte cloud**.

| Dimension | ARTCB blockchain | ARTCB-TERMINATOR |
|---|---|---|
| Dépôt Git | `vgactech/artcb` (privé) | `vgactech/ARTCB-TERMINATOR` |
| AWS compte | `599128160879` (IAM `node_artcb_3_agent`) | `769488121557` (WSParticipantRole hackathon) |
| OVH | Deux comptes (N2/N4) | Aucun |
| Doppler | `artcb-2`, `artcb3`, `artcb-4`, `artcb-blockchain` | `artcb-terminator`, `aws` |
| SSH key | Par nœud dans Doppler dédié | `artcb_terminator_ed25519` |
| Port 8000 | API blockchain ARTCB | Guardian FastAPI |

**Règle** : ne jamais utiliser les credentials d'un projet pour l'autre.

---

## Règle R4 — Clés SSH des nœuds

Les clés SSH **ne sont pas** dans `artcb-blockchain/dev`. Elles sont dans les projets dédiés :

| Nœud | Projet Doppler | Clé |
|---|---|---|
| N2 | `artcb-2/dev` → `SSH_PRIVATE_KEY` | Commentaire : `artcb-ovh-node-2-*` |
| N3 | `artcb3/dev` → `SSH_PRIVATE_KEY` | ⚠️ Peut nécessiter re-provisionnement |
| N4 | `artcb-4/dev` → `SSH_PRIVATE_KEY` | Commentaire : `artcb-ovh-node-4-20260902` |

**Règle** : pour accéder à un nœud, toujours lire sa clé depuis son projet Doppler dédié.

---

## Règle R5 — ARTCB_API_URL dans artcb-blockchain/dev est stale

```
ARTCB_API_URL = http://152.228.144.34:8000   ← STALE — pointe sur N1 retiré
```

L'URL correcte du nœud principal actif est N4 : `http://91.134.45.8:8000`  
(ou N2 : `http://151.80.107.29:8000` comme failover)

**Règle** : ne jamais utiliser `ARTCB_API_URL` de `artcb-blockchain/dev` tel quel. Utiliser l'IP de N4 ou N2 directement.

---

## Règle R6 — Alias DNS n1.artcb.me

L'alias `n1.artcb.me` existe dans `scripts/artcb_dns_fix.py` du dépôt ARTCB comme **alias de compatibilité** pointant vers N4 (`91.134.45.8`). Il n'est pas une porte d'entrée vers N1.

**Règle** : ne pas supprimer cet alias sans vérification des dépendances dans le dépôt `vgactech/artcb`. Toute modification dans ce dépôt nécessite une autorisation explicite.

---

## Règle R7 — Pattern de saturation des nœuds OVH

N2 et N4 présentent un pattern de saturation après ~26 jours sans redémarrage :
- RAM : 6.6–6.7 / 7.6 Go occupée
- Charge CPU : 10–17
- Symptôme : `Exceeded concurrency limit` → HTTP 503

**Correction** : `sudo systemctl restart artcb` sur le nœud (peut prendre 30–60s).  
**Note** : le redémarrage est déclenché depuis cette machine via SSH avec la clé Doppler.

---

## Règle R8 — Compte AWS artcb-blockchain ≠ compte hackathon

| Compte | Rôle | Usage |
|---|---|---|
| `769488121557` | `WSParticipantRole/Participant` (STS temporaire) | Hackathon ARTCB-TERMINATOR uniquement |
| `599128160879` | `node_artcb_3_agent` (IAM permanent) | Nœud N3 ARTCB blockchain uniquement |

Les credentials du compte `769488121557` (Doppler `aws/dev`) ne donnent **aucun accès** à N3.  
Les credentials N3 sont dans Doppler `artcb3/dev` (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).

---

## Synthèse des interdits encodés

| Interdit | Cible |
|---|---|
| Ne jamais cibler | `152.228.144.34` (N1/OVH1 retiré) |
| Ne jamais confondre | AWS `769488121557` (hackathon) avec `599128160879` (ARTCB N3) |
| Ne jamais utiliser | `ARTCB_API_URL` de `artcb-blockchain/dev` sans correction |
| Ne jamais modifier | `vgactech/artcb` sans autorisation explicite |
| Ne jamais supposer | L'état d'un nœud sans vérification live SSH ou HTTP récente |

---

*R047 — règles opérationnelles permanentes. Réf : R046 (2026-10-10). À conserver indéfiniment.*
