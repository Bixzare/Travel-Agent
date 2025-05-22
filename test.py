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
    cabin_class: str = "ECONOMY",
    currency: str = "USD",
    direct_only: bool = False,
    max_results: int = 10
) -> str:
 
    try:
        # Initialize client (could be made into a singleton for efficiency)
        # amadeus = Client(client_id=amadeus_api_key, client_secret=amadeus_api_secret)
        
        # Basic parameters for the flight search
        search_params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "currencyCode": currency,
            "max": max_results,
            "travelClass": cabin_class
        }
        
        # Add return date if it's a round trip
        if return_date:
            search_params["returnDate"] = return_date
            
        # Get search results from Amadeus
        response = amadeus.shopping.flight_offers_search.get(**search_params)
        flight_offers = response.data
        return flight_offers

    except ResponseError as error:
        return {"error": str(error)}



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
    data = search_flights(
        origin="JFK",
        destination="DEN",
        departure_date="2025-10-26",  # Future date
        adults=1,
        cabin_class="ECONOMY",
        direct_only=False,
        max_results=1
    )
    print(data)
    
    # bag = get_flight_details(data[0])

    # print(bag)

