"""
Filter Agent - Specialist agent for filtering and ranking properties.

This agent analyzes properties against user requirements and ranks them
by relevance, returning the top 10 matches.

Based on Google ADK Day 1 concepts: Specialized agents with focused responsibilities.
"""

import logging
from typing import Any, Dict, List

from google.adk.agents import LlmAgent

from src.config import ADKConfig, AgentConfig, SearchConfig

# Configure logging
logger = logging.getLogger(__name__)


class FilterAgent:
    """
    Specialist agent for property filtering and ranking.
    
    This agent:
    - Evaluates properties against user requirements
    - Calculates match scores (0.0 to 1.0)
    - Ranks properties by relevance
    - Returns top N properties (default: 10)
    """
    
    def __init__(self, model: str = ADKConfig.MODEL_NAME):
        """
        Initialize the filter agent.
        
        Args:
            model: Name of the LLM model to use
        """
        self.model = model
        self._agent = self._create_agent()
        
        logger.info("Filter agent initialized successfully")
    
    def _create_agent(self) -> LlmAgent:
        """
        Create the ADK LlmAgent instance.
        
        Returns:
            LlmAgent configured for filtering and ranking
        """
        agent = LlmAgent(
            name="property_filter",
            model=self.model,
            instruction=AgentConfig.FILTER_AGENT_INSTRUCTION,
            # Note: Temperature controlled by model in ADK
        )
        
        return agent
    
    async def filter_and_rank(
        self,
        properties: List[Dict[str, Any]],
        requirements: Dict[str, Any],
        max_results: int = SearchConfig.MAX_RESULTS,
    ) -> List[Dict[str, Any]]:
        """
        Filter and rank properties based on requirements.
        
        Args:
            properties: List of property dictionaries to filter
            requirements: User search requirements
            max_results: Maximum number of results to return
            
        Returns:
            List of top N ranked properties with match scores
        """
        logger.info(f"Filtering {len(properties)} properties")
        
        if not properties:
            logger.warning("No properties to filter")
            return []
        
        try:
            # Calculate match scores
            scored_properties = self._calculate_scores(properties, requirements)
            
            # Filter by minimum score
            filtered = [
                p for p in scored_properties
                if p.get("match_score", 0) >= SearchConfig.MIN_MATCH_SCORE
            ]
            
            logger.info(f"{len(filtered)} properties passed minimum score threshold")
            
            # Sort by score (descending)
            ranked = sorted(
                filtered,
                key=lambda p: p.get("match_score", 0),
                reverse=True
            )
            
            # Return top N
            top_properties = ranked[:max_results]
            
            logger.info(f"Returning top {len(top_properties)} properties")
            return top_properties
            
        except Exception as e:
            logger.error(f"Filtering failed: {str(e)}", exc_info=True)
            return []
    
    def _calculate_scores(
        self,
        properties: List[Dict[str, Any]],
        requirements: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Calculate match scores for all properties.
        
        The scoring algorithm considers:
        - Location match (exact > nearby)
        - Property type match (boolean)
        - Typology match (boolean)
        - Price range match (scaled score)
        - WC count match (bonus if specified)
        - Transport distance match (bonus if specified)
        - Usage state match (bonus if specified)
        
        Args:
            properties: List of properties to score
            requirements: Search requirements
            
        Returns:
            List of properties with added match_score field
        """
        scored_properties = []
        
        for prop in properties:
            score = self._calculate_single_score(prop, requirements)
            prop["match_score"] = round(score, 2)
            scored_properties.append(prop)
        
        return scored_properties
    
    def _calculate_single_score(
        self,
        property_data: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> float:
        """
        Calculate match score for a single property.
        
        Args:
            property_data: Property information
            requirements: Search requirements
            
        Returns:
            Match score between 0.0 and 1.0
        """
        score = 0.0
        weights = {
            "location": 0.25,
            "property_type": 0.15,
            "typology": 0.20,
            "price": 0.25,
            "wcs": 0.05,
            "transport": 0.05,
            "usage_state": 0.05,
        }
        
        # Location match
        if "location" in requirements:
            if self._match_location(property_data.get("location", ""), requirements["location"]):
                score += weights["location"]
            else:
                # Partial match for nearby areas
                score += weights["location"] * 0.5
        
        # Property type match
        if "property_type" in requirements:
            if property_data.get("type") == requirements["property_type"]:
                score += weights["property_type"]
        
        # Typology match
        if "typology" in requirements:
            required_typologies = requirements["typology"]
            if isinstance(required_typologies, str):
                required_typologies = [required_typologies]
            
            if property_data.get("typology") in required_typologies:
                score += weights["typology"]
        
        # Price range match
        price = property_data.get("price", 0)
        price_min = requirements.get("price_min", 0)
        price_max = requirements.get("price_max", float('inf'))
        
        if price_min <= price <= price_max:
            # Full score if in range
            score += weights["price"]
        elif price < price_min:
            # Partial score if below (might be good deal)
            score += weights["price"] * 0.7
        else:
            # Lower score if above range
            score += weights["price"] * 0.3
        
        # WC count match (bonus)
        req_wcs = requirements.get("wcs")
        if req_wcs is not None and req_wcs != "any":
            if property_data.get("wcs") == req_wcs:
                score += weights["wcs"]
        else:
            # Give half weight if not specified
            score += weights["wcs"] * 0.5
        
        # Transport distance match (bonus)
        req_transport = requirements.get("public_transport")
        if req_transport is not None and req_transport != "any":
            prop_transport = property_data.get("transport_distance", float('inf'))
            
            # Convert req_transport to int if it's a string
            try:
                req_transport_int = int(req_transport) if isinstance(req_transport, str) else req_transport
                if prop_transport <= req_transport_int:
                    score += weights["transport"]
            except (ValueError, TypeError):
                # If conversion fails, give half weight
                score += weights["transport"] * 0.5
        else:
            score += weights["transport"] * 0.5
        
        # Usage state match (bonus)
        if "usage_state" in requirements:
            if property_data.get("state") == requirements["usage_state"]:
                score += weights["usage_state"]
        else:
            score += weights["usage_state"] * 0.5
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _match_location(self, property_location: str, required_location: str) -> bool:
        """
        Check if property location matches requirements.
        
        Args:
            property_location: Property's location string
            required_location: Required location from search
            
        Returns:
            True if locations match (case-insensitive)
        """
        prop_loc = property_location.lower().strip()
        req_loc = required_location.lower().strip()
        
        # Exact match
        if prop_loc == req_loc:
            return True
        
        # Partial match (property location contains required location)
        if req_loc in prop_loc:
            return True
        
        return False
    
    @property
    def agent(self) -> LlmAgent:
        """Get the underlying ADK LlmAgent instance."""
        return self._agent


def create_filter_agent(model: str = ADKConfig.MODEL_NAME) -> LlmAgent:
    """
    Factory function to create a filter agent.
    
    Args:
        model: LLM model name
        
    Returns:
        LlmAgent instance configured for filtering
    """
    filter_agent = FilterAgent(model=model)
    return filter_agent.agent


# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create filter agent
    agent = FilterAgent()
    
    # Example properties
    properties = [
        {
            "location": "Lisboa, Setúbal",
            "type": "flat",
            "typology": "T2",
            "price": 150000,
            "wcs": 1,
            "state": "used",
        },
        {
            "location": "Porto",
            "type": "house",
            "typology": "T3",
            "price": 250000,
            "wcs": 2,
            "state": "new",
        },
    ]
    
    requirements = {
        "location": "Lisboa",
        "property_type": "flat",
        "typology": ["T2"],
        "price_min": 100000,
        "price_max": 200000,
    }
    
    # Filter and rank
    results = asyncio.run(agent.filter_and_rank(properties, requirements))
    
    print(f"Filtered to {len(results)} properties")
    for prop in results:
        print(f"  - {prop['location']}: {prop['match_score']}")
