# R007 — Plan de validation indépendante R006 : JCS, JSON Schema 2020-12 et parité Rust/Python

**Date :** 2026-10-09  
**Dépôt cible :** `vgactech/ARTCB-TERMINATOR`  
**Périmètre d'écriture :** `rapports/` uniquement  
**Prérequis :** R006 — Schéma JSON Schema 2020-12, fixtures golden et référence Rust/Python  
**Statut :** plan d'essais et audit documentaire ; aucune exécution Rust/Python revendiquée  
**Protection du périmètre :** aucun code applicatif, fichier de configuration, dépendance, secret ou log brut ne doit être modifié ou ajouté. Le dépôt historique `vgactech/artcb` est consulté en lecture seule uniquement.

## Expertises mobilisées

- Audit de contrats de données et JSON Schema Draft 2020-12 ;
- canonicalisation JSON JCS selon RFC 8785 ;
- cryptographie appliquée, SHA-256 et séparation de domaines ;
- interopérabilité Rust/Python et tests différentiels ;
- conception de tests adversariaux et de fixtures golden ;
- intégrité de ledger, idempotence, causalité et durabilité ;
- reproductibilité, gestion de preuves et audit de chaîne d'approvisionnement logicielle.

## 1. Résumé exécutif

R006 définit un schéma, un vecteur golden F-001, des cas négatifs et un protocole de comparaison. La prochaine étape ne doit pas être une implémentation applicative : elle doit être une **validation indépendante et reproductible des références R006**, suivie d'un rapport de résultats expurgé.

R007 transforme les critères de sortie de R006 en une campagne d'essais avec des préconditions, des résultats attendus, des règles d'arrêt et des preuves à conserver. Il sépare explicitement :
1. la validité syntaxique JSON ;
2. la validation du schéma ;
3. la canonicalisation JCS ;
4. le calcul de l'empreinte ;
5. les propriétés de protocole qui nécessitent un ledger ou un graphe causal ;
6. la conformité différentielle entre Rust et Python.

**Résultat réel à ce stade : NOT_TESTED.** Le contenu du rapport est une spécification de test. Il ne prouve ni qu'une bibliothèque a été installée, ni qu'un validateur a été exécuté, ni que le digest de référence a été certifié par une implémentation JCS conforme.

## 2. Processus, problème, solution

### Processus — comment la validation doit fonctionner

Pour chaque fixture synthétique, deux parcours indépendants (Rust et Python) lisent les mêmes octets source, détectent les clés JSON dupliquées avant la construction d'un objet, valident le document en mode Draft 2020-12, canonicalisent avec une implémentation JCS conforme, puis calculent les empreintes et produisent un résultat structuré.

### Problème — ce qui peut fausser la preuve

Un résultat identique obtenu par deux sérialiseurs non conformes ne suffit pas à démontrer la conformité RFC 8785. De même, une fixture structurellement valide ne prouve ni l'existence des parents dans le ledger, ni l'idempotence transactionnelle, ni la durabilité après panne. Enfin, un statut attendu écrit dans un tableau n'est pas un résultat observé.

### Solution — règle de preuve

Chaque résultat doit être lié à un identifiant de test, à la version de l'implémentation, aux empreintes des fichiers d'entrée et à un statut explicite : PASS, FAIL, INCONCLUSIVE ou NOT_TESTED. Les sorties détaillées et journaux bruts restent hors du dépôt. Seul un résumé expurgé, sans données sensibles, peut être publié dans `rapports/`.

## 3. Audit documentaire préalable de R006

Avant d'exécuter les tests, le réviseur doit confirmer les points suivants :

1. **Corpus immuable.** Enregistrer l'empreinte SHA-256 des fixtures et du schéma effectivement testés. Toute modification après le début de la campagne crée une nouvelle version du corpus.
2. **JCS réel.** Ne pas considérer le tri récursif des clés comme une implémentation générale de RFC 8785. Utiliser une bibliothèque JCS dédiée et confronter son résultat aux vecteurs normatifs pertinents.
3. **Parseur strict.** Refuser les noms de propriétés dupliqués avant la validation et la canonicalisation. Un parseur qui garde silencieusement la dernière valeur n'est pas acceptable.
4. **Formats activés.** Vérifier que les deux validateurs activent l'assertion des formats, notamment `date-time` et `uuid`, au lieu de traiter ces contraintes comme de simples annotations.
5. **Unicode.** Vérifier que la canonicalisation n'applique pas de normalisation Unicode implicite ; les deux représentations distinctes prévues par F-003 doivent rester distinctes.
6. **Séparation des couches.** Ne pas présenter les tests de schéma comme une preuve d'idempotence, de causalité, d'authenticité, de durabilité ou de signature.
7. **Golden cryptographique.** Recalculer le corps canonique de F-001 et le digest avec une implémentation JCS conforme. Tant que ce recalcul n'est pas observé et archivé, le digest publié reste une référence candidate, non certifiée.
8. **Enveloppe et corps.** Garder la portée du hash explicitement définie : les métadonnées de ledger, la signature et les champs d'ingestion ne doivent pas être ajoutés implicitement au corps canonique.

Toute divergence documentaire doit être enregistrée avant les essais ; ne pas modifier R006 en place. Une correction doit faire l'objet d'un rapport numéroté ultérieur, dans `rapports/` seulement.

## 4. Matrice de campagne

| Campagne | Cas | Vérification | Preuve minimale | Statut initial |
|---|---|---|---|---|
| C-01 Parsing strict | JSON valide, JSON invalide, clés dupliquées | Le parseur rejette toute ambiguïté avant validation | Code résultat + chemin/position, sans contenu sensible | NOT_TESTED |
| C-02 Schéma positif | F-001 | Acceptation par les deux validateurs Draft 2020-12 | Résultat Rust et Python + versions | NOT_TESTED |
| C-03 Schéma négatif | F-010, F-014 à F-020 | Rejet des champs inconnus et contraintes invalides | Codes stables et chemins JSON | NOT_TESTED |
| C-04 Formats | date-time et UUID | Les formats sont effectivement assertés | Configuration de validation et cas de test | NOT_TESTED |
| C-05 JCS golden | F-001 | Octets canoniques égaux au vecteur de référence | Longueur, empreinte des octets, comparaison exacte | NOT_TESTED |
| C-06 Invariance d'ordre | F-002 | Réordonnancement et espaces ne changent pas les octets JCS | Comparaison byte-for-byte | NOT_TESTED |
| C-07 Unicode | F-003 | Les deux chaînes restent distinctes | Octets et digest des deux objets | NOT_TESTED |
| C-08 Hash de domaine | F-001/F-002 | Digest du préfixe + octet nul + corps JCS | Digest calculé et vecteur de référence | NOT_TESTED |
| C-09 Différentiel | Corpus commun Rust/Python | Statuts, octets et digests concordent | Résumé de comparaison automatique | NOT_TESTED |
| C-10 Protocole | F-004 à F-008, F-011 à F-013 | Idempotence, causalité, crash/reprise, politique | Rapport synthétique du banc isolé | NOT_TESTED |

## 5. Protocole d'exécution reproductible

### Étape A — figer les entrées

- Copier le schéma et les fixtures depuis la révision examinée vers un environnement temporaire isolé.
- Calculer et conserver leurs empreintes SHA-256.
- Consigner la révision GitHub, la date UTC, le système d'exploitation, les versions de Rust/Python et les versions exactes des bibliothèques.
- Ne pas inclure de secret, donnée utilisateur, mémoire privée ou journal de production dans le corpus.

### Étape B — vérifier le parsing

- Lire le document source comme des octets.
- Détecter les propriétés dupliquées au niveau du parseur.
- Refuser le document en cas de doublon ou de JSON invalide.
- Ne pas tenter de « réparer » silencieusement les données d'entrée.

### Étape C — valider le schéma

- Utiliser un validateur compatible Draft 2020-12 dans chaque langage.
- Activer explicitement l'assertion des formats.
- Tester au minimum F-001 comme positif et F-010, F-014 à F-020 comme négatifs.
- Normaliser uniquement les codes et chemins de diagnostic ; les messages humains peuvent différer.

### Étape D — canonicaliser et hacher

- Utiliser une bibliothèque conforme à RFC 8785 dans chaque langage.
- Comparer les octets canoniques, pas seulement les chaînes affichées ou les hashes.
- Vérifier la longueur attendue de F-001 et comparer les octets au golden.
- Calculer séparément le SHA-256 simple des octets canoniques pour le diagnostic.
- Calculer ensuite le hash d'événement selon le domaine documenté dans R006.
- Toute divergence entraîne FAIL et interdit de poursuivre en présentant la campagne comme réussie.

### Étape E — comparer Rust/Python

Le comparateur doit comparer au minimum :
- identifiant de fixture ;
- statut de parsing ;
- statut de schéma ;
- profil JCS ;
- longueur des octets canoniques ;
- empreinte des octets canoniques ;
- hash d'événement ;
- code d'erreur stable et chemin JSON ;
- nom et version des implémentations.

Le comparateur ne doit jamais ignorer une divergence d'octets, de digest ou de statut sous prétexte que les messages d'erreur sont différents.

### Étape F — tests de protocole, séparés

Les scénarios d'idempotence, de parents absents, de cycles, de retry après écriture durable, de mutation et de classification nécessitent un composant de ledger ou un simulateur isolé. Ils ne doivent pas être déclarés PASS sur la seule base du validateur JSON Schema.

Si aucun composant testable n'est disponible sans modifier le code du projet, conserver ces cas à NOT_TESTED et décrire précisément la précondition manquante. Ne pas créer de code applicatif ni modifier la configuration pour contourner cette limite.

## 6. Contrat minimal de résultat

Chaque exécution doit produire une fiche structurée contenant :

- `campaign_id` et `fixture_id` ;
- empreinte SHA-256 des octets source ;
- révision du schéma et profil de canonicalisation ;
- nom/version du parseur, du validateur et de la bibliothèque JCS ;
- `parse_result`, `schema_result`, `canonicalization_result`, `hash_result` ;
- `protocol_result`, ou `NOT_TESTED` si le composant correspondant n'existe pas ;
- longueur et empreinte des octets canoniques ;
- digest avec séparation de domaine ;
- codes d'erreur et chemins JSON ;
- horodatage UTC de l'exécution ;
- limites connues et raison de tout statut INCONCLUSIVE.

Aucun champ ne doit inclure un secret ou recopier une donnée classifiée dans un message d'erreur. Les résultats bruts restent dans l'environnement de test et ne sont pas committés.

## 7. Règles de décision

- **PASS** : tous les contrôles applicables ont réellement été exécutés et satisfont les références.
- **FAIL** : au moins une contrainte obligatoire échoue ou une implémentation diverge.
- **INCONCLUSIVE** : exécution réelle, mais preuve insuffisante pour conclure.
- **NOT_TESTED** : test non exécuté ou précondition absente.

Le statut global ne peut être PASS que si toutes les étapes obligatoires de la campagne correspondante sont PASS. Un test non exécuté, un résultat attendu ou une revue documentaire ne peut pas être converti en PASS.

## 8. Critères de sortie R007

- [ ] Corpus de schéma et de fixtures figé par empreinte.
- [ ] Parsing strict et rejet des clés dupliquées démontrés.
- [ ] Schéma accepté par deux validateurs indépendants Draft 2020-12.
- [ ] Assertion des formats démontrée dans les deux langages.
- [ ] F-001 canonicalisé avec une implémentation JCS conforme.
- [ ] Octets canoniques et digest de F-001 comparés au golden.
- [ ] F-002 produit les mêmes octets et digest que F-001.
- [ ] F-003 conserve la distinction Unicode attendue.
- [ ] Cas négatifs structurels rejetés avec résultats cohérents.
- [ ] Comparaison Rust/Python exécutée et examinée.
- [ ] Tests de protocole marqués séparément ; aucune inférence depuis JSON Schema.
- [ ] Résumé des résultats expurgé, reproductible et publié uniquement dans `rapports/`.
- [ ] Aucun code applicatif, configuration ou dépendance du projet modifié.
- [ ] Aucun log brut committé.
- [ ] Dépôt `vgactech/artcb` resté en lecture seule.

## 9. Risques et corrections

| Risque | Explication | Correction |
|---|---|---|
| Faux positif de canonicalisation | Deux sorties identiques ne prouvent pas à elles seules la conformité JCS | Tester des vecteurs RFC 8785 et comparer les octets exacts |
| JSON ambigu | Des clés dupliquées peuvent être masquées par le parseur | Détection avant la construction de l'objet |
| Format non asserté | Une date invalide peut passer si le format est une annotation | Activer et tester l'assertion des formats |
| Résultat attendu confondu avec observation | Le rapport peut donner une assurance non démontrée | Enregistrer statuts et preuves de chaque exécution |
| Test de protocole simulé présenté comme réel | Un validateur de schéma ne prouve pas la durabilité ou l'idempotence | Exécuter dans un banc isolé ou conserver NOT_TESTED |
| Logs sensibles dans Git | Les sorties peuvent contenir des données ou chemins internes | Garder les bruts hors dépôt et publier un résumé expurgé |

## 10. Références normatives et techniques

- RFC 8785 — JSON Canonicalization Scheme : https://www.rfc-editor.org/rfc/rfc8785.html
- RFC 9562 — UUIDs : https://www.rfc-editor.org/rfc/rfc9562.html
- JSON Schema Draft 2020-12 : https://json-schema.org/draft/2020-12
- R006 — contrat, golden et matrice de fixtures : https://github.com/vgactech/ARTCB-TERMINATOR/blob/main/rapports/R006_schema_json_schema_2020_12_fixtures_golden_reference_rust_python.md

## Conclusion

La prochaine étape est une campagne de validation indépendante, pas une modification applicative. R007 fixe comment démontrer la conformité du schéma, de JCS, du digest et de la parité Rust/Python sans confondre spécification et exécution. Tant que les preuves d'exécution ne sont pas collectées, le statut demeure **NOT_TESTED**.

**Règle finale : aucune réussite ne doit être revendiquée sans résultat reproductible, aucune divergence ne doit être masquée, et tous les changements restent confinés au dossier `rapports/` du dépôt ARTCB-TERMINATOR.**
