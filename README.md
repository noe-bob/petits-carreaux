# Petits Carreaux

**→ [noe-bob.github.io/petits-carreaux](https://noe-bob.github.io/petits-carreaux/)**

Application personnelle : tâches, agenda et carnet d'idées de vidéos.
Un seul fichier, `index.html`, sans rien à installer ni à compiler.

Sur téléphone, le menu du navigateur propose « Ajouter à l'écran d'accueil » :
l'application s'ouvre alors en plein écran, avec sa propre icône.

## Ce qu'elle fait

**Tâches** — échéances, horaires et durées, catégories colorées, priorités,
répétition quotidienne, hebdomadaire ou mensuelle, sous-tâches avec
progression, notes, recherche et réorganisation par glisser-déposer.

**Agenda** — grille mensuelle et vue semaine avec créneaux horaires ; les blocs
se déplacent à la souris. Sur téléphone, la semaine devient un jour à la fois.
Un emploi du temps au format `.ics` peut être importé : les cours apparaissent
en fond, non modifiables, et une tâche peut être rattachée à l'un d'eux.

**Ascension Maths** — un carnet d'idées de vidéos, rangées par rubrique et par
catégorie, chacune suivant un cycle en trois temps : idée brute, prête à être
tournée, tournée. Un **mode tournage** affiche le script en grand sur fond
sombre et empêche l'écran de s'éteindre pendant la prise.

## Où vivent les données

Le navigateur est la source d'affichage : l'application fonctionne **hors
ligne**, et reste utilisable si la base est injoignable.

Avec un compte, trois collections — tâches, idées, emploi du temps — sont
synchronisées entre appareils. L'arbitrage se fait au plus récent, collection
par collection. Sans compte, tout reste sur l'appareil.

Un export complet au format JSON est disponible à tout moment, avec
restauration.

## Mise en place

La base est un projet [Supabase](https://supabase.com) gratuit. Le schéma est
dans [`supabase.sql`](supabase.sql) : une table, des règles de sécurité par
ligne, un horodatage automatique. À exécuter une fois dans l'éditeur SQL.

La clé publiée dans `index.html` est une **clé publiable**, prévue pour être
exposée : elle n'ouvre rien sans connexion. Ce sont les règles de sécurité par
ligne qui protègent les données — chaque ligne n'est lisible que par son
propriétaire.

Un projet Supabase gratuit est suspendu après sept jours sans requête. La tâche
[`garder-active.yml`](.github/workflows/garder-active.yml) l'interroge chaque
matin pour l'éviter. Elle a besoin des secrets `SUPABASE_URL` et
`SUPABASE_ANON_KEY`.

## Aucune donnée personnelle ici

Le `.gitignore` fonctionne en liste blanche : seuls les fichiers du site
peuvent être publiés. Ni les tâches, ni les idées, ni l'emploi du temps, ni le
lien d'abonnement au calendrier ne se trouvent dans ce dépôt.
