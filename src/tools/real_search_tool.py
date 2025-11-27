"""
Real Search Tool - Property search using LLM + Google Search.

This tool uses Gemini with Google Search to find real properties online.
NO HTML scraping needed - LLM extracts data from Google Search snippets!

Flow:
1. Discovery Agent finds real estate sites for country
2. LLM searches Google with site: filters  
3. LLM extracts property data from search result snippets
4. Returns structured property data

Author: José Neto
Date: November 2024
"""

import logging
import json
import re
from typing import Dict, List, Any

from google.genai import Client
from google.genai.types import GenerateContentConfig, Tool, GoogleSearch as GoogleSearchTool

from src.config import ADKConfig
from src.agents.discovery_agent import SiteDiscoveryAgent

logger = logging.getLogger(__name__)


class RealSearchTool:
    """
    Tool for searching real property listings using LLM + Google Search.
    
    This is the CORRECT approach:
    - Discovery Agent finds sites dynamically
    - Google Search finds property listings
    - LLM extracts data from search snippets (not HTML!)
    - Works for ANY country without hardcoded parsers
    """
    
    def __init__(self):
        """Initialize the real search tool."""
        self.client = Client(api_key=ADKConfig.GOOGLE_API_KEY)
        self.model_name = ADKConfig.MODEL_NAME
        self.discovery_agent = SiteDiscoveryAgent()
        logger.info("✅ RealSearchTool initialized with LLM + Google Search")
    
    async def search_properties(
        self,
        requirements: Dict[str, Any],
        max_results: int = 20
    ) -> List[Dict]:
        """
        Search for properties using Discovery + LLM + Google Search.
        
        Args:
            requirements: Search criteria dictionary
            max_results: Maximum number of results
            
        Returns:
            List of property dictionaries
        """
        country = requirements.get("country", "Portugal")
        location = requirements.get("location", "")
        property_type = requirements.get("property_type", "flat")
        typology = requirements.get("typology", [])
        price_min = requirements.get("price_min", 0)
        price_max = requirements.get("price_max", 1000000)
        currency = requirements.get("currency", "EUR")
        
        logger.info(f"🔍 Searching {country} - {location}...")
        
        try:
            # PHASE 1: Discover sites for this country
            logger.info(f"  📡 Phase 1: Discovering sites...")
            discovered = await self.discovery_agent.discover_sites(
                country=country,
                location=location,
                max_sites=5
            )
            
            # Extract site domains
            sites = []
            for site in discovered.get('national_sites', []):
                sites.append(site['domain'])
            for site in discovered.get('regional_sites', []):
                sites.append(site['domain'])
            
            if not sites:
                logger.warning(f"  ⚠️  No sites discovered for {country}")
                return []
            
            logger.info(f"  ✅ Discovered {len(sites)} sites: {sites}")
            
            # PHASE 2: Search properties using Google Search
            logger.info(f"  📡 Phase 2: Searching properties...")
            properties = await self._search_with_google(
                country=country,
                location=location,
                property_type=property_type,
                typology=typology,
                price_min=price_min,
                price_max=price_max,
                currency=currency,
                sites=sites,
                max_results=max_results
            )
            
            if properties:
                logger.info(f"  ✅ Found {len(properties)} REAL properties!")
                return properties
            else:
                logger.warning(f"  ⚠️  No properties found")
                return []
            
        except Exception as e:
            logger.error(f"❌ Real search failed: {str(e)}")
            return []
    
    async def _search_with_google(
        self,
        country: str,
        location: str,
        property_type: str,
        typology: List[str],
        price_min: int,
        price_max: int,
        currency: str,
        sites: List[str],
        max_results: int
    ) -> List[Dict]:
        """
        Search for properties using LLM + Google Search.
        
        LLM will:
        1. Use Google Search with site: filters
        2. Extract property data from search result SNIPPETS
        3. Return structured JSON
        
        No HTML scraping needed!
        """
        try:
            # Normalize location (Portuguese to English for better results)
            location_normalized = self._normalize_location(location, country)
            
            # Build site filter for Google Search
            site_filter = " OR ".join([f"site:{s}" for s in sites])
            
            # Build search description
            typology_str = " or ".join(typology) if typology else "any size"
            
            # Handle property_type "any"
            if property_type == "any":
                type_str = "apartment OR house OR flat"
            else:
                type_str = "apartment" if property_type == "flat" else property_type
            
            # Build prompt for LLM with VERY specific instructions
            prompt = f"""You are searching for real estate properties to BUY (NOT rent).

TARGET LOCATION: Search in BOTH "{location}" AND "{location_normalized}", {country}
- Try searches with BOTH location names
- Include nearby areas if needed to get {max_results}+ results

SEARCH CRITERIA:
- Property Type: {type_str}
- Bedrooms: {typology_str}
- Price Range: {price_min:,} - {price_max:,} {currency}
- Websites: {site_filter}

YOUR TASK:
1. Use Google Search to find AT LEAST {max_results} property listings
2. Extract information from the search result SNIPPETS ONLY
3. Return a JSON array of properties

CRITICAL - URLs:
- ONLY include a URL if you can see the COMPLETE, REAL property URL in the search snippet
- The URL MUST be a direct link to a specific property listing
- The URL MUST start with https:// and be from one of: {', '.join(sites)}
- If you're not 100% sure the URL is correct, set it to null
- DO NOT generate, guess, or construct URLs
- DO NOT use homepage URLs or search result URLs
- BETTER TO HAVE null URL than wrong URL

CRITICAL - Data Quality:
- Extract ONLY information you can see in the snippets
- Use null for fields not available in snippets
- DO NOT make up or guess any information
- If you find fewer than {max_results} properties with valid URLs, that's OK

OUTPUT FORMAT - Return ONLY valid JSON (no markdown, no text):
[
  {{
    "title": "Exact title from snippet",
    "price": 250000,
    "location": "City/neighborhood from snippet",
    "typology": "T2",
    "property_type": "flat",
    "size_sqm": 85,
    "rooms": 2,
    "wcs": 1,
    "usage_state": "used",
    "transport_minutes": null,
    "agency": "Agency name if visible",
    "url": "https://full-real-url-from-snippet-or-null",
    "source": "Website name",
    "description": "Brief description from snippet"
  }}
]

EXAMPLE GOOD URL: "https://www.idealista.pt/imovel/12345678/"
EXAMPLE BAD URL (set to null): "https://www.idealista.pt/", "https://example.com/property"

NOW: Search for properties and return ONLY the JSON array."""
            
            # Call LLM with Google Search
            config = GenerateContentConfig(
                temperature=0.1,  # Low for factual extraction
                tools=[Tool(google_search=GoogleSearchTool())],  # Correct field!
                response_modalities=["TEXT"]
            )
            
            logger.info(f"  📝 Search parameters:")
            logger.info(f"     Location: '{location}' → '{location_normalized}'")
            logger.info(f"     Type: '{property_type}' → '{type_str}'")
            logger.info(f"     Sites: {len(sites)} discovered")
            logger.info(f"     Max results: {max_results}")
            
            logger.info(f"  🤖 Calling LLM with Google Search (this may take 30-60 seconds)...")
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            
            # Parse response
            response_text = response.text
            
            # Log response for debugging
            logger.debug(f"  LLM Response (first 500 chars): {response_text[:500]}")
            
            properties = self._extract_properties(response_text, country, location)
            
            return properties
            
        except Exception as e:
            logger.error(f"  ❌ Google Search failed: {str(e)}")
            return []
    
    def _normalize_location(self, location: str, country: str) -> str:
        """
        Normalize location names to English for better search results.
        
        Many real estate sites use English names.
        
        Args:
            location: Original location name
            country: Country name
            
        Returns:
            Normalized (English) location name
        """
        # Common location mappings by country
        location_mappings = {
            "Portugal": {
                "lisboa": "lisbon",
                "porto": "porto",  # Already English
                "coimbra": "coimbra",  # Keep as is
                "braga": "braga",
                "setúbal": "setubal",
                "faro": "faro",
                "évora": "evora",
                "aveiro": "aveiro",
                "viseu": "viseu",
                "leiria": "leiria"
            },
            "Spain": {
                "madrid": "madrid",
                "barcelona": "barcelona",
                "valencia": "valencia",
                "sevilla": "seville",
                "zaragoza": "zaragoza",
                "málaga": "malaga",
                "murcia": "murcia",
                "palma": "palma"
            },
            "Italy": {
                "roma": "rome",
                "milano": "milan",
                "napoli": "naples",
                "torino": "turin",
                "palermo": "palermo",
                "genova": "genoa",
                "bologna": "bologna",
                "firenze": "florence",
                "venezia": "venice"
            },
            "France": {
                "paris": "paris",
                "marseille": "marseille",
                "lyon": "lyon",
                "toulouse": "toulouse",
                "nice": "nice",
                "nantes": "nantes",
                "strasbourg": "strasbourg",
                "montpellier": "montpellier",
                "bordeaux": "bordeaux"
            },
            "Germany": {
                "berlin": "berlin",
                "münchen": "munich",
                "hamburg": "hamburg",
                "köln": "cologne",
                "frankfurt": "frankfurt",
                "stuttgart": "stuttgart",
                "düsseldorf": "dusseldorf",
                "dortmund": "dortmund",
                "essen": "essen"
            }
        }
        
        # Normalize to lowercase for comparison
        location_lower = location.lower().strip()
        
        # Check if we have a mapping for this country
        if country in location_mappings:
            # Check if location needs normalization
            if location_lower in location_mappings[country]:
                normalized = location_mappings[country][location_lower]
                logger.info(f"  🌍 Normalized location: '{location}' → '{normalized}'")
                return normalized
        
        # Return original if no mapping found
        return location
    
    def _extract_properties(self, response_text: str, country: str, location: str) -> List[Dict]:
        """
        Extract property data from LLM response.
        
        Args:
            response_text: LLM response with JSON
            country: Country name for fallback search URLs
            location: Location name for fallback search URLs
            
        Returns:
            List of property dictionaries
        """
        try:
            if not response_text or not response_text.strip():
                logger.warning("  ⚠️  Empty response from LLM")
                return []
            
            # Log first part of response for debugging
            logger.info(f"  📄 Response preview: {response_text[:200]}...")
            
            # Remove markdown code blocks
            cleaned = re.sub(r'```json\s*', '', response_text)
            cleaned = re.sub(r'```\s*', '', cleaned)
            cleaned = cleaned.strip()
            
            # Try to find JSON array or object
            json_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Maybe it's an object with properties array
                json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    logger.error(f"  ❌ No JSON found in response")
                    logger.debug(f"  Response text: {cleaned[:500]}")
                    return []
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Extract array
            if isinstance(data, list):
                properties = data
            elif isinstance(data, dict):
                # Look for common keys
                for key in ['properties', 'results', 'listings', 'items']:
                    if key in data:
                        properties = data[key]
                        break
                else:
                    logger.warning("  ⚠️  Response is dict but no properties array found")
                    return []
            else:
                logger.warning("  ⚠️  Response is not list or dict")
                return []
            
            # Validate and clean properties
            valid_properties = []
            skipped_count = 0
            null_url_count = 0
            
            for prop in properties:
                if isinstance(prop, dict) and "title" in prop and "price" in prop:
                    # Ensure URL is valid OR null (we'll handle null later)
                    url = prop.get("url", None)
                    
                    # Accept null URLs (LLM wasn't sure)
                    if url is None or url == "null":
                        null_url_count += 1
                        # Create a search URL as fallback
                        search_query = f"{prop.get('title', '')} {prop.get('location', '')} {country}".replace(' ', '+')
                        prop["url"] = f"https://www.google.com/search?q={search_query}"
                        prop["url_type"] = "search"
                        logger.info(f"  🔍 Created search URL for: {prop.get('title', 'Unknown')[:50]}")
                    else:
                        # Strict URL validation for non-null URLs
                        if url == "#":
                            skipped_count += 1
                            logger.warning(f"  ⚠️  Skipped (# URL): {prop.get('title', 'Unknown')[:50]}")
                            continue
                        
                        if not url.startswith("http"):
                            skipped_count += 1
                            logger.warning(f"  ⚠️  Skipped (invalid protocol): {url[:50]}")
                            continue
                        
                        # Check if URL looks like a real property listing
                        if len(url) < 25:  # Real property URLs are longer
                            skipped_count += 1
                            logger.warning(f"  ⚠️  Skipped (URL too short): {url}")
                            continue
                        
                        # Check for common fake/generic URL patterns
                        fake_patterns = ["example.com", "test.com", "domain.com", "website.com"]
                        homepage_indicators = ["/search", "/comprar", "/buy", "/venda"]
                        
                        url_lower = url.lower()
                        if any(pattern in url_lower for pattern in fake_patterns):
                            skipped_count += 1
                            logger.warning(f"  ⚠️  Skipped (fake domain): {url[:50]}")
                            continue
                        
                        # Check if it's a homepage/search page (not specific property)
                        # Real property URLs have unique IDs or slugs
                        if url.rstrip('/').count('/') < 3:  # Too few path segments
                            # Could be homepage, convert to search
                            null_url_count += 1
                            search_query = f"{prop.get('title', '')} {prop.get('location', '')} {country}".replace(' ', '+')
                            prop["url"] = f"https://www.google.com/search?q={search_query}"
                            prop["url_type"] = "search"
                            logger.info(f"  🔍 Converted generic URL to search for: {prop.get('title', 'Unknown')[:50]}")
                        else:
                            prop["url_type"] = "direct"
                    
                    # Ensure required fields exist
                    if not prop.get("source"):
                        prop["source"] = "Web Search"
                    if not prop.get("typology"):
                        prop["typology"] = "Unknown"
                    if not prop.get("location"):
                        prop["location"] = "Unknown"
                    
                    # Ensure numeric fields are numeric or None
                    for field in ['price', 'size_sqm', 'rooms', 'wcs', 'transport_minutes']:
                        if field in prop and prop[field] is not None:
                            try:
                                prop[field] = float(prop[field]) if '.' in str(prop[field]) else int(prop[field])
                            except (ValueError, TypeError):
                                prop[field] = None
                    
                    valid_properties.append(prop)
            
            if skipped_count > 0:
                logger.info(f"  ⚠️  Skipped {skipped_count} properties with invalid URLs")
            if null_url_count > 0:
                logger.info(f"  🔍 Created {null_url_count} search URLs for properties without direct links")
            
            if valid_properties:
                logger.info(f"  ✅ Extracted {len(valid_properties)} valid properties")
            else:
                logger.warning(f"  ⚠️  No valid properties in response")
            
            return valid_properties
            
        except json.JSONDecodeError as e:
            logger.error(f"  ❌ Failed to parse JSON: {str(e)}")
            logger.debug(f"  Attempted to parse: {json_str[:200] if 'json_str' in locals() else cleaned[:200]}...")
            return []
        except Exception as e:
            logger.error(f"  ❌ Error extracting properties: {str(e)}")
            return []


def create_real_search_tool() -> RealSearchTool:
    """Factory function to create a real search tool."""
    return RealSearchTool()
