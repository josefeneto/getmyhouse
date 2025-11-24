"""
Site Discovery Agent - Dynamically discovers real estate websites.

This agent uses web search to find relevant property listing websites
for a given country/location, demonstrating ADK's multi-agent capabilities.

Author: José Neto
Course: 5-Day AI Agents Intensive with Google ADK
Date: November 2024
"""

import logging
import json
import re
from typing import Dict, List, Optional

from google.genai import Client
from google.genai.types import GenerateContentConfig, Tool, GoogleSearch as GoogleSearchTool

from src.config import ADKConfig

logger = logging.getLogger(__name__)


class SiteDiscoveryAgent:
    """
    Agent responsible for discovering relevant real estate websites
    for a given location dynamically using web search.
    """
    
    def __init__(self):
        """Initialize the Site Discovery Agent."""
        self.client = Client(api_key=ADKConfig.GOOGLE_API_KEY)
        self.model_name = ADKConfig.MODEL_NAME
        logger.info(f"✅ SiteDiscoveryAgent initialized with model={self.model_name}")
    
    async def discover_sites(
        self,
        country: str,
        location: Optional[str] = None,
        max_sites: int = 5
    ) -> Dict[str, List[Dict]]:
        """
        Discover the best real estate websites for the given location.
        
        Args:
            country: Country name (e.g., "Portugal", "Spain")
            location: Optional specific city/region
            max_sites: Maximum number of sites to discover
            
        Returns:
            Dictionary with 'national_sites' and 'regional_sites' lists
        """
        logger.info(f"🔍 Starting site discovery for {country}" + 
                   (f" - {location}" if location else ""))
        
        try:
            # Build search query
            query = self._build_search_query(country, location)
            
            # Build prompt
            prompt = f"""Find the top {max_sites} real estate property listing websites for:
- Country: {country}
- Location: {location if location else "Nationwide"}

Return ONLY valid JSON with this structure:
{{
  "national_sites": [
    {{"name": "Site Name", "domain": "example.com", "relevance_score": 0.95}}
  ],
  "regional_sites": []
}}

Focus on major property portals like Idealista, Rightmove, Zillow equivalents."""
            
            # Call LLM with Google Search
            # Use google_search field (not google_search_retrieval!)
            config = GenerateContentConfig(
                temperature=0.2,
                tools=[Tool(google_search=GoogleSearchTool())],  # Correct field!
                response_modalities=["TEXT"]
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            
            # Parse response
            discovered_sites = self._parse_discovery_response(response.text)
            
            # Log results
            national_count = len(discovered_sites.get('national_sites', []))
            regional_count = len(discovered_sites.get('regional_sites', []))
            logger.info(
                f"✅ Discovery complete: {national_count} national + {regional_count} regional sites"
            )
            
            return discovered_sites
            
        except Exception as e:
            logger.error(f"❌ Site discovery failed: {str(e)}")
            # Return fallback for the country
            return self._get_fallback_sites(country)
    
    def _build_search_query(
        self,
        country: str,
        location: Optional[str]
    ) -> str:
        """Build search query for discovering sites."""
        query = f"best real estate property listing websites {country}"
        if location:
            query += f" {location}"
        return query
    
    def _parse_discovery_response(self, response_text: str) -> Dict[str, List[Dict]]:
        """Parse LLM response into structured site data."""
        try:
            # Extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON directly
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                json_str = json_match.group(0) if json_match else response_text
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Validate structure
            if 'national_sites' not in data:
                data['national_sites'] = []
            if 'regional_sites' not in data:
                data['regional_sites'] = []
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to parse discovery response: {str(e)}")
            raise
    
    def _get_fallback_sites(self, country: str) -> Dict[str, List[Dict]]:
        """Provide fallback site lists when discovery fails."""
        fallback_sites = {
            "Portugal": {
                "national_sites": [
                    {"name": "Idealista", "domain": "idealista.pt", "relevance_score": 0.95},
                    {"name": "Imovirtual", "domain": "imovirtual.com", "relevance_score": 0.90},
                    {"name": "Supercasa", "domain": "supercasa.pt", "relevance_score": 0.75}
                ],
                "regional_sites": []
            },
            "Spain": {
                "national_sites": [
                    {"name": "Idealista", "domain": "idealista.com", "relevance_score": 0.95},
                    {"name": "Fotocasa", "domain": "fotocasa.es", "relevance_score": 0.85}
                ],
                "regional_sites": []
            },
            "United Kingdom": {
                "national_sites": [
                    {"name": "Rightmove", "domain": "rightmove.co.uk", "relevance_score": 0.95},
                    {"name": "Zoopla", "domain": "zoopla.co.uk", "relevance_score": 0.90}
                ],
                "regional_sites": []
            }
        }
        
        result = fallback_sites.get(country, {"national_sites": [], "regional_sites": []})
        logger.warning(f"⚠️  Using fallback sites for {country}")
        return result


def create_discovery_agent() -> SiteDiscoveryAgent:
    """Factory function to create a site discovery agent."""
    return SiteDiscoveryAgent()
