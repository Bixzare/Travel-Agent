import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import requests
from amadeus import Client, ResponseError
from dotenv import load_dotenv

""" Eseential : 
search_flights(...)
get_flight_offer_details(...)
create_mock_booking(...)
"""
class AmadeusFlightAPI:
    def __init__(self, api_key: str, api_secret: str):
        """Initialize the Amadeus API client with credentials."""
        self.amadeus = Client(
            client_id=api_key,
            client_secret=api_secret
        )
        self.session_data = {}
        
    def search_flights(self, origin: str, destination: str, 
                      departure_date: str, return_date: Optional[str] = None, 
                      adults: int = 1, currency: str = "USD") -> List[Dict]:
        """
        Search for flights using origin, destination and dates.
        
        Args:
            origin: Origin airport IATA code (e.g., "NYC")
            destination: Destination airport IATA code (e.g., "LON")
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date in YYYY-MM-DD format (optional)
            adults: Number of adult passengers
            currency: Currency code for prices
            
        Returns:
            List of flight offers
        """
        try:
            print(f"Searching flights from {origin} to {destination} on {departure_date}...")
            
            # For one-way trips
            if return_date is None:
                response = self.amadeus.shopping.flight_offers_search.get(
                    originLocationCode=origin,
                    destinationLocationCode=destination,
                    departureDate=departure_date,
                    adults=adults,
                    currencyCode=currency,
                    max=25
                )
            # For round trips
            else:
                response = self.amadeus.shopping.flight_offers_search.get(
                    originLocationCode=origin,
                    destinationLocationCode=destination,
                    departureDate=departure_date,
                    returnDate=return_date,
                    adults=adults,
                    currencyCode=currency,
                    max=25
                )
            
            return response.data
            
        except ResponseError as error:
            print(f"Error searching flights: {error}")
            return []
    
    def get_detailed_flight_info(self, flight_offer: Dict) -> Dict:
        """
        Extract detailed information from a flight offer, including layovers,
        baggage allowances, and other important details.
        
        Args:
            flight_offer: A flight offer dictionary from Amadeus API
            
        Returns:
            Dictionary with user-friendly flight details
        """
        details = {
            "price": {},
            "segments": [],
            "baggage": {},
            "flight_type": "DIRECT",
            "total_duration": "",
        }
        
        # Extract price information
        if "price" in flight_offer:
            details["price"] = {
                "total": flight_offer["price"]["total"],
                "currency": flight_offer["price"]["currency"],
                "base": flight_offer["price"]["base"],
                "fees": flight_offer["price"].get("fees", []),
                "grand_total": flight_offer["price"]["grandTotal"] if "grandTotal" in flight_offer["price"] else flight_offer["price"]["total"]
            }
        
        # Process each itinerary (outbound, return)
        for itinerary in flight_offer["itineraries"]:
            segments_count = len(itinerary["segments"])
            if segments_count > 1:
                details["flight_type"] = "CONNECTING"
            
            total_duration = itinerary.get("duration", "")
            if total_duration:
                details["total_duration"] = total_duration
            
            # Process each segment in the itinerary
            for segment in itinerary["segments"]:
                segment_info = {
                    "departure": {
                        "airport": segment["departure"]["iataCode"],
                        "terminal": segment["departure"].get("terminal", ""),
                        "time": segment["departure"]["at"]
                    },
                    "arrival": {
                        "airport": segment["arrival"]["iataCode"],
                        "terminal": segment["arrival"].get("terminal", ""),
                        "time": segment["arrival"]["at"]
                    },
                    "duration": segment.get("duration", ""),
                    "flight_number": f"{segment['carrierCode']} {segment['number']}",
                    "operating_carrier": segment.get("operating", {}).get("carrierCode", segment["carrierCode"])
                }
                details["segments"].append(segment_info)
        
        # Extract baggage allowance information
        if "travelerPricings" in flight_offer:
            for traveler in flight_offer["travelerPricings"]:
                baggage_info = {}
                
                # Check for included checked bags
                if "includedCheckedBags" in traveler:
                    checked_bags = traveler["includedCheckedBags"]
                    baggage_info["checked"] = {
                        "quantity": checked_bags.get("quantity", 0),
                        "weight": checked_bags.get("weight", 0),
                        "weightUnit": checked_bags.get("weightUnit", "")
                    }
                else:
                    baggage_info["checked"] = {"quantity": 0, "included": False}
                
                # Carry-on information (not always explicitly provided)
                baggage_info["cabin"] = {"included": True}  # Default assumption
                
                details["baggage"][f"traveler_{traveler['travelerId']}"] = baggage_info
        
        return details
    
    def format_flight_for_display(self, flight_details: Dict) -> str:
        """
        Format flight details into a user-friendly display string.
        
        Args:
            flight_details: Processed flight details
            
        Returns:
            String representation of flight details
        """
        display = []
        
        # Price information
        display.append(f"PRICE: {flight_details['price'].get('currency', 'USD')} {flight_details['price'].get('total', 'N/A')}")
        display.append(f"FLIGHT TYPE: {flight_details['flight_type']} | DURATION: {flight_details['total_duration']}")
        
        # Segment information
        display.append("\nFLIGHT SEGMENTS:")
        for idx, segment in enumerate(flight_details['segments']):
            if idx > 0:
                display.append("  ↓  LAYOVER  ↓  ")
                
            display.append(f"  {segment['departure']['airport']} ({segment['departure']['time']}) → "
                         f"{segment['arrival']['airport']} ({segment['arrival']['time']})")
            display.append(f"  Flight: {segment['flight_number']} | Duration: {segment['duration']}")
        
        # Baggage information
        display.append("\nBAGGAGE INFORMATION:")
        for traveler_id, baggage in flight_details['baggage'].items():
            checked_bags = baggage.get('checked', {})
            display.append(f"  Checked bags: {checked_bags.get('quantity', 0)} included")
            display.append(f"  Cabin baggage: {'Included' if baggage.get('cabin', {}).get('included', False) else 'Not included'}")
        
        return "\n".join(display)

    def flight_price_quote(self, flight_offer: Dict) -> Dict:
        """
        Get a confirmed price quote for a flight offer.
        
        Args:
            flight_offer: Flight offer from search results
            
        Returns:
            Price quote information
        """
        try:
            response = self.amadeus.shopping.flight_offers.pricing.post(
                flight_offer
            )
            return response.data
        except ResponseError as error:
            print(f"Error getting price quote: {error}")
            return {}
    
    def create_flight_order(self, flight_offer: Dict, travelers: List[Dict]) -> Dict:
        """
        Create a flight order (booking) but don't confirm payment.
        
        Args:
            flight_offer: Flight offer to book
            travelers: List of traveler information dictionaries
            
        Returns:
            Order creation response
        """
        try:
            # Example booking structure
            booking_data = {
                "data": {
                    "type": "flight-order",
                    "flightOffers": [flight_offer],
                    "travelers": travelers,
                    "remarks": {
                        "general": [
                            {
                                "subType": "GENERAL_MISCELLANEOUS",
                                "text": "TEST BOOKING - DO NOT PROCESS PAYMENT"
                            }
                        ]
                    },
                    "ticketingAgreement": {
                        "option": "DELAY_TO_CANCEL",
                        "delay": "24H"
                    },
                    "contacts": [
                        {
                            "addresseeName": {
                                "firstName": travelers[0]["name"]["firstName"],
                                "lastName": travelers[0]["name"]["lastName"]
                            },
                            "companyName": "DUMMY COMPANY",
                            "purpose": "STANDARD",
                            "phones": [
                                {
                                    "deviceType": "MOBILE",
                                    "countryCallingCode": "1",
                                    "number": "5555555555"
                                }
                            ],
                            "emailAddress": "test@example.com",
                            "address": {
                                "lines": ["123 Test Street"],
                                "postalCode": "10000",
                                "cityName": "New York",
                                "countryCode": "US"
                            }
                        }
                    ]
                }
            }
            
            print("Creating flight order (test only, no actual booking)...")
            # In a real implementation, you would call:
            # response = self.amadeus.booking.flight_orders.post(booking_data)
            # return response.data
            
            # For testing purposes, we'll return a mock response:
            return {
                "id": "mock-order-id-123456",
                "status": "UNCONFIRMED",
                "flightOffers": [flight_offer],
                "travelers": travelers,
                "message": "This is a mock order creation response for testing"
            }
            
        except ResponseError as error:
            print(f"Error creating order: {error}")
            return {}

    def collect_traveler_info(self) -> List[Dict]:
        """
        Interactive function to collect traveler information from user input.
        
        Returns:
            List of traveler dictionaries formatted for Amadeus API
        """
        travelers = []
        
        while True:
            print("\n--- Traveler Information ---")
            id = str(len(travelers) + 1)
            
            traveler = {
                "id": id,
                "dateOfBirth": "",
                "name": {"firstName": "", "lastName": ""},
                "gender": "",
                "contact": {"emailAddress": "", "phones": []},
                "documents": []
            }
            
            # Collect basic info
            traveler["name"]["firstName"] = input("First Name: ")
            traveler["name"]["lastName"] = input("Last Name: ")
            
            # Date of birth
            while True:
                dob = input("Date of Birth (YYYY-MM-DD): ")
                try:
                    # Validate date format
                    datetime.strptime(dob, "%Y-%m-%d")
                    traveler["dateOfBirth"] = dob
                    break
                except ValueError:
                    print("Invalid date format. Please use YYYY-MM-DD.")
            
            # Gender
            gender = input("Gender (M/F): ").upper()
            traveler["gender"] = "MALE" if gender == "M" else "FEMALE"
            
            # Contact info
            traveler["contact"]["emailAddress"] = input("Email Address: ")
            
            # Phone number
            phone = {
                "deviceType": "MOBILE",
                "countryCallingCode": input("Phone Country Code (e.g., 1 for US): "),
                "number": input("Phone Number (without country code): ")
            }
            traveler["contact"]["phones"].append(phone)
            
            # Document (passport)
            document = {
                "documentType": "PASSPORT",
                "birthPlace": input("Birth Place (City): "),
                "issuanceLocation": input("Passport Issuance Location: "),
                "issuanceDate": input("Passport Issuance Date (YYYY-MM-DD): "),
                "number": input("Passport Number: "),
                "expiryDate": input("Passport Expiry Date (YYYY-MM-DD): "),
                "issuanceCountry": input("Passport Issuance Country Code (e.g., US): "),
                "validityCountry": input("Passport Validity Country Code (e.g., US): "),
                "nationality": input("Nationality (Country Code, e.g., US): "),
                "holder": True
            }
            traveler["documents"].append(document)
            
            travelers.append(traveler)
            
            if input("\nAdd another traveler? (y/n): ").lower() != 'y':
                break
                
        return travelers

    def interactive_flight_booking(self):
        """
        Run an interactive flight booking process with the user.
        """
        print("=== FLIGHT BOOKING ASSISTANT ===")
        print("Let's help you find and book a flight!\n")
        
        # Step 1: Collect flight search parameters
        origin = input("Origin airport code (e.g., JFK, LAX): ").upper()
        destination = input("Destination airport code (e.g., LHR, CDG): ").upper()
        
        # Validate and collect departure date
        while True:
            departure_date = input("Departure date (YYYY-MM-DD): ")
            try:
                # Validate date format
                departure_datetime = datetime.strptime(departure_date, "%Y-%m-%d")
                # Make sure date is in the future
                if departure_datetime < datetime.now():
                    print("Departure date must be in the future.")
                    continue
                break
            except ValueError:
                print("Invalid date format. Please use YYYY-MM-DD.")
        
        # Check if round trip
        is_round_trip = input("Is this a round trip? (y/n): ").lower() == 'y'
        return_date = None
        
        if is_round_trip:
            while True:
                return_date = input("Return date (YYYY-MM-DD): ")
                try:
                    # Validate date format and ensure it's after departure date
                    return_datetime = datetime.strptime(return_date, "%Y-%m-%d")
                    if return_datetime < departure_datetime:
                        print("Return date must be after departure date.")
                        continue
                    break
                except ValueError:
                    print("Invalid date format. Please use YYYY-MM-DD.")
        
        # Number of passengers
        while True:
            try:
                adults = int(input("Number of adult passengers: "))
                if adults < 1:
                    print("Must have at least 1 passenger.")
                    continue
                break
            except ValueError:
                print("Please enter a valid number.")
        
        # Currency preference
        currency = input("Preferred currency (e.g., USD, EUR) [default: USD]: ").upper() or "USD"
        
        # Step 2: Search for flights
        print("\nSearching for flights. This may take a moment...")
        flight_offers = self.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
            currency=currency
        )
        
        if not flight_offers:
            print("No flights found matching your criteria. Please try again with different parameters.")
            return
        
        print(f"\nFound {len(flight_offers)} flights matching your criteria.")
        
        # Step 3: Display flight options to user
        for idx, offer in enumerate(flight_offers[:10], 1):  # Limit to 10 options for display
            detailed_info = self.get_detailed_flight_info(offer)
            print(f"\n--- FLIGHT OPTION {idx} ---")
            print(self.format_flight_for_display(detailed_info))
        
        # Step 4: Let user select a flight
        while True:
            try:
                selection = int(input("\nSelect a flight number (1-10) or 0 to exit: "))
                if selection == 0:
                    return
                if 1 <= selection <= min(10, len(flight_offers)):
                    selected_flight = flight_offers[selection-1]
                    break
                print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Step 5: Confirm price (in a real scenario, this would check for price changes)
        print("\nConfirming price and availability...")
        # price_quote = self.flight_price_quote(selected_flight)  # Use in real implementation
        
        # Step 6: Collect traveler information
        print("\nNow, let's collect traveler information for the booking.")
        travelers = self.collect_traveler_info()
        
        # Step 7: Review booking details
        print("\n=== BOOKING REVIEW ===")
        detailed_flight = self.get_detailed_flight_info(selected_flight)
        print(self.format_flight_for_display(detailed_flight))
        
        print("\nTRAVELER INFORMATION:")
        for traveler in travelers:
            print(f"  {traveler['name']['firstName']} {traveler['name']['lastName']}")
        
        # Step 8: Confirm booking (without payment)
        if input("\nConfirm booking? (y/n): ").lower() == 'y':
            # Create the order
            booking_result = self.create_flight_order(selected_flight, travelers)
            
            print("\n=== BOOKING CONFIRMATION ===")
            print(f"Booking Reference: {booking_result.get('id', 'N/A')}")
            print(f"Status: {booking_result.get('status', 'N/A')}")
            print("\nNOTE: This is a test booking only, no actual reservation has been made.")
            print("In a real implementation, you would proceed to payment here.")
        else:
            print("\nBooking cancelled.")

def main():
    """Main function to run the Amadeus flight API test."""
    # Get API credentials from environment variables or prompt user
    load_dotenv()
    api_key = os.getenv("AMADEUS_API_KEY")
    api_secret = os.getenv("AMADEUS_API_SECRET")
    
    if not api_key:
        api_key = input("Enter your Amadeus API Key: ")
    if not api_secret:
        api_secret = input("Enter your Amadeus API Secret: ")
    
    if not api_key or not api_secret:
        print("API credentials are required to continue.")
        sys.exit(1)
    
    # Initialize the API client
    flight_api = AmadeusFlightAPI(api_key, api_secret)
    
    # Start the interactive booking process
    flight_api.interactive_flight_booking()

if __name__ == "__main__":
    main()