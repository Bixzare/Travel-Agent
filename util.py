def parse_flight_offer(offer):
    itinerary = offer['itineraries'][0]
    segment = itinerary['segments'][0]
    departure = segment['departure']
    arrival = segment['arrival']
    price = offer['price']
    traveler_pricing = offer['travelerPricings'][0]
    fare_details = traveler_pricing['fareDetailsBySegment'][0]

    dep_time = departure['at']
    arr_time = arrival['at']
    dep_airport = departure['iataCode']
    arr_airport = arrival['iataCode']
    flight_number = f"{segment['carrierCode']} {segment['number']}"
    duration = segment['duration']
    flight_date = dep_time.split('T')[0]

    total_price = price['total']
    currency = price['currency']
    checked_bag_fee = None
    for service in price.get('additionalServices', []):
        if service['type'] == 'CHECKED_BAGS':
            checked_bag_fee = service['amount']

    stops = segment['numberOfStops']
    is_direct = stops == 0

    # Checked bags
    checked_bags_info = fare_details.get("includedCheckedBags", {})
    if "quantity" in checked_bags_info:
        checked_bags_included = checked_bags_info["quantity"]
    elif "weight" in checked_bags_info:
        checked_bags_included = f"{checked_bags_info['weight']} {checked_bags_info.get('weightUnit', '')}"
    else:
        checked_bags_included = "Unknown"

    # Cabin bags (optional)
    carryon_bags_info = fare_details.get("includedCabinBags", {})
    carryon_bags_included = carryon_bags_info.get("quantity", "Unknown")

    amenities = fare_details.get("amenities", [])

    summary = {
        "flight_date": flight_date,
        "departure_time": dep_time,
        "arrival_time": arr_time,
        "from": dep_airport,
        "to": arr_airport,
        "flight_number": flight_number,
        "duration": duration,
        "is_direct": is_direct,
        "stops": stops,
        "total_price": f"{total_price} {currency}",
        "checked_bags_included": checked_bags_included,
        "carryon_bags_included": carryon_bags_included,
        "checked_bag_fee": checked_bag_fee,
        "amenities": amenities,
    }
    return summary

def parse_pricing_offer(pricing_response: dict):
    offer = pricing_response["flightOffers"][0]

    itinerary = offer["itineraries"][0]
    segment = itinerary["segments"][0]
    departure = segment["departure"]
    arrival = segment["arrival"]
    price = offer["price"]
    traveler_pricing = offer["travelerPricings"][0]
    fare_details = traveler_pricing["fareDetailsBySegment"][0]

    # Times and locations
    dep_time = departure["at"]
    arr_time = arrival["at"]
    dep_airport = departure["iataCode"]
    arr_airport = arrival["iataCode"]
    flight_number = f"{segment['carrierCode']} {segment['number']}"
    duration = segment["duration"]
    flight_date = dep_time.split("T")[0]

    # Price info
    total_price = price["total"]
    currency = price["currency"]

    # Baggage info (might be missing)
    checked_bags_info = fare_details.get("includedCheckedBags", {})
    if "quantity" in checked_bags_info:
        checked_bags_included = checked_bags_info["quantity"]
    elif "weight" in checked_bags_info:
        checked_bags_included = f"{checked_bags_info['weight']} {checked_bags_info.get('weightUnit', '')}"
    else:
        checked_bags_included = "Unknown"

    carryon_bags_info = fare_details.get("includedCabinBags", {})
    carryon_bags_included = carryon_bags_info.get("quantity", "Unknown")

    # Optional: CO2 emissions
    co2 = segment.get("co2Emissions", [])
    co2_kg = co2[0]["weight"] if co2 else "Unknown"

    # Stops
    stops = segment["numberOfStops"]
    is_direct = stops == 0

    # Taxes (if present)
    taxes = traveler_pricing["price"].get("taxes", [])

    return {
        "flight_date": flight_date,
        "departure_time": dep_time,
        "arrival_time": arr_time,
        "from": dep_airport,
        "to": arr_airport,
        "flight_number": flight_number,
        "duration": duration,
        "is_direct": is_direct,
        "stops": stops,
        "total_price": f"{total_price} {currency}",
        "checked_bags_included": checked_bags_included,
        "carryon_bags_included": carryon_bags_included,
        "co2_emission_kg": co2_kg,
        "taxes": taxes
    }
def text_bool(value):
    """
    Convert a boolean to string"""

    return "true" if value else "false"