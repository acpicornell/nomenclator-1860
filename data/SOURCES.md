# Procedència i llicència de les dades

El codi del projecte està sota **AGPL-3.0** (vegeu `/LICENSE`), però el fitxer `web/data/*.parquet` és un derivat tècnic d'una font externa amb llicència pròpia.

---

## Nomenclàtor de 1860

- **Font primària**: *Nomenclátor de los pueblos de España según el Censo de 25 de diciembre de 1860*, Junta General de Estadística (predecessora de l'INE).
- **Forma d'ingesta**: PDF facsímil de l'INE, extracció pàgina a pàgina amb Claude Vision (Anthropic) i validació contra els subtotals impresos.
- **Validació**: les pàgines 3-5 i 6-8 estan transcrites a mà (`data/pages_3_5.py`, `data/pages_6_8.py`) i serveixen com a *ground truth* per mesurar la qualitat de l'extracció automàtica.
- **Estat legal**: **domini públic** per antiguitat (l'obra té més de 160 anys).
- **Atribució recomanada**: «Nomenclátor de 1860, Junta General de Estadística (digitalització INE)».
