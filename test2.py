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


#New search flights tool that uses the Amadeus API

def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: Optional[int] = None,
    infants: Optional[int] = None,
    cabin_class: Optional[str] = None,
    direct_only: Optional[bool] = False,
    included_airline_codes: Optional[str] = None,
    excluded_airline_codes: Optional[str] = None,
    max_price: Optional[int] = None,
    max_results: Optional[int] = None
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
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": int(adults),
            "nonStop": direct_only,
        }

        # Conditionally add optional parameters if provided
        if return_date:
            search_params["returnDate"] = return_date
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
        if max_price is not None:
            search_params["maxPrice"] = max_price
        if max_results is not None:
            search_params["max"] = max_results

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
    
# # Additional tool to get detailed information about a specific flight offer

# def get_flight_details(flight_offer: dict) -> dict:
  
#     # Note: In a real implementation, you would likely need to store the flight offers
#     # from the search results in a session or database to retrieve them by ID.
#     # This function is a placeholder that would need to be implemented based on your
#     # specific caching or storage strategy.
#     try:
#         response = amadeus.shopping.flight_offers.pricing.post(flight_offer)
#         return response.data
#     except ResponseError as error:
#         return {"error": str(error)}



def get_flight_details(flight_offer: dict) -> dict:
    """
    Get detailed information about a specific flight offer by ID.
    
    Args:
        index: Index of the return result of the search_flight function
        
    Returns:
        Detailed information about the flight offer
    """
   
    try:
        response = amadeus.shopping.flight_offers.pricing.post(flight_offer)
        return response.data
    except ResponseError as error:
        return {"error": str(error)}
        


if __name__ == "__main__":
    flight = {'adults': 1, "origin": "JFK", 'destination': 'DEN', 'return_date': '2025-05-31', 'departure_date': '2025-05-27', "max_results": 1}
    print("Search parameters:", flight)
    data = search_flights(**flight)
    print("Search results:")
    print(json.dumps(data, indent=2) if not isinstance(data, str) else data)
