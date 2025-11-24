"""
Coordinator Agent - Root agent for GetMyHouse multi-agent system.

This agent orchestrates the entire property search workflow by coordinating
specialized agents for searching, filtering, and reporting.

Based on Google ADK Day 1 concepts: Multi-agent architecture with LlmAgent.
"""

import logging
from typing import Any, Dict, List, Optional

from google.adk.agents import LlmAgent

from src.config import ADKConfig, AgentConfig, SearchConfig, FeatureFlags
from src.agents.search_agent import create_search_agent
from src.agents.filter_agent import create_filter_agent
from src.agents.report_agent import create_report_agent

# Discovery Agent import (v2.0)
try:
    from src.agents.discovery_agent import create_discovery_agent
    DISCOVERY_AVAILABLE = True
except ImportError:
    DISCOVERY_AVAILABLE = False
    logger.warning("Discovery Agent not available - will use mock data only")

# Configure logging
logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """
    Root coordinator agent for GetMyHouse.
    
    Implements the multi-agent architecture pattern from ADK Day 1:
    - Uses LlmAgent for intelligent coordination
    - Orchestrates specialized agents as tools
    - Manages workflow execution
    - Maintains session context
    
    Architecture (MVP):
        For the MVP, the app.py handles the workflow directly:
        app.py → MockSearchTool → FilterAgent → ReportAgent → Results
        
        Future: Will use ParallelAgent and SequentialAgent for orchestration
    """
    
    def __init__(
        self,
        model: str = ADKConfig.MODEL_NAME,
        temperature: float = ADKConfig.TEMPERATURE,
    ):
        """
        Initialize the coordinator agent.
        
        Args:
            model: Name of the LLM model to use
            temperature: Temperature for LLM generation
        """
        self.model = model
        self.temperature = temperature
        
        # Initialize specialized agents
        logger.info("Initializing specialized agents...")
        self._search_agent = create_search_agent()
        self._filter_agent = create_filter_agent()
        self._report_agent = create_report_agent()
        
        # Create the root agent (coordinator)
        # Note: For MVP, we're not using workflow agents yet
        # The app.py handles the workflow directly
        self._agent = self._create_root_agent()
        
        logger.info("Coordinator agent initialized successfully")
    
    def _create_root_agent(self) -> LlmAgent:
        """
        Create the root LlmAgent that coordinates everything.
        
        In ADK, you can use agents directly as tools without wrapping them.
        
        Returns:
            LlmAgent configured as the root coordinator
        """
        # Use specialized agents directly as tools
        # No need for AgentTool wrapper - just pass agents directly
        agent = LlmAgent(
            name="coordinator",
            model=self.model,
            instruction=AgentConfig.COORDINATOR_INSTRUCTION,
            tools=[self._search_agent, self._filter_agent, self._report_agent],
            # Note: ADK doesn't accept generation_config dict
            # Temperature and other settings are handled by model parameter
        )
        
        return agent
    
    async def search_properties(
        self,
        user_requirements: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a property search based on user requirements.
        
        This is the main entry point for property searches. It coordinates
        the entire workflow: Search → Filter → Report.
        
        Args:
            user_requirements: Dictionary containing search criteria
            session_id: Optional session ID for context persistence
            
        Returns:
            Dictionary containing search results and metadata
            
        Example:
            >>> requirements = {
            ...     "location": "Lisboa",
            ...     "property_type": "flat",
            ...     "typology": ["T2", "T3"],
            ...     "price_min": 100000,
            ...     "price_max": 300000,
            ... }
            >>> results = await coordinator.search_properties(requirements)
        """
        logger.info(f"Starting property search with requirements: {user_requirements}")
        
        try:
            # Step 0: Discovery phase (v2.0)
            # Discovery runs if enabled, regardless of scraping mode
            discovered_sites = []
            if FeatureFlags.USE_DISCOVERY_AGENT and DISCOVERY_AVAILABLE:
                logger.info("🔍 Executing website discovery phase...")
                discovered_sites = await self._execute_discovery_phase(user_requirements)
                logger.info(f"✅ Discovered {len(discovered_sites)} websites")
            else:
                logger.info("⚠️  Discovery Agent disabled or unavailable, using mock data")
            
            # Step 1: Execute search phase (parallel)
            logger.debug("Executing parallel search phase...")
            search_results = await self._execute_search_phase(user_requirements, discovered_sites)
            
            # Step 2: Execute processing phase (sequential: filter → report)
            logger.debug("Executing sequential processing phase...")
            final_results = await self._execute_processing_phase(
                search_results,
                user_requirements
            )
            
            # Step 3: Add metadata
            final_results["metadata"] = {
                "session_id": session_id,
                "requirements": user_requirements,
                "status": "success",
            }
            
            logger.info(f"Search completed successfully. Found {len(final_results.get('properties', []))} properties")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error during property search: {str(e)}", exc_info=True)
            return {
                "properties": [],
                "error": str(e),
                "metadata": {
                    "session_id": session_id,
                    "requirements": user_requirements,
                    "status": "error",
                },
            }
    
    async def _execute_discovery_phase(
        self,
        requirements: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Execute the website discovery phase (v2.0).
        
        Uses Discovery Agent to dynamically find relevant real estate websites
        for the specified country/location.
        
        Args:
            requirements: Search criteria including country and location
            
        Returns:
            List of discovered website information dictionaries
        """
        try:
            if not DISCOVERY_AVAILABLE:
                logger.warning("Discovery agent not available")
                return []
            
            discovery_agent = create_discovery_agent()
            country = requirements.get("country", "Portugal")
            location = requirements.get("location")
            
            discovered = await discovery_agent.discover_sites(
                country=country,
                location=location,
                max_sites=5
            )
            
            # Flatten national and regional sites
            all_sites = discovered.get("national_sites", []) + discovered.get("regional_sites", [])
            
            logger.info(f"✅ Discovered {len(all_sites)} websites for {country}")
            return all_sites
            
        except Exception as e:
            logger.error(f"Discovery phase failed: {str(e)}")
            return []
    
    async def _execute_search_phase(
        self,
        requirements: Dict[str, Any],
        discovered_sites: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute the parallel search phase.
        
        Args:
            requirements: Search criteria
            discovered_sites: List of websites discovered by Discovery Agent
            
        Returns:
            List of raw property results from all sources
        """
        properties = []
        
        # Check if real scraping is enabled
        enable_real_scraping = FeatureFlags.ENABLE_REAL_SCRAPING
        
        if discovered_sites and len(discovered_sites) > 0:
            site_names = [site.get('name', 'Unknown') for site in discovered_sites[:3]]
            logger.info(f"🌐 Discovery Agent found {len(discovered_sites)} websites:")
            for i, site in enumerate(discovered_sites[:5], 1):
                logger.info(f"  {i}. {site.get('name', 'Unknown')} - {site.get('domain', 'N/A')}")
            
            if enable_real_scraping:
                logger.info(f"🔍 ENABLE_REAL_SCRAPING=true - Attempting real web scraping...")
                
                # Try real search tool
                try:
                    from src.tools.real_search_tool import RealSearchTool
                    real_tool = RealSearchTool()
                    
                    # Try to scrape each discovered site
                    for site in discovered_sites[:3]:  # Try top 3 sites
                        logger.info(f"  🌐 Attempting to scrape: {site.get('name')}...")
                        site_properties = real_tool.search_properties(
                            site_info=site,
                            requirements=requirements,
                            max_results=requirements.get("max_results", 20)
                        )
                        
                        if site_properties:
                            properties.extend(site_properties)
                            logger.info(f"  ✅ Found {len(site_properties)} properties from {site.get('name')}")
                        else:
                            logger.warning(f"  ⚠️  No properties scraped from {site.get('name')} (parsing not implemented)")
                    
                    if properties:
                        logger.info(f"✅ Real scraping returned {len(properties)} total properties")
                        return properties
                    else:
                        logger.warning("⚠️  Real scraping returned 0 properties - falling back to mock data")
                        logger.info("💡 Reason: Site-specific parsing not yet implemented for discovered websites")
                        logger.info("📦 Using mock data as fallback to provide results")
                
                except Exception as e:
                    logger.error(f"❌ Real scraping failed: {str(e)}")
                    logger.info("📦 Falling back to mock data")
            else:
                logger.info(f"📦 ENABLE_REAL_SCRAPING=false - Using mock data")
                logger.info(f"💡 To enable real scraping: Set ENABLE_REAL_SCRAPING=true in .env")
                logger.info(f"⚠️  Note: Real scraping requires site-specific parsers (not yet implemented)")
        else:
            logger.info(f"📦 No sites discovered - using mock data")
        
        # Fallback to mock data
        logger.info("🔄 Using MockSearchTool for stable results...")
        from src.tools.mock_search_tool import MockSearchTool
        mock_tool = MockSearchTool()
        
        properties = mock_tool.search_properties(
            country=requirements.get("country", "Portugal"),
            location=requirements.get("location"),
            property_type=requirements.get("property_type"),
            typology=requirements.get("typology"),
            price_min=requirements.get("price_min", 0),
            price_max=requirements.get("price_max", 1000000),
            max_results=requirements.get("max_results", 20)
        )
        
        logger.info(f"✅ Mock search returned {len(properties)} properties")
        
        return properties
    
    async def _execute_processing_phase(
        self,
        raw_properties: List[Dict[str, Any]],
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the sequential processing phase (filter → report).
        
        Args:
            raw_properties: Raw property data from search
            requirements: Original search requirements
            
        Returns:
            Formatted results with filtered and reported properties
        """
        # Step 1: Filter and rank properties
        filter_input = {
            "properties": raw_properties,
            "requirements": requirements,
            "max_results": SearchConfig.MAX_RESULTS,
        }
        
        filtered_response = await self._filter_agent.run(str(filter_input))
        filtered_properties = self._parse_filter_results(filtered_response)
        
        # Step 2: Generate report
        report_input = {
            "properties": filtered_properties,
            "requirements": requirements,
        }
        
        report_response = await self._report_agent.run(str(report_input))
        final_results = self._parse_report_results(report_response)
        
        return final_results
    
    def _format_search_query(self, requirements: Dict[str, Any]) -> str:
        """
        Format search requirements into a natural language query.
        
        Args:
            requirements: Search criteria dictionary
            
        Returns:
            Natural language search query
        """
        parts = []
        
        if "location" in requirements:
            parts.append(f"in {requirements['location']}")
        
        if "property_type" in requirements:
            parts.append(f"type: {requirements['property_type']}")
        
        if "typology" in requirements:
            typologies = requirements["typology"]
            if isinstance(typologies, list):
                typologies = ", ".join(typologies)
            parts.append(f"typology: {typologies}")
        
        if "price_min" in requirements or "price_max" in requirements:
            price_min = requirements.get("price_min", 0)
            price_max = requirements.get("price_max", "unlimited")
            parts.append(f"price: €{price_min} - €{price_max}")
        
        query = f"Search for properties {' '.join(parts)}"
        logger.debug(f"Formatted search query: {query}")
        
        return query
    
    def _parse_search_results(self, response: Any) -> List[Dict[str, Any]]:
        """
        Parse search agent response into property list.
        
        Args:
            response: Agent response object
            
        Returns:
            List of property dictionaries
        """
        # TODO: Implement proper parsing based on agent response structure
        # For now, return mock structure
        logger.debug("Parsing search results...")
        return []
    
    def _parse_filter_results(self, response: Any) -> List[Dict[str, Any]]:
        """
        Parse filter agent response into ranked property list.
        
        Args:
            response: Agent response object
            
        Returns:
            List of filtered and ranked property dictionaries
        """
        # TODO: Implement proper parsing based on agent response structure
        logger.debug("Parsing filter results...")
        return []
    
    def _parse_report_results(self, response: Any) -> Dict[str, Any]:
        """
        Parse report agent response into final results structure.
        
        Args:
            response: Agent response object
            
        Returns:
            Dictionary with formatted results
        """
        # TODO: Implement proper parsing based on agent response structure
        logger.debug("Parsing report results...")
        return {"properties": [], "summary": {}}
    
    async def refine_search(
        self,
        previous_requirements: Dict[str, Any],
        refinements: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Refine a previous search with updated criteria.
        
        Implements the search refinement feature by merging previous
        requirements with new refinements.
        
        Args:
            previous_requirements: Original search criteria
            refinements: Updated criteria to apply
            session_id: Optional session ID for context
            
        Returns:
            Dictionary containing refined search results
        """
        logger.info(f"Refining search with updates: {refinements}")
        
        # Merge requirements (refinements override previous)
        updated_requirements = {**previous_requirements, **refinements}
        
        # Execute new search with updated requirements
        return await self.search_properties(updated_requirements, session_id)
    
    @property
    def agent(self) -> LlmAgent:
        """Get the underlying ADK LlmAgent instance."""
        return self._agent


def create_coordinator_agent(
    model: str = ADKConfig.MODEL_NAME,
    temperature: float = ADKConfig.TEMPERATURE,
) -> CoordinatorAgent:
    """
    Factory function to create a coordinator agent.
    
    Args:
        model: LLM model name
        temperature: Temperature for generation
        
    Returns:
        CoordinatorAgent instance
    """
    return CoordinatorAgent(model=model, temperature=temperature)


# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create coordinator
    coordinator = create_coordinator_agent()
    
    # Example search
    requirements = {
        "location": "Lisboa",
        "property_type": "flat",
        "typology": ["T2"],
        "price_min": 100000,
        "price_max": 200000,
    }
    
    # Run search
    results = asyncio.run(coordinator.search_properties(requirements))
    print(f"Results: {results}")
