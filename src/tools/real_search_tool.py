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
            # Build site filter for Google Search
            site_filter = " OR ".join([f"site:{s}" for s in sites])
            
            # Build search description
            typology_str = " or ".join(typology) if typology else "any size"
            type_str = "apartment" if property_type == "flat" else property_type
            
            # Build prompt for LLM
            prompt = f"""Search for properties to BUY (not rent) in {location}, {country}:

Property Type: {type_str}
Bedrooms/Typology: {typology_str}
Price Range: {price_min:,} - {price_max:,} {currency}

Search on these real estate websites: {site_filter}

Use Google Search to find property listings matching these criteria.
Extract property information from the search result SNIPPETS and URLs.

YOU MUST return ONLY a valid JSON array, nothing else.
Do NOT include explanations, markdown, or any text outside the JSON.

Return this EXACT format:
[
  {{
    "title": "Property title from search result",
    "price": 250000,
    "location": "City/area",
    "typology": "T2",
    "size_sqm": 85,
    "rooms": 2,
    "url": "https://full-url-from-search",
    "source": "Website name",
    "description": "Brief description"
  }}
]

CRITICAL RULES:
1. Return ONLY the JSON array - NO other text
2. Use REAL data from actual search results
3. URLs must be from actual search results
4. Return up to {max_results} properties
5. If no properties found, return []
6. Prices must be numeric (no currency symbols)
7. VALID JSON ONLY - test it before returning

Search now and return the JSON array."""
            
            # Call LLM with Google Search
            config = GenerateContentConfig(
                temperature=0.1,  # Low for factual extraction
                tools=[Tool(google_search=GoogleSearchTool())],  # Correct field!
                response_modalities=["TEXT"]
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            
            # Parse response
            response_text = response.text
            
            # Log response for debugging
            logger.debug(f"  LLM Response (first 500 chars): {response_text[:500]}")
            
            properties = self._extract_properties(response_text)
            
            return properties
            
        except Exception as e:
            logger.error(f"  ❌ Google Search failed: {str(e)}")
            return []
    
    def _extract_properties(self, response_text: str) -> List[Dict]:
        """
        Extract property data from LLM response.
        
        Args:
            response_text: LLM response with JSON
            
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
            for prop in properties:
                if isinstance(prop, dict) and "title" in prop and "price" in prop:
                    # Ensure required fields exist
                    if not prop.get("url"):
                        prop["url"] = "#"
                    if not prop.get("source"):
                        prop["source"] = "Web Search"
                    if not prop.get("typology"):
                        prop["typology"] = "Unknown"
                    if not prop.get("location"):
                        prop["location"] = "Unknown"
                    
                    valid_properties.append(prop)
            
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
