# R009 — Périmètre retenu, frontière Rust/Python, espace SPECIal et exigences de compatibilité

**Date :** 2026-10-09  
**Dépôt de ce rapport :** `vgactech/ARTCB-TERMINATOR`  
**Emplacement d’écriture autorisé :** `rapports/` uniquement  
**Référence historique consultée en lecture seule :** `vgactech/artcb`, révision `7304d493018995d851ed5c13107c5e9d5bd79268`  
**Statut :** décisions de cadrage reçues ; inventaire fonctionnel complet, tests et validation matérielle non exécutés.  
**Autorité de passage à l’implémentation :** exclusivement l’utilisateur, après examen et approbation explicite.

## Expertises mobilisées

- Gouvernance de migration et traçabilité Git ;
- inventaire fonctionnel et tests de caractérisation ;
- architecture Rust/Python et conception de frontières inter-langages ;
- compatibilité de protocoles, API, données persistées et événements ;
- cybersécurité, hygiène des journaux et prévention des fuites de secrets ;
- TPM, attestation matérielle, stockage amovible et préparation de tests matériels ;
- reproductibilité des validations et gouvernance de certification.

## 1. Décisions de cadrage enregistrées

Les réponses de l’utilisateur établissent les décisions suivantes. Elles deviennent les contraintes de travail du plan de migration, mais ne constituent pas encore une preuve d’implémentation ni de conformité.

1. **Périmètre fonctionnel :** uniquement les capacités ARTCB retenues. Ne pas élargir la migration à tout le dépôt par défaut ; établir l’inventaire pour identifier précisément les capacités retenues et leurs dépendances.
2. **Environnement de test :** un espace isolé nommé exactement `SPECIal`, demandé pour les essais de la version ARTCB, contenant une copie de travail de la référence existante.
3. **Répartition des langages :** Rust pour le backend ; Python uniquement pour les composants côté LLM dont le fonctionnement dépend réellement de Python ou de son écosystème. Le maintien d’un module en Python doit être justifié composant par composant.
4. **Matériel :** une clé USB déjà connectée au PC local est destinée à l’usage matériel de test et l’utilisateur souhaite la formater pour cet usage exclusif.
5. **Compatibilité :** conserver la compatibilité des API, des données persistées, des versions de protocole et des formats existants. Les journaux de développement suivant le protocole ARTCB doivent être conservés dans l’espace de travail ARTCB prévu, sans être publiés ni copiés dans d’autres projets.
6. **Niveau de validation :** appliquer le critère de rigueur maximal déjà exigé par ARTCB. Les preuves, exclusions et limites doivent être explicites ; ne pas transformer un test réussi en déclaration générale de certification.
7. **Autorisation :** seul l’utilisateur peut autoriser le passage de la documentation à l’implémentation. Aucun agent ne doit déduire cette autorisation d’un rapport, d’une préparation terminée ou d’un résultat de test.

## 2. Frontière entre les dépôts et l’espace SPECIal

### Processus prévu

- `vgactech/artcb` reste la référence historique en lecture seule.
- Les tests qui nécessitent d’écrire, de générer des fichiers ou de modifier un état doivent s’exécuter dans une copie de travail isolée et jetable, appelée `SPECIal`, séparée du dépôt de référence et de tout environnement de production.
- `vgactech/ARTCB-TERMINATOR` reçoit, à ce stade, uniquement les rapports dans `rapports/`.
- Les journaux bruts, traces, captures, dumps, états de test et artefacts potentiellement sensibles sont conservés localement dans l’espace de test protégé ; ils ne sont pas commités, poussés, attachés à une issue publique ni transférés dans un dépôt tiers.
- Les rapports versionnés ne contiennent que les résumés nécessaires à l’audit : statut, versions, commandes, empreintes non sensibles, compteurs, écarts et références aux preuves conservées localement. Ils ne reproduisent pas les secrets ni les journaux bruts.

### Point de sécurité important

Le nom `SPECIal` désigne ici un espace de travail de test local, pas une permission de modifier le dépôt historique distant. Comme la règle existante interdit toute modification de `vgactech/artcb`, le dossier doit être créé dans une copie locale isolée de ce dépôt ou dans un répertoire de validation distinct ; il ne doit pas être ajouté ni poussé dans le dépôt historique sans une autorisation explicite distincte. Le dépôt cible `ARTCB-TERMINATOR` reste limité à `rapports/` tant que l’utilisateur n’a pas autorisé l’implémentation.

### Risque et correction

**Risque :** des journaux ou données de test peuvent contenir des identifiants, des chemins locaux, des données personnelles, des valeurs de challenge, des métadonnées d’équipement ou des secrets. Un simple changement de nom de dossier ne protège pas contre un commit accidentel.

**Mesures :** garder l’espace hors de l’index Git ; contrôler `git status` avant toute opération ; ajouter une exclusion locale non versionnée ou une règle d’exclusion adaptée dans la copie isolée ; vérifier le diff et la liste des fichiers avant chaque commit ; ne jamais pousser les logs bruts. Ces mesures doivent être testées avant de commencer une campagne de validation. Aucun de ces contrôles n’est déclaré exécuté par le présent rapport.

## 3. Répartition Rust/Python proposée conformément à la décision

### Backend Rust

Par défaut, les capacités backend retenues doivent être conçues pour Rust, sous réserve de l’inventaire et des contrats de compatibilité. Cela inclut les responsabilités backend qui n’ont pas de dépendance démontrée à l’exécution Python : logique métier, validation des entrées, règles d’état, gestion des erreurs, persistance, protocoles, orchestration backend et fonctions de sécurité qui relèvent du serveur.

Il ne faut cependant pas assigner un composant à Rust uniquement sur la base de son chemin de fichier. La décision doit prendre en compte les appels entrants et sortants, les dépendances natives, les formats échangés, les effets de bord et le comportement observé.

### Python réservé au côté LLM

Un composant ne reste en Python que si l’inventaire prouve qu’il dépend d’un écosystème ou d’une capacité Python indispensable au fonctionnement LLM et qu’un remplacement compatible en Rust n’est pas raisonnablement disponible ou ne répond pas aux exigences retenues.

Pour chaque composant Python conservé, consigner :
- la capacité LLM exacte et la dépendance qui impose Python ;
- la version et la licence des dépendances ;
- les données envoyées au composant et les données retournées ;
- le schéma d’échange versionné, les erreurs et les délais d’expiration ;
- les règles de confidentialité, de journalisation et de gestion des secrets ;
- les tests de contrat et de non-régression ;
- le plan de remplacement si la dépendance cesse d’être nécessaire.

### Frontière inter-langages

La communication Rust ↔ Python doit avoir un contrat explicite et versionné. Il faut comparer les formats de messages, encodages, nombres, dates, champs optionnels, erreurs et délais d’attente. Aucun secret ne doit être inclus dans les journaux par défaut. Le backend Rust doit traiter le service LLM Python comme une frontière de confiance distincte et valider ses sorties avant de les utiliser.

**Décision à ne pas prendre prématurément :** ne pas choisir une bibliothèque IPC, RPC ou un binding natif avant de connaître les contraintes réelles de latence, de déploiement, de concurrence, d’isolation et de compatibilité. Ce choix relève de la conception détaillée après inventaire.

## 4. Compatibilité : exigence de non-régression

L’expression « tout doit rester compatible » est retenue comme exigence directrice. Pour la rendre vérifiable, l’inventaire doit repérer, au minimum :

- API publiques et internes consommées par d’autres composants ;
- structures de requête et de réponse, noms de champs, valeurs par défaut et codes d’erreur ;
- protocoles réseau et versions annoncées ;
- formats de logs et d’événements ARTCB, sans confondre logs de diagnostic et messages normatifs du protocole ;
- schémas de données persistées, clés, identifiants, index et règles de migration ;
- formats cryptographiques, sérialisation, canonicalisation, empreintes, signatures et règles de vérification ;
- comportements d’idempotence, ordre des événements, reprise après panne et traitement des doublons ;
- compatibilité des versions anciennes et nouvelles, stratégie de déploiement et retour arrière.

Pour chaque élément, enregistrer la source de vérité, la version, un exemple de référence assaini, le test de caractérisation, le test de compatibilité et le critère d’acceptation. Les changements incompatibles ne sont pas présumés autorisés : ils nécessitent une décision explicite et une stratégie de versionnage, de migration et de retour arrière approuvée par l’utilisateur.

## 5. USB et TPM : vérification préalable obligatoire

### Distinction technique

Une clé USB de stockage n’est pas automatiquement un TPM. Le TPM est un composant de sécurité qui fournit des fonctions cryptographiques et des mécanismes d’attestation ; une clé USB ordinaire ne devient pas un TPM parce qu’elle est formatée. Certains équipements USB peuvent être des authentificateurs matériels ou des dispositifs cryptographiques dédiés, mais leur nature doit être identifiée à partir du modèle et de la documentation du fabricant.

Les rapports historiques de référence consultés décrivent une liaison TPM et une mesure PCR, mais précisent également que l’attestation distante complète par challenge/response n’est pas implémentée dans l’état documenté. Ils déclarent `CERTIFIED_100=false`. Ces déclarations historiques sont des indices à revérifier dans l’environnement de test, pas une certification indépendante. Voir :
- [Spécification ARTCB Hardware Identity v2](https://github.com/vgactech/artcb/blob/7304d493018995d851ed5c13107c5e9d5bd79268/docs/ARTCB_HARDWARE_IDENTITY_V2.md)
- [Rapport historique R462 — Quote TPM PCR](https://github.com/vgactech/artcb/blob/7304d493018995d851ed5c13107c5e9d5bd79268/rapports/R462_pcr_quote_tpm_binding_v2_2026-09-25.md)

### Avant tout formatage

**Ne pas formater l’équipement avant identification certaine et confirmation de son contenu.** Le formatage est destructif : il peut effacer les données de la mauvaise unité si l’identification est erronée, et il ne confère pas de fonctions TPM à un périphérique qui n’en possède pas.

Séquence obligatoire :
1. relever marque, modèle, identifiant matériel et type exact d’équipement, sans publier de numéro de série brut ;
2. confirmer si le périphérique est un stockage USB, un authentificateur FIDO2, une clé cryptographique/HSM USB ou un autre matériel ;
3. sauvegarder toute donnée qui doit être conservée et vérifier la cible par plusieurs attributs indépendants ;
4. établir les exigences de formatage uniquement si l’équipement est bien un support de stockage et si le formatage est réellement requis ;
5. identifier séparément le TPM disponible au niveau système, son pilote, son accès et les outils d’attestation compatibles ;
6. exécuter d’abord les tests simulés, puis les tests sur matériel réel avec preuves et limites documentées.

Le présent rapport ne détecte pas le périphérique connecté au PC local, ne peut pas confirmer qu’il s’agit d’un TPM et n’a procédé à aucun formatage.

### Classes de tests matériels

- **Sans matériel réel :** validation des schémas, vecteurs cryptographiques, logique de vérification, erreurs, rejeu et tests négatifs sur données synthétiques clairement identifiées.
- **Avec TPM réel :** découverte du TPM, accès par le processus, lecture contrôlée des PCR, génération de quote, validation de signature, vérification du nonce frais et liaison au nœud.
- **Avec authentificateur USB/FIDO2 ou HSM USB :** tests propres au protocole et aux capacités exactes du dispositif ; ne pas les présenter comme des tests TPM.
- **En attente de preuve distante complète :** challenge frais du vérificateur, quote produite par le TPM, validation de la signature et des PCR, protection contre le rejeu et politique de confiance explicitée.

Un résultat synthétique ne peut pas faire passer un test matériel réel à l’état PASS. Si le matériel ou l’attestation distante n’est pas disponible, le statut doit rester `BLOCKED`, `NOT_TESTED` ou `INCONCLUSIVE`.

## 6. Critère de validation maximal

Le niveau de rigueur attendu est celui déjà exigé par ARTCB, mais chaque affirmation doit préciser le périmètre effectivement prouvé. Le dossier de validation devra réunir :
- révision source et empreintes des corpus ;
- environnement, versions d’outils et commandes exactes ;
- résultats complets conservés dans l’espace local protégé ;
- tests de caractérisation et de non-régression ;
- tests différentiels Rust/Python ;
- tests de compatibilité des données et protocoles ;
- tests adversariaux, de panne, de reprise et de confidentialité ;
- résultats matériels réels lorsqu’ils sont requis ;
- écarts connus, exclusions, risques résiduels et preuves indépendantes ;
- rapport de décision signé ou explicitement approuvé par l’utilisateur.

« Tous les tests exécutés passent » ne signifie pas automatiquement « toutes les capacités sont certifiées ». La conclusion doit être bornée aux tests, versions, matériels et menaces réellement couverts. Une certification formelle ne peut être revendiquée sans référentiel applicable et processus formel démontré.

## 7. Autorisation de l’implémentation

Le passage de la documentation à l’implémentation est réservé exclusivement à l’utilisateur. L’agent peut inventorier, analyser, proposer des contrats, concevoir les tests et rédiger des rapports dans `rapports/`; il ne peut pas s’auto-autoriser à écrire du code applicatif dans `ARTCB-TERMINATOR`.

Avant toute implémentation, présenter un dossier Go/No-Go qui montre :
1. l’inventaire des seules capacités retenues ;
2. la matrice de traçabilité complète ;
3. les résultats de baseline réellement exécutés ;
4. les contrats de compatibilité ;
5. les décisions Rust/Python justifiées ;
6. les résultats et limites des tests matériels ;
7. les risques ouverts et la stratégie de retour arrière.

Sans approbation explicite de l’utilisateur, le statut demeure **DOCUMENTATION / VALIDATION PRÉALABLE — PAS D’AUTORISATION DE CODER**.

## 8. État d’avancement et prochaines actions

| Élément | État |
|---|---|
| Périmètre limité aux capacités retenues | Décision reçue ; inventaire à réaliser |
| Backend Rust / Python uniquement pour besoins LLM | Décision reçue ; affectation détaillée à établir |
| Espace de test `SPECIal` | Spécifié ; création locale non effectuée par ce rapport |
| Protection des logs bruts | Exigence enregistrée ; contrôles techniques à tester |
| Compatibilité des API, données et protocoles | Exigence enregistrée ; baseline de compatibilité non exécutée |
| Identification de la clé USB | Non vérifiée depuis cette session |
| Formatage du périphérique | Non effectué ; interdit avant identification et confirmation |
| Tests TPM matériel réel | Non exécutés |
| Attestation distante complète | À vérifier ; le rapport historique R462 la signale comme non implémentée |
| Tests de référence et parité Rust/Python | `NOT_TESTED` |
| Autorisation de coder dans `ARTCB-TERMINATOR` | Non accordée |

### Ordre de travail recommandé

1. Inventorier la révision source figée, uniquement pour les capacités retenues.
2. Préparer l’espace `SPECIal` dans une copie isolée et vérifier l’absence de publication des journaux.
3. Identifier le périphérique USB et le TPM séparément, sans formatage à ce stade.
4. Construire la matrice de compatibilité des API, données, protocoles et événements.
5. Établir la baseline de tests et les preuves réelles.
6. Soumettre le dossier Go/No-Go à l’utilisateur.

**Aucun code applicatif n’a été ajouté ou modifié par ce rapport. Aucun log brut n’a été poussé.**
