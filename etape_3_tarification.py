"""
Projet : Tarification d'une assurance temporaire décès
Étape 3 : calcul de la prime pure (unique et annuelle)

Garantie : capital C versé aux bénéficiaires si l'assuré décède avant la fin du contrat.
Hypothèses :
  - capital payé en fin d'année de décès
  - primes annuelles payées en début d'année, tant que l'assuré est en vie
  - table : Insee 2022-2024 (étape 2), taux technique i
"""
import pandas as pd

# ---------- Paramètres du contrat ----------
CAPITAL = 100_000      # capital décès en euros
AGE = 40               # âge de l'assuré à la souscription
DUREE = 10             # durée du contrat en années
TAUX = 0.015           # taux technique (hypothèse, testée à l'étape 4)
SEXE = "Femmes"

# ---------- Lecture de la table construite à l'étape 2 ----------
table = pd.read_csv("data/table_mortalite_2022_2024.csv", header=[0, 1], index_col=0)
lx = table[(SEXE, "lx")]
dx = table[(SEXE, "dx")]
v = 1 / (1 + TAUX)     # facteur d'actualisation : 1 € dans un an vaut v € aujourd'hui


# ---------- Méthode 1 : calcul direct, année par année ----------
def detail_annuel(x, n, lx, dx, v):
    lignes = []
    for k in range(n):
        kpx = lx[x + k] / lx[x]                 # proba d'être vivant au début de l'année k
        q = dx[x + k] / lx[x + k]               # proba de décéder pendant l'année k
        lignes.append({
            "annee": k + 1,
            "age": x + k,
            "proba_vivant_debut (kpx)": kpx,
            "proba_deces_annee (q)": q,
            "proba_deces_cette_annee (kpx*q)": kpx * q,
            "actualisation_deces (v^(k+1))": v ** (k + 1),
            "valeur_capital (kpx*q*v^(k+1))": kpx * q * v ** (k + 1),
            "valeur_prime (kpx*v^k)": kpx * v ** k,
        })
    return pd.DataFrame(lignes).set_index("annee")


detail = detail_annuel(AGE, DUREE, lx, dx, v)
A = detail["valeur_capital (kpx*q*v^(k+1))"].sum()   # A¹x:n  valeur actuelle de 1 € payé au décès
a = detail["valeur_prime (kpx*v^k)"].sum()           # äx:n   valeur actuelle de 1 € payé chaque année

prime_unique = CAPITAL * A
prime_annuelle = prime_unique / a                      # principe d'équivalence

# ---------- Méthode 2 : contrôle par les nombres de commutation ----------
ages = lx.index
Dx = lx * v ** ages                       # Dx = lx * v^x
Cx = dx * v ** (ages + 1)                 # Cx = dx * v^(x+1)
Mx = Cx[::-1].cumsum()[::-1]              # Mx = somme des Cx à partir de x
Nx = Dx[::-1].cumsum()[::-1]              # Nx = somme des Dx à partir de x
A_comm = (Mx[AGE] - Mx[AGE + DUREE]) / Dx[AGE]
a_comm = (Nx[AGE] - Nx[AGE + DUREE]) / Dx[AGE]

# ---------- Résultats ----------
pd.set_option("display.float_format", "{:.5f}".format)
pd.set_option("display.width", 200)
print(f"Assurance temporaire décès : {SEXE.lower()}, {AGE} ans, {DUREE} ans, "
      f"capital {CAPITAL:,} €, taux technique {TAUX:.1%}\n")
print(detail.round(5).to_string())
print(f"\nA¹x:n  (valeur actuelle de 1 € de capital décès) = {A:.6f}   contrôle commutation : {A_comm:.6f}")
print(f"äx:n   (valeur actuelle de 1 € de prime annuelle)  = {a:.6f}   contrôle commutation : {a_comm:.6f}")
print(f"\nPrime pure unique   = {prime_unique:,.2f} €")
print(f"Prime pure annuelle = {prime_annuelle:,.2f} € par an pendant {DUREE} ans (si l'assuré est en vie)")

detail.to_csv(f"resultats/detail_{SEXE.lower()}_{AGE}ans_{DUREE}ans.csv")