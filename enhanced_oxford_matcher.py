#!/usr/bin/env python3
"""
Enhanced Oxford Address Matcher
===============================

This script fixes the address matching issue for Oxford HMOs by implementing
enhanced address normalization and comparison logic that handles the different
address formats between the HMO Register Copy file and the database.

Key improvements:
1. Enhanced address normalization for different formats
2. Multiple matching strategies (postcode, street name, house number)
3. Better handling of Oxford-specific address patterns
4. Fuzzy matching for similar addresses
5. Confidence scoring based on multiple factors
"""

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedOxfordAddressMatcher:
    """Enhanced address matcher specifically designed for Oxford HMO data"""
    
    def __init__(self):
        self.oxford_area_names = {
            'headington', 'marston', 'cowley', 'iffley', 'summertown', 
            'jericho', 'botley', 'osney', 'grandpont', 'new hinksey',
            'old headington', 'new headington', 'temple cowley'
        }
        
        # Common Oxford street name abbreviations and variations
        self.oxford_street_variations = {
            'st': ['street', 'st.', 'st'],
            'rd': ['road', 'rd.', 'rd'],
            'ave': ['avenue', 'ave.', 'ave'],
            'cl': ['close', 'cl.', 'cl'],
            'ln': ['lane', 'ln.', 'ln'],
            'dr': ['drive', 'dr.', 'dr'],
            'pl': ['place', 'pl.', 'pl'],
            'ct': ['court', 'ct.', 'ct'],
            'crt': ['court', 'crt.', 'crt'],
            'grv': ['grove', 'grv.', 'grv']
        }
    
    def normalize_oxford_address(self, address: str) -> Dict[str, str]:
        """
        Normalize Oxford address into components for better matching
        
        Returns:
            Dict with normalized components: full, street, number, postcode, area
        """
        if not address:
            return {'full': '', 'street': '', 'number': '', 'postcode': '', 'area': ''}
        
        # Clean the input
        cleaned = self._clean_address_text(address)
        
        # Extract components
        postcode = self._extract_postcode(cleaned)
        house_number = self._extract_house_number(cleaned) 
        street_name = self._extract_street_name(cleaned)
        area_name = self._extract_area_name(cleaned)
        
        # Create normalized full address
        normalized_full = self._create_normalized_full_address(cleaned)
        
        return {
            'full': normalized_full,
            'street': street_name if street_name else '',
            'number': house_number if house_number else '',
            'postcode': postcode if postcode else '',
            'area': area_name if area_name else ''
        }
    
    def _clean_address_text(self, address: str) -> str:
        """Clean and standardize address text"""
        # Handle unicode and encoding issues
        address = unicodedata.normalize('NFKD', str(address))
        
        # Replace line breaks with spaces (common in raw data)
        address = re.sub(r'[\r\n]+', ' ', address)
        
        # Clean up multiple spaces
        address = re.sub(r'\s+', ' ', address)
        
        # Remove extra punctuation
        address = re.sub(r'[,]{2,}', ',', address)
        address = re.sub(r'\s*,\s*', ', ', address)
        
        # Standardize case
        address = address.strip().title()
        
        # Handle specific Oxford formatting issues
        address = self._fix_oxford_specific_issues(address)
        
        return address
    
    def _fix_oxford_specific_issues(self, address: str) -> str:
        """Fix common issues in Oxford addresses"""
        # Fix common Oxford area name variations
        address = re.sub(r'\bOld Town\b', 'Old Town', address, flags=re.IGNORECASE)
        address = re.sub(r'\bNew Hinksey\b', 'New Hinksey', address, flags=re.IGNORECASE)
        
        # Standardize "Oxford" references
        address = re.sub(r'\b,?\s*Oxford\s*,?\s*Oxfordshire\b', ', Oxford', address, flags=re.IGNORECASE)
        address = re.sub(r'\b,?\s*Oxford\s*,?\s*UK\b', ', Oxford', address, flags=re.IGNORECASE)
        
        return address
    
    def _extract_postcode(self, address: str) -> str:
        """Extract UK postcode with Oxford-specific patterns"""
        # Oxford postcodes start with OX
        patterns = [
            r'\b(OX[0-9]{1,2}\s?[0-9][A-Z]{2})\b',  # OX postcodes specifically
            r'\b([A-Z]{1,2}[0-9]{1,2}[A-Z]?\s?[0-9][A-Z]{2})\b',  # General UK pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, address.upper())
            if match:
                postcode = match.group(1).strip()
                # Ensure proper spacing
                if len(postcode) > 3 and ' ' not in postcode:
                    postcode = postcode[:-3] + ' ' + postcode[-3:]
                return postcode.upper()
        
        return ''
    
    def _extract_house_number(self, address: str) -> str:
        """Extract house number from address"""
        # Look for various house number patterns
        patterns = [
            r'^(\d+[A-Z]?)\b',  # Simple number at start
            r'^([\d-]+[A-Z]?)\b',  # Range like "133-135"
            r'(?:Flat|Apartment|Unit)\s*(\d+[A-Z]?)',  # After flat/apartment
            r'(\d+[A-Z]?)\s+\w+\s+(?:Street|Road|Avenue|Lane|Close|Drive|Place|Court|Grove)',  # Before street name
        ]
        
        for pattern in patterns:
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ''
    
    def _extract_street_name(self, address: str) -> str:
        """Extract and normalize street name - using the working simple approach"""
        if not address:
            return ''
        
        # Remove house numbers and flat references (from the working simple version)
        clean = re.sub(r'^(?:Flat|Apartment|Unit)\s*\d*[A-Z]?\s*,?\s*', '', address, flags=re.IGNORECASE)
        clean = re.sub(r'^\d+[A-Z]?[-\d]*[A-Z]?\s*', '', clean).strip()
        
        if not clean:
            return ''
        
        # Take everything before the first comma
        if ',' in clean:
            street = clean.split(',')[0].strip()
        else:
            # If no comma, take first few words
            words = clean.split()
            if len(words) >= 2:
                street = ' '.join(words[:2])  # Take first 2 words
            else:
                street = clean
        
        # Remove Oxford references
        street = re.sub(r'\s+Oxford.*$', '', street, flags=re.IGNORECASE)
        street = street.strip()
        
        # Normalize street type abbreviations
        if street:
            for abbrev, variations in self.oxford_street_variations.items():
                for variation in variations:
                    pattern = r'\b' + re.escape(variation) + r'\b'
                    street = re.sub(pattern, abbrev, street, flags=re.IGNORECASE)
        
        return street
    
    def _extract_area_name(self, address: str) -> str:
        """Extract Oxford area name if present"""
        address_lower = address.lower()
        
        # Check for known Oxford areas
        for area in self.oxford_area_names:
            if area in address_lower:
                return area.title()
        
        return ''
    
    def _create_normalized_full_address(self, address: str) -> str:
        """Create a normalized version of the full address"""
        # Remove extra Oxford references but keep one
        normalized = re.sub(r'\b,?\s*Oxford\s*,?\s*Oxfordshire\b', ', Oxford', address, flags=re.IGNORECASE)
        normalized = re.sub(r'\b,?\s*Oxford\s*,?\s*UK\b', ', Oxford', normalized, flags=re.IGNORECASE)
        
        # Ensure it ends with Oxford if it's an Oxford address
        if not re.search(r'\boxford\b', normalized, re.IGNORECASE):
            if re.search(r'\bOX\d', normalized):  # Has Oxford postcode
                normalized += ', Oxford'
        
        return normalized.strip()
    
    def calculate_address_match_confidence(self, addr1: str, addr2: str) -> float:
        """
        Calculate confidence score for address match using multiple factors
        
        Returns confidence score between 0.0 and 1.0
        """
        # Normalize both addresses
        norm1 = self.normalize_oxford_address(addr1)
        norm2 = self.normalize_oxford_address(addr2)
        
        confidence_factors = {}
        
        # Factor 1: Postcode match (highest weight - 40%)
        if norm1['postcode'] and norm2['postcode']:
            if norm1['postcode'] == norm2['postcode']:
                confidence_factors['postcode_exact'] = 0.4
            else:
                # Check if postcodes are similar (same area)
                postcode_sim = self._calculate_postcode_similarity(norm1['postcode'], norm2['postcode'])
                confidence_factors['postcode_similar'] = postcode_sim * 0.2
        
        # Factor 2: House number match (30%)
        if norm1['number'] and norm2['number']:
            if norm1['number'] == norm2['number']:
                confidence_factors['number_exact'] = 0.3
            else:
                # Handle ranges and similar numbers - but be more strict
                number_sim = self._calculate_number_similarity(norm1['number'], norm2['number'])
                if number_sim >= 0.8:  # Only very similar numbers get partial credit
                    confidence_factors['number_similar'] = number_sim * 0.15
                else:
                    # Apply strong penalty for different house numbers on same street
                    if norm1['street'] and norm2['street'] and norm1['street'].lower() == norm2['street'].lower():
                        confidence_factors['number_mismatch_penalty'] = -0.3  # Increased penalty
        
        # Factor 3: Street name match (25%)
        if norm1['street'] and norm2['street']:
            street_sim = SequenceMatcher(None, norm1['street'].lower(), norm2['street'].lower()).ratio()
            if street_sim >= 0.9:
                confidence_factors['street_exact'] = 0.25
            elif street_sim >= 0.7:
                confidence_factors['street_similar'] = street_sim * 0.2
            else:
                confidence_factors['street_different'] = -0.4  # Strong penalty for different streets
        elif norm1['street'] and norm2['street'] and norm1['street'] != norm2['street']:
            # Both have streets but they're clearly different
            confidence_factors['street_different'] = -0.4
        
        # Factor 4: Area name match (5%)
        if norm1['area'] and norm2['area']:
            if norm1['area'].lower() == norm2['area'].lower():
                confidence_factors['area_match'] = 0.05
        
        # Factor 5: Overall text similarity (bonus)
        text_sim = SequenceMatcher(None, norm1['full'].lower(), norm2['full'].lower()).ratio()
        confidence_factors['text_similarity'] = text_sim * 0.1
        
        # Calculate final confidence
        total_confidence = sum(confidence_factors.values())
        
        # Apply additional penalties for clear mismatches
        if 'street_different' in confidence_factors and confidence_factors['street_different'] < 0:
            total_confidence = max(0.0, total_confidence)
        
        if 'number_mismatch_penalty' in confidence_factors:
            total_confidence = max(0.0, total_confidence)
        
        # Cap at 1.0 and ensure minimum 0.0
        return min(1.0, max(0.0, total_confidence))
    
    def _calculate_postcode_similarity(self, pc1: str, pc2: str) -> float:
        """Calculate similarity between two postcodes"""
        if not pc1 or not pc2:
            return 0.0
        
        # Same area code (e.g., both OX1, OX2, etc.)
        area1 = re.match(r'^([A-Z]+\d+)', pc1)
        area2 = re.match(r'^([A-Z]+\d+)', pc2)
        
        if area1 and area2 and area1.group(1) == area2.group(1):
            return 0.7  # Same area, different district
        
        return SequenceMatcher(None, pc1, pc2).ratio() * 0.3
    
    def _calculate_number_similarity(self, num1: str, num2: str) -> float:
        """Calculate similarity between house numbers"""
        if not num1 or not num2:
            return 0.0
        
        # Handle ranges (e.g., "133-135" vs "133")
        nums1 = re.findall(r'\d+', num1)
        nums2 = re.findall(r'\d+', num2)
        
        # Check if any numbers match
        for n1 in nums1:
            for n2 in nums2:
                if n1 == n2:
                    return 1.0
        
        # Check if numbers are close
        if nums1 and nums2:
            try:
                diff = abs(int(nums1[0]) - int(nums2[0]))
                if diff <= 2:  # Very close numbers
                    return 0.8
                elif diff <= 5:  # Somewhat close
                    return 0.5
            except (ValueError, IndexError):
                pass
        
        return 0.0
    
    def find_potential_matches(self, target_address: str, candidate_addresses: List[Dict[str, Any]], 
                             min_confidence: float = 0.5) -> List[Dict[str, Any]]:
        """
        Find potential matches for a target address from a list of candidates
        
        Args:
            target_address: The address to match
            candidate_addresses: List of dicts with 'address' and other fields
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of matches with confidence scores
        """
        matches = []
        
        for candidate in candidate_addresses:
            candidate_addr = candidate.get('address', '')
            if not candidate_addr:
                continue
            
            confidence = self.calculate_address_match_confidence(target_address, candidate_addr)
            
            if confidence >= min_confidence:
                match_result = {
                    **candidate,  # Include all original fields
                    'confidence_score': confidence,
                    'target_address_normalized': self.normalize_oxford_address(target_address),
                    'candidate_address_normalized': self.normalize_oxford_address(candidate_addr)
                }
                matches.append(match_result)
        
        # Sort by confidence score (highest first)
        matches.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        return matches


def update_oxford_hmo_integration():
    """
    Main function to update the Oxford HMO integration with enhanced address matching
    """
    print("🏛️ Enhanced Oxford HMO Address Matching Update")
    print("=" * 60)
    
    try:
        # Import required modules (adjust imports based on your project structure)
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from database import SessionLocal
        from hmo_registry.database_models import HMORegistry
        from models import Property, PropertyHMOMatch  # Import PropertyHMOMatch from models
        from sqlalchemy import or_, func
        
        matcher = EnhancedOxfordAddressMatcher()
        db = SessionLocal()
        
        print("1. Loading Oxford HMO records from database...")
        
        # Get Oxford HMO records
        oxford_hmos = db.query(HMORegistry).filter(
            HMORegistry.city == 'oxford'
        ).all()
        
        print(f"   Found {len(oxford_hmos)} Oxford HMO records")
        
        print("2. Loading Oxford properties from database...")
        
        # Get Oxford properties
        oxford_properties = db.query(Property).filter(
            or_(
                Property.city.ilike('%oxford%'),
                Property.postcode.ilike('OX%'),
                Property.address.ilike('%oxford%')
            )
        ).all()
        
        print(f"   Found {len(oxford_properties)} Oxford properties")
        
        print("3. Starting enhanced address matching...")
        
        new_matches = 0
        updated_matches = 0
        total_processed = 0
        
        for property_obj in oxford_properties:
            if not property_obj.address:
                continue
            
            total_processed += 1
            
            # Check if property already has matches
            existing_matches = db.query(PropertyHMOMatch).filter(
                PropertyHMOMatch.property_id == str(property_obj.id)
            ).all()
            
            # Prepare candidate HMO addresses
            candidate_hmos = []
            for hmo in oxford_hmos:
                if hmo.raw_address:  # Changed from address to raw_address
                    candidate_hmos.append({
                        'hmo_id': str(hmo.id),
                        'address': hmo.raw_address,  # Changed from address to raw_address
                        'case_number': hmo.case_number,  # Changed from external_case_number
                        'licence_expiry': hmo.licence_expiry_date
                    })
            
            # Find potential matches using enhanced matcher
            potential_matches = matcher.find_potential_matches(
                property_obj.address, 
                candidate_hmos,
                min_confidence=0.6  # Lower threshold for Oxford due to format differences
            )
            
            # Process matches
            for match in potential_matches[:3]:  # Top 3 matches only
                confidence = match['confidence_score']
                hmo_id = match['hmo_id']
                
                # Check if this match already exists
                existing_match = next(
                    (em for em in existing_matches if em.hmo_register_id == hmo_id), 
                    None
                )
                
                if existing_match:
                    # Update existing match if confidence is higher
                    if confidence > existing_match.confidence_score:
                        existing_match.confidence_score = confidence
                        existing_match.match_method = 'enhanced_oxford_matcher'
                        existing_match.updated_at = datetime.utcnow()
                        updated_matches += 1
                else:
                    # Create new match
                    new_match = PropertyHMOMatch(
                        property_id=str(property_obj.id),
                        hmo_register_id=hmo_id,
                        confidence_score=confidence,
                        match_method='enhanced_oxford_matcher',
                        verified_status='pending',
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(new_match)
                    new_matches += 1
            
            # Progress update
            if total_processed % 100 == 0:
                print(f"   Processed {total_processed}/{len(oxford_properties)} properties...")
        
        # Commit changes
        db.commit()
        
        print("4. Enhanced matching completed!")
        print(f"   - Properties processed: {total_processed}")
        print(f"   - New matches created: {new_matches}")
        print(f"   - Existing matches updated: {updated_matches}")
        
        # Show some sample matches for verification
        print("\n5. Sample high-confidence matches:")
        sample_matches = db.query(PropertyHMOMatch).filter(
            PropertyHMOMatch.match_method == 'enhanced_oxford_matcher',
            PropertyHMOMatch.confidence_score >= 0.8
        ).limit(5).all()
        
        for i, match in enumerate(sample_matches, 1):
            property_obj = db.query(Property).filter(Property.id == int(match.property_id)).first()
            hmo_obj = db.query(HMORegistry).filter(HMORegistry.id == int(match.hmo_register_id)).first()
            
            if property_obj and hmo_obj:
                print(f"\n   Match {i} (Confidence: {match.confidence_score:.2f}):")
                print(f"     Property: {property_obj.address}")
                print(f"     HMO: {hmo_obj.raw_address}")  # Changed from address to raw_address
                print(f"     Case: {hmo_obj.case_number}")  # Changed from external_case_number
        
        return True
        
    except Exception as e:
        print(f"❌ Error during enhanced matching: {e}")
        if 'db' in locals():
            db.rollback()
        return False
    
    finally:
        if 'db' in locals():
            db.close()


def test_address_matching():
    """Test the enhanced address matcher with sample Oxford addresses"""
    print("🧪 Testing Enhanced Oxford Address Matcher")
    print("=" * 50)
    
    matcher = EnhancedOxfordAddressMatcher()
    
    # Test cases with different formats
    test_cases = [
        {
            'hmo_address': "61 Catherine Street, OX4 3AH",
            'property_address': "61 Catherine Street, Oxford, OX4 3AH",
            'expected_high': True
        },
        {
            'hmo_address': "45 Gipsy Lane, Headington, OX3 7PT", 
            'property_address': "45 Gipsy Lane\nHeadington\nOxford\nOX3 7PT",
            'expected_high': True
        },
        {
            'hmo_address': "133-135 Manchester Road, OX1 2AB",
            'property_address': "Flat 133 Manchester Road, Oxford OX1 2AB", 
            'expected_high': True
        },
        {
            'hmo_address': "61 Catherine Street, OX4 3AH",
            'property_address': "63 Catherine Street, Oxford, OX4 3AH",
            'expected_high': False  # Different house number
        },
        {
            'hmo_address': "61 Catherine Street, OX4 3AH", 
            'property_address': "61 Victoria Road, Oxford, OX4 3AH",
            'expected_high': False  # Different street
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  HMO: {test_case['hmo_address']}")
        print(f"  Property: {test_case['property_address']}")
        
        confidence = matcher.calculate_address_match_confidence(
            test_case['hmo_address'], 
            test_case['property_address']
        )
        
        print(f"  Confidence: {confidence:.3f}")
        
        # Check if result matches expectation
        is_high_confidence = confidence >= 0.7
        expected = test_case['expected_high']
        
        if is_high_confidence == expected:
            print(f"  ✅ PASS - {'High' if is_high_confidence else 'Low'} confidence as expected")
        else:
            print(f"  ❌ FAIL - Expected {'high' if expected else 'low'} confidence")
        
        # Show normalization for debugging
        norm_hmo = matcher.normalize_oxford_address(test_case['hmo_address'])
        norm_prop = matcher.normalize_oxford_address(test_case['property_address'])
        
        print(f"  HMO normalized: {norm_hmo}")
        print(f"  Property normalized: {norm_prop}")
        
        # Debug street extraction specifically
        hmo_street = matcher._extract_street_name(test_case['hmo_address'])
        prop_street = matcher._extract_street_name(test_case['property_address'])
        print(f"  HMO street: '{hmo_street}'")
        print(f"  Property street: '{prop_street}'")


if __name__ == "__main__":
    print("Enhanced Oxford Address Matcher")
    print("==============================")
    print()
    print("Available functions:")
    print("1. test_address_matching() - Test the matcher with sample data")
    print("2. update_oxford_hmo_integration() - Update the database with enhanced matching")
    print()
    print("Example usage:")
    print("  python enhanced_oxford_matcher.py")
    print("  >>> test_address_matching()")
    print("  >>> update_oxford_hmo_integration()")
    
    # Run tests by default
    test_address_matching()