#!/usr/bin/env python3
"""
Test aggregator functionality, especially the filtering logic
"""
from aggregator import ScreeningAggregator
from scrapers.base import Screening, BaseScraper


def test_static_methods_work():
    """Test that BaseScraper static methods can be called without instance"""
    # Test _get_awards_data
    awards_data = BaseScraper._get_awards_data()
    assert len(awards_data) == 4, "Should return 4 elements (festival_films, oscar_contenders, festival_keywords, awards_keywords)"
    
    # Test is_festival_film
    result = BaseScraper.is_festival_film('Test Film', 'Premiered at Cannes')
    assert isinstance(result, bool), "Should return boolean"
    
    # Test is_awards_contender
    result = BaseScraper.is_awards_contender('Test Film', 'Oscar contender')
    assert isinstance(result, bool), "Should return boolean"
    
    # Test is_prestigious_film
    result = BaseScraper.is_prestigious_film('Random Movie', 'Just a regular movie')
    assert isinstance(result, bool), "Should return boolean"
    
    print("✓ All static method tests passed")


def test_aggregator_filtering():
    """Test that aggregator filtering works without trying to instantiate BaseScraper"""
    aggregator = ScreeningAggregator()
    
    # Create test screenings
    test_screenings = [
        Screening('The Substance', 'Film Forum', '2025-11-20', '7:00 PM', 'Cannes winner'),
        Screening('Random Movie', 'AMC', '2025-11-20', '7:00 PM', 'Regular screening'),
        Screening('Duplicate', 'AMC', '2025-11-20', '7:00 PM', 'Regular screening'),
        Screening('Duplicate', 'AMC', '2025-11-20', '7:00 PM', 'Regular screening'),
    ]
    
    # Test filter_and_deduplicate - this previously failed with TypeError
    try:
        filtered = aggregator.filter_and_deduplicate(test_screenings)
        assert isinstance(filtered, list), "Should return a list"
        print(f"✓ Aggregator filtering test passed ({len(filtered)} screenings filtered)")
    except TypeError as e:
        if "Can't instantiate abstract class" in str(e):
            raise AssertionError("Failed: Still trying to instantiate abstract BaseScraper class") from e
        raise


def test_basescraper_cannot_be_instantiated():
    """Test that BaseScraper remains abstract and cannot be instantiated"""
    try:
        scraper = BaseScraper("test")
        raise AssertionError("BaseScraper should not be instantiatable!")
    except TypeError as e:
        if "abstract" in str(e).lower():
            print("✓ BaseScraper correctly remains abstract")
        else:
            raise


if __name__ == '__main__':
    print("Running aggregator tests...")
    print("-" * 60)
    
    test_static_methods_work()
    test_aggregator_filtering()
    test_basescraper_cannot_be_instantiated()
    
    print("-" * 60)
    print("✓ All tests passed!")
