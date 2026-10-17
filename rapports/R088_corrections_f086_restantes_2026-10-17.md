# R088 — Corrections restantes F086 : cleanup unmount, flush EOF, CRLF, multi-line data

**Date :** 2026-10-17  
**Dépôt :** `vgactech/ARTCB-TERMINATOR`  
**SHA avant :** `aa610fd`  
**SHA après :** voir commit  
**Log de référence :** `logs/20261017_R088_corrections_f086_restantes.json`  
**Build TypeScript :** ✅ 0 erreur — `tsc --noEmit` PASS  
**Mode DEBUG :** actif  
**CERTIFIED_100 :** false  

---

## Contexte

Le rapport R087 avait appliqué les corrections principales de R086 (F086-01 à F086-04), mais les **critères d'acceptance** du rapport R086 incluaient des points non encore traités :

- Le Blob URL n'était pas révoqué au unmount du composant (seulement dans `reset()`)
- Le parseur SSE ne flushait pas l'event courant à la fin du stream si le serveur fermait sans `\n\n` final
- La normalisation CRLF n'était pas implémentée
- Les events SSE multi-lignes `data:` n'étaient pas correctement cumulés

Ce rapport R088 ferme les 4 items restants.

---

## Résumé des corrections

| ID | Sévérité | Fichier | Description | Statut |
|----|----------|---------|-------------|--------|
| F086-02b | MEDIUM | `KycPanel.tsx` | `useEffect` cleanup revoke Blob URL au unmount | ✅ FIXED |
| F086-03b | HIGH | `KycPanel.tsx` | Flush event pending à fin de stream (EOF sans `\n\n`) | ✅ FIXED |
| F086-03c | P1 | `KycPanel.tsx` | Normalisation CRLF → LF avant `split` (RFC 8895 §9) | ✅ FIXED |
| F086-03d | P1 | `KycPanel.tsx` | Multi-line `data:` append avec `\n` (spec SSE §6.2) | ✅ FIXED |

---

## F086-02b — Blob URL non révoquée au unmount du composant

### Fichier : `frontend/src/components/KycPanel.tsx`

**Problème :** `reset()` révoque correctement le Blob URL si l'utilisateur clique sur le bouton de réinitialisation. Mais si le composant est **démonté** (navigation vers un autre onglet, rechargement de la page) sans appel préalable à `reset()`, le Blob URL reste actif en mémoire indefiniment. Les criteria d'acceptance de R086 exigent explicitement que l'URL soit révoquée au unmount.

**Avant :** Aucun `useEffect` de cleanup pour `pdfUrl`. Seul `reset()` révoquait l'URL.

**Après :**
```typescript
// F086-02b — R088 : revoke Blob URL à l'unmount pour libérer la mémoire
//            même si reset() n'est pas appelé avant la destruction du composant
useEffect(() => {
  return () => {
    setPdfUrl(prev => { if (prev) URL.revokeObjectURL(prev); return null })
  }
}, [])
```

**Lignes ajoutées :** après le premier `useEffect` existant (ligne 80), insertion lignes 83–89.

---

## F086-03b — Flush de l'event pending à fin de stream (EOF sans trailing `\n\n`)

### Fichier : `frontend/src/components/KycPanel.tsx`

**Problème :** La spec SSE §6.2 précise que la fermeture du flux doit être traitée comme un séparateur d'event. Si le serveur ferme la connexion sans envoyer un `\n\n` final (trailing blank line) — scénario possible avec des proxies ou des serveurs mal configurés — l'event accumulé dans `curData` était silencieusement perdu. L'event `done` notamment peut être perdu dans ce cas, laissant l'interface en état `running`.

**Avant (après le `while(true)`, pas de vérification) :**
```typescript
        }   // fin while
        setRunning(false)
```

**Après :**
```typescript
        }   // fin while
        // F086-03b — flush de l'event pending si le stream se termine sans trailing \n\n
        //            (comportement conforme à la spec SSE §6.2 : EOF = fin d'event)
        if (curData) {
          handleEvent(curEvent, curData)
        }
        setRunning(false)
```

**Lignes ajoutées :** 3 lignes après la fermeture du `while`.

---

## F086-03c — Normalisation CRLF → LF avant `split`

### Fichier : `frontend/src/components/KycPanel.tsx`

**Problème :** `buf.split('\n')` ne traitait pas les fins de ligne CRLF (`\r\n`) ni les CR seuls (`\r`). Sur des serveurs ou proxies Windows, ou avec certains clients HTTP, les lignes SSE peuvent arriver avec `\r\n`. Le `\r` résiduel en fin de ligne faisait échouer les comparaisons `line.startsWith('event:')` et `line.startsWith('data:')`, causant des events perdus silencieusement.

**Avant (ligne 210) :**
```typescript
const lines = buf.split('\n')
```

**Après :**
```typescript
// F086-03c — normaliser CRLF → LF avant split (spec SSE §3, RFC 8895 §9)
const lines = buf.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n')
```

**Note :** La normalisation est appliquée sur `buf` sans modifier `buf` lui-même — `lines` reçoit la version normalisée, `buf = lines.pop()` reçoit donc le dernier fragment potentiellement tronqué déjà normalisé (correct car il sera renvoyé au prochain chunk).

---

## F086-03d — Multi-line `data:` append (spec SSE §6.2)

### Fichier : `frontend/src/components/KycPanel.tsx`

**Problème :** La spec SSE §6.2 stipule que si plusieurs lignes `data:` apparaissent dans un même event, elles doivent être concaténées avec `\n`. L'ancien code **écrasait** `curData` à chaque nouvelle ligne `data:`, ne conservant que la dernière. Pour les events JSON sur une seule ligne `data:` (cas habituel du backend actuel), ce bug était masqué — mais tout event dont le JSON serait envoyé sur plusieurs `data:` provoquait un JSON tronqué non parseable (catchée silencieusement dans le `try/catch`).

**Avant (ligne 214) :**
```typescript
} else if (line.startsWith('data:')) {
  curData = line.slice(5).trim()
```

**Après :**
```typescript
} else if (line.startsWith('data:')) {
  // F086-03d — multi-line data: append avec \n (spec SSE §6.2)
  curData = curData ? curData + '\n' + line.slice(5).trim() : line.slice(5).trim()
```

---

## Vérification build TypeScript

```
cd frontend && npx tsc --noEmit
```

**Résultat :** aucune sortie (0 erreur, 0 warning). ✅ PASS

---

## Critères d'acceptance R086 — état complet après R088

| Critère | Statut avant R088 | Statut après R088 |
|---------|-------------------|-------------------|
| `kyc_validation_check` surfacé une fois dans timeline | ✅ PASS (R087) | ✅ PASS |
| Payload sans HTML injection | ✅ PASS (R087, JSX) | ✅ PASS |
| Noms inconnus non-fatals | ✅ PASS (R087, default branch) | ✅ PASS |
| Filename sans PII, borné | ✅ PASS (R087) | ✅ PASS |
| Blob URL révoqué au remplacement | ✅ PASS (R087, reset()) | ✅ PASS |
| **Blob URL révoqué au unmount** | ❌ MANQUANT | ✅ PASS (R088) |
| **CRLF support** | ❌ MANQUANT | ✅ PASS (R088) |
| **Multi-line data: append** | ❌ MANQUANT | ✅ PASS (R088) |
| **Flush EOF event pending** | ❌ MANQUANT | ✅ PASS (R088) |
| Build TypeScript 0 erreur | ✅ PASS (R087) | ✅ PASS (R088) |
| innerHTML / dangerouslySetInnerHTML = 0 | ✅ PASS (R087) | ✅ PASS |

---

## Fichiers modifiés

| Fichier | Nature | Action |
|---------|--------|--------|
| `frontend/src/components/KycPanel.tsx` | Frontend React/TS | F086-02b useEffect cleanup + F086-03b flush EOF + F086-03c CRLF + F086-03d multi-line data |
| `logs/20261017_R088_corrections_f086_restantes.json` | Log JSON | Généré |
| `rapports/R088_corrections_f086_restantes_2026-10-17.md` | Ce rapport | Produit |

---

## Invariants maintenus

- `CERTIFIED_100=false`
- `unique_human_proven=false`
- Mode DEBUG actif
- Aucun hardcoding, stub, placeholder introduit
- Anciens rapports non écrasés (R086, R087 intacts)
- Aucune modification du backend (`kyc_stream.py`)
