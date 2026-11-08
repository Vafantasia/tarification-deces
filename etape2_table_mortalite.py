"""
Projet : Tarification d'une assurance temporaire décès
Construction et contrôle de la table de mortalité (INSEE 2022-2024)

Source : Insee, Table de mortalité en données triennales, France (DEC6),
onglet "2024" = années 2022 à 2024 (résultat provisoire).
"""

import pandas as pd
import matplotlib.pyplot as plt

FICHIER = "data/6_FR_Table_mortalite_triennale.xlsx"
ONGLET = "2024"

# 1. Lecture : on saute les 5 lignes d'en-tête et on nomme les colonnes
colonnes = ["age",
            "lx_ens", "q_ens", "e_ens",
            "lx_f", "q_f", "e_f",
            "lx_h", "q_h", "e_h"]
brut = pd.read_excel(FICHIER, sheet_name=ONGLET, skiprows=5, header=None, names=colonnes)

# 2. Nettoyage : on garde seulement les lignes dont l'âge est un nombre (on enlève les notes de bas de page)
brut = brut[pd.to_numeric(brut["age"], errors="coerce").notna()].astype(float)
brut["age"] = brut["age"].astype(int)

# 3. Table de travail par sexe : lx (survivants), qx (probabilité de décès), dx (nombre de décès)
def construire_table(df, sexe):
    t = pd.DataFrame({"age": df["age"],
                      "lx": df[f"lx_{sexe}"],
                      "qx": df[f"q_{sexe}"] / 100_000})   # l'INSEE publie qx pour 100 000
    t["dx"] = t["lx"] - t["lx"].shift(-1)                # décès entre x et x+1
    return t.set_index("age")

table = {"Hommes": construire_table(brut, "h"),
         "Femmes": construire_table(brut, "f")}

# 4. Contrôles de cohérence
for sexe, t in table.items():
    qx_recalcule = t["dx"] / t["lx"]
    ecart = (qx_recalcule - t["qx"]).abs().iloc[:-1]
    print(f"{sexe} : âges 0 à {t.index.max()}, l0 = {t['lx'].iloc[0]:,.0f}, "
          f"écart max qx publié / recalculé = {ecart.max():.5f}")

# 5. Premiers indicateurs utiles pour la tarification décès
print("\nProbabilité de décéder dans les 10 ans (1 - l(x+10) / l(x))")
print(f"{'Âge':>5} {'Hommes':>9} {'Femmes':>9}")
for x in [30, 40, 50, 60]:
    ph = 1 - table["Hommes"].loc[x + 10, "lx"] / table["Hommes"].loc[x, "lx"]
    pf = 1 - table["Femmes"].loc[x + 10, "lx"] / table["Femmes"].loc[x, "lx"]
    print(f"{x:>5} {ph:>9.2%} {pf:>9.2%}")

# 6. Graphique : courbe de mortalité (échelle logarithmique)
fig, ax = plt.subplots(figsize=(8, 4.5))
for sexe, couleur in [("Hommes", "#1b3a5c"), ("Femmes", "#7a2e3a")]:
    t = table[sexe].loc[0:100]
    ax.plot(t.index, t["qx"], label=sexe, color=couleur)
ax.set_yscale("log")
ax.set_xlabel("Âge")
ax.set_ylabel("Probabilité de décès qx (échelle log)")
ax.set_title("Mortalité en France, 2022-2024 (Insee)")
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("graphiques/courbe_mortalite.png", dpi=150)
print("\nGraphique enregistré : graphiques/courbe_mortalite.png")

# 7. Sauvegarde de la table propre pour les étapes suivantes
pd.concat(table, axis=1).to_csv("data/table_mortalite_2022_2024.csv")
print("Table enregistrée : data/table_mortalite_2022_2024.csv")