"""
Test script for event classifier to verify enhanced special event detection
"""
from event_classifier import EventClassifier, classify_screening


def test_event_classifier():
    """Test the event classifier with various screening descriptions"""
    print("Testing Event Classifier\n" + "=" * 60)

    test_cases = [
        {
            'description': 'Special screening with Q&A with director John Smith',
            'expected_tags': ['Q&A', 'Director Appearance']
        },
        {
            'description': 'Opening night premiere with filmmaker in person',
            'expected_tags': ['Filmmaker Appearance', 'Opening Night']
        },
        {
            'description': 'Sneak preview screening - IMAX',
            'expected_tags': ['IMAX', 'Sneak Preview']
        },
        {
            'description': '70mm restoration for the 25th anniversary',
            'expected_tags': ['70mm', 'Anniversary', 'Restoration']
        },
        {
            'description': 'Advance screening in Dolby Cinema',
            'expected_tags': ['Advance Screening', 'Dolby']
        },
        {
            'description': 'New 4K restoration premiere',
            'expected_tags': ['Premiere', 'Restoration']
        },
        {
            'description': 'Festival screening with Q and A',
            'expected_tags': ['Festival', 'Q&A']
        },
        {
            'description': 'Triple feature marathon in 35mm',
            'expected_tags': ['35mm', 'Fan Event']
        },
        {
            'description': 'Director in person for opening night',
            'expected_tags': ['Director Appearance', 'Opening Night']
        },
        {
            'description': 'Sneak peek advance screening',
            'expected_tags': ['Sneak Preview', 'Advance Screening']
        }
    ]

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        description = test_case['description']
        expected_tags = set(test_case['expected_tags'])

        # Run classifier
        tags = EventClassifier.classify(description)
        tags_set = set(tags)
        formatted = EventClassifier.format_tags(tags)

        # Check if all expected tags are present
        missing_tags = expected_tags - tags_set
        extra_tags = tags_set - expected_tags

        # Test passes if all expected tags are found (extra tags are okay)
        if not missing_tags:
            passed += 1
            status = "✓ PASS"
        else:
            failed += 1
            status = "✗ FAIL"

        print(f"\nTest {i}: {status}")
        print(f"  Description: {description}")
        print(f"  Expected: {', '.join(sorted(expected_tags))}")
        print(f"  Got: {formatted}")

        if missing_tags:
            print(f"  Missing: {', '.join(sorted(missing_tags))}")
        if extra_tags and not missing_tags:
            print(f"  Extra (bonus): {', '.join(sorted(extra_tags))}")

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 60)

    return failed == 0


def test_is_special():
    """Test the is_special convenience method"""
    print("\n\nTesting is_special() method\n" + "=" * 60)

    test_cases = [
        ('Regular screening at 7pm', False),
        ('Q&A with director', True),
        ('IMAX screening', True),
        ('Standard showing', False),
        ('70mm restoration', True),
        ('Sneak preview tonight', True),
        ('With filmmaker in person', True),
    ]

    passed = 0
    for text, expected in test_cases:
        result = EventClassifier.is_special(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text}' -> {result} (expected {expected})")
        if result == expected:
            passed += 1

    print("=" * 60)
    print(f"Results: {passed}/{len(test_cases)} passed")
    print("=" * 60)


def test_all_keywords():
    """Display all keywords being tracked"""
    print("\n\nAll Keywords Tracked\n" + "=" * 60)

    for category, keywords in EventClassifier.KEYWORDS.items():
        print(f"\n{category}:")
        print(f"  {', '.join(keywords)}")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    # Run all tests
    success = test_event_classifier()
    test_is_special()
    test_all_keywords()

    # Exit with appropriate code
    exit(0 if success else 1)
