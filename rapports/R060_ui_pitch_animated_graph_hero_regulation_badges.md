# R060 — Audit différentiel UI : graphe animé, titre hero, badges tech & réglementaires
**Commit :** `ceb2ae4` · **Branche :** `feat/artcb-forensic-integration`
**Date :** 2025-07-24 · **Déployé :** `http://35.90.101.61/`
**Périmètre :** `frontend/src/components/PitchPage.tsx` · `frontend/src/components/AnimatedArchitectureGraph.tsx`

---

## 1. Contexte

Suite au rapport R059 (fix validation KYC Bedrock C3), trois demandes UI distinctes ont été appliquées en session :

1. Ajout d'un **graphe d'architecture animé** pleine largeur entre le hero et la section « Pourquoi »
2. Correction du **titre H1 hero** + ajout des badges technologiques **RUST** et **PYTHON**
3. Remplacement du texte plat « Réglementations couvertes » par des **badges colorés individuels**

Tous les changements sont purement frontend (React/Tailwind/SVG inline). Aucune modification du backend, des routes API, de la logique Guardian, ou des tests Python/Rust.

---

## 2. Changement 1 — AnimatedArchitectureGraph

### Fichier créé
`frontend/src/components/AnimatedArchitectureGraph.tsx` (441 lignes)

### Description
Composant SVG inline full-width, inspiré du diagramme « AI Agent Architecture » (image de référence fournie), transposé dans le contexte ARTCB TERMINATOR FORENSIC.

| Propriété | Valeur |
|---|---|
| Dimensions viewBox | `900 × 620` |
| Nœuds | 14 (12 `rect` arrondis + 2 `diamond` décisionnels) |
| Arêtes | 14 (courbes cubiques de Bézier, auto-orientées par port cardinal) |
| Arêtes pointillées | 9 (flux secondaires / décisions) |
| Arêtes solides | 5 (flux principal + Guardian) |
| Particules animées | `<animateMotion>` sur `Action→Guardian BLOCK` et `Guardian BLOCK→Preuve R0` |
| Pulse glow | Nœuds `guardian_block`, `proof`, `safety` en surbrillance SVG `<animate>` |
| Séquence d'activation | 14 nœuds activés séquentiellement (Δt=420ms), boucle infinie avec pause 2s |
| Bouton | ↺ Rejouer — relance la séquence |
| Badge LIVE | Indicateur pulsé `animate-pulse` en en-tête |
| Fond | Grille `pattern` + watermark ARTCB en opacité 2.5% |
| Style | Dark navy `#050a12`, palette existante (emerald/amber/violet/cyan/rose/sky) |

### Nœuds déclarés
`input` · `understanding` · `memory` · `reasoning` · `goal_check` · `respond_direct` · `output_direct` · `action_tool` · `planning` · `mcp` · `monitoring` · `safety` · `guardian_block` · `proof`

### Chemin critique mis en évidence
```
input → understanding → reasoning → respond_direct → action_tool
  → guardian_block (BLOCK/ALLOW) → proof (SHA-256)
```
Particules voyagent en continu sur `action_tool→guardian_block→proof` quand ces nœuds sont actifs.

### Intégration dans PitchPage
```tsx
// PitchPage.tsx — entre Hero et section Pourquoi
<AnimatedArchitectureGraph />
```

---

## 3. Changement 2 — Titre hero et badges tech

### Avant
```tsx
<h1>
  La première plateforme de{' '}
  <span className="text-emerald-300">sécurité forensique</span>{' '}
  pour agents IA dans les processus bancaires et juridiques
</h1>
```

### Après
```tsx
<div className="flex flex-wrap items-center gap-3 mb-2">
  <h1>
    Backend de{' '}
    <span className="text-emerald-300">sécurité forensique</span>{' '}
    pour agents IA dans les processus bancaires et juridiques
  </h1>
  <span class="... border-orange-400/40 bg-orange-400/10 text-orange-300 ...">RUST</span>
  <span class="... border-sky-400/40 bg-sky-400/10 text-sky-300 ...">PYTHON</span>
</div>
```

| Élément | Changement |
|---|---|
| Texte supprimé | `La première plateforme de` |
| Texte ajouté | `Backend de` |
| Badge RUST | `px-3 py-1.5 rounded-lg border border-orange-400/40 bg-orange-400/10 text-orange-300 font-mono font-bold` |
| Badge PYTHON | `px-3 py-1.5 rounded-lg border border-sky-400/40 bg-sky-400/10 text-sky-300 font-mono font-bold` |
| Layout | `flex flex-wrap` — badges sur la même ligne que le H1, retour à la ligne sur mobile |

---

## 4. Changement 3 — Badges réglementaires colorés

### Avant
```tsx
<p className="font-mono text-[10px] text-slate-400">{group.regulation}</p>
// rendu : "DORA · AMF · BCB · DSP2 · LCB-FT"  (texte plat, très petit, faible contraste)
```

### Après
Chaque réglementation est un badge `<span>` individuel avec border + bg + texte coloré, `text-xs font-bold font-mono`.

#### Carte Banques & Institutions financières
| Badge | Couleur |
|---|---|
| `DORA` | 🟡 amber |
| `AMF` | 🔵 sky |
| `BCB` | 🔵 sky |
| `DSP2` | 🟡 amber |
| `LCB-FT` | 🟣 violet |

#### Carte Cabinets juridiques & Juristes
| Badge | Couleur |
|---|---|
| `RGPD` | 🟣 violet |
| `eIDAS` | 🔵 sky |
| `NIS2` | 🟡 amber |
| `Code civil 1366` | 🟣 violet |

#### Carte Fintechs & Scale-ups
| Badge | Couleur |
|---|---|
| `AI Act 2024` | 🟡 amber |
| `ISO 27001` | 🔵 sky |
| `SOC 2` | 🟣 violet |

Label section : `text-[11px] font-bold text-white uppercase tracking-widest` (était `text-[10px] text-slate-400`).

---

## 5. Validation build & déploiement

| Étape | Résultat |
|---|---|
| `npm run build` (Vite 8.3.4) | ✅ `built in 11.03s` — 0 erreur TS, 0 warning bloquant |
| Bundle JS hash | `index-G3NWw-NO.js` (nouveau hash post-changements) |
| `scp dist/* → EC2:dist_new/` | ✅ sans erreur |
| `cp dist_new/* → /var/www/html/artcb/` + `nginx reload` | ✅ `DEPLOYED_OK` |
| Vérification marqueurs en production | `Backend de` ✅ · `DORA` ✅ · `LCB-FT` ✅ · `eIDAS` ✅ · `AI Act` ✅ · `amber-400` ✅ · `violet-400` ✅ · `RUST` ✅ · `PYTHON` ✅ · `guardian_block` ✅ · `animateMotion` ✅ |

---

## 6. Traçabilité Git

```
commit ceb2ae4
feat(ui): animated arch graph + hero title/badges + regulation badges color

Fichiers modifiés :
  frontend/src/components/AnimatedArchitectureGraph.tsx  (créé, +441 lignes)
  frontend/src/components/PitchPage.tsx                  (modifié, +49/-10 lignes)

Branche : feat/artcb-forensic-integration
```

---

## 7. Non-régressions confirmées

- Aucune modification des composants `KycPanel`, `ForensicPanel`, `ExecutionGraphOverlay`, `AgentFlow`
- Aucune modification du backend `guardian_api/`
- Aucun test Python/Rust affecté (169 tests Python, 27 tests Rust inchangés)
- L'onglet KYC Forensic reste masqué (`hidden: true`) — non modifié
- La section `AnimatedArchitectureGraph` est un ajout pur, aucune suppression de contenu existant

---

## 8. Limites de cette vérification

Les points suivants sont **déclarés** mais non certifiés par vérification navigateur indépendante :

| Affirmation | Niveau de confiance | Vérification complémentaire |
|---|---|---|
| Graphe SVG visible et animé à l'écran | Déclaré — marqueurs JS confirmés | Capture navigateur indépendante |
| `animateMotion` réellement rendu (support navigateur) | Déclaré | Test cross-browser (Chrome/Firefox/Safari) |
| Badges RUST/PYTHON alignés sur mobile 375px | Non testé | Replay.io ou DevTools responsive |
| Badges réglementaires lisibles (contraste WCAG AA) | Non mesuré | Contraste programmatique sur les nouvelles couleurs |
| Aucune régression sur le flux Guardian/KYC | Structurellement garanti | Test e2e complet recommandé |

---

## 9. Prochaines actions recommandées

1. **Vérification navigateur indépendante** — ouvrir `http://35.90.101.61/` et confirmer le rendu du graphe, des badges et du titre
2. **Test responsive mobile** — vérifier l'alignement RUST/PYTHON sur 375px
3. **Mesure contraste WCAG** — les nouveaux badges amber/sky/violet sur fond dark doivent passer 4.5:1
4. **Re-enable KYC tab** — dès validation du graphe, activer `hidden: false` pour rendre la tab KYC testable (cf. verdict R054)
5. **Push branche** — `git push origin feat/artcb-forensic-integration` pour synchroniser le dépôt distant
