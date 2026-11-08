"""
Projet : Tarification d'une assurance temporaire décès
Étape 4 : analyses de sensibilité et passage de la prime pure à la prime commerciale

Question : comment la prime annuelle varie-t-elle selon le sexe, l'âge, la durée et le taux technique ?
"""
import os
import pandas as pd
import matplotlib.pyplot as plt

table = pd.read_csv("data/table_mortalite_2022_2024.csv", header=[0, 1], index_col=0)
os.makedirs("resultats", exist_ok=True)
os.makedirs("graphiques", exist_ok=True)

# Contrat de référence (le même qu'à l'étape 3)
REF = {"age": 40, "duree": 10, "taux": 0.015, "capital": 100_000}


# ---------- 1. La tarification de l'étape 3, écrite comme une fonction réutilisable ----------
def prime_annuelle(sexe, age, duree, taux, capital):
    lx = table[(sexe, "lx")]
    dx = table[(sexe, "dx")]
    v = 1 / (1 + taux)
    A = sum(dx[age + k] / lx[age] * v ** (k + 1) for k in range(duree))  # A¹x:n
    a = sum(lx[age + k] / lx[age] * v ** k for k in range(duree))         # äx:n
    return capital * A / a


def ecart(f, h):
    return f"{(f / h - 1):+.0%}"


# ---------- 2. Sensibilité au sexe (contrat de référence) ----------
p_h = prime_annuelle("Hommes", **REF)
p_f = prime_annuelle("Femmes", **REF)
print("1) Sexe : 40 ans, 10 ans, 1,5 %, 100 000 €")
print(f"   Hommes {p_h:8.2f} €   Femmes {p_f:8.2f} €   écart femmes / hommes {ecart(p_f, p_h)}\n")

# ---------- 3. Sensibilité à l'âge ----------
ages = [25, 30, 35, 40, 45, 50, 55, 60]
par_age = pd.DataFrame({
    "Hommes": [prime_annuelle("Hommes", a, REF["duree"], REF["taux"], REF["capital"]) for a in ages],
    "Femmes": [prime_annuelle("Femmes", a, REF["duree"], REF["taux"], REF["capital"]) for a in ages],
}, index=pd.Index(ages, name="age"))
print("2) Âge à la souscription (10 ans, 1,5 %) : prime annuelle en €")
print(par_age.round(2).to_string(), "\n")

# ---------- 4. Sensibilité à la durée ----------
durees = [5, 10, 15, 20]
par_duree = pd.DataFrame({
    "Hommes": [prime_annuelle("Hommes", REF["age"], n, REF["taux"], REF["capital"]) for n in durees],
    "Femmes": [prime_annuelle("Femmes", REF["age"], n, REF["taux"], REF["capital"]) for n in durees],
}, index=pd.Index(durees, name="duree"))
print("3) Durée du contrat (40 ans, 1,5 %) : prime annuelle en €")
print(par_duree.round(2).to_string(), "\n")

# ---------- 5. Sensibilité au taux technique ----------
taux = [0.0, 0.01, 0.015, 0.025, 0.035]
par_taux = pd.DataFrame({
    "Hommes": [prime_annuelle("Hommes", REF["age"], REF["duree"], i, REF["capital"]) for i in taux],
}, index=pd.Index([f"{i:.1%}" for i in taux], name="taux"))
par_taux["variation vs 1,5 %"] = par_taux["Hommes"] / p_h - 1
print("4) Taux technique (homme 40 ans, 10 ans) : prime annuelle en €")
print(par_taux.to_string(formatters={"Hommes": "{:.2f}".format, "variation vs 1,5 %": "{:+.1%}".format}), "\n")

# ---------- 6. Tarif unisexe ----------
# La loi interdit de différencier le tarif selon le sexe. Hypothèse prudente retenue ici :
# tout le monde est tarifé avec la table des hommes (la plus défavorable pour un risque décès).
# En pratique, l'assureur peut aussi utiliser une table mixte selon la composition de son portefeuille.
print("5) Tarif unisexe, hypothèse prudente (table hommes pour tous) : surcoût pour une femme de 40 ans")
print(f"   Prime femme au tarif unisexe {p_h:.2f} €  au lieu de {p_f:.2f} €  soit {p_h - p_f:.2f} € de plus par an\n")

# ---------- 7. De la prime pure à la prime commerciale ----------
# Hypothèses illustratives (chaque assureur fixe les siennes) :
CHARGEMENT_PRIME = 0.15     # 15 % de la prime commerciale : acquisition (commissions) et encaissement
FRAIS_GESTION = 20.0        # 20 € par an et par contrat : gestion administrative
p_comm = (p_h + FRAIS_GESTION) / (1 - CHARGEMENT_PRIME)
print("6) Prime commerciale (homme 40 ans, 10 ans, 1,5 %)")
print(f"   Prime pure {p_h:.2f} €  + frais de gestion {FRAIS_GESTION:.0f} €  "
      f"puis chargement de {CHARGEMENT_PRIME:.0%} sur prime  =  prime commerciale {p_comm:.2f} €")
print(f"   Part du risque dans le prix payé par le client : {p_h / p_comm:.0%}")

# ---------- 8. Graphiques ----------
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
couleurs = {"Hommes": "#1b3a5c", "Femmes": "#7a2e3a"}
for sexe in ["Hommes", "Femmes"]:
    axes[0].plot(par_age.index, par_age[sexe], marker="o", label=sexe, color=couleurs[sexe])
    axes[1].plot(par_duree.index, par_duree[sexe], marker="o", label=sexe, color=couleurs[sexe])
axes[0].set_title("Prime annuelle selon l'âge (10 ans, 1,5 %)")
axes[0].set_xlabel("Âge à la souscription")
axes[1].set_title("Prime annuelle selon la durée (40 ans, 1,5 %)")
axes[1].set_xlabel("Durée du contrat (années)")
for ax in axes:
    ax.set_ylabel("Prime pure annuelle (€)")
    ax.grid(alpha=0.3)
    ax.legend()
fig.suptitle("Temporaire décès, capital 100 000 €, table Insee 2022-2024")
fig.tight_layout()
fig.savefig("graphiques/sensibilites_age_duree.png", dpi=150)

# ---------- 9. Sauvegarde ----------
par_age.to_csv("resultats/primes_par_age.csv")
par_duree.to_csv("resultats/primes_par_duree.csv")
par_taux.to_csv("resultats/primes_par_taux.csv")
print("\nGraphique : graphiques/sensibilites_age_duree.png  |  Tableaux : dossier resultats/")
