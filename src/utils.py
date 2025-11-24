"""
Utility functions for GetMyHouse application.

This module provides helper functions for data formatting, validation,
and common operations across the application.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


# =============================================================================
# Data Formatting
# =============================================================================

def format_price(price: Union[int, float], currency: str = "EUR") -> str:
    """
    Format price with currency symbol.
    
    Args:
        price: Price value
        currency: Currency code (default: EUR)
        
    Returns:
        Formatted price string
        
    Example:
        >>> format_price(150000)
        '€150,000'
    """
    currency_symbols = {
        "EUR": "€",
        "USD": "$",
        "GBP": "£",
    }
    
    symbol = currency_symbols.get(currency, currency)
    return f"{symbol}{price:,.0f}"


def format_percentage(value: float) -> str:
    """
    Format value as percentage.
    
    Args:
        value: Value between 0 and 1
        
    Returns:
        Formatted percentage string
        
    Example:
        >>> format_percentage(0.95)
        '95%'
    """
    return f"{value * 100:.0f}%"


def format_area(area_m2: Union[int, float]) -> str:
    """
    Format area in square meters.
    
    Args:
        area_m2: Area in square meters
        
    Returns:
        Formatted area string
        
    Example:
        >>> format_area(120)
        '120 m²'
    """
    return f"{area_m2:.0f} m²"


def format_distance(distance_km: Union[int, float, str]) -> str:
    """
    Format distance in kilometers.
    
    Args:
        distance_km: Distance in kilometers
        
    Returns:
        Formatted distance string
        
    Example:
        >>> format_distance(5)
        '5 km'
        >>> format_distance('any')
        'any'
    """
    if isinstance(distance_km, str):
        return distance_km
    return f"{distance_km} km"


def format_timestamp(dt: datetime) -> str:
    """
    Format datetime as readable string.
    
    Args:
        dt: Datetime object
        
    Returns:
        Formatted datetime string
        
    Example:
        >>> format_timestamp(datetime.now())
        '2024-11-20 14:30:45'
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# =============================================================================
# Data Validation
# =============================================================================

def validate_price_range(price_min: int, price_max: int) -> tuple[bool, Optional[str]]:
    """
    Validate price range.
    
    Args:
        price_min: Minimum price
        price_max: Maximum price
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> validate_price_range(100000, 200000)
        (True, None)
        >>> validate_price_range(200000, 100000)
        (False, 'Minimum price cannot be greater than maximum price')
    """
    if price_min < 0:
        return False, "Minimum price cannot be negative"
    
    if price_max < 0:
        return False, "Maximum price cannot be negative"
    
    if price_min > price_max:
        return False, "Minimum price cannot be greater than maximum price"
    
    return True, None


def validate_location(location: str) -> tuple[bool, Optional[str]]:
    """
    Validate location string.
    
    Args:
        location: Location string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not location or not location.strip():
        return False, "Location cannot be empty"
    
    if len(location) < 2:
        return False, "Location must be at least 2 characters"
    
    # Check for valid characters (letters, spaces, hyphens, accents)
    if not re.match(r'^[a-zA-ZÀ-ÿ\s\-]+$', location):
        return False, "Location contains invalid characters"
    
    return True, None


def validate_typology(typology: Union[str, List[str]]) -> tuple[bool, Optional[str]]:
    """
    Validate typology selection.
    
    Args:
        typology: Typology string or list
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_typologies = ["T0", "T1", "T2", "T3", "T4", "T4+"]
    
    if isinstance(typology, str):
        typology = [typology]
    
    if not typology:
        return False, "At least one typology must be selected"
    
    for t in typology:
        if t not in valid_typologies:
            return False, f"Invalid typology: {t}"
    
    return True, None


# =============================================================================
# Data Transformation
# =============================================================================

def normalize_location(location: str) -> str:
    """
    Normalize location string for comparison.
    
    Args:
        location: Raw location string
        
    Returns:
        Normalized location string
        
    Example:
        >>> normalize_location("  LiSbOa  ")
        'lisboa'
    """
    return location.strip().lower()


def parse_typology_string(typology_str: str) -> List[str]:
    """
    Parse comma-separated typology string into list.
    
    Args:
        typology_str: Comma-separated typology string
        
    Returns:
        List of typology strings
        
    Example:
        >>> parse_typology_string("T2, T3, T4")
        ['T2', 'T3', 'T4']
    """
    if not typology_str:
        return []
    
    return [t.strip().upper() for t in typology_str.split(",") if t.strip()]


def convert_distance_to_km(distance: Union[int, float, str]) -> Optional[float]:
    """
    Convert distance value to kilometers.
    
    Args:
        distance: Distance value (can be int, float, or string like "5 km")
        
    Returns:
        Distance in kilometers, or None if 'any'
        
    Example:
        >>> convert_distance_to_km(5)
        5.0
        >>> convert_distance_to_km("5 km")
        5.0
        >>> convert_distance_to_km("any")
        None
    """
    if isinstance(distance, str):
        if distance.lower() == "any":
            return None
        # Try to extract number from string
        match = re.search(r'(\d+\.?\d*)', distance)
        if match:
            return float(match.group(1))
        return None
    
    return float(distance)


# =============================================================================
# Property Data Helpers
# =============================================================================

def extract_property_id(url: str) -> Optional[str]:
    """
    Extract property ID from URL.
    
    Args:
        url: Property URL
        
    Returns:
        Property ID or None
        
    Example:
        >>> extract_property_id("https://www.idealista.pt/property/123456")
        '123456'
    """
    match = re.search(r'/(\d+)/?$', url)
    if match:
        return match.group(1)
    return None


def summarize_features(features: List[str], max_features: int = 5) -> str:
    """
    Summarize property features list.
    
    Args:
        features: List of feature strings
        max_features: Maximum features to display
        
    Returns:
        Comma-separated features string
        
    Example:
        >>> summarize_features(['elevator', 'parking', 'balcony'], 2)
        'elevator, parking, +1 more'
    """
    if not features:
        return "N/A"
    
    if len(features) <= max_features:
        return ", ".join(features)
    
    displayed = features[:max_features]
    remaining = len(features) - max_features
    return f"{', '.join(displayed)}, +{remaining} more"


def calculate_price_per_sqm(price: int, area_m2: int) -> Optional[float]:
    """
    Calculate price per square meter.
    
    Args:
        price: Property price
        area_m2: Property area in square meters
        
    Returns:
        Price per square meter, or None if area is 0
        
    Example:
        >>> calculate_price_per_sqm(150000, 100)
        1500.0
    """
    if area_m2 <= 0:
        return None
    
    return round(price / area_m2, 2)


# =============================================================================
# Search Result Helpers
# =============================================================================

def filter_duplicate_properties(properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate properties from list.
    
    Duplicates are identified by matching location, typology, and price.
    
    Args:
        properties: List of property dictionaries
        
    Returns:
        List with duplicates removed
    """
    seen = set()
    unique_properties = []
    
    for prop in properties:
        # Create unique key from key attributes
        key = (
            prop.get("location", "").lower(),
            prop.get("typology", ""),
            prop.get("price", 0)
        )
        
        if key not in seen:
            seen.add(key)
            unique_properties.append(prop)
        else:
            logger.debug(f"Duplicate property filtered: {key}")
    
    return unique_properties


def sort_properties_by_score(
    properties: List[Dict[str, Any]],
    descending: bool = True
) -> List[Dict[str, Any]]:
    """
    Sort properties by match score.
    
    Args:
        properties: List of property dictionaries
        descending: Sort in descending order (highest score first)
        
    Returns:
        Sorted list of properties
    """
    return sorted(
        properties,
        key=lambda p: p.get("match_score", 0),
        reverse=descending
    )


def group_properties_by_typology(
    properties: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group properties by typology.
    
    Args:
        properties: List of property dictionaries
        
    Returns:
        Dictionary mapping typology to list of properties
    """
    groups = {}
    
    for prop in properties:
        typology = prop.get("typology", "Unknown")
        if typology not in groups:
            groups[typology] = []
        groups[typology].append(prop)
    
    return groups


# =============================================================================
# Error Handling
# =============================================================================

def format_error_message(error: Exception) -> str:
    """
    Format exception into user-friendly error message.
    
    Args:
        error: Exception object
        
    Returns:
        Formatted error message
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Map common errors to user-friendly messages
    error_mappings = {
        "ConnectionError": "Unable to connect to the service. Please check your internet connection.",
        "TimeoutError": "The search is taking too long. Please try again with more specific criteria.",
        "ValueError": "Invalid search parameters. Please check your input.",
        "KeyError": "Missing required information. Please ensure all fields are filled correctly.",
    }
    
    return error_mappings.get(error_type, f"An error occurred: {error_msg}")


# =============================================================================
# Logging Helpers
# =============================================================================

def log_search_params(params: Dict[str, Any]):
    """
    Log search parameters in a structured format.
    
    Args:
        params: Search parameters dictionary
    """
    logger.info("Search parameters:", extra={
        "location": params.get("location"),
        "property_type": params.get("property_type"),
        "typology": params.get("typology"),
        "price_range": f"{params.get('price_min', 0)}-{params.get('price_max', 0)}",
    })


def log_search_results(results: Dict[str, Any]):
    """
    Log search results summary.
    
    Args:
        results: Search results dictionary
    """
    num_properties = len(results.get("table_data", []))
    logger.info(f"Search completed: {num_properties} properties found")


# =============================================================================
# Export helpers
# =============================================================================

__all__ = [
    # Formatting
    "format_price",
    "format_percentage",
    "format_area",
    "format_distance",
    "format_timestamp",
    
    # Validation
    "validate_price_range",
    "validate_location",
    "validate_typology",
    
    # Transformation
    "normalize_location",
    "parse_typology_string",
    "convert_distance_to_km",
    
    # Property helpers
    "extract_property_id",
    "summarize_features",
    "calculate_price_per_sqm",
    
    # Search helpers
    "filter_duplicate_properties",
    "sort_properties_by_score",
    "group_properties_by_typology",
    
    # Error handling
    "format_error_message",
    
    # Logging
    "log_search_params",
    "log_search_results",
]
