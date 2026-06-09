import requests


WMS_URL = "https://gdi.berlin.de/services/wms/ua_stratlaerm_2022"


def get_laerm_feature_info(latitude: str, longitude: str, layer_name: str) -> dict:
    """
    Fragt einen Berliner Lärmkarten-Layer per WMS GetFeatureInfo ab.
    """

    lat = float(latitude)
    lon = float(longitude)

    delta = 0.0005
    minx = lon - delta
    miny = lat - delta
    maxx = lon + delta
    maxy = lat + delta

    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetFeatureInfo",
        "LAYERS": layer_name,
        "QUERY_LAYERS": layer_name,
        "STYLES": "",
        "CRS": "EPSG:4326",
        "BBOX": f"{miny},{minx},{maxy},{maxx}",
        "WIDTH": 101,
        "HEIGHT": 101,
        "I": 50,
        "J": 50,
        "INFO_FORMAT": "application/json",
        "FEATURE_COUNT": 10,
    }

    headers = {
        "User-Agent": "gutachten-tool/1.0"
    }

    response = requests.get(WMS_URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()

    try:
        data = response.json()
    except Exception:
        return {
            "success": False,
            "raw_text": response.text[:2000],
            "features": []
        }

    return {
        "success": True,
        "features": data.get("features", []),
        "raw_data": data
    }


def _extract_first_property_value(feature_result: dict) -> str | None:
    """
    Gibt den ersten Property-Wert des ersten Features zurück.
    """
    if not feature_result.get("success"):
        return None

    features = feature_result.get("features", [])
    if not features:
        return None

    properties = features[0].get("properties", {})
    if not properties:
        return None

    first_value = next(iter(properties.values()), None)
    return first_value


def get_laerm_data(latitude: str, longitude: str) -> dict:
    """
    Holt die für Gutachten sinnvollen Lärmwerte:
    - Gesamtverkehr L_DEN
    - Gesamtverkehr L_N
    """

    den_result = get_laerm_feature_info(latitude, longitude, "bf_gesamtlaerm_den2022")
    night_result = get_laerm_feature_info(latitude, longitude, "cf_gesamtlaerm_n2022")

    return {
        "lden": _extract_first_property_value(den_result),
        "lnight": _extract_first_property_value(night_result),
        "lden_success": den_result.get("success", False),
        "lnight_success": night_result.get("success", False),
    }