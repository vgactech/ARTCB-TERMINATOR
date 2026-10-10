# R026 — Contre-audit R025 : portée des preuves, fuite indirecte par exception et contrat du replay

## Métadonnées

| Champ | Valeur |
|---|---|
| Numéro | R026 |
| Date | 2026-10-10 |
| Dépôt audité | `vgactech/ARTCB-TERMINATOR`, branche `main` |
| HEAD observé | `3ecb6731e220fa3fc8ab90e0fec27715e45014d3` |
| Rapport examiné | `rapports/R025_reponse_contre_audit_r024_chemins_execution_journaux_uuid_anomalies.md` |
| Portée | Vérification statique ciblée des affirmations R025 sur les journaux, le replay et la force probante |
| Écriture applicative | Aucune |
| Dépôt historique `vgactech/artcb` | Lecture seule ; aucune écriture |
| Logs bruts | Aucun créé ni ajouté au dépôt |

## 1. Expertises activées

- Audit de code Python et cohérence documentation/implémentation
- Sécurité MCP et contrôle des appels d'outils
- Confidentialité des journaux et gestion des exceptions
- Intégrité cryptographique, hashage et chaîne d'événements
- Forensic, provenance et replay
- Qualification des preuves et limites des tests
- Audit GitHub et maîtrise du périmètre de modification

## 2. Synthèse exécutive

R025 apporte des clarifications utiles : il distingue correctement l'UUID EvidenceId d'une signature cryptographique, reconnaît que le stockage actuel est en mémoire et maintient plusieurs anomalies ouvertes.

Le contre-audit ciblé identifie toutefois trois points à traiter :

1. **P2 — Confidentialité des erreurs :** l'affirmation selon laquelle les arguments ne sont pas passés explicitement aux appels `logger.*` est exacte pour les appels inspectés, mais elle ne démontre pas que les journaux ou les réponses ne peuvent jamais divulguer des données sensibles indirectement via le texte d'une exception.
2. **P2 — Contrat documentaire du replay :** la documentation de `DefenderAgent.verify_chain_r0()` annonce une vérification du lien entre événements via `previous_event_hash`, alors que le corps actuellement visible vérifie les hashes individuels et la monotonie des séquences, sans vérifier ce lien parent-hash.
3. **P2 — Portée des preuves :** les hashes et les tests en mémoire détectent certaines mutations, mais ne suffisent pas à prouver la résistance à un attaquant capable de modifier simultanément les objets, les hashes stockés ou le registre en mémoire.

Ces points ne démontrent pas que le scénario BLOCK décrit dans R025 exécute l'outil : pour un outil présent dans `_SENSITIVE_TOOLS`, la branche BLOCK ne fait effectivement pas appel à l'exécuteur. Ils empêchent plutôt de généraliser ce constat spécifique en garantie universelle sur les journaux, le replay ou un processus compromis.

## 3. Point A — Journalisation et exceptions

### Processus

Dans `guardian_mcp/instrumentation.py`, les branches ALLOW et REDACT appellent l'exécuteur dans un bloc `try`. En cas d'exception, le code journalise le message de l'exception :

- `logger.error("Erreur outil %s : %s", tool_name, exc)`
- `logger.error("Erreur outil %s (REDACT) : %s", tool_name, exc)`

Dans la branche ALLOW, la réponse renvoyée contient également `str(exc)` dans le champ de texte. La branche REDACT, elle, renvoie le texte fixe `[REDACTED]` en cas d'exception.

### Problème

Les appels de journalisation n'incluent pas directement le dictionnaire `arguments`. Cela ne permet cependant pas de conclure que le texte journalisé ne peut jamais contenir une valeur sensible : un exécuteur ou une bibliothèque peut inclure des paramètres, un jeton, une URL avec secret ou une partie de la requête dans son message d'exception.

Même distinction pour la réponse ALLOW : `str(exc)` est renvoyé au demandeur. Ce chemin ne s'applique pas à l'appel `wallet.sign` bloqué avant exécution, mais il existe pour les outils autorisés qui échouent.

La formulation R025 « aucun appel logger ne logue les arguments en clair » est littéralement compatible avec le code inspecté. En revanche, elle ne suffit pas à prouver l'invariant plus large « aucun secret ne peut apparaître dans les journaux ou les réponses d'erreur ».

### Solution recommandée

1. Ne journaliser que le nom de l'outil, un identifiant d'événement, le type d'exception et un code d'erreur stable ; ne pas inclure par défaut `str(exc)`.
2. Pour les réponses ALLOW, retourner un message générique et un identifiant de corrélation. Conserver le détail technique dans un canal diagnostique contrôlé et assaini.
3. Ajouter des tests avec un exécuteur qui lève volontairement une exception contenant une valeur sentinelle secrète. Vérifier que cette sentinelle est absente des journaux capturés et des réponses externes.
4. Tester séparément ALLOW et REDACT ; ne pas inférer la sûreté d'un chemin à partir de la seule branche BLOCK.
5. Documenter précisément l'invariant : « les arguments ne sont pas transmis directement au logger » plutôt que « aucune donnée sensible ne peut fuiter ».

### Critère de clôture

Un test automatisé capture les journaux et réponses d'erreur de tous les chemins d'exécution, y compris les exceptions contenant une sentinelle secrète ; aucune occurrence de la sentinelle ne doit être observée. Les tests doivent échouer si le texte brut de l'exception est journalisé ou renvoyé.

**État : OUVERT — P2.** Il s'agit d'une vérification complémentaire recommandée, pas d'une preuve que le placeholder du scénario BLOCK a été divulgué.

## 4. Point B — Documentation de replay versus implémentation

### Processus

Le fichier actuel `guardian_mcp/defender_agent.py` contient dans la documentation de `verify_chain_r0()` l'affirmation que le replay vérifie notamment que deux événements consécutifs sont liés par le hash précédent. Le commentaire de classe mentionne aussi un replay R0 « chaîné ».

Le corps visible de la méthode effectue deux contrôles :

1. recalcul du hash de chaque événement et comparaison au hash conservé ;
2. vérification que `sequence_no` augmente strictement.

Le code consulté ne lit pas de champ `previous_event_hash` pour vérifier une relation entre un événement et le hash de son prédécesseur.

### Problème

Le comportement réel et la documentation ne décrivent pas le même niveau de garantie. R025 reconnaît par ailleurs que `previous_event_hash` n'est pas implémenté et maintient R023-002 ouverte. Cette réserve est correcte, mais le contrat documentaire présent dans le code devrait également être aligné afin qu'un lecteur ou un futur intégrateur ne confonde pas ordre monotone et chaîne cryptographique.

C'est-à-dire : une suite numérotée 1, 2, 3 prouve un ordre représenté en mémoire ; elle ne prouve pas que l'événement 3 référence cryptographiquement l'événement 2.

### Solution recommandée

Choisir explicitement l'une de ces deux voies :

- **Voie documentaire immédiate :** modifier uniquement les rapports et, lorsqu'une correction applicative sera autorisée, corriger la docstring pour dire que R0 vérifie les hashes individuels et la monotonie, sans parent-hash.
- **Voie d'implémentation ultérieure :** ajouter un champ parent-hash canonique, l'inclure dans le contenu hashé, vérifier chaque lien au replay et tester la détection de suppression, réordonnancement, insertion et mutation. La chaîne doit avoir une règle explicite pour le premier événement.

Le présent audit n'a modifié aucun fichier de code.

### Critère de clôture

La docstring correspond au comportement réel ; si le chaînage est ensuite implémenté, des tests négatifs démontrent que la modification d'un parent-hash, le réordonnancement et la suppression d'un événement intermédiaire sont détectés.

**État : OUVERT — P2, lié à R023-002.**

## 5. Point C — Ce que le hash en mémoire prouve réellement

### Processus

Chaque `MCPToolEvent` est sérialisé de façon canonique puis haché avec SHA-256 et un préfixe de domaine. Le sink par défaut conserve un couple `(event, event_hash)` dans la liste `_events`.

Cette construction permet de détecter une modification du contenu de l'événement lorsque le hash de référence reste inchangé.

### Problème

Le hash n'est pas une signature et le couple événement/hash se trouve dans le même espace mémoire contrôlé par le processus. Si un attaquant peut modifier l'événement et le hash de référence ensemble, ou remplacer la liste entière, le contrôle local ne fournit pas à lui seul une racine de confiance indépendante.

Cette limite est cohérente avec les réserves de R025 sur l'absence de persistance et de chaîne parent-hash. Il faut éviter de présenter « hash recalculé égal au hash stocké » comme une preuve d'authenticité ou de résistance à un administrateur/processus compromis.

### Solution recommandée

- Maintenir la formulation « détection de modification si le hash de référence reste fiable ».
- Ajouter une persistance durable avec procédure write/reload/replay, conformément à R021-005.
- Pour une résistance à la suppression, chaîner les événements et ancrer périodiquement une racine dans un domaine de confiance indépendant.
- Si l'authenticité de l'émetteur est exigée, ajouter une signature vérifiable et un modèle de gestion des clés ; ne pas attribuer cette propriété à SHA-256 seul.
- Tester les scénarios de menace séparément : mutation du contenu, mutation du hash stocké, suppression, réordonnancement, redémarrage et altération du registre de preuves.

**État : OUVERT — P2 pour le renforcement de la preuve ; la limite conceptuelle est déjà reconnue dans R025.**

## 6. État des anomalies et continuité

| ID | État retenu | Action suivante |
|---|---|---|
| R021-005 — persistance durable / write-reload-replay | OUVERT | Test de cycle de vie du stockage Rust et replay après rechargement |
| R023-001 — nom `DEMO_SECRET_PLACEHOLDER` | OUVERT P2 | Renommer la fixture lorsque la correction sera autorisée et vérifier les scanners |
| R023-002 — parent-hash | OUVERT P2 | Implémentation et tests négatifs ; corriger également la documentation du replay |
| L-019-002 — invariants R2/R3 | OUVERT P2 | Définir les invariants avant d'annoncer la couverture R2/R3 |
| R026-001 — fuite indirecte via exceptions | OUVERT P2 | Tests sentinelles sur logs et réponses d'erreur |
| R026-002 — docstring replay trop forte | OUVERT P2 | Aligner contrat et comportement réel |

Aucune anomalie antérieure n'est clôturée par le présent rapport.

## 7. Limites de cette vérification

Cette revue est une inspection statique ciblée des fichiers actuellement servis par GitHub. Elle confirme le contenu visible de `instrumentation.py` et `defender_agent.py`, mais **ne prétend pas avoir reproduit dans un environnement isolé les 30 tests PASS annoncés par R025**. Les résultats d'exécution rapportés par R025 sont donc traités comme des résultats déclarés dans ce rapport, et non comme une exécution indépendante effectuée pendant R026.

L'analyse AST, les tests D4-03/D4-11 et le comptage des appels logger doivent être considérés comme des preuves de portée limitée et reproductibles, non comme une démonstration universelle de confinement.

## 8. Contrôle de périmètre

- Seul un rapport est ajouté dans `rapports/`.
- Aucun fichier applicatif n'est modifié.
- Aucun code n'est modifié dans `vgactech/artcb`.
- Aucune migration ni intégration dans VLC&ARTCB.
- Aucun log brut n'est ajouté au dépôt.
- Les anomalies antérieures restent ouvertes.

## 9. Conclusion

R025 est une amélioration utile et prudente sur l'identification des limites de preuve. Le contre-audit ne remet pas en cause le fait que le scénario sensible ciblé est bloqué avant exécution. Il précise trois frontières qui doivent rester explicites :

- **arguments absents des paramètres de log ≠ garantie d'absence de secrets dans un message d'exception ;**
- **séquence monotone ≠ chaîne parent-hash ;**
- **hash stocké en mémoire ≠ authenticité ou résistance à la modification par un attaquant contrôlant cette mémoire.**

Priorité immédiate : ajouter des tests de fuite indirecte via exception et corriger le contrat documentaire du replay au prochain changement autorisé. La persistance durable et le parent-hash restent des chantiers distincts et ouverts.
