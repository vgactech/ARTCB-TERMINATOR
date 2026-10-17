# R074 — DNS artcb.me corrigé : OVH2 uniquement, isolation complète

**Date :** 2026-10-17T12:00:00Z  
**Mode :** DEBUG actif  
**CERTIFIED_100=false** | **unique_human_proven=false**

---

## Actions DNS effectuées (interface OVH manager)

### AVANT
```
www.artcb.me.  60  A  91.134.45.8   ← OVH4 blockchain
artcb.me.          A  (absent)
```

### APRÈS
```
artcb.me.      300  A  151.80.107.29  ← OVH2 TERMINATOR ✅
www.artcb.me.  300  A  151.80.107.29  ← OVH2 TERMINATOR ✅
```

**Record supprimé :** `www.artcb.me → 91.134.45.8` (OVH4)  
**Records créés :** `artcb.me → 151.80.107.29` + `www.artcb.me → 151.80.107.29`

---

## Propagation DNS (vérifiée immédiatement après)

```
dig +short www.artcb.me A  → 151.80.107.29 ✅ (propagé)
dig +short artcb.me A      → 91.134.45.8 + 151.80.107.29 (cache en cours de vidage, max 24h)
```

---

## Architecture finale — isolation complète

```
artcb.me / www.artcb.me → 151.80.107.29 (OVH2)
  nginx :80  → 301 HTTPS
  nginx :443 → frontend ARTCB-TERMINATOR index.html
             → /api/* → Guardian :8002
  artcb-guardian.service → actif, ElevenLabs voice_enabled=true
  artcb.service → DÉSACTIVÉ définitivement

n4.artcb.me → 91.134.45.8 (OVH4) — blockchain uniquement
n3.artcb.me → 13.38.209.25 (AWS3) — blockchain uniquement
Mac → tests locaux uniquement, aucun rôle production
```

---

## Credentials OVH app BOBARTCB1 stockés dans Doppler artcb-4

```
OVH_APPLICATION_KEY    → Doppler artcb-4/dev ✅
OVH_APPLICATION_SECRET → Doppler artcb-4/dev ✅
OVH_CONSUMER_KEY       → Doppler artcb-4/dev ✅
```

---

## Rapports précédents conservés

R065 → R073 — non modifiés.
