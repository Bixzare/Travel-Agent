from amadeus import Client, ResponseError
from langchain.tools import tool
import os
from typing import Optional, List, Dict, Any
import json
from dotenv import load_dotenv
from datetime import datetime
from util import parse_flight_offer, text_bool, parse_pricing_offer

load_dotenv()
amadeus_api_key = os.getenv("AMADEUS_API_KEY")
amadeus_api_secret = os.getenv("AMADEUS_API_SECRET")
amadeus = Client(client_id=amadeus_api_key, client_secret=amadeus_api_secret)

@tool
def collect_flight_info(
    originLocationCode: str,
    destinationLocationCode: str,
    departureDate: str,
    adults: int = 1,
    returnDate: Optional[str] = None,
    children: Optional[int] = None,
    infants: Optional[int] = None,
    travelClass: Optional[str] = None,
    includedAirlineCodes: Optional[str] = None,
    excludedAirlineCodes: Optional[str] = None,
    nonStop: Optional[bool] = False,
    include_checked_bag: Optional[bool] = False,  # not part of API spec, keep only if used in logic
    maxPrice: Optional[int] = None,
    max: Optional[int] = None,
) -> str:
    """
    Collects flight search parameters compatible with flight search API.

    Args:
    Required:
    - originLocationCode: IATA code of departure airport (e.g., "SYD")
    - destinationLocationCode: IATA code of destination airport (e.g., "BKK")
    - departureDate: Date of departure (YYYY-MM-DD)
    - adults: Number of adult travelers (12+). Default: 1

    Optional:
    - returnDate: Return date (YYYY-MM-DD), if round-trip
    - children: Number of children (2-11)
    - infants: Number of infants (under 2)
    - travelClass: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
    - includedAirlineCodes: Only include these airlines (comma-separated IATA codes)
    - excludedAirlineCodes: Exclude these airlines (comma-separated IATA codes)
    - nonStop: Only direct flights (default: False)
    - maxPrice: Max price per traveler (whole number)
    - max: Max number of results (default from API is 250)

    Return:
    Structured format of flight information, if optional field is not present, don't dislpay its accompanying text

    """
    return f"""Flight request captured:
    From: {originLocationCode} → To: {destinationLocationCode}
    Departing: {departureDate}, Returning: {returnDate or "One-way"}
    Adults: {adults}{f", Children: {children}" if children is not None else ""}{f", Infants: {infants}" if infants is not None else ""}
    Cabin Class: {travelClass or "Any"}
    Direct only: {nonStop}
    Included Airlines: {includedAirlineCodes or "Any"}
    Excluded Airlines: {excludedAirlineCodes or "None"}
    Max Price: {maxPrice or "No limit"}, Max Results: {max or "Default (250)"}
    Checked Bag Preference: {"Included" if include_checked_bag else "Not specified"}
    """

@tool
def collect_passenger_info(
    first_name: str,
    last_name: str,
    email: str,
    date_of_birth: str,
    phone: str,

) -> str:
    """Collects passenger information for booking"""

    return f"""User info captured:
    First Name: {first_name}
    Last name : {last_name}
    Email : {email}
    Date of Birth: {date_of_birth}
    Phone Number: {phone}
      """


@tool
def get_airport_code(city: str) -> dict:
    """Search for airport code using city name"""
    response = amadeus.reference_data.locations.get(keyword=city, subType='AIRPORT')
    return response.data

@tool
def search_flights(
    originLocationCode: str,
    destinationLocationCode: str,
    departureDate: str,
    returnDate: Optional[str] = None,
    adults: int = 1,
    children: Optional[int] = None,
    infants: Optional[int] = None,
    cabin_class: Optional[str] = None,
    direct_only: Optional[bool] = False,
    included_airline_codes: Optional[str] = None,
    excluded_airline_codes: Optional[str] = None,
    maxPrice: Optional[int] = None,
    max: Optional[int] = None
) -> str:
    """
    Search for flights using the Amadeus API.
    
    Args:

        Required:
            originLocationCode: IATA code of departure airport (e.g., "SYD")
            destinationLocationCode: IATA code of destination airport (e.g., "BKK")
            departureDate: Date of departure (YYYY-MM-DD)
            adults: Number of adult travelers (12+). Default: 1

        Optional:
            returnDate: Return date in YYYY-MM-DD format (null for one-way)
            children: Number of child passengers
            infants: Number of infant passengers
            cabinClass: Cabin class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
            direct_only: If True, return only direct flights
            includedAirlineCodes: Only show results from these airlines (IATA codes, comma-separated)
            excludedAirlineCodes: Exclude these airlines (IATA codes, comma-separated)
            maxPrice: Max price per traveler
            max: Max number of results to return

    Returns:
        JSON string with flight search results
    """
    try:
        search_params = {
            "originLocationCode": originLocationCode,
            "destinationLocationCode": destinationLocationCode,
            "departureDate": departureDate,
            "adults": int(adults),
            "nonStop": text_bool(direct_only),
            "currencyCode": "USD",  # Default currency, can be changed if needed
        }

        # Conditionally add optional parameters if provided
        if returnDate:
            search_params["returnDate"] = returnDate
        if children is not None:
            search_params["children"] = children
        if infants is not None:
            search_params["infants"] = infants
        if cabin_class:
            search_params["travelClass"] = cabin_class
        if included_airline_codes:
            search_params["includedAirlineCodes"] = included_airline_codes
        if excluded_airline_codes:
            search_params["excludedAirlineCodes"] = excluded_airline_codes
        if maxPrice is not None:
            search_params["maxPrice"] = maxPrice
        if max is not None:
            search_params["max"] = 10

        # Conflict check
        if included_airline_codes and excluded_airline_codes:
            return "Error: You cannot specify both includedAirlineCodes and excludedAirlineCodes."

        print(search_params) # testing

        # Get search results from Amadeus
        response = amadeus.shopping.flight_offers_search.get(**search_params)

        flight_offers = response.data
        
        

        res = []

        for offer in flight_offers:
            res.append(parse_flight_offer(offer))

        return res
       
       
    except ResponseError as error:
        return json.dumps({
            "error": f"Amadeus API error: {str(error)}",
            "status_code": error.response.status_code
        })
    except Exception as e:
        return json.dumps({
            "error": f"An unexpected error occurred: {str(e)}"
        })
    
