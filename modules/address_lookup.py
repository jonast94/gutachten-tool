import requests


def lookup_address(street: str, house_number: str, postal_code: str) -> dict:
    """
    Sucht eine Berliner Adresse über die Nominatim-Suche von OpenStreetMap
    und liefert Standardadresse, Koordinaten und Adressbestandteile zurück.
    """
    query = f"{street} {house_number}, {postal_code} Berlin, Germany"
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 1
    }
    headers = {
        "User-Agent": "aedvice-gutachten-tool/1.0 (https://gutachten-tool-aedvice.streamlit.app)"
    }

    response = requests.get(url, params=params, headers=headers, timeout=20)
    response.raise_for_status()
    results = response.json()

    if not results:
        raise ValueError("Adresse wurde nicht gefunden.")

    result = results[0]
    address = result.get("address", {})

    return {
        "display_name": result.get("display_name"),
        "standard_address_clean": f"{address.get('road', '')} {address.get('house_number', '')}, {address.get('postcode', '')} {address.get('city', 'Berlin')}".strip(),
        "latitude": result.get("lat"),
        "longitude": result.get("lon"),
        "road": address.get("road"),
        "house_number": address.get("house_number"),
        "postcode": address.get("postcode"),
        "suburb": address.get("suburb"),
        "quarter": address.get("quarter"),
        "city_district": address.get("city_district"),
        "borough": address.get("borough"),
        "city": address.get("city")
    }