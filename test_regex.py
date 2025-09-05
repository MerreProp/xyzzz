import re

print("Testing basic regex patterns...")

# Test the postcode pattern specifically
try:
    postcode_pattern = r'([A-Z]{1,2}[0-9]{1,2}[A-Z]?\s?[0-9][A-Z]{2})'
    test_address = "123 Main Street, Oxford OX1 2AB"
    match = re.search(postcode_pattern, test_address.upper())
    print(f"✅ Postcode pattern works: {match.group(1) if match else 'No match'}")
except Exception as e:
    print(f"❌ Postcode pattern failed: {e}")

# Test the address cleaning patterns
try:
    test_patterns = [
        r'\s+',
        r'\b(flat|apartment|apt|unit)\s*\d*\s*,?\s*',
        r'\b(ground|first|second|third|top)\s*floor\s*,?\s*',
        r'\b(front|rear|back)\s*,?\s*',
        r'\bst\b',
        r'\brd\b',
        r'\bave\b',
        r'\bdr\b',
        r'\bcl\b'
    ]
    
    for i, pattern in enumerate(test_patterns):
        re.compile(pattern)
        print(f"✅ Pattern {i+1} compiles successfully")
        
except Exception as e:
    print(f"❌ Pattern compilation failed: {e}")

print("Basic regex test completed.")