# Procedència i llicència de les dades

El codi del projecte està sota **AGPL-3.0** (vegeu `/LICENSE`), però els fitxers `web/data/*.json` són un derivat tècnic d'una font externa amb llicència pròpia.

---

## Nomenclàtor de 1860

- **Font primària**: *Nomenclátor que comprende las poblaciones, grupos, edificios, viviendas, albergues, etc., de las cuarenta y nueve provincias de España*, Junta General de Estadística del Reino, Madrid (publicat 1863-1871, Imprenta de José María Ortiz). 5 volums totals.
- **Digitalització de referència**: [Biblioteca Nacional de España, BDH](http://bdh.bne.es/bnesearch/detalle/bdh0000167814) (signatura 2/45404 V.1 - 2/45408 V.5). PDFs CC-BY 4.0:
  - [Volum 1](https://bnedigital.bne.es/bd/es/viewer?id=a98dc0b2-620e-436f-ab9b-ed039ee3754c)
  - [Volum 2](https://bnedigital.bne.es/bd/es/viewer?id=32e3d5d6-2b1a-4aec-a30e-94c7b250b9d6)
  - [Volum 3](https://bnedigital.bne.es/bd/es/viewer?id=bdc937a9-670d-4990-a06e-572c91b6d15b)
  - [Volum 4](https://bnedigital.bne.es/bd/es/viewer?id=adfdc195-0261-4907-a632-643804d0a4ce)
  - [Volum 5](https://bnedigital.bne.es/bd/es/viewer?id=57cd9a43-ac47-4376-a728-9a751cc9ea54)
- **Forma d'ingesta**: PDF facsímil de la província de Balears (51 pàgines extretes de l'obra completa), extracció pàgina a pàgina amb Claude Vision (Anthropic) i validació contra els subtotals impresos.
- **Validació**: les pàgines 3-5 i 6-8 estan transcrites a mà (`data/pages_3_5.py`, `data/pages_6_8.py`) i serveixen com a *ground truth* per mesurar la qualitat de l'extracció automàtica.
- **Estat legal**: **domini públic** per antiguitat (l'obra té més de 160 anys). Tant l'INE com la BNE en serveixen còpies sota llicències permissives (la BNE explícitament com a CC-BY 4.0).
- **Atribució recomanada**: «*Nomenclátor de 1860*, Junta General de Estadística del Reino (digitalització: Biblioteca Nacional de España, CC-BY 4.0)».
