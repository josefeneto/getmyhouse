"""
Mock Search Tool - Provides realistic property data for MVP phase.

This tool generates mock Portuguese property data to enable development
and testing without requiring real web scraping infrastructure.

Based on Google ADK Day 2 concepts: Custom tools with structured outputs.
"""

import logging
import random
from typing import Any, Dict, List, Optional

from src.config import MockDataConfig, SearchConfig

# Configure logging
logger = logging.getLogger(__name__)


class MockSearchTool:
    """
    Mock property search tool for MVP development.
    
    Generates realistic Portuguese property data matching search criteria.
    This tool is used during the MVP phase before real web scraping is implemented.
    """
    
    def __init__(self, country: str = "Portugal"):
        """
        Initialize the mock search tool.
        
        Args:
            country: Country for which to generate mock properties (default: Portugal)
        """
        self._current_country = country
        self._properties = self._generate_mock_properties(country)
        logger.info(f"Mock search tool initialized with {len(self._properties)} properties for {country}")
    
    def _get_cities_for_country(self, country: str) -> List[str]:
        """
        Get mock cities for a given country.
        
        Args:
            country: Country name
            
        Returns:
            List of city names for the country
        """
        # Check if country has predefined cities
        if country in MockDataConfig.MOCK_CITIES_BY_COUNTRY:
            return MockDataConfig.MOCK_CITIES_BY_COUNTRY[country]
        
        # Fallback: generate generic city names
        logger.debug(f"No predefined cities for {country}, using generic fallback")
        return [
            f"{country} - City Center",
            f"{country} - North District",
            f"{country} - South District", 
            f"{country} - East District",
            f"{country} - West District",
            f"{country} - Downtown",
            f"{country} - Suburban Area A",
            f"{country} - Suburban Area B",
            f"{country} - Metropolitan Zone",
            f"{country} - Coastal Region"
        ]
    
    def _generate_mock_properties(self, country: str = "Portugal") -> List[Dict[str, Any]]:
        """
        Generate a pool of mock properties for the specified country with balanced distribution.
        
        Args:
            country: Country for which to generate properties (default: Portugal)
        
        Ensures good coverage of all property types, typologies, and price ranges
        for better search results.
        
        Returns:
            List of mock property dictionaries
        """
        properties = []
        
        # Get cities for this country
        cities = self._get_cities_for_country(country)
        
        # Generate properties for each city with balanced distribution
        for city in cities:
            # Generate properties ensuring coverage of all types and typologies
            # Split generation: 50% flats, 50% houses
            # Within each, distribute typologies evenly
            
            flats_count = MockDataConfig.PROPERTIES_PER_CITY // 2
            houses_count = MockDataConfig.PROPERTIES_PER_CITY - flats_count
            
            # Generate flats with balanced typology distribution
            typologies = SearchConfig.TYPOLOGIES
            typology_cycle_flats = typologies * (flats_count // len(typologies) + 1)
            for i in range(flats_count):
                typology = typology_cycle_flats[i % len(typology_cycle_flats)]
                prop = self._generate_single_property(city, "flat", typology)
                properties.append(prop)
            
            # Generate houses with balanced typology distribution
            typology_cycle_houses = typologies * (houses_count // len(typologies) + 1)
            for i in range(houses_count):
                typology = typology_cycle_houses[i % len(typology_cycle_houses)]
                prop = self._generate_single_property(city, "house", typology)
                properties.append(prop)
        
        logger.debug(f"Generated {len(properties)} mock properties with balanced distribution")
        return properties
    
    def _generate_single_property(self, city: str, property_type: str = None, typology: str = None) -> Dict[str, Any]:
        """
        Generate a single mock property.
        
        Args:
            city: City name for the property
            property_type: Type of property (flat/house) - if None, chosen randomly
            typology: Typology (T0-T4+) - if None, chosen randomly
            
        Returns:
            Dictionary with property attributes
        """
        # Use provided or random typology
        if typology is None:
            typology = random.choice(SearchConfig.TYPOLOGIES)
        
        # Use provided or random property type
        if property_type is None:
            property_type = random.choice(SearchConfig.PROPERTY_TYPES)
        
        # Price based on typology
        price_range = MockDataConfig.PRICE_RANGES.get(typology, (100000, 300000))
        price = random.randint(price_range[0], price_range[1])
        
        # Number of WCs (typically 1-2 for T0-T2, 2-3 for T3+)
        if typology in ["T0", "T1"]:
            wcs = 1
        elif typology == "T2":
            wcs = random.choice([1, 2])
        else:
            wcs = random.choice([2, 3])
        
        # Usage state
        state = random.choice(SearchConfig.USAGE_STATES)
        
        # Transport distance (minutes walking)
        transport_distance = random.choice([5, 10, 15, 20, 30])
        
        # Generate location string
        # For Greater Lisbon area, include district
        if city in ["Lisboa", "Almada", "Barreiro", "Seixal", "Amadora", "Cascais"]:
            districts = ["Centro", "Norte", "Sul", "Oriente", "Ocidente"]
            location = f"{city}, {random.choice(districts)}, Setúbal"
        else:
            location = f"{city}, {city} District"
        
        # Mock agencies (real Portuguese agencies from config)
        agency = random.choice(MockDataConfig.MOCK_AGENCIES)
        
        # Generate mock URL
        url = f"https://www.{agency.lower().replace(' ', '')}.pt/property/{random.randint(100000, 999999)}"
        
        # Additional features (random selection)
        features = []
        possible_features = [
            "elevator", "parking", "balcony", "terrace", "garden",
            "swimming_pool", "air_conditioning", "central_heating",
            "double_glazing", "equipped_kitchen", "furnished"
        ]
        features = random.sample(possible_features, k=random.randint(2, 5))
        
        property_dict = {
            "id": f"MOCK-{random.randint(10000, 99999)}",
            "location": location,
            "city": city,
            "type": property_type,
            "typology": typology,
            "price": price,
            "wcs": wcs,
            "state": state,
            "transport_distance": transport_distance,
            "agency": agency,
            "url": url,
            "features": features,
            "area_m2": random.randint(40, 200),  # Square meters
            "year_built": random.randint(1960, 2024) if state != "brand new" else 2024,
            "energy_rating": random.choice(["A", "A+", "B", "B-", "C", "D"]),
        }
        
        return property_dict
    
    def search(
        self,
        country: str = "Portugal",  # NEW in v2.0.2
        location: Optional[str] = None,
        property_type: Optional[str] = None,
        typology: Optional[List[str]] = None,
        price_min: int = 0,
        price_max: int = 10000000,
        wcs: Optional[int] = None,
        usage_state: Optional[str] = None,
        transport_distance: Optional[int] = None,
        max_results: int = 20,  # NEW in v2.0
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search for properties matching criteria.
        
        Args:
            country: Country to search in (v2.0.2 - multi-country support)
            location: City or area to search in
            property_type: Type of property (house/flat)
            typology: List of typologies (T0, T1, T2, etc.)
            price_min: Minimum price in EUR
            price_max: Maximum price in EUR
            wcs: Number of WCs
            usage_state: Usage state (brand new, new, used, recovery)
            transport_distance: Maximum walking distance to transport (minutes)
            max_results: Maximum number of properties to return (v2.0)
            **kwargs: Additional search criteria
            
        Returns:
            List of matching properties (limited to max_results)
        """
        logger.info(f"Searching mock data: country={country}, location={location}, type={property_type}, typology={typology}, max_results={max_results}")
        
        # Regenerate properties if country changed (v2.0.2)
        if country != self._current_country:
            logger.info(f"Country changed from {self._current_country} to {country}, regenerating mock data")
            self._current_country = country
            self._properties = self._generate_mock_properties(country)
        
        # Start with all properties
        results = self._properties.copy()
        
        # Apply filters
        if location:
            results = [
                p for p in results
                if self._match_location(p["location"], location) or
                   self._match_location(p["city"], location)
            ]
            logger.debug(f"After location filter: {len(results)} properties")
        
        if property_type:
            results = [p for p in results if p["type"] == property_type]
            logger.debug(f"After type filter: {len(results)} properties")
        
        if typology:
            if isinstance(typology, str):
                typology = [typology]
            results = [p for p in results if p["typology"] in typology]
            logger.debug(f"After typology filter: {len(results)} properties")
        
        if price_min or price_max:
            results = [
                p for p in results
                if price_min <= p["price"] <= price_max
            ]
            logger.debug(f"After price filter: {len(results)} properties")
        
        if wcs:
            results = [p for p in results if p["wcs"] == wcs]
            logger.debug(f"After WC filter: {len(results)} properties")
        
        if usage_state:
            results = [p for p in results if p["state"] == usage_state]
            logger.debug(f"After state filter: {len(results)} properties")
        
        if transport_distance:
            results = [
                p for p in results
                if p["transport_distance"] <= transport_distance
            ]
            logger.debug(f"After transport filter: {len(results)} properties")
        
        logger.info(f"Mock search returned {len(results)} properties")
        
        # Shuffle to simulate real-world variation
        random.shuffle(results)
        
        # Limit to max_results (v2.0)
        if max_results and len(results) > max_results:
            logger.debug(f"Limiting results from {len(results)} to {max_results}")
            results = results[:max_results]
        
        return results
    
    def _match_location(self, property_location: str, search_location: str) -> bool:
        """
        Check if property location matches search location.
        
        Args:
            property_location: Property's location string
            search_location: Search query location
            
        Returns:
            True if locations match (case-insensitive, partial)
        """
        prop_loc = property_location.lower()
        search_loc = search_location.lower()
        
        # Check if search location is in property location
        return search_loc in prop_loc
    
    def search_properties(
        self,
        country: str = "Portugal",
        location: Optional[str] = None,
        property_type: Optional[str] = None,
        typology: Optional[List[str]] = None,
        price_min: int = 0,
        price_max: int = 10000000,
        wcs: Optional[int] = None,
        usage_state: Optional[str] = None,
        transport_distance: Optional[int] = None,
        max_results: int = 20,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Backward compatibility alias for search() method.
        
        This method exists to maintain compatibility with existing code
        that calls search_properties() instead of search().
        
        Args:
            Same as search() method
            
        Returns:
            List of matching properties (limited to max_results)
        """
        return self.search(
            country=country,
            location=location,
            property_type=property_type,
            typology=typology,
            price_min=price_min,
            price_max=price_max,
            wcs=wcs,
            usage_state=usage_state,
            transport_distance=transport_distance,
            max_results=max_results,
            **kwargs
        )
    
    def as_adk_tool(self):
        """
        Convert this tool to an ADK-compatible tool.
        
        Returns:
            Tool function that can be used by ADK agents
        """
        def mock_search_function(
            country: str = "Portugal",  # NEW in v2.0.2
            location: Optional[str] = None,
            property_type: Optional[str] = None,
            typology: Optional[str] = None,
            price_min: int = 0,
            price_max: int = 10000000,
            **kwargs
        ) -> str:
            """
            Mock property search tool.
            
            Searches a pre-generated database of properties for the specified country.
            
            Args:
                country: Country to search in (e.g., "Portugal", "Spain", "Italy")
                location: City or area (e.g., "Lisboa", "Madrid", "Rome")
                property_type: "house" or "flat"
                typology: Comma-separated list (e.g., "T2,T3")
                price_min: Minimum price in local currency
                price_max: Maximum price in local currency
                
            Returns:
                JSON string with matching properties
            """
            import json
            
            # Parse typology if comma-separated
            typology_list = None
            if typology:
                typology_list = [t.strip() for t in typology.split(",")]
            
            # Execute search
            results = self.search(
                country=country,  # NEW in v2.0.2
                location=location,
                property_type=property_type,
                typology=typology_list,
                price_min=price_min,
                price_max=price_max,
                **kwargs
            )
            
            # Return as JSON
            return json.dumps(results, ensure_ascii=False)
        
        return mock_search_function
    
    def get_property_by_id(self, property_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific property by ID.
        
        Args:
            property_id: Property ID
            
        Returns:
            Property dictionary or None if not found
        """
        for prop in self._properties:
            if prop["id"] == property_id:
                return prop
        
        return None
    
    def get_all_properties(self) -> List[Dict[str, Any]]:
        """
        Get all mock properties.
        
        Returns:
            List of all properties
        """
        return self._properties.copy()


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create mock tool
    tool = MockSearchTool()
    
    # Example search
    results = tool.search(
        location="Lisboa",
        property_type="flat",
        typology=["T2"],
        price_min=100000,
        price_max=200000
    )
    
    print(f"\nFound {len(results)} properties:")
    for prop in results[:5]:  # Show first 5
        print(f"  - {prop['typology']} in {prop['city']}: €{prop['price']:,}")
