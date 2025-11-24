"""
Search Agent - Specialist agent for property searching.

This agent is responsible for executing property searches using available
tools (mock data or real web scrapers).

Based on Google ADK Day 2 concepts: Agent Tools and MCP integration.
"""

import logging
from typing import Any, Dict, List

from google.adk.agents import LlmAgent

from src.config import ADKConfig, AgentConfig, FeatureFlags
from src.tools.mock_search_tool import MockSearchTool

# Configure logging
logger = logging.getLogger(__name__)


class SearchAgent:
    """
    Specialist agent for property searching.
    
    This agent uses various tools to search for properties:
    - MockSearchTool: Provides mock data during MVP phase
    - RealScraperTool: Implements real web scraping (future)
    
    The agent intelligently selects tools based on configuration and
    handles errors gracefully with fallback mechanisms.
    """
    
    def __init__(self, model: str = ADKConfig.MODEL_NAME):
        """
        Initialize the search agent.
        
        Args:
            model: Name of the LLM model to use
        """
        self.model = model
        
        # Initialize tools
        self._tools = self._initialize_tools()
        
        # Create the agent
        self._agent = self._create_agent()
        
        logger.info("Search agent initialized successfully")
    
    def _initialize_tools(self) -> List:
        """
        Initialize search tools based on feature flags.
        
        In ADK, tools are simply Python functions. The framework
        automatically converts them to the appropriate tool format.
        
        Returns:
            List of tool functions
        """
        tools = []
        
        # Always include mock data tool (fallback)
        mock_tool = MockSearchTool()
        tools.append(mock_tool.as_adk_tool())
        
        # Add real scraper if enabled
        if FeatureFlags.ENABLE_REAL_SCRAPING:
            logger.info("Real scraping enabled - initializing web scraper tool")
            # TODO: Import and initialize RealScraperTool
            # from src.tools.web_scraper_tool import RealScraperTool
            # real_tool = RealScraperTool()
            # tools.append(real_tool.as_adk_tool())
        
        logger.info(f"Initialized {len(tools)} search tool(s)")
        return tools
    
    def _create_agent(self) -> LlmAgent:
        """
        Create the ADK LlmAgent instance.
        
        Returns:
            LlmAgent configured for property searching
        """
        agent = LlmAgent(
            name="property_search",
            model=self.model,
            instruction=AgentConfig.SEARCH_AGENT_INSTRUCTION,
            tools=self._tools,
            # Note: Temperature is controlled by model parameter in ADK
        )
        
        return agent
    
    async def search(
        self,
        country: str,  # NEW in v2.0.2
        location: str,
        property_type: str,
        typology: List[str],
        price_min: int = 0,
        price_max: int = 1000000,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search for properties matching criteria.
        
        Args:
            country: Country to search in (v2.0.2)
            location: City or area to search in
            property_type: Type of property (house/flat)
            typology: List of typologies (T0, T1, T2, etc.)
            price_min: Minimum price in local currency
            price_max: Maximum price in local currency
            **kwargs: Additional search criteria
            
        Returns:
            List of property dictionaries matching criteria
        """
        logger.info(f"Searching for {property_type} in {location}, {country}")
        logger.debug(f"Search criteria: typology={typology}, price={price_min}-{price_max}")
        
        try:
            # Format search query for agent
            query = self._format_query(
                country, location, property_type, typology,
                price_min, price_max, **kwargs
            )
            
            # Execute agent
            response = await self._agent.run(query)
            
            # Parse and return results
            properties = self._parse_response(response)
            
            logger.info(f"Search completed. Found {len(properties)} properties")
            return properties
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}", exc_info=True)
            # Return empty list on error
            return []
    
    def _format_query(
        self,
        country: str,  # NEW in v2.0.2
        location: str,
        property_type: str,
        typology: List[str],
        price_min: int,
        price_max: int,
        **kwargs
    ) -> str:
        """
        Format search criteria into a natural language query.
        
        Args:
            country: Country to search in (v2.0.2)
            location: Search location
            property_type: Type of property
            typology: List of typologies
            price_min: Minimum price
            price_max: Maximum price
            **kwargs: Additional criteria
            
        Returns:
            Formatted query string
        """
        typology_str = ", ".join(typology) if isinstance(typology, list) else typology
        
        query = f"""
        Search for properties with the following criteria:
        
        Country: {country}
        Location: {location}
        Property Type: {property_type}
        Typology: {typology_str}
        Price Range: €{price_min:,} - €{price_max:,}
        """
        
        # Add optional criteria
        if "distance" in kwargs:
            query += f"\nDistance to Location: {kwargs['distance']} km"
        
        if "wcs" in kwargs:
            query += f"\nNumber of WCs: {kwargs['wcs']}"
        
        if "usage_state" in kwargs:
            query += f"\nUsage State: {kwargs['usage_state']}"
        
        if "public_transport" in kwargs:
            query += f"\nPublic Transport: {kwargs['public_transport']} minutes walking"
        
        if "other_requirements" in kwargs and kwargs["other_requirements"]:
            query += f"\n\nAdditional Requirements:\n{kwargs['other_requirements']}"
        
        query += "\n\nReturn all properties that match these criteria as a structured list."
        
        return query.strip()
    
    def _parse_response(self, response: Any) -> List[Dict[str, Any]]:
        """
        Parse agent response into property list.
        
        Args:
            response: Agent response object
            
        Returns:
            List of property dictionaries
        """
        # TODO: Implement proper response parsing
        # For now, assume response contains property list in content
        logger.debug("Parsing agent response...")
        
        # Placeholder implementation
        if hasattr(response, 'content'):
            # Extract property data from response content
            # This will depend on how the tools return data
            pass
        
        return []
    
    @property
    def agent(self) -> LlmAgent:
        """Get the underlying ADK LlmAgent instance."""
        return self._agent


def create_search_agent(model: str = ADKConfig.MODEL_NAME) -> LlmAgent:
    """
    Factory function to create a search agent.
    
    Args:
        model: LLM model name
        
    Returns:
        LlmAgent instance configured for searching
    """
    search_agent = SearchAgent(model=model)
    return search_agent.agent


# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create search agent
    agent = SearchAgent()
    
    # Example search
    results = asyncio.run(agent.search(
        location="Lisboa",
        property_type="flat",
        typology=["T2"],
        price_min=100000,
        price_max=200000
    ))
    
    print(f"Found {len(results)} properties")
