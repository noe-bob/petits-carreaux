"""Convertit un calendrier iCalendar en la liste de cours attendue par l'application.

    python ics_vers_cours.py fichier.ics > cours.json

Produit {"cours": [{id, uid, titre, lieu, date, debut, duree}, ...]}, exactement
la forme que le lecteur JavaScript de l'application produit de son côté.
"""

import io
import json
import re
import sys
from datetime import datetime, timedelta, timezone

MOTIF_DATE = re.compile(r"^(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2})(\d{2})?(Z)?)?")


def deplier(texte):
    """Une ligne iCalendar peut être coupée : la suite commence par une espace."""
    lignes = texte.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out = []
    for l in lignes:
        if l[:1] in (" ", "\t") and out:
            out[-1] += l[1:]
        else:
            out.append(l)
    return out


def detexte(v):
    v = (v.replace("\\n", " ").replace("\\N", " ").replace("\\,", ",")
          .replace("\\;", ";").replace("\\\\", "\\"))
    return re.sub(r"\s+", " ", v).strip()


def dedate(valeur):
    """Renvoie (AAAA-MM-JJ, HH:MM ou None). Les heures en UTC passent en local."""
    m = MOTIF_DATE.match(valeur.strip())
    if not m:
        return None
    a, mo, j, h, mi, _s, z = m.groups()
    if not h:
        return ("%s-%s-%s" % (a, mo, j), None)
    if z == "Z":
        t = datetime(int(a), int(mo), int(j), int(h), int(mi),
                     tzinfo=timezone.utc).astimezone()
        return (t.strftime("%Y-%m-%d"), t.strftime("%H:%M"))
    return ("%s-%s-%s" % (a, mo, j), "%s:%s" % (h, mi))


def minutes(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def evenements(texte):
    """Les blocs VEVENT seulement : VTIMEZONE contient aussi des DTSTART."""
    blocs, courant, dans = [], None, False
    for ligne in deplier(texte):
        t = ligne.strip()
        if t == "BEGIN:VEVENT":
            courant, dans = {}, True
            continue
        if t == "END:VEVENT":
            if courant:
                blocs.append(courant)
            courant, dans = None, False
            continue
        if not dans or ":" not in ligne:
            continue
        gauche, valeur = ligne.split(":", 1)
        nom = gauche.split(";")[0].upper()
        courant.setdefault(nom, valeur)
    return blocs


def convertir(texte):
    cours, vus, repetitions = [], set(), 0

    for n, e in enumerate(evenements(texte)):
        if "RRULE" in e:
            repetitions += 1
            continue

        deb = dedate(e.get("DTSTART", ""))
        if not deb:
            continue
        fin = dedate(e.get("DTEND", "")) if e.get("DTEND") else None

        duree = None
        if deb[1]:
            duree = 60
            if fin and fin[1]:
                ecart = minutes(fin[1]) - minutes(deb[1])
                if fin[0] > deb[0]:
                    ecart += 1440
                if 15 <= ecart <= 1440:
                    duree = ecart

        uid = detexte(e.get("UID", "")) or ("ics%d" % n)
        ident = "%s@%s" % (uid, deb[0])
        if ident in vus:
            continue
        vus.add(ident)

        cours.append({
            "id": ident,
            "uid": uid,
            "titre": detexte(e.get("SUMMARY", "")) or "Cours",
            "lieu": detexte(e.get("LOCATION", "")),
            "date": deb[0],
            "debut": deb[1],
            "duree": duree,
        })

    cours.sort(key=lambda c: (c["date"], c["debut"] or ""))
    return cours, repetitions


def main():
    texte = io.open(sys.argv[1], encoding="utf-8", errors="replace").read()

    if "BEGIN:VCALENDAR" not in texte and "BEGIN:VEVENT" not in texte:
        sys.exit("Ce fichier n'est pas un calendrier iCalendar.")

    cours, repetitions = convertir(texte)

    if repetitions:
        # mieux vaut échouer bruyamment que perdre des cours en silence
        sys.exit("%d evenement(s) a repetition : le convertisseur ne les developpe "
                 "pas. Signale-le, le format de l'export a change." % repetitions)

    if not cours:
        sys.exit("Aucun cours trouve dans ce calendrier.")

    sys.stderr.write("%d cours, du %s au %s, %d avec une salle\n"
                     % (len(cours), cours[0]["date"], cours[-1]["date"],
                        sum(1 for c in cours if c["lieu"])))

    sys.stdout.write(json.dumps({"cours": cours}, ensure_ascii=False,
                                separators=(",", ":")))


if __name__ == "__main__":
    main()
