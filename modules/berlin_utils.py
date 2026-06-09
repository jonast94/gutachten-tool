def normalize_text(value: str) -> str:
    if not value:
        return ""
    return value.strip().lower()


ORTSTEIL_TO_BEZIRK = {
    "mitte": "Mitte",
    "moabit": "Mitte",
    "hansaviertel": "Mitte",
    "tiergarten": "Mitte",
    "wedding": "Mitte",
    "gesundbrunnen": "Mitte",

    "friedrichshain": "Friedrichshain-Kreuzberg",
    "kreuzberg": "Friedrichshain-Kreuzberg",

    "prenzlauer berg": "Pankow",
    "weißensee": "Pankow",
    "weissensee": "Pankow",
    "blankenburg": "Pankow",
    "heinersdorf": "Pankow",
    "karow": "Pankow",
    "stadtrandsiedlung malchow": "Pankow",
    "pankow": "Pankow",
    "blankenfelde": "Pankow",
    "buch": "Pankow",
    "französisch buchholz": "Pankow",
    "franzoesisch buchholz": "Pankow",
    "niederschönhausen": "Pankow",
    "niederschoenhausen": "Pankow",
    "rosenthal": "Pankow",
    "wilhelmsruh": "Pankow",

    "charlottenburg": "Charlottenburg-Wilmersdorf",
    "charlottenburg-nord": "Charlottenburg-Wilmersdorf",
    "grunewald": "Charlottenburg-Wilmersdorf",
    "halensee": "Charlottenburg-Wilmersdorf",
    "schmargendorf": "Charlottenburg-Wilmersdorf",
    "westend": "Charlottenburg-Wilmersdorf",
    "wilmersdorf": "Charlottenburg-Wilmersdorf",

    "spandau": "Spandau",
    "haselhorst": "Spandau",
    "siemensstadt": "Spandau",
    "staaken": "Spandau",
    "gatow": "Spandau",
    "kladow": "Spandau",
    "hakenfelde": "Spandau",
    "falkenhagener feld": "Spandau",
    "wilhelmstadt": "Spandau",

    "steglitz": "Steglitz-Zehlendorf",
    "lichterfelde": "Steglitz-Zehlendorf",
    "lankwitz": "Steglitz-Zehlendorf",
    "zehlendorf": "Steglitz-Zehlendorf",
    "dahlem": "Steglitz-Zehlendorf",
    "nikolassee": "Steglitz-Zehlendorf",
    "wannsee": "Steglitz-Zehlendorf",

    "schöneberg": "Tempelhof-Schöneberg",
    "schoeneberg": "Tempelhof-Schöneberg",
    "friedenau": "Tempelhof-Schöneberg",
    "tempelhof": "Tempelhof-Schöneberg",
    "mariendorf": "Tempelhof-Schöneberg",
    "marienfelde": "Tempelhof-Schöneberg",
    "lichtenrade": "Tempelhof-Schöneberg",

    "neukölln": "Neukölln",
    "neukoelln": "Neukölln",
    "britz": "Neukölln",
    "buckow": "Neukölln",
    "rudow": "Neukölln",
    "gropiusstadt": "Neukölln",

    "alt-treptow": "Treptow-Köpenick",
    "alt treptow": "Treptow-Köpenick",
    "plänterwald": "Treptow-Köpenick",
    "plaenterwald": "Treptow-Köpenick",
    "baumschulenweg": "Treptow-Köpenick",
    "johannisthal": "Treptow-Köpenick",
    "niederschöneweide": "Treptow-Köpenick",
    "niederschoeneweide": "Treptow-Köpenick",
    "altglienicke": "Treptow-Köpenick",
    "adlershof": "Treptow-Köpenick",
    "bohnsdorf": "Treptow-Köpenick",
    "oberschöneweide": "Treptow-Köpenick",
    "oberschoeneweide": "Treptow-Köpenick",
    "köpenick": "Treptow-Köpenick",
    "koepenick": "Treptow-Köpenick",
    "friedrichshagen": "Treptow-Köpenick",
    "rahnsdorf": "Treptow-Köpenick",
    "grünau": "Treptow-Köpenick",
    "gruenau": "Treptow-Köpenick",
    "müggelheim": "Treptow-Köpenick",
    "mueggelheim": "Treptow-Köpenick",
    "schmöckwitz": "Treptow-Köpenick",
    "schmoeckwitz": "Treptow-Köpenick",

    "marzahn": "Marzahn-Hellersdorf",
    "biesdorf": "Marzahn-Hellersdorf",
    "kaulsdorf": "Marzahn-Hellersdorf",
    "mahlsdorf": "Marzahn-Hellersdorf",
    "hellersdorf": "Marzahn-Hellersdorf",

    "friedrichsfelde": "Lichtenberg",
    "karlshorst": "Lichtenberg",
    "lichtenberg": "Lichtenberg",
    "falkenberg": "Lichtenberg",
    "malchow": "Lichtenberg",
    "wartenberg": "Lichtenberg",
    "neu-hohenschönhausen": "Lichtenberg",
    "neu-hohenschoenhausen": "Lichtenberg",
    "alt-hohenschönhausen": "Lichtenberg",
    "alt-hohenschoenhausen": "Lichtenberg",
    "fennpfuhl": "Lichtenberg",
    "rummelsburg": "Lichtenberg",

    "reinickendorf": "Reinickendorf",
    "tegel": "Reinickendorf",
    "konradshöhe": "Reinickendorf",
    "konradshoehe": "Reinickendorf",
    "heiligensee": "Reinickendorf",
    "frohnau": "Reinickendorf",
    "hermsdorf": "Reinickendorf",
    "waidmannslust": "Reinickendorf",
    "lübars": "Reinickendorf",
    "luebars": "Reinickendorf",
    "wittenau": "Reinickendorf",
    "märkisches viertel": "Reinickendorf",
    "maerkisches viertel": "Reinickendorf",
    "borsigwalde": "Reinickendorf",
}


BERLIN_BEZIRKE = [
    "Mitte",
    "Friedrichshain-Kreuzberg",
    "Pankow",
    "Charlottenburg-Wilmersdorf",
    "Spandau",
    "Steglitz-Zehlendorf",
    "Tempelhof-Schöneberg",
    "Neukölln",
    "Treptow-Köpenick",
    "Marzahn-Hellersdorf",
    "Lichtenberg",
    "Reinickendorf",
]


def normalize_berlin_district(address_data: dict) -> str:
    """
    Ermittelt den Berliner Bezirk robust.
    Priorität:
    1. Ortsteil -> Bezirk
    2. borough / city_district direkt
    """

    ortsteil_candidates = [
        address_data.get("suburb"),
        address_data.get("quarter"),
    ]

    for ortsteil in ortsteil_candidates:
        ortsteil_norm = normalize_text(ortsteil)
        if ortsteil_norm in ORTSTEIL_TO_BEZIRK:
            return ORTSTEIL_TO_BEZIRK[ortsteil_norm]

    district_candidates = [
        address_data.get("borough"),
        address_data.get("city_district"),
    ]

    for value in district_candidates:
        value_norm = normalize_text(value)
        for bezirk in BERLIN_BEZIRKE:
            if normalize_text(bezirk) in value_norm:
                return bezirk

    return "Unbekannt"