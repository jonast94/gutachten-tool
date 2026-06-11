from modules.address_lookup import lookup_address
from modules.alkis_wfs import get_alkis_location_data
from modules.berlin_utils import normalize_berlin_district
from modules.district_data import get_district_data
from modules.mietspiegel_wfs import get_wohnlage_from_wfs
from modules.mss_wfs import get_mss_data_from_wfs
from modules.milieuschutz_wfs import get_milieuschutz_data
from modules.bplan_wfs import get_bplan_data
from modules.hochwasser_wfs import get_hochwasser_data
from modules.denkmalschutz_wfs import get_denkmalschutz_data
from modules.fnp_wfs import get_fnp_data
from modules.bnp_manual import get_bnp_manual_info
from modules.wohnmarktreport_lookup import get_kaufkraft_data
from modules.laerm_wms import get_laerm_data
from modules.brw_wfs import get_brw_data
from modules.export import save_result


META = {
    "bezirksdaten": {
        "source": "Lokale CSV: data/berlin_districts.csv",
        "date": "lokal hinterlegt / bitte bei Bedarf aktualisieren",
    },
    "wohnlage": {
        "source": "Berlin Open Data / Wohnlagen nach Adressen zum Berliner Mietspiegel 2024 - WFS",
        "date": "10.06.2024",
    },
    "mss": {
        "source": "Berlin Open Data / Monitoring Soziale Stadtentwicklung (MSS) 2025 - WFS",
        "date": "Datenstand 31.12.2022–31.12.2024",
    },
    "milieuschutz": {
        "source": "Berlin Open Data / Erhaltungsverordnungsgebiete § 172 BauGB - WFS",
        "date": "22.01.2026",
    },
    "bplan": {
        "source": "Berlin Open Data / Bebauungsplanverfahren in Berlin - WFS",
        "date": "03.05.2004",
    },
    "hochwasser": {
        "source": "Berlin Open Data / Überschwemmungsgebiete (Umweltatlas) - WFS",
        "date": "01.07.2018",
    },
    "denkmalschutz": {
        "source": "Berlin Open Data / Denkmale - WFS",
        "date": "06.11.2025",
    },
    "fnp": {
        "source": "Berlin Open Data / FNP (Flächennutzungsplan Berlin), Stand Neubekanntmachung 2025 - WFS",
        "date": "07.02.2025",
    },
    "bnp": {
        "source": "Berlin Open Data / Baunutzungsplan - WMS",
        "date": "30.06.1961",
    },
    "kaufkraft": {
        "source": "Lokale CSV aus Wohnmarktreport Berlin 2026 (Berlin Hyp & CBRE)",
        "date": "2026",
    },
    "laerm": {
        "source": "Berlin Open Data / Strategische Lärmkarten 2022 (Umweltatlas)",
        "date": "2022",
    },
    "brw": {
        "source": "Berlin Open Data / Bodenrichtwerte 01.01.2026 - WFS",
        "date": "01.01.2026",
    },
    "adresse": {
        "source": "Nominatim / OpenStreetMap",
        "date": "Abrufzeitpunkt",
    },
    "alkis": {
        "source": "Berlin Open Data / ALKIS Berlin Bezirke und Ortsteile - WFS",
        "date": "06.03.2026",
    },
}


def bool_to_text(value):
    if value is True:
        return "vorhanden"
    if value is False:
        return "nicht vorhanden"
    return value


def with_meta(value, source, date, unit=""):
    value = bool_to_text(value)

    if value in (None, "", "None"):
        return f"nicht hinterlegt (Quelle: {source}; Stichtag: {date})"

    return f"{value}{unit} (Quelle: {source}; Stichtag: {date})"


def main():
    print("Adressprüfung für Berliner Gutachten")
    print("-" * 40)

    street = input("Straße: ").strip()
    house_number = input("Hausnummer: ").strip()
    postal_code = input("PLZ: ").strip()

    try:
        result = lookup_address(street, house_number, postal_code)
        alkis_data = get_alkis_location_data(result["latitude"], result["longitude"])

        bezirk_clean = alkis_data["bezirk_wfs"] or normalize_berlin_district(result)
        ortsteil_clean = alkis_data["ortsteil_wfs"] or result["suburb"]

        district_data = get_district_data(bezirk_clean)
        wohnlage_data = get_wohnlage_from_wfs(result["latitude"], result["longitude"])
        mss_data = get_mss_data_from_wfs(result["latitude"], result["longitude"])
        milieuschutz_data = get_milieuschutz_data(result["latitude"], result["longitude"])
        bplan_data = get_bplan_data(result["latitude"], result["longitude"])
        hochwasser_data = get_hochwasser_data(result["latitude"], result["longitude"])
        denkmalschutz_data = get_denkmalschutz_data(result["latitude"], result["longitude"])
        fnp_data = get_fnp_data(result["latitude"], result["longitude"])
        bnp_data = get_bnp_manual_info(result["latitude"], result["longitude"])
        kaufkraft_data = get_kaufkraft_data(result["postcode"], bezirk_clean)
        laerm_data = get_laerm_data(result["latitude"], result["longitude"])
        brw_data = get_brw_data(result["latitude"], result["longitude"])

        export_data = {
            "adresse": {
                **result,
                "ortsteil_wfs": ortsteil_clean,
                "bezirk_wfs": bezirk_clean,
            },
            "alkis": alkis_data,
            "bezirk": district_data,
            "wohnlage": wohnlage_data,
            "mss": mss_data,
            "milieuschutz": milieuschutz_data,
            "bplan": bplan_data,
            "hochwasser": hochwasser_data,
            "denkmalschutz": denkmalschutz_data,
            "fnp": fnp_data,
            "bnp": bnp_data,
            "kaufkraft": kaufkraft_data,
            "laerm": laerm_data,
            "brw": brw_data,
            "meta": META,
        }

        file_path = save_result(export_data, street, house_number, postal_code)

        print("\nErgebnis")
        print("=" * 60)

        # ADRESSE & LAGE
        print("\n[ADRESSE & LAGE]")
        print("-" * 40)
        print(
            "Adresse: "
            + with_meta(
                result["standard_address_clean"],
                META["adresse"]["source"],
                META["adresse"]["date"],
            )
        )
        print(f"Straße / Nr.: {result['road']} {result['house_number']}")
        print(f"PLZ: {result['postcode']}")
        print(
            "Ortsteil des Standorts: "
            + with_meta(
                ortsteil_clean,
                META["alkis"]["source"],
                META["alkis"]["date"],
            )
        )
        print(
            "Bezirk: "
            + with_meta(
                bezirk_clean,
                META["alkis"]["source"],
                META["alkis"]["date"],
            )
        )
        print(f"Koordinaten: {result['latitude']}, {result['longitude']}")

        # GEBIET & STRUKTUR
        print("\n[GEBIET & STRUKTUR]")
        print("-" * 40)
        print(
            "Einwohner Bezirk: "
            + with_meta(
                district_data["einwohner"],
                META["bezirksdaten"]["source"],
                META["bezirksdaten"]["date"],
            )
        )
        print(
            "Fläche Bezirk: "
            + with_meta(
                district_data["flaeche_km2"],
                META["bezirksdaten"]["source"],
                META["bezirksdaten"]["date"],
                " km²",
            )
        )
        print(f"Ortsteile Bezirk: {district_data['ortsteile']}")
        print(
            "Ortsteil des Standorts: "
            + with_meta(
                ortsteil_clean,
                META["alkis"]["source"],
                META["alkis"]["date"],
            )
        )

        # PLANUNGSRECHT
        print("\n[PLANUNGSRECHT]")
        print("-" * 40)

        print(
            "FNP: "
            + with_meta(
                fnp_data["in_fnp"],
                META["fnp"]["source"],
                META["fnp"]["date"],
            )
        )
        if fnp_data["in_fnp"]:
            print(
                "  Nutzung: "
                + with_meta(
                    fnp_data["nutzungsart"],
                    META["fnp"]["source"],
                    META["fnp"]["date"],
                )
            )
            print(
                "  Zweckbestimmung: "
                + with_meta(
                    fnp_data["zweckbestimmung"],
                    META["fnp"]["source"],
                    META["fnp"]["date"],
                )
            )
            print(
                "  GISID: "
                + with_meta(
                    fnp_data["gisid"],
                    META["fnp"]["source"],
                    META["fnp"]["date"],
                )
            )

        print(
            "B-Plan: "
            + with_meta(
                bplan_data["in_bplan"],
                META["bplan"]["source"],
                META["bplan"]["date"],
            )
        )
        if bplan_data["in_bplan"]:
            print(
                "  Bezeichnung: "
                + with_meta(
                    bplan_data["bezeichnung"],
                    META["bplan"]["source"],
                    META["bplan"]["date"],
                )
            )
            print(
                "  Inhalt: "
                + with_meta(
                    bplan_data["inhalt"],
                    META["bplan"]["source"],
                    META["bplan"]["date"],
                )
            )
            print(
                "  PDF: "
                + with_meta(
                    bplan_data["scan_www"],
                    META["bplan"]["source"],
                    META["bplan"]["date"],
                )
            )

        print(
            "Baunutzungsplan: "
            + with_meta(
                bnp_data["status"],
                META["bnp"]["source"],
                META["bnp"]["date"],
            )
        )
        print(
            "  Hinweis: "
            + with_meta(
                bnp_data["hinweis"],
                META["bnp"]["source"],
                META["bnp"]["date"],
            )
        )

        print(
            "Milieuschutz/Erhaltungsverordnung: "
            + with_meta(
                milieuschutz_data["in_milieuschutz"],
                META["milieuschutz"]["source"],
                META["milieuschutz"]["date"],
            )
        )
        if milieuschutz_data["in_milieuschutz"]:
            print(
                "  Gebiet: "
                + with_meta(
                    milieuschutz_data["gebietsname"],
                    META["milieuschutz"]["source"],
                    META["milieuschutz"]["date"],
                )
            )
            print(
                "  Bezirk: "
                + with_meta(
                    milieuschutz_data["bezirk"],
                    META["milieuschutz"]["source"],
                    META["milieuschutz"]["date"],
                )
            )
            print(
                "  Inkrafttreten: "
                + with_meta(
                    milieuschutz_data["inkraft"],
                    META["milieuschutz"]["source"],
                    META["milieuschutz"]["date"],
                )
            )
            print(
                "  Fläche: "
                + with_meta(
                    milieuschutz_data["flaeche_ha"],
                    META["milieuschutz"]["source"],
                    META["milieuschutz"]["date"],
                    " ha",
                )
            )

        # MARKT & LAGE
        print("\n[MARKT & LAGE]")
        print("-" * 40)

        print(
            "Wohnlage: "
            + with_meta(
                wohnlage_data["wohnlage"],
                META["wohnlage"]["source"],
                META["wohnlage"]["date"],
            )
        )
        print(
            "MSS Status: "
            + with_meta(
                mss_data["status"],
                META["mss"]["source"],
                META["mss"]["date"],
            )
        )
        print(
            "MSS Dynamik: "
            + with_meta(
                mss_data["dynamik"],
                META["mss"]["source"],
                META["mss"]["date"],
            )
        )
        print(
            "MSS Kombination: "
            + with_meta(
                mss_data["kombination"],
                META["mss"]["source"],
                META["mss"]["date"],
            )
        )

        print("\nKaufkraft:")
        print(
            "  Kaufkraft je Haushalt im PLZ-Gebiet: "
            + with_meta(
                kaufkraft_data["kaufkraft_plz"],
                META["kaufkraft"]["source"],
                META["kaufkraft"]["date"],
            )
        )
        print(
            "  Rang des PLZ-Gebiets: "
            + with_meta(
                kaufkraft_data["rang_plz"],
                META["kaufkraft"]["source"],
                META["kaufkraft"]["date"],
            )
        )
        print(
            "  Bezirk aus Adresslogik: "
            + with_meta(
                kaufkraft_data["bezirk_aus_adresse"],
                META["kaufkraft"]["source"],
                META["kaufkraft"]["date"],
            )
        )
        print(
            "  Bezirk aus PLZ-Tabelle: "
            + with_meta(
                kaufkraft_data["bezirk_aus_plz_tabelle"],
                META["kaufkraft"]["source"],
                META["kaufkraft"]["date"],
            )
        )
        print(
            "  Bezirk für Bezirkswert: "
            + with_meta(
                kaufkraft_data["bezirk_fuer_bezirkswert"],
                META["kaufkraft"]["source"],
                META["kaufkraft"]["date"],
            )
        )
        print(
            "  Kaufkraft je Haushalt im Bezirk: "
            + with_meta(
                kaufkraft_data["kaufkraft_bezirk"],
                META["kaufkraft"]["source"],
                META["kaufkraft"]["date"],
            )
        )
        print(
            "  Berliner Durchschnitt: "
            + with_meta(
                kaufkraft_data["kaufkraft_berlin"],
                META["kaufkraft"]["source"],
                META["kaufkraft"]["date"],
            )
        )
        if kaufkraft_data["bezirksabweichung"]:
            print("  Hinweis: PLZ-Zuordnung und Adress-Bezirkslogik weichen voneinander ab. Bitte fachlich prüfen.")

        print("\nBodenrichtwert:")
        if not brw_data["in_brw_zone"]:
            print(
                "  Kein Treffer: "
                + with_meta(
                    "nein",
                    META["brw"]["source"],
                    META["brw"]["date"],
                )
            )
        elif brw_data["grenzfall"]:
            print(
                "  Grenzfall: "
                + with_meta(
                    "ja",
                    META["brw"]["source"],
                    META["brw"]["date"],
                )
            )
            print(
                "  Hinweis: "
                + with_meta(
                    brw_data["hinweis"],
                    META["brw"]["source"],
                    META["brw"]["date"],
                )
            )
            for zone in brw_data["zonen_details"]:
                print(
                    "    - "
                    + with_meta(
                        f"{zone.get('brw')} € | {zone.get('nutzung')} | Bezirk: {zone.get('bezirk')} | ID: {zone.get('brwid')}",
                        META["brw"]["source"],
                        META["brw"]["date"],
                    )
                )
        else:
            print(
                "  Wert: "
                + with_meta(
                    brw_data["brw"],
                    META["brw"]["source"],
                    META["brw"]["date"],
                    " €",
                )
            )
            print(
                "  Nutzung: "
                + with_meta(
                    brw_data["nutzung"],
                    META["brw"]["source"],
                    META["brw"]["date"],
                )
            )
            print(
                "  Stichtag BRW: "
                + with_meta(
                    brw_data["stichtag"],
                    META["brw"]["source"],
                    META["brw"]["date"],
                )
            )
            print(
                "  GFZ: "
                + with_meta(
                    brw_data["gfz"],
                    META["brw"]["source"],
                    META["brw"]["date"],
                )
            )
            print(
                "  Beitragszustand: "
                + with_meta(
                    brw_data["beitragszustand"],
                    META["brw"]["source"],
                    META["brw"]["date"],
                )
            )
            print(
                "  Bezirk: "
                + with_meta(
                    brw_data["bezirk"],
                    META["brw"]["source"],
                    META["brw"]["date"],
                )
            )
            print(
                "  BRW-ID: "
                + with_meta(
                    brw_data["brwid"],
                    META["brw"]["source"],
                    META["brw"]["date"],
                )
            )

        # UMWELT & RISIKEN
        print("\n[UMWELT & RISIKEN]")
        print("-" * 40)

        print(
            "Hochwasser: "
            + with_meta(
                hochwasser_data["in_hochwasser"],
                META["hochwasser"]["source"],
                META["hochwasser"]["date"],
            )
        )
        if hochwasser_data["in_hochwasser"]:
            print(
                "  Bezeichnung: "
                + with_meta(
                    hochwasser_data["bezeichnung"],
                    META["hochwasser"]["source"],
                    META["hochwasser"]["date"],
                )
            )
            print(
                "  Gewässer: "
                + with_meta(
                    hochwasser_data["gewaesser"],
                    META["hochwasser"]["source"],
                    META["hochwasser"]["date"],
                )
            )
            print(
                "  Rechtsstand: "
                + with_meta(
                    hochwasser_data["rechtsstand"],
                    META["hochwasser"]["source"],
                    META["hochwasser"]["date"],
                )
            )

        print(
            "Denkmalschutz: "
            + with_meta(
                denkmalschutz_data["denkmalschutz_exakt"],
                META["denkmalschutz"]["source"],
                META["denkmalschutz"]["date"],
            )
        )
        if denkmalschutz_data["denkmalschutz_exakt"]:
            print(
                "  Art: "
                + with_meta(
                    denkmalschutz_data["trefferart"],
                    META["denkmalschutz"]["source"],
                    META["denkmalschutz"]["date"],
                )
            )
            print(
                "  ID: "
                + with_meta(
                    denkmalschutz_data["id"],
                    META["denkmalschutz"]["source"],
                    META["denkmalschutz"]["date"],
                )
            )
            print(
                "  Link: "
                + with_meta(
                    denkmalschutz_data["link"],
                    META["denkmalschutz"]["source"],
                    META["denkmalschutz"]["date"],
                )
            )

        print("\nLärm:")
        print(
            "  L_DEN: "
            + with_meta(
                laerm_data["lden"],
                META["laerm"]["source"],
                META["laerm"]["date"],
            )
        )
        print(
            "  L_N: "
            + with_meta(
                laerm_data["lnight"],
                META["laerm"]["source"],
                META["laerm"]["date"],
            )
        )

        # BEWERTUNGSHINWEISE
        print("\n[BEWERTUNGSHINWEISE]")
        print("-" * 40)

        if brw_data["grenzfall"]:
            print("- Bodenrichtwert kritisch: Grenzlage zwischen mehreren Zonen")

        if kaufkraft_data["bezirksabweichung"]:
            print("- Kaufkraft: PLZ und Bezirk stimmen nicht überein")

        if milieuschutz_data["in_milieuschutz"]:
            print("- Milieuschutz/Erhaltungsverordnung beachten")

        if denkmalschutz_data["denkmalschutz_exakt"]:
            print("- Denkmalschutz vorhanden")

        print(f"\nGespeichert unter: {file_path}")

    except Exception as e:
        print("\nFehler:")
        print(e)


if __name__ == "__main__":
    main()