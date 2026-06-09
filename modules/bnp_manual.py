def get_bnp_manual_info(latitude: str, longitude: str) -> dict:
    """
    Gibt einen manuellen Hinweis zum Baunutzungsplan zurück,
    da der offizielle Berliner WMS nicht queryable ist.
    """

    return {
        "automatisiert_verfuegbar": False,
        "status": "manuell prüfen",
        "hinweis": "Der offizielle Berliner WMS zum Baunutzungsplan ist nicht direkt abfragbar.",
        "latitude": latitude,
        "longitude": longitude,
        "quelle": "Geoportal Berlin / WMS Baunutzungsplan"
    }