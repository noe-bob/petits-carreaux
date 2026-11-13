"""Télécharge l'emploi du temps et l'écrit dans la base, si et seulement s'il a changé.

Attend dans l'environnement :
    CALENDRIER_URL   lien iCal (secret)
    CALENDRIER_L3_URL  lien iCal de la L3 de maths (secret, facultatif) :
                       seuls ses examens « + Ecole des Mines » sont gardés
    SUPABASE_URL     adresse du projet
    SUPABASE_ANON_KEY  clé publiable
    APP_COURRIEL     compte de l'application
    APP_MOTDEPASSE   son mot de passe

Se connecte comme l'utilisateur : n'accède donc qu'à ses propres données,
et jamais à l'administration du projet.
"""

import json
import os
import sys
import urllib.error
import urllib.request

from ics_vers_cours import convertir, examens_l3


def obligatoire(nom):
    v = os.environ.get(nom, "").strip()
    if not v:
        sys.exit("Secret manquant : %s" % nom)
    return v


def http(url, donnees=None, entetes=None, methode=None):
    r = urllib.request.Request(url, method=methode or ("POST" if donnees else "GET"))
    for k, v in (entetes or {}).items():
        r.add_header(k, v)
    corps = None
    if donnees is not None:
        corps = json.dumps(donnees).encode("utf-8")
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, corps, timeout=60) as rep:
            brut = rep.read().decode("utf-8", "replace")
            return rep.status, brut
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def telecharger(lien):
    demande = urllib.request.Request(lien, headers={
        "User-Agent": "petits-carreaux/1.0", "Accept": "text/calendar, */*"})
    with urllib.request.urlopen(demande, timeout=60) as rep:
        return rep.read().decode("utf-8", "replace")


def main():
    lien = obligatoire("CALENDRIER_URL")
    base = obligatoire("SUPABASE_URL").rstrip("/")
    cle = obligatoire("SUPABASE_ANON_KEY")
    courriel = obligatoire("APP_COURRIEL")
    mdp = obligatoire("APP_MOTDEPASSE")

    # 1. le calendrier
    texte = telecharger(lien)

    if "BEGIN:VEVENT" not in texte:
        sys.exit("Le lien ne renvoie pas un calendrier (page de connexion ?).")

    cours, repetitions = convertir(texte)
    if repetitions:
        sys.exit("%d evenement(s) a repetition non developpes : le format de "
                 "l'export a change, il faut adapter le convertisseur." % repetitions)
    if not cours:
        sys.exit("Aucun cours dans le calendrier.")

    print("Calendrier : %d cours, du %s au %s, %d avec une salle"
          % (len(cours), cours[0]["date"], cours[-1]["date"],
             sum(1 for c in cours if c["lieu"])))

    # 1 bis. les examens de la L3 de maths, s'il y a un lien.
    #   Le serveur de la fac peut tomber : on ne veut ni bloquer Prométhée,
    #   ni effacer les examens déjà connus. None = « reprendre ceux de la base ».
    l3 = []
    lien_l3 = os.environ.get("CALENDRIER_L3_URL", "").strip()
    if lien_l3:
        try:
            texte_l3 = telecharger(lien_l3)
            if "BEGIN:VEVENT" not in texte_l3:
                raise ValueError("pas un calendrier")
            l3 = examens_l3(texte_l3)
            print("L3 maths : %d examen(s) Ecole des Mines" % len(l3))
        except Exception as e:
            print("::warning::Calendrier L3 illisible (%s) : on garde les examens deja en base." % e)
            l3 = None

    # 2. connexion, comme l'utilisateur
    code, rep = http(base + "/auth/v1/token?grant_type=password",
                     {"email": courriel, "password": mdp}, {"apikey": cle})
    if code != 200:
        sys.exit("Connexion refusee (%d) : %s" % (code, rep[:200]))
    jeton = json.loads(rep).get("access_token")
    if not jeton:
        sys.exit("Pas de jeton dans la reponse.")

    entetes = {"apikey": cle, "Authorization": "Bearer " + jeton}

    # 3. ne rien ecrire si rien n'a bouge : cela eviterait aussi d'ecraser
    #    inutilement une version locale plus recente
    code, rep = http(base + "/rest/v1/donnees?cle=eq.cours&select=valeur", None, entetes)
    actuels = []
    if code == 200:
        lignes = json.loads(rep)
        if lignes:
            actuels = lignes[0].get("valeur", {}).get("cours") or []

    if l3 is None:
        l3 = [c for c in actuels if c.get("source") == "l3"]
    cours = sorted(cours + l3, key=lambda c: (c["date"], c["debut"] or ""))

    if code == 200:
        if actuels == cours:
            print("Identique a ce qui est deja en base : rien a ecrire.")
            return

    # 4. ecriture
    code, rep = http(
        base + "/rest/v1/donnees",
        [{"cle": "cours", "valeur": {"cours": cours}}],
        dict(entetes, **{"Prefer": "resolution=merge-duplicates,return=representation"}),
    )
    if code not in (200, 201):
        sys.exit("Ecriture refusee (%d) : %s" % (code, rep[:200]))

    print("Emploi du temps mis a jour : %s" % json.loads(rep)[0]["maj"])


if __name__ == "__main__":
    main()
