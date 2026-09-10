-- Petits Carreaux — schéma à exécuter une fois dans Supabase
-- (menu de gauche : SQL Editor → New query → coller → Run)
--
-- Une seule table. L'application raisonne par collections entières
-- (taches, idees, cours, reglages) : chacune est stockée en un document
-- JSON, exactement comme elle l'est aujourd'hui dans le navigateur.

create table if not exists donnees (
  -- rempli automatiquement par le serveur : le client n'a jamais a
  -- envoyer son identifiant, et ne peut donc pas se tromper de compte
  utilisateur uuid        not null default auth.uid()
                          references auth.users(id) on delete cascade,
  cle         text        not null,
  valeur      jsonb       not null,
  maj         timestamptz not null default now(),
  primary key (utilisateur, cle)
);

-- Sécurité au niveau des lignes : sans ceci, la clé publique de
-- l'application donnerait accès aux données de tout le monde.
alter table donnees enable row level security;

drop policy if exists "lecture de ses donnees"       on donnees;
drop policy if exists "insertion de ses donnees"     on donnees;
drop policy if exists "mise a jour de ses donnees"   on donnees;
drop policy if exists "suppression de ses donnees"   on donnees;

create policy "lecture de ses donnees" on donnees
  for select using (auth.uid() = utilisateur);

create policy "insertion de ses donnees" on donnees
  for insert with check (auth.uid() = utilisateur);

create policy "mise a jour de ses donnees" on donnees
  for update using (auth.uid() = utilisateur)
              with check (auth.uid() = utilisateur);

create policy "suppression de ses donnees" on donnees
  for delete using (auth.uid() = utilisateur);

-- Horodatage fiable, même si le client oublie de l'envoyer :
-- c'est lui qui départagera deux appareils modifiés séparément.
create or replace function touche_maj() returns trigger
  language plpgsql as $$
begin
  new.maj = now();
  return new;
end $$;

drop trigger if exists donnees_maj on donnees;
create trigger donnees_maj
  before update on donnees
  for each row execute function touche_maj();
