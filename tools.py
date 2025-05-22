from amadeus import Client, ResponseError
from langchain.tools import tool
import os
from typing import Optional, List, Dict, Any
import json
from dotenv import load_dotenv
from datetime import datetime
from rules import CARRY_ON_RULES


# LAST_FLIGHT_SEARCH_RESULT = None

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
    returnDate: str = None,
    children: int = None,
    infants: int = None,
    travelClass: str = None,
    includedAirlineCodes: str = None,
    excludedAirlineCodes: str = None,
    nonStop: bool = False,
    include_checked_bag: bool = False,  # not part of API spec, keep only if used in logic
    currencyCode: str = None,
    maxPrice: int = None,
    max: int = None,
) -> str:
    """
    Collects flight search parameters compatible with flight search API.

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
    - currencyCode: Preferred currency (ISO 4217, e.g., USD)
    - maxPrice: Max price per traveler (whole number)
    - max: Max number of results (default from API is 250)
    """

    return f"""Flight request captured:
    From: {originLocationCode} → To: {destinationLocationCode}
    Departing: {departureDate}, Returning: {returnDate or "One-way"}
    Adults: {adults}{f", Children: {children}" if children is not None else ""}{f", Infants: {infants}" if infants is not None else ""}
    Cabin Class: {travelClass or "Any"}
    Direct only: {nonStop}
    Included Airlines: {includedAirlineCodes or "Any"}
    Excluded Airlines: {excludedAirlineCodes or "None"}
    Currency: {currencyCode or "Default (USD)"}
    Max Price: {maxPrice or "No limit"}, Max Results: {max or "Default (250)"}
    Checked Bag Preference: {"Included" if include_checked_bag else "Not specified"}
    """

# @tool
# def collect_flight_info(
#     origin_airport: str,
#     destination_airport: str,
#     departure_date: str,
#     return_date: str = None,
#     passengers: int = 1,
#     cabin_class: str = "ECONOMY",
#     direct_only: bool = False,
#     include_checked_bag: bool = False,
    
# ) -> str:
#     """
#     Collects domestic U.S. flight search parameters.
#     """
#     return f"""Flight request captured:
#     From: {origin_airport} → To: {destination_airport}
#     Departing: {departure_date}, Returning: {return_date or "One-way"}
#     Passengers: {passengers}, Cabin: {cabin_class}
#     Direct only: {direct_only}
#     Bags: Checked - {include_checked_bag}, 
#     """

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

#New search flights tool that uses the Amadeus API


@tool
def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: Optional[int] = None,
    infants: Optional[int] = None,
    cabin_class: Optional[str] = None,
    currency: Optional[str] = None,
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
        currency: Currency code for prices
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
        if currency:
            search_params["currencyCode"] = currency
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
        res = []
        for offer in flight_offers:
            res.append(get_flight_details(offer))

        # global LAST_FLIGHT_SEARCH_RESULT

        # LAST_FLIGHT_SEARCH_RESULT = flight_offers

        # res = []

        # for offer in flight_offers:
        #     res.append(get_flight_details(offer))

        # return res
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
        
# @tool
# def get_flight_details(index):
#     """
#     Get detailed information about a specific flight offer by ID.
    
#     Args:
#         index: Index of the return result of the search_flight function
        
#     Returns:
#         Detailed information about the flight offer
#     """
#     index = int(index)
#     global LAST_FLIGHT_SEARCH_RESULT

#     if LAST_FLIGHT_SEARCH_RESULT and 0 <= index < len(LAST_FLIGHT_SEARCH_RESULT):
#         flight_offer = LAST_FLIGHT_SEARCH_RESULT[index]
   
#         try:
#             response = amadeus.shopping.flight_offers.pricing.post(flight_offer)
#             return response.data
#         except ResponseError as error:
#             return {"error": str(error)}
        
#     return {"error": "Invalid flight offer index."}

# @tool
# def infer_carry_on(carrier_code: str, branded_fare: str) ->Optional[Dict[str, bool]]:
#     """Infers carry-on baggage rules based on carrier code and branded fare.
    
#     Args:
#         carrier_code: Value returned from the get_flight_details tool Eg(B6)
#         branded_fare: Value returned from the get_flight_details tool Eg(DN)
        
#     Returns:
#             Information about the carry on allowance for a flight"""
#     carrier_rules = CARRY_ON_RULES.get(carrier_code.upper())

#     if not carrier_rules:
#         return None
#     return carrier_rules.get(branded_fare.upper())


   

# @tool
# def search_flights(
#     origin: str,
#     destination: str,
#     departure_date: str,
#     return_date: Optional[str] = None,
#     adults: int = 1,
#     cabin_class: str = "ECONOMY",
#     currency: str = "USD",
#     direct_only: bool = False,
#     max_results: int = 10
# ) -> str:
#     """
#     Search for flights using the Amadeus API.
    
#     Args:
#         origin: Origin airport IATA code (e.g., "JFK")
#         destination: Destination airport IATA code (e.g., "DEN")
#         departure_date: Departure date in YYYY-MM-DD format
#         return_date: Return date in YYYY-MM-DD format (null for one-way)
#         adults: Number of adult passengers
#         cabin_class: Cabin class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
#         currency: Currency code for prices
#         direct_only: If True, return only direct flights
#         max_results: Maximum number of results to return
        
#     Returns:
#         JSON string with flight search results
#     """
#     try:
#         # Initialize client (could be made into a singleton for efficiency)
#         # amadeus = Client(client_id=amadeus_api_key, client_secret=amadeus_api_secret)
        
#         # Basic parameters for the flight search
#         search_params = {
#             "originLocationCode": origin,
#             "destinationLocationCode": destination,
#             "departureDate": departure_date,
#             "adults": adults,
#             "currencyCode": currency,
#             "max": max_results,
#             "travelClass": cabin_class
#         }
        
#         # Add return date if it's a round trip
#         if return_date:
#             search_params["returnDate"] = return_date
            
#         # Get search results from Amadeus
#         response = amadeus.shopping.flight_offers_search.get(**search_params)

#         print(response) # testing purposes
#         flight_offers = response.data
        
#         # Filter for direct flights if requested
#         if direct_only:
#             flight_offers = [
#                 offer for offer in flight_offers
#                 if all(len(itinerary["segments"]) == 1 for itinerary in offer["itineraries"])
#             ]
        
#         # Process results to extract key information for each flight
#         processed_results = []
#         for offer in flight_offers:
#             # Process basic information
#             processed_offer = {
#                 "id": offer["id"],
#                 "price": {
#                     "total": offer["price"]["total"],
#                     "currency": offer["price"]["currency"]
#                 },
#                 "itineraries": []
#             }
            
#             # Process each itinerary (outbound and return if applicable)
#             for itinerary_index, itinerary in enumerate(offer["itineraries"]):
#                 segments = []
#                 connections = []
#                 is_direct = len(itinerary["segments"]) == 1
#                 num_stops = len(itinerary["segments"]) -1

#                 # process segemnts

#                 for i, segment in enumerate(itinerary["segments"]):
#                     segment_info = {
#                         "departure": {
#                             "airport": segment["departure"]["iataCode"],
#                             "terminal": segment["departure"].get("terminal"),
#                             "time": segment["departure"]["at"]
#                         },
#                         "arrival": {
#                             "airport": segment["arrival"]["iataCode"],
#                             "terminal": segment["arrival"].get("terminal"),
#                             "time": segment["arrival"]["at"]
#                         },
#                         "flight_number": f"{segment['carrierCode']} {segment['number']}",
#                         "duration": segment.get("duration", ""),
#                         "aircraft": segment.get("aircraft", {}).get("code")
#                     }
#                     segments.append(segment_info)

#                     #calculate layover/connection time (if not the last segment)
#                     if i < len(itinerary["segments"]) - 1:
#                         next_segment = itinerary["segments"][i+1]
                        
#                         # Parse datetime strings to calculate connection time
#                         arrival_time = datetime.fromisoformat(segment["arrival"]["at"].replace('Z', '+00:00'))
#                         departure_time = datetime.fromisoformat(next_segment["departure"]["at"].replace('Z', '+00:00'))
                        
#                         connection_duration = departure_time - arrival_time
#                         hours, remainder = divmod(connection_duration.seconds, 3600)
#                         minutes, _ = divmod(remainder, 60)
                        
#                         connection_info = {
#                             "airport": segment["arrival"]["iataCode"],
#                             "duration": f"{hours}h {minutes}m",
#                             "duration_minutes": connection_duration.seconds // 60,
#                             "arrival_terminal": segment["arrival"].get("terminal"),
#                             "departure_terminal": next_segment["departure"].get("terminal")
#                         }
#                         connections.append(connection_info)

#                 processed_offer["itineraries"].append({
#                     "duration": itinerary.get("duration", ""),
#                     "segments": segments,
#                     "connections": connections,
#                     "is_direct": is_direct,
#                     "stops": num_stops,
#                     "connection_airports": [conn["airport"] for conn in connections] if connections else []
#                 })  
            
#             if "travelerPricings" in offer:
#                     # Initialize baggage info dictionary
#                     baggage_info = {
#                         "checked": {
#                             "included": 0,
#                             "weight": None,
#                             "weightUnit": None,
#                             "additionalFees": []
#                         },
#                         "cabin": {
#                             "included": True,  # Default assumption
#                             "restrictions": None,
#                             "additionalFees": []
#                         }
#                     }
                    
#                     # Extract checked baggage information
#                     for traveler_pricing in offer["travelerPricings"]:
#                         if "includedCheckedBags" in traveler_pricing:
#                             included_bags = traveler_pricing["includedCheckedBags"]
#                             baggage_info["checked"]["included"] = included_bags.get("quantity", 0)
#                             baggage_info["checked"]["weight"] = included_bags.get("weight", None)
#                             baggage_info["checked"]["weightUnit"] = included_bags.get("weightUnit", None)
                        
#                         # Extract cabin baggage information if available
#                         if "includedCabinBags" in traveler_pricing:
#                             cabin_bags = traveler_pricing["includedCabinBags"]
#                             baggage_info["cabin"]["included"] = cabin_bags.get("quantity", 1) > 0
                    
#                     # Extract additional baggage fees if available in the response
#                     if "additionalServices" in offer:
#                         for service in offer.get("additionalServices", []):
#                             if service.get("type") == "CHECKED_BAGS":
#                                 baggage_info["checked"]["additionalFees"].append({
#                                     "amount": service.get("amount", ""),
#                                     "currency": service.get("currencyCode", ""),
#                                     "description": service.get("description", "")
#                                 })
#                             elif service.get("type") == "CABIN_BAGS":
#                                 baggage_info["cabin"]["additionalFees"].append({
#                                     "amount": service.get("amount", ""),
#                                     "currency": service.get("currencyCode", ""),
#                                     "description": service.get("description", "")
#                                 })
    
#                             processed_offer["baggage"] = baggage_info
#             processed_results.append(processed_offer)
        
#         # Return the processed results
#         return json.dumps({
#             "result_count": len(processed_results),
#             "flights": processed_results
#         }, indent=2)
        
#     except ResponseError as error:
#         return json.dumps({
#             "error": f"Amadeus API error: {str(error)}",
#             "status_code": error.response.status_code
#         })
#     except Exception as e:
#         return json.dumps({
#             "error": f"An unexpected error occurred: {str(e)}"
#         })
    
