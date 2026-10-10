# R021 — Audit critique de la démo Guardian 4 rôles après le commit 5f5cf08

## Métadonnées

| Champ | Valeur |
|---|---|
| Numéro | R021 |
| Date | 2026-10-10 |
| Dépôt | `vgactech/ARTCB-TERMINATOR` |
| Commit audité | `5f5cf08716a9ee35332a5b2b8857d671d509ef29` |
| Référence | [Commit 5f5cf08](https://github.com/vgactech/ARTCB-TERMINATOR/commit/5f5cf08716a9ee35332a5b2b8857d671d509ef29) |
| Portée | Audit en lecture seule du code et du rapport R020 ; aucun code applicatif modifié |
| Priorité | P0 compétition Track 2 — « Defenders Augmented » |

## Expertises activées

- Audit de sécurité des agents et des appels d'outils MCP ;
- ingénierie des tests Python et analyse de la couverture fonctionnelle ;
- intégrité cryptographique, provenance et chaînes de preuves ;
- conception et validation de rejeu déterministe ;
- analyse de la frontière Python/Rust et de la persistance des preuves ;
- revue de dépôt GitHub et conformité du périmètre de changement.

## 1. Résumé exécutif

Le commit audité existe et contient les quatre fichiers annoncés dans `guardian_mcp/` : `attacker_agent.py`, `defender_agent.py`, `demo_scenario.py` et `test_demo_scenario.py`. Le message du commit annonce 12 tests D4 PASS et un total de 80/80.

**Limite de vérification :** le commit confirme le code et les déclarations associées, mais les informations consultées pendant cet audit ne fournissent pas une exécution indépendante des 80 tests. Aucun workflow GitHub Actions n'a été retourné pour ce SHA. Le résultat 80/80 est donc enregistré comme résultat déclaré, pas comme résultat réexécuté et observé dans cette session.

**Verdict critique :** la démonstration constitue un scénario local utile et contient plusieurs contrôles défensifs réels, notamment un exécuteur factice et un test d'altération. Toutefois, le verdict « GO » est actuellement plus fort que ce que certains contrôles prouvent. Les tests établissent surtout un scénario Python en mémoire ; ils ne démontrent pas encore quatre agents isolés, une chaîne de hash chaînée, une preuve EvidenceId distincte liée formellement à la décision, ni un rejeu R1 par le moteur Rust.

Le livrable P0 est donc **présent dans le dépôt**, mais la preuve technique doit être présentée avec des limites explicites jusqu'à la fermeture des points ci-dessous.

## 2. Processus, problème et correction

### 2.1 Le nombre d'agents est déclaré, mais seulement deux objets agents sont instanciés

**Processus — c'est-à-dire :** `run_demo_scenario()` instancie `AttackerAgent` et `DefenderAgent`. Les identifiants de l'orchestrateur et du propagateur sont ensuite affichés dans les détails de S0 ; les rôles C et D sont regroupés dans `DefenderAgent`.

**Problème — c'est-à-dire :** le rapport annonce quatre rôles logiques, mais le code visible ne crée pas quatre instances indépendantes. Le propagateur et le défenseur sont des identités déclarées et des fonctions au sein du même objet. Cela ne rend pas la démonstration inutile, mais ne prouve pas une architecture de quatre agents isolés ou exécutant chacun leur propre cycle.

**Correction suggérée :**
1. Dans le libellé de la compétition, parler de « scénario à quatre rôles logiques simulés » tant que quatre instances distinctes ne sont pas créées.
2. Si quatre agents sont un critère de jury, instancier explicitement l'orchestrateur, l'attaquant, le propagateur et le défenseur, avec interfaces et événements de transmission propres à chacun.
3. Ajouter un test qui vérifie les quatre identités d'exécution et les transmissions entre elles, pas seulement la présence de quatre chaînes dans le rapport.

### 2.2 Le rejeu R0 vérifie des hashes d'événements, pas une chaîne chaînée

**Processus — c'est-à-dire :** `verify_chain_r0()` parcourt les événements en mémoire et compare `event.compute_hash()` au hash conservé pour chaque événement. Le test d'altération recalcule aussi le hash d'événements fournis et vérifie une divergence.

**Problème — c'est-à-dire :** ce contrôle détecte la modification d'un événement si le hash conservé n'est pas recalculé avec lui. Il ne vérifie pas, à lui seul, une relation cryptographique parent-hash/tip entre les événements, l'ordre canonique complet, l'absence de suppression/réordonnancement, ni l'authenticité d'une archive persistante. Le terme « chaîne » peut donc laisser entendre davantage que ce qui est effectivement testé.

**Correction suggérée :**
1. Nommer précisément le contrôle actuel « vérification des hashes des événements en mémoire ».
2. Pour revendiquer une chaîne de preuves, inclure et valider un lien au hash précédent, un numéro de séquence strict et un hash de tête attendu ; ajouter des tests de suppression, insertion et réordonnancement.
3. Conserver la distinction entre détection d'une altération d'un événement et vérification d'une archive complète.

### 2.3 R1 ne vérifie pas encore un EvidenceId distinct et lié à la décision

**Processus — c'est-à-dire :** `attempt_tool_call()` définit l'`evidence_id` comme le hash du dernier événement retourné par l'instrumentation si la décision est BLOCK. `verify_decisions_r1()` vérifie ensuite que le hash d'un événement BLOCK n'est pas vide.

**Problème — c'est-à-dire :** un hash d'événement non vide est une preuve d'intégrité potentielle, mais ce test ne vérifie pas un champ EvidenceId distinct dans l'événement, une référence vers un enregistrement de preuve, ni une association explicite entre cette preuve et la décision BLOCK. Le contrôle est en partie tautologique : un hash calculé pour un événement existant est normalement non vide. Le code ne démontre pas non plus que l'EvidenceId a été accepté par le moteur de rejeu Rust.

**Correction suggérée :**
1. Définir le contrat EvidenceId : format, propriétaire, événement cible et relation avec la décision.
2. Vérifier que le même EvidenceId est présent dans le résultat de blocage et dans l'enregistrement d'audit canonique.
3. Ajouter un test négatif qui supprime ou remplace l'EvidenceId sans toucher au hash de l'événement, et exiger R1 FAIL.
4. Ne présenter R1 comme une validation Rust de bout en bout qu'après appel effectif du moteur Rust et preuve d'un test d'intégration correspondant.

### 2.4 Le test d'altération prouve une divergence sur une copie, mais le résultat FAIL est attendu

**Processus — c'est-à-dire :** le scénario modifie une copie de test, puis appelle le vérificateur. Le résultat du vérificateur est FAIL lorsqu'il détecte une divergence.

**Problème — c'est-à-dire :** le mot FAIL désigne ici le résultat du rejeu altéré, qui est le comportement attendu. Le test global peut donc être PASS alors que le rejeu de la copie altérée est FAIL. Présenter les deux niveaux sans les distinguer peut troubler un jury.

**Correction suggérée :** afficher séparément « test de détection : PASS » et « rejeu de la copie altérée : FAIL attendu ». Confirmer explicitement que l'original est inchangé en comparant son hash avant et après l'expérience.

### 2.5 Le blocage avant exécution est un contrôle utile, mais son périmètre doit être précisé

**Processus — c'est-à-dire :** l'exécuteur factice incrémente un compteur lorsqu'il est appelé. Le scénario exige BLOCK et un compteur d'exécution nul pour l'appel sensible.

**Problème — c'est-à-dire :** c'est un bon test local de l'ordre « décision avant exécution » pour cet exécuteur factice. Il ne démontre pas que tous les connecteurs ou outils de production sont branchés derrière le même point de contrôle. L'appel testé est bloqué par le nom de l'outil sensible ; le rapport ne doit pas suggérer que le contenu d'injection déclenche à lui seul une analyse sémantique complète.

**Correction suggérée :** préciser que la preuve porte sur le chemin MCP simulé et le stub de test. Pour un argument de sécurité plus large, ajouter des tests d'intégration sur chaque adaptateur d'outil et une vérification indépendante que l'exécuteur n'a jamais été appelé.

### 2.6 Le scénario et les preuves restent en mémoire

**Processus — c'est-à-dire :** l'instrumentation C-07 conserve les événements dans son stockage en mémoire par défaut ; les fonctions R0/R1 examinées relisent ces événements Python.

**Problème — c'est-à-dire :** le succès du scénario ne prouve pas la persistance après redémarrage, l'écriture dans le ledger Rust, ni la reconstruction de provenance à partir d'une archive durable.

**Correction suggérée :** annoncer explicitement « preuve de démonstration en mémoire ». Garder ouverte l'intégration MCP→ledger Rust et n'annoncer une preuve durable qu'après un test qui écrit, ferme/recharge le stockage et rejoue l'archive rechargée.

### 2.7 Défaut de construction du contexte du payload

**Processus — c'est-à-dire :** le modèle du payload utilise `{{context}}` puis appelle `format(context=context)`. En Python, les doubles accolades produisent des accolades littérales.

**Problème — c'est-à-dire :** la chaîne finale contient littéralement « {context} » au lieu de la valeur passée, par exemple « process user document ». Le marqueur d'injection reste présent, donc le test de détection actuel peut réussir, mais la fixture ne représente pas correctement le contexte annoncé.

**Correction suggérée :** remplacer le placeholder par un mécanisme de formatage qui insère réellement le contexte, puis ajouter une assertion qui vérifie que le texte de contexte choisi figure dans le payload et que les accolades littérales n'y figurent pas involontairement.

## 3. Qualité et portée des tests annoncés

Le commit annonce les 12 tests D4-01 à D4-12. Leur présence dans le fichier de test est confirmée. La lecture du code montre des tests de chemin nominal, de blocage, de provenance simplifiée, de rejeu en mémoire, de copie altérée, d'exception et d'isolation entre deux instances.

Les tests ne suffisent toutefois pas, à eux seuls, à prouver :
- une exécution indépendante des 80 tests dans cette session ;
- quatre agents effectivement instanciés et isolés ;
- un adaptateur Python MCP vers ledger Rust ;
- un EvidenceId canonique et vérifié indépendamment ;
- une chaîne cryptographique chaînée et résistante à la suppression ou au réordonnancement ;
- une persistance durable des preuves.

Le nombre « 80/80 PASS » doit donc être attribué au bilan fourni/au message de commit tant que les journaux de CI ou une exécution reproductible ne sont pas examinés. Aucun journal brut n'est à ajouter au dépôt.

## 4. Tableau de priorités

| ID | Constat | Priorité | État |
|---|---|---:|---|
| R021-001 | Quatre rôles annoncés, mais seulement deux objets agents instanciés | P0 si le jury exige quatre agents réels | À corriger ou à qualifier |
| R021-002 | R0 vérifie les hashes individuels, pas une chaîne complète chaînée | P0 pour toute revendication de chaîne de preuves | À corriger ou à qualifier |
| R021-003 | R1 vérifie un hash non vide, pas un EvidenceId canonique lié à BLOCK | P0 pour la revendication BLOCK→EvidenceId | À corriger |
| R021-004 | Contexte de payload non interpolé à cause des doubles accolades | P1 | À corriger |
| R021-005 | Preuves et rejeu uniquement en mémoire dans le chemin audité | P1 pour une démonstration de persistance ; acceptable si déclaré | À qualifier / intégration ouverte |
| R021-006 | Le statut 80/80 n'a pas été réexécuté dans cet audit | P1 validation | À vérifier via CI ou exécution reproductible |
| R021-007 | Test d'altération : distinguer verdict du rejeu et verdict du test | P2 clarté de présentation | À clarifier |

## 5. Recommandation pour la compétition

**Recommandation : GO conditionnel pour une démo locale de défense simulée ; pas encore GO sans réserve pour une preuve de sécurité de bout en bout.**

Le scénario montre utilement une tentative hostile inerte, une propagation tracée, un blocage de l'outil sensible par C-07, un exécuteur factice non appelé, puis des vérifications de hashes en mémoire. Il faut décrire ces faits précisément.

Avant d'affirmer « quatre agents autonomes », « preuve durable », « chaîne de preuves complète » ou « replay Rust R1 », fermer les constats R021-001 à R021-003 et R021-005. Pour le contexte de compétition, une formulation exacte et défendable est préférable à un niveau d'assurance que le code actuel ne prouve pas.

## 6. Registre des tâches persistantes

| ID | Tâche | Priorité | Statut |
|---|---|---:|---|
| L-019-001 | Démo Guardian quatre rôles | P0 | Code présent ; audit R021 identifie des écarts de revendication/preuve |
| I-019-004 | Vérifier la présence éventuelle d'un PAT dans la configuration locale signalée par R019 | P1 sécurité | NON VÉRIFIÉE dans cette session |
| L-019-002 | Replay R2/R3 | P2 | OUVERTE |
| L-019-003 | API ARTCB OVH hors ligne | P2 | OUVERTE / dépendance externe |
| L-019-004 | Attestation TPM distante | P1 futur | OUVERTE |
| L-019-005 | Fixtures Python natives C-10 | P2 | OUVERTE |
| L-019-006 | Espace de test local SPECIal | P2 | OUVERTE |
| R021-001 à R021-007 | Correctifs/qualifications de la démo | P0–P2 | OUVERTS selon le tableau ci-dessus |

## 7. Contrôle du périmètre

- Dépôt audité : `vgactech/ARTCB-TERMINATOR`, commit `5f5cf08716a9ee35332a5b2b8857d671d509ef29`.
- Dépôt historique `vgactech/artcb` : aucune écriture.
- Code applicatif : aucune modification effectuée dans cet audit.
- Fichiers de rapport : ce rapport R021 uniquement.
- Logs bruts : aucun ajouté au dépôt.
- VLC&ARTCB : aucune intégration ou migration effectuée.
- Tests : 80/80 est un résultat annoncé dans le commit ; aucune réexécution indépendante n'est revendiquée ici.

## 8. Conclusion

Le commit marque une avancée concrète : le scénario et les tests sont désormais présents. Le prochain effort ne devrait pas chercher à augmenter artificiellement le nombre de tests, mais à renforcer l'alignement entre les affirmations du rapport et ce que les contrôles démontrent réellement : agents distincts si requis, contrat EvidenceId vérifiable, rejeu réellement chaîné, intégration Rust si revendiquée, et contexte de fixture correctement construit.

La règle d'audit demeure : **ce qui est simulé doit être annoncé comme simulé ; ce qui est en mémoire ne doit pas être appelé persistant ; et un test PASS ne doit pas être confondu avec une preuve de sécurité de bout en bout.**
