"""
Test script for web scrapers.

Tests the new direct scraping functionality.

Author: José Neto
Date: November 2024
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.scrapers import get_scraper_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_single_scraper():
    """Test a single scraper (Idealista)."""
    logger.info("=" * 60)
    logger.info("TEST 1: Single Scraper (Idealista)")
    logger.info("=" * 60)
    
    from src.scrapers.idealista import create_idealista_scraper
    
    scraper = create_idealista_scraper()
    
    properties = scraper.search_properties(
        location="Lisboa",
        property_type="flat",
        typology=["T2", "T3"],
        price_min=100000,
        price_max=300000,
        max_results=5
    )
    
    logger.info(f"\n✅ Found {len(properties)} properties")
    
    if properties:
        logger.info("\n📋 Sample property:")
        prop = properties[0]
        for key, value in prop.items():
            logger.info(f"  {key}: {value}")
    
    return len(properties) > 0


def test_registry_sequential():
    """Test registry with sequential execution."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Registry (Sequential)")
    logger.info("=" * 60)
    
    registry = get_scraper_registry()
    
    properties = registry.search_all_sites(
        country="Portugal",
        location="Lisboa",
        property_type="flat",
        typology=["T2"],
        price_min=150000,
        price_max=250000,
        max_results=5,
        parallel=False  # Sequential
    )
    
    logger.info(f"\n✅ Found {len(properties)} total properties")
    
    # Group by source
    by_source = {}
    for prop in properties:
        source = prop.get('source', 'Unknown')
        by_source[source] = by_source.get(source, 0) + 1
    
    logger.info("\n📊 Properties by source:")
    for source, count in by_source.items():
        logger.info(f"  {source}: {count} properties")
    
    return len(properties) > 0


def test_registry_parallel():
    """Test registry with parallel execution."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Registry (Parallel)")
    logger.info("=" * 60)
    
    registry = get_scraper_registry()
    
    import time
    start_time = time.time()
    
    properties = registry.search_all_sites(
        country="Portugal",
        location="Porto",
        property_type="flat",
        typology=["T2", "T3"],
        price_min=100000,
        price_max=300000,
        max_results=10,
        parallel=True  # Parallel
    )
    
    elapsed = time.time() - start_time
    
    logger.info(f"\n✅ Found {len(properties)} total properties")
    logger.info(f"⚡ Time: {elapsed:.2f} seconds")
    
    # Group by source
    by_source = {}
    for prop in properties:
        source = prop.get('source', 'Unknown')
        by_source[source] = by_source.get(source, 0) + 1
    
    logger.info("\n📊 Properties by source:")
    for source, count in by_source.items():
        logger.info(f"  {source}: {count} properties")
    
    return len(properties) > 0


def test_fallback():
    """Test fallback to mock data."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Fallback to Mock Data")
    logger.info("=" * 60)
    
    registry = get_scraper_registry()
    
    # Try a country with no scrapers
    properties = registry.search_all_sites(
        country="Luxembourg",  # No scrapers for Luxembourg
        location="Luxembourg City",
        property_type="flat",
        typology=["T2"],
        price_min=200000,
        price_max=400000,
        max_results=5,
    )
    
    logger.info(f"\n✅ Scrapers returned {len(properties)} properties")
    logger.info("💡 This should trigger mock data fallback in real app")
    
    return True


def main():
    """Run all tests."""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 SCRAPER TESTING SUITE")
    logger.info("=" * 60)
    
    tests = [
        ("Single Scraper", test_single_scraper),
        ("Registry Sequential", test_registry_sequential),
        ("Registry Parallel", test_registry_parallel),
        ("Fallback Test", test_fallback),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = "✅ PASS" if success else "⚠️  PARTIAL"
        except Exception as e:
            logger.error(f"\n❌ {test_name} failed: {str(e)}", exc_info=True)
            results[test_name] = "❌ FAIL"
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        logger.info(f"  {test_name}: {result}")
    
    # Overall result
    passed = sum(1 for r in results.values() if "✅" in r)
    total = len(results)
    
    logger.info(f"\n🎯 {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n✅ ALL TESTS PASSED! 🎉")
        return 0
    else:
        logger.info("\n⚠️  Some tests failed or had issues")
        return 1


if __name__ == "__main__":
    exit(main())
