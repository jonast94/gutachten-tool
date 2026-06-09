import requests


WFS_URL = "https://gdi.berlin.de/services/wfs/mss_2023"
WFS_TYPENAME = "mss_2023:mss2023_indizes_542"


def get_mss_data_from_wfs(latitude: str, longitude: str) -> dict:
    """
    Holt MSS 2023-Daten über den Berliner WFS-Dienst.
    Gibt Status, Dynamik und kombinierte Beschreibung zurück.
    """

    lat = float(latitude)
    lon = float(longitude)

    delta = 0.001

    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": WFS_TYPENAME,
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
        "bbox": f"{lon - delta},{lat - delta},{lon + delta},{lat + delta},EPSG:4326",
    }

    headers = {
        "User-Agent": "gutachten-tool/1.0"
    }

    response = requests.get(WFS_URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    features = data.get("features", [])

    if not features:
        raise ValueError("Keine MSS-Daten im WFS für diese Koordinate gefunden.")

    feature = features[0]
    properties = feature.get("properties", {})

    status = properties.get("si_v")
    dynamik = properties.get("di_v")
    kombination = properties.get("sdi_v")
    bez_id = properties.get("bez_id")
    einwohner = properties.get("ew")
    kommentar = properties.get("kom")

    if not status and not dynamik:
        available_fields = ", ".join(properties.keys())
        raise ValueError(
            "Status und Dynamik konnten nicht ausgelesen werden. "
            f"Verfügbare Felder: {available_fields}"
        )

    return {
        "status": status or "nicht erkannt",
        "dynamik": dynamik or "nicht erkannt",
        "kombination": kombination or "nicht erkannt",
        "bez_id": bez_id,
        "einwohner": einwohner,
        "kommentar": kommentar,
        "feature_count": len(features),
    }