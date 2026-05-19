"""
Datos transcritos del Nomenclátor 1860 — Provincia de las Baleares.
Páginas 3, 4 y 5 (Partido Judicial de Ibiza).

Convenciones:
  - El símbolo "»" del original (significa cero / nada) se almacena como 0.
  - La distancia se convierte: "9'3" -> 9.3, "9" -> 9.0, "»" (vacío) -> None.
  - Texto de "poblacion" y "su_clase" se conserva LITERAL como aparece en el PDF.
  - `destacado=True` marca entradas que aparecen en negrita (típicamente la
    cabecera o capital del Ayuntamiento).
  - Filas con `es_total_ayuntamiento=True` son los subtotales del PDF.
"""

# Esquema de cada tupla:
# (pagina, partido, ayto, hab_ayto, poblacion, clase, km,
#  h_const, h_temp, inhab, p1, p2, p3, pmas, alb, total,
#  nota_ref, es_total, destacado)

ENTRADAS = [
    # ============================================================
    # PÁGINA 3 - PARTIDO JUDICIAL DE IBIZA
    # ============================================================

    # FORMENTERA (b). (1.684 habitantes)
    (3, "Ibiza", "Formentera", 1684, "Cap de Berbería", "Torre de vigía", 9.3, 0, 0, 1, 1, 0, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "Corralizas de ganado", "Albergues", None, 0, 0, 18, 0, 0, 0, 0, 18, 18, "a", False, False),
    (3, "Ibiza", "Formentera", 1684, "Espalmadez (palmar) (El)", "Torre de vigía", 8.3, 0, 0, 1, 1, 0, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "Gavina (gaviota) (La)", "Torre de vigía", 2.2, 0, 0, 1, 1, 0, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "Molí (molino) de la Mirada", "Molino de viento", 0.4, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "Molí de la Mola", "Molino de viento", 12.1, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "Molí d'en Geroni", "Molino de viento", 0.6, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "Molí d'en Simó", "Molino de viento", 2.0, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "Molí d'en Tanet", "Molino de viento", 0.8, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "Molí d'es Platé", "Molino de viento", 2.4, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "Nuestra Señora del Pilar", "Parróquia y casa", 11.9, 1, 0, 1, 0, 2, 0, 0, 0, 2, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "Pí (pino) d'es Catalá", "Torre de vigía", 2.5, 0, 0, 1, 1, 0, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "Punta del Siglo malo", "Torre de faro", 14.2, 0, 0, 1, 1, 0, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "Punta prima", "Torre de vigía", 4.1, 0, 0, 1, 1, 0, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "San Fernando", "Parróquia y casa", 11.1, 1, 0, 1, 0, 2, 0, 0, 0, 2, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "San Francisco Javier", "Caserío", None, 18, 0, 0, 15, 3, 0, 0, 0, 18, None, False, True),
    (3, "Ibiza", "Formentera", 1684, "Venda (comarca) de la Mola", "Caserío", 8.7, 77, 0, 0, 73, 4, 0, 0, 0, 77, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "Venda d'el Cap de Berbería", "Caserío", 4.2, 70, 0, 0, 66, 4, 0, 0, 0, 70, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "Venda d'el Pí d'el Catalá", "Caserío", 2.0, 32, 0, 0, 28, 4, 0, 0, 0, 32, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "Venda de Portusalé", "Caserío", 2.4, 57, 0, 0, 53, 4, 0, 0, 0, 57, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "Venda de San Fernando", "Caserío", 2.2, 63, 1, 0, 56, 8, 0, 0, 0, 64, None, False, False),
    (3, "Ibiza", "Formentera", 1684, "TOTAL Formentera", None, None, 323, 1, 26, 303, 31, 0, 0, 18, 352, None, True, False),

    # IBIZA. (5.522 habitantes)
    (3, "Ibiza", "Ibiza", 5522, "Abourador (abrevadero) (El)", "Casa de labor", 1.1, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Alfarería (La)", "Almacen de alfarería", 1.2, 0, 0, 1, 1, 0, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Bodega (La)", "Casa de huerto", 1.7, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Botigas (tiendas) (Las)", "Casas de labor", 1.2, 0, 0, 3, 3, 0, 0, 0, 0, 3, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Ca na Comisária", "Casa de huerto", 1.8, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Ca na Gláudis", "Casa de huerto", 1.6, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Ca na Rita Escandell", "Casa de huerto", 1.2, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Ca'n Bagot", "Casa de huerto", 1.6, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Ca'n Cantó", "Casa de labor", 2.5, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Ca'n Chuméu Jáume", "Casa de labor", 2.7, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Ca'n Escandell", "Casa de labor", 3.2, 2, 0, 0, 0, 2, 0, 0, 0, 2, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Ca'n Frasquet", "Casa de labor", 1.6, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Ca'n Misas", "Casa de huerto", 2.0, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Ca'n Paláu d'abáix", "Casa de labor", 2.7, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Ca'n Paláu d'adalt", "Casa de labor", 3.1, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Ca'n Paneca", "Casa de labor", 3.2, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Ca'n Simonet", "Casa de labor", 2.8, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Ca'n Vich", "Casa de labor", 2.5, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Cañas (Las)", "Casa de huerto", 1.7, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Caseta de don Narciso", "Casas de labor", 3.3, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Ca's Mut", "Casas de labor", 3.4, 2, 0, 0, 0, 2, 0, 0, 0, 2, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Clot (hoyo) d'abáix", "Casa de huerto", 1.6, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Clot d'adalt", "Casa de huerto", 1.9, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Creuéta (La)", "Casa de huerto", 1.5, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Chozas de pastores", "Albergues", None, 0, 0, 14, 0, 0, 0, 0, 14, 14, "c", False, False),
    (3, "Ibiza", "Ibiza", 5522, "Chuvería (La)", "Casa de labor", 2.0, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Dominguets (Els)", "Casas de labor", 2.1, 2, 0, 0, 0, 2, 0, 0, 0, 2, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Fábrica (La)", "Fábrica de fideos", 2.2, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Figueretas (Las)", "Casa de labor", 2.0, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Galamonas (papadas) (Las)", "Casa de huerto", 2.2, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Gorch (lago) (El)", "Casa de huerto", 1.9, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Hort de don Andrés Damiá", "Casa de huerto", 1.2, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Hort de don Carlos Ramon", "Casa de huerto", 1.3, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Hort de don Pedro Calvet", "Casa de huerto", 1.5, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (3, "Ibiza", "Ibiza", 5522, "Hort d'el Bisbe (Obispo)", "Casa de huerto", 1.4, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),

    # ============================================================
    # PÁGINA 4 - PARTIDO DE IBIZA (cont.)
    # ============================================================

    # IBIZA (cont.)
    (4, "Ibiza", "Ibiza", 5522, "Hort d'el Corredor", "Casa de huerto", 1.2, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Hort d'els Llimoners", "Casa de huerto", 1.6, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Hort d'en Calafat", "Casa de huerto", 1.5, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Hort d'en Chim", "Casa de huerto", 1.5, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Hort d'en Gotarredona", "Casa de huerto", 1.5, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Hort d'en Tinet", "Casa de huerto", 1.6, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Ibiza", "Ciudad", None, 346, 0, 13, 215, 97, 27, 20, 0, 359, None, False, True),
    (4, "Ibiza", "Ibiza", 5522, "Marina (La)", "Arrabal", 1.4, 563, 0, 5, 157, 278, 106, 25, 2, 568, None, False, True),
    (4, "Ibiza", "Ibiza", 5522, "Molí de la Alquería", "Molino de viento", 1.4, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Molí de las Covas", "Molino de viento", 2.4, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Molí d'el Cap", "Molino de viento", 1.7, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Molí d'el Corredor", "Molino de viento", 1.3, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Molí d'en Félix", "Molino de viento", 1.3, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Molí d'en Francesquet", "Molino de viento", 1.7, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Molí d'en Muson", "Molino de viento", 1.7, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Molí d'en Pep Félix", "Casa y molino de viento", 1.4, 2, 0, 0, 0, 2, 0, 0, 0, 2, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Molí d'en António Pujol", "Molino de viento", 1.5, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Palmer (El)", "Casa de huerto", 1.6, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Polvorin (El)", "Almac. de pólvora y cpo. de guard.", 1.4, 1, 0, 1, 2, 0, 0, 0, 0, 2, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Póu sant (El)", "Casa de huerto", 1.2, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Punta (La)", "Casa de labor", 2.7, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Puiget (montecito) (El)", "Casas de labor", 2.3, 2, 0, 0, 1, 1, 0, 0, 0, 2, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Rafal (prédio rústico) (El)", "Casa de labor", 2.0, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Real (La)", "Casa de huerto", 1.7, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Respayá", "Casa de labor", 2.6, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Tanca (cercado) de na Gutiérrez", "Casa de labor", 1.6, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "Trúi (almazara) d'en Berméu", "Casa de labor", 2.4, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "Ibiza", 5522, "TOTAL Ibiza", None, None, 971, 0, 37, 393, 421, 133, 45, 16, 1008, None, True, False),

    # SAN ANTÓNIO ABAD. (4.031 habitantes)
    (4, "Ibiza", "San António Abad", 4031, "Basora", "Caserío", 16.9, 12, 0, 0, 8, 4, 0, 0, 0, 12, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Benimaimó", "Caserío", 15.5, 10, 0, 0, 4, 6, 0, 0, 0, 10, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Bouéts (Els)", "Caserío", 16.7, 9, 0, 0, 6, 3, 0, 0, 0, 9, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Buscastell", "Caserío", 13.9, 15, 0, 0, 11, 4, 0, 0, 0, 15, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Camp véi", "Caserío", 16.7, 19, 0, 0, 7, 12, 0, 0, 0, 19, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Ca'n San Gelabert", "Caserío", 13.8, 7, 0, 0, 2, 5, 0, 0, 0, 7, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Ca'n Tunis", "Caserío", 4.1, 13, 0, 0, 4, 9, 0, 0, 0, 13, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Ca's Arabins", "Caserío", 11.1, 7, 0, 0, 4, 3, 0, 0, 0, 7, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Ca's Hereva (heredera)", "Caserío", 11.2, 8, 0, 0, 2, 6, 0, 0, 0, 8, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Ca's Jáis (ancianos)", "Caserío", 4.1, 6, 0, 0, 2, 4, 0, 0, 0, 6, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Coll (puerto) (El)", "Caserío", 13.9, 6, 0, 0, 1, 5, 0, 0, 0, 6, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Corona", "Caserío", 13.8, 15, 0, 0, 4, 11, 0, 0, 0, 15, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Forca (La)", "Caserío", 13.0, 18, 0, 0, 7, 11, 0, 0, 0, 18, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Isla Conejera", "Torre de faro", 5.5, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Púig blanch", "Caserío", 16.9, 5, 0, 0, 4, 1, 0, 0, 0, 5, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Púig de Planells", "Caserío", 15.3, 9, 0, 0, 6, 3, 0, 0, 0, 9, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Punta de la Font", "Molino de viento", 0.6, 0, 0, 1, 1, 0, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Rolas (novales) (Las)", "Caserío", None, 15, 0, 0, 7, 8, 0, 0, 0, 15, "a", False, False),
    (4, "Ibiza", "San António Abad", 4031, "San António Abad", "Villa", None, 83, 0, 10, 34, 59, 0, 0, 0, 93, None, False, True),
    (4, "Ibiza", "San António Abad", 4031, "San Matéo", "Parróquia y casa", 11.1, 1, 0, 1, 0, 2, 0, 0, 0, 2, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Sanoguera", "Caserío", 8.3, 16, 0, 0, 5, 11, 0, 0, 0, 16, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "San Rafael", "Parróquia y casa", 7.4, 1, 0, 1, 1, 1, 0, 0, 0, 2, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Santa Inés", "Parróquia y casa", 6.8, 1, 0, 1, 1, 1, 0, 0, 0, 2, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Venda de Aubarca", "Caserío", 5.3, 103, 0, 0, 60, 43, 0, 0, 0, 103, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Venda de la Casa roja", "Caserío", 3.7, 61, 0, 0, 39, 22, 0, 0, 0, 61, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Venda de la Corona", "Caserío", 3.3, 93, 0, 0, 61, 32, 0, 0, 0, 93, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Venda de la Forca", "Caserío", 7.9, 18, 0, 0, 4, 14, 0, 0, 0, 18, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Venda d'el Plá de Vila", "Caserío", 11.7, 30, 0, 0, 12, 18, 0, 0, 0, 30, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "Venda de Pormany", "Caserío", 6.9, 151, 0, 8, 71, 80, 0, 0, 8, 159, None, False, False),
    (4, "Ibiza", "San António Abad", 4031, "TOTAL San António Abad", None, None, 733, 0, 22, 369, 378, 0, 0, 8, 755, None, True, False),

    # SAN JOSÉ. (3.653 habitantes) - inicio
    (4, "Ibiza", "San José", 3653, "Casa de la Villa", "Casa consistorial", None, 0, 0, 1, 1, 0, 0, 0, 0, 1, None, False, True),
    (4, "Ibiza", "San José", 3653, "Cubells (tinas) (Els)", "Ermita y casa", 6.7, 1, 0, 1, 1, 1, 0, 0, 0, 2, None, False, False),
    (4, "Ibiza", "San José", 3653, "Fábrica (La)", "Fábrica de productos químicos", 9.1, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "San José", 3653, "Isla d'els Penjats (ahorcados)", "Torre de faro", 16.7, 0, 0, 1, 0, 1, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "San José", 3653, "Molí de la Punta", "Molino de viento", 7.1, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "San José", 3653, "Molí de las Covas", "Molino de viento", 7.2, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "San José", 3653, "Molí de las Salinas", "Molino de viento", 15.3, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (4, "Ibiza", "San José", 3653, "San Agustin", "Caserío", 2.7, 7, 0, 1, 1, 7, 0, 0, 0, 8, None, False, False),
    (4, "Ibiza", "San José", 3653, "San Francisco", "Parróquia y casa", 6.1, 1, 0, 1, 1, 1, 0, 0, 0, 2, None, False, False),
    (4, "Ibiza", "San José", 3653, "San Jorge", "Parróquia y casa", 15.3, 1, 0, 1, 1, 1, 0, 0, 0, 2, None, False, False),

    # ============================================================
    # PÁGINA 5 - PARTIDO DE IBIZA (cont.)
    # ============================================================

    # SAN JOSÉ (cont.)
    (5, "Ibiza", "San José", 3653, "San José", "Parróquia y casa", 0.1, 1, 0, 1, 1, 1, 0, 0, 0, 2, "a", False, False),
    (5, "Ibiza", "San José", 3653, "Torre de Rovira", "Torre de vigía", 11.1, 0, 0, 1, 0, 1, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "San José", 3653, "Torre de las Portas", "Torre de vigía", 6.8, 0, 0, 1, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "San José", 3653, "Torre d'es Carregador", "Torre de vigía", 5.7, 0, 0, 1, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "San José", 3653, "Torre d'es Sibinar", "Torre de vigía", 3.9, 0, 0, 1, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "San José", 3653, "Venda de Binamusa", "Caserío", 5.5, 57, 0, 0, 32, 25, 0, 0, 0, 57, None, False, False),
    (5, "Ibiza", "San José", 3653, "Venda de ca's Costas", "Caserío", 6.2, 68, 0, 0, 53, 15, 0, 0, 0, 68, None, False, False),
    (5, "Ibiza", "San José", 3653, "Venda de ca's Marins", "Caserío", 2.7, 75, 0, 34, 58, 17, 0, 0, 34, 109, None, False, False),
    (5, "Ibiza", "San José", 3653, "Venda de ca's Serras", "Caserío", 2.5, 60, 0, 0, 28, 32, 0, 0, 0, 60, None, False, False),
    (5, "Ibiza", "San José", 3653, "Venda de la Alquería", "Caserío", 4.7, 70, 0, 48, 31, 39, 0, 0, 48, 118, None, False, False),
    (5, "Ibiza", "San José", 3653, "Venda d'el Horta", "Caserío", 5.3, 82, 0, 0, 64, 18, 0, 0, 0, 82, None, False, False),
    (5, "Ibiza", "San José", 3653, "Venda d'el Recó", "Caserío", 6.7, 66, 0, 0, 54, 12, 0, 0, 0, 66, None, False, False),
    (5, "Ibiza", "San José", 3653, "Venda de San Francisco", "Caserío", 5.3, 59, 0, 0, 39, 20, 0, 0, 0, 59, None, False, False),
    (5, "Ibiza", "San José", 3653, "Venda de la Atalayasa", "Caserío", 4.1, 44, 0, 17, 28, 16, 0, 0, 17, 61, None, False, False),
    (5, "Ibiza", "San José", 3653, "Venda d'es Vedrá", "Caserío", 6.2, 63, 0, 0, 43, 20, 0, 0, 0, 63, None, False, False),
    (5, "Ibiza", "San José", 3653, "TOTAL San José", None, None, 659, 0, 110, 443, 227, 0, 0, 99, 769, None, True, False),

    # SAN JUAN BAUTISTA. (3.964 habitantes)
    (5, "Ibiza", "San Juan Bautista", 3964, "Molí d'en Ferrer", "Aceñas", 6.8, 2, 0, 0, 2, 0, 0, 0, 0, 2, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Molí d'en Juan Petit", "Aceña", 3.0, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Molí d'en Juan Viñas", "Aceñas", 3.3, 2, 0, 0, 2, 0, 0, 0, 0, 2, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Molí d'en Pep Lluch", "Aceña", 3.4, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Molí d'en Perdal", "Aceñas", 6.4, 2, 0, 0, 2, 0, 0, 0, 0, 2, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Molí de la Plana d'en Viñas", "Molino de viento", 7.6, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Molí d'es Blandu", "Aceña", 7.0, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "San Juan Bautista", "Caserío", None, 4, 0, 2, 1, 5, 0, 0, 0, 6, None, False, True),
    (5, "Ibiza", "San Juan Bautista", 3964, "San Lorenzo", "Parróquia y casa", 5.9, 1, 0, 1, 1, 1, 0, 0, 0, 2, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "San Miguel", "Parróquia y casa", 6.0, 1, 0, 1, 1, 1, 0, 0, 0, 2, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "San Vicente", "Parróquia y casa", 3.9, 1, 0, 1, 1, 1, 0, 0, 0, 2, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Torre de Balanzat", "Torre de vigía", 7.1, 0, 0, 1, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Torre de Purtináix", "Torre de vigía", 5.1, 0, 0, 1, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Trúis", "Almazaras", None, 0, 8, 0, 8, 0, 0, 0, 0, 8, "b", False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda de Baláfia", "Caserío", 3.9, 21, 0, 0, 15, 6, 0, 0, 0, 21, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda de Binirrás", "Caserío", 4.3, 77, 0, 1, 49, 29, 0, 0, 0, 78, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda de ca's Cavallers", "Caserío", 1.9, 22, 0, 0, 12, 10, 0, 0, 0, 22, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda de ca's Ripolls", "Caserío", 0.2, 29, 0, 0, 20, 9, 0, 0, 0, 29, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda de ca's Vidals", "Caserío", 3.5, 22, 0, 0, 8, 14, 0, 0, 0, 22, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda de Charraca", "Caserío", 2.4, 15, 0, 0, 9, 6, 0, 0, 0, 15, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda de Charracó", "Caserío", 3.0, 22, 0, 0, 12, 10, 0, 0, 0, 22, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda de la Bricha", "Caserío", 2.4, 19, 0, 23, 9, 10, 0, 0, 23, 42, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda de la Cala", "Caserío", 6.9, 103, 0, 1, 54, 50, 0, 0, 0, 104, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda de Purtináix", "Caserío", 3.8, 26, 0, 0, 14, 12, 0, 0, 0, 26, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda de Purrats", "Caserío", 4.0, 21, 0, 2, 16, 7, 0, 0, 0, 23, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda de Rubió", "Caserío", 8.7, 59, 0, 0, 46, 13, 0, 0, 0, 59, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda de Santa Lucía", "Caserío", 4.4, 27, 0, 0, 23, 4, 0, 0, 0, 27, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda de Xulata", "Caserío", 7.2, 38, 0, 0, 30, 8, 0, 0, 0, 38, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda d'es Cudulá (pedregal)", "Caserío", 6.3, 32, 0, 1, 25, 8, 0, 0, 0, 33, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda de Farvell", "Caserío", 8.0, 31, 0, 1, 23, 9, 0, 0, 0, 32, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda d'es Murtá", "Caserío", 1.3, 19, 0, 0, 10, 9, 0, 0, 0, 19, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda d'es Níu (nido) d'es Corp (cuervo)", "Caserío", 1.9, 18, 0, 0, 11, 7, 0, 0, 0, 18, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "Venda d'es Port", "Caserío", 6.8, 71, 0, 0, 54, 17, 0, 0, 0, 71, None, False, False),
    (5, "Ibiza", "San Juan Bautista", 3964, "TOTAL San Juan Bautista", None, None, 689, 8, 36, 463, 247, 0, 0, 23, 733, None, True, False),

    # SANTA EULÁLIA. (4.638 habitantes) - inicio
    (5, "Ibiza", "Santa Eulália", 4638, "Botafoch", "Torre de faro", 10.3, 0, 0, 1, 0, 1, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "Santa Eulália", 4638, "Botiga de na Benita", "Casa de labor", 6.4, 0, 0, 1, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "Santa Eulália", 4638, "Botiga d'en Arabí", "Casa de labor", 1.5, 0, 0, 1, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "Santa Eulália", 4638, "Botiga d'en Ferrer", "Casa de labor", 8.3, 0, 0, 1, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "Santa Eulália", 4638, "Botiga d'en Pera Antoni", "Casa de labor", 6.3, 0, 0, 1, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "Santa Eulália", 4638, "Jesús", "Parróquia y casa", 9.0, 0, 0, 1, 1, 0, 0, 0, 0, 2, None, False, False),
    (5, "Ibiza", "Santa Eulália", 4638, "Molí de don Edmundo", "Aceña", 0.1, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "Santa Eulália", 4638, "Molí d'en Bartoméu Lluch", "Aceña", 0.4, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "Santa Eulália", 4638, "Molí d'en Marge", "Aceña", 0.2, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "Santa Eulália", 4638, "Molí d'en Mata", "Molino de viento", 6.8, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "Santa Eulália", 4638, "Molí d'en Ribas", "Aceña", 0.6, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "Santa Eulália", 4638, "Molí d'en Talamanca", "Molino de viento", 7.8, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "Santa Eulália", 4638, "Molí d'en Valls", "Molino de viento", 8.9, 1, 0, 0, 0, 1, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "Santa Eulália", 4638, "Molí d'es Valenciá", "Molino de viento", 8.2, 1, 0, 0, 1, 0, 0, 0, 0, 1, None, False, False),
    (5, "Ibiza", "Santa Eulália", 4638, "Pont d'en Llatze", "Albergues", 7.1, 0, 0, 6, 0, 0, 0, 0, 6, 6, None, False, False),
]

NOTAS = [
    # Página 3
    (3, "a", "Estos albergues están diseminados por el término jurisdiccional; distando de la cabeza del distrito 370 metros el mas próximo, y 9.460 el mas remoto.", "Formentera"),
    (3, "b", "Formentera, que es el nombre de una de las Islas, lo es también oficial de este Ayuntamiento, pero no corresponde á entidad real y concreta de poblacion.", "Formentera"),
    (3, "c", "Estos albergues están diseminados por el término jurisdiccional; distando de la cabeza del distrito 190 metros el mas próximo, y 325 el mas remoto.", "Ibiza"),
    # Página 4
    (4, "a", "Este caserío está diseminado. Sus viviendas distan de la cabeza del distrito 11.000 metros la mas próxima, y 12.537 la mas remota.", "San António Abad"),
    # Página 5
    (5, "a", "La iglésia parroquial de San José dá nombre á esta Municipalidad; pero la cabeza de la misma se encuentra en Casa de la Villa.", "San José"),
    (5, "b", "Estas almazaras están diseminadas por el término jurisdiccional; distando de la cabeza del distrito 2.430 metros la mas próxima, y 8.900 la mas remota.", "San Juan Bautista"),
]
