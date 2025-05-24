from amadeus import Client, ResponseError
import os
from typing import Optional, List, Dict, Any
import json
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()
amadeus_api_key = os.getenv("AMADEUS_API_KEY")
amadeus_api_secret = os.getenv("AMADEUS_API_SECRET")
    
temp = None
amadeus = Client(client_id=amadeus_api_key, client_secret=amadeus_api_secret)

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
        origin: Origin airport IATA code (e.g., "JFK")
        destination: Destination airport IATA code (e.g., "DEN")
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Return date in YYYY-MM-DD format (null for one-way)
        adults: Number of adult passengers
        children: Number of child passengers
        infants: Number of infant passengers
        cabin_class: Cabin class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
        direct_only: If True, return only direct flights
        included_airline_codes: Only show results from these airlines (IATA codes, comma-separated)
        excluded_airline_codes: Exclude these airlines (IATA codes, comma-separated)
        max_price: Max price per traveler
        max_results: Max number of results to return

    Returns:
        JSON string with flight search results
    """
    try:
        search_params = {
            "originLocationCode": originLocationCode,
            "destinationLocationCode": destinationLocationCode,
            "departureDate": departureDate,
            "adults": int(adults),
            "nonStop": direct_only,
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
            search_params["max"] = max

        # Conflict check
        if included_airline_codes and excluded_airline_codes:
            return "Error: You cannot specify both includedAirlineCodes and excludedAirlineCodes."

   
        # Get search results from Amadeus
        response = amadeus.shopping.flight_offers_search.get(**search_params)

        flight_offers = response.data
        
        return flight_offers
       
       
    except ResponseError as error:
        return json.dumps({
            "error": f"Amadeus API error: {str(error)}",
            "status_code": error.response.status_code
        })
    except Exception as e:
        return json.dumps({
            "error": f"An unexpected error occurred: {str(e)}"
        })
    
if __name__ == "__main__":

    data = search_flights(
        adults= 1.0, originLocationCode= 'JFK', cabin_class= 'ECONOMY', destinationLocationCode= 'LAX', departureDate= '2025-06-27'
    )

# Invoking: `search_flights` with `{'adults': 1.0, 'originLocationCode': 'JFK', 'cabin_class': 'ECONOMY', 'destinationLocationCode': 'LAX', 'departureDate': '2025-06-27'}`
# responded: Okay, no problem. I will proceed with a search using the parameters you've provided, without any baggage or direct flight preferences, and no maximum price.


originLocationCode
originLocationCode

destinationLocationCode
destinationLocationCode