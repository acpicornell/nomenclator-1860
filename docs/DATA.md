# Font, dades i llicència

Digitalització completa del *Nomenclátor de la Provincia de las Baleares*, redactat el **25 de desembre de 1860** per la Junta General d'Estadística (predecessora de l'INE) sota Alejandro Oliván. És el primer nomenclàtor espanyol amb tabulació a nivell d'edifici.

Cada poble balear declara els edificis per ús (habitats permanentment, temporals, inhabitats), per nombre de plantes, més albergs i la distància al centre del municipi. Domini públic per antiguitat.

🔗 **Demo en directe**: <https://1860.corpusbalear.org>
📂 **Codi**: <https://github.com/acpicornell/nomenclator-1860>

| Font | Període | Taules | Files |
|---|---|---|---|
| **Nomenclàtor 1860** — *Junta General de Estadística* | 25 desembre 1860 | `entries`, `notes`, `summaries`, `errata` | 3.026 entrades |

## Font primària

L'obra completa — «*Nomenclátor que comprende las poblaciones, grupos, edificios, viviendas, albergues, etc., de las cuarenta y nueve provincias de España*», editat per la Junta General de Estadística entre 1863-1871, Imprenta de José María Ortiz, Madrid — està digitalitzada per la **Biblioteca Nacional de España** (signatura 2/45404 V.1 - 2/45408 V.5, domini públic, llicència CC-BY 4.0):

- 📚 **Registre BNE**: [bdh-rd.bne.es/bdh0000167814](http://bdh.bne.es/bnesearch/detalle/bdh0000167814)
- 📄 [Volum 1 (PDF)](https://bnedigital.bne.es/bd/es/viewer?id=a98dc0b2-620e-436f-ab9b-ed039ee3754c)
- 📄 [Volum 2 (PDF)](https://bnedigital.bne.es/bd/es/viewer?id=32e3d5d6-2b1a-4aec-a30e-94c7b250b9d6)
- 📄 [Volum 3 (PDF)](https://bnedigital.bne.es/bd/es/viewer?id=bdc937a9-670d-4990-a06e-572c91b6d15b)
- 📄 [Volum 4 (PDF)](https://bnedigital.bne.es/bd/es/viewer?id=adfdc195-0261-4907-a632-643804d0a4ce)
- 📄 [Volum 5 (PDF)](https://bnedigital.bne.es/bd/es/viewer?id=57cd9a43-ac47-4376-a728-9a751cc9ea54)

Les 49 províncies de l'època apareixen disposades alfabèticament a través dels 5 volums. El PDF que digitalitzem aquí (`pdfs/Nomenclàtor 1860 balears.pdf`, no versionat — vegeu `.gitignore`) és l'extracció de les pàgines de la província de Balears.

## Schema

El schema complet és a `db/schema.sql`. Taula principal `entries`:

| Columna | Tipus | Significat |
|---|---|---|
| `judicial_district` | TEXT | Palma / Inca / Manacor / Eivissa / Maó |
| `municipality` | TEXT | Literal del PDF |
| `place` | TEXT | Població o entitat |
| `place_class`, `class_normalized` | TEXT | Caserío, Casa de labor, Molino, Iglesia… |
| `distance_km` | DOUBLE | Distància al centre del municipi |
| `inhabited_permanent`, `inhabited_seasonal`, `uninhabited` | INT | Per ús |
| `buildings_1_floor`…`buildings_over_3_floors`, `shelters` | INT | Per construcció |
| `total` | INT | Suma per fila |

La pàgina 50 del PDF (quadres-resum) es carrega a la BD però s'amaga a la pestanya d'exploració; es mostra a la pestanya *Estadístiques*.

## Comprovacions de consistència

`db/check_consistency.py` executa 8 comprovacions sobre la BD:

- Coherència interna de fila (HC+HT+Inh = P1+P2+P3+PM+Alb = total)
- Σfiles de municipi vs subtotal imprès
- Σmunis de partit vs total del partit
- Σentries vs Quadre 3 pàg. 50
- Anomalies de NULL i zeros
- Files duplicades (mateix page+muni+place)
- Estat de la fe d'errates (8 correccions verificades)
- Gaps de normalització de `class_normalized`

Estat actual: **100% coherència aritmètica interna** post-fix Ca'n Mena. Les 15 desviacions Σfiles vs subtotal imprès (Δ ∈ [-1, +3], net +11 sobre 74.107 edificis, 0,015%) **són del propi impressor del 1860**, no de la digitalització — tots els subtotals impresos s'han verificat visualment contra el facsímil i coincideixen exactament amb la BD.

## Llicència

- **Codi**: GNU **AGPL-3.0-or-later** — vegeu `LICENSE`.
- **Dades** (`web/data/*.json`): la font original (Nomenclátor de 1860) és **domini públic** per antiguitat (l'obra té més de 160 anys i és una publicació oficial de l'Estat anterior a 1880). Vegeu `data/SOURCES.md` per a l'atribució recomanada.
