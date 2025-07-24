#!/usr/bin/env python3
"""
Test script to verify assignment versioning system functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.assignment import AssignmentService
from app.models.assignment import Assignment
from datetime import date, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_versioning_system():
    """Test the assignment versioning system"""
    service = AssignmentService()
    
    print("=== Testing Assignment Versioning System ===\n")
    
    # Test 1: Create new assignment (should be version 1, is_current=True)
    print("Test 1: Creating new assignment...")
    test_assignment = Assignment(
        person_id=1,
        unit_id=1, 
        job_title_id=1,
        percentage=0.8,
        valid_from=date.today()
    )
    
    try:
        # Check if assignment already exists
        existing = service._get_current_assignment(1, 1, 1)
        if existing:
            print(f"Assignment already exists with version {existing.version}, terminating it first...")
            service.terminate_assignment(existing.id)
        
        created = service.create_assignment(test_assignment)
        print(f"✓ Created assignment: ID={created.id}, version={created.version}, is_current={created.is_current}")
        assert created.version == 1, f"Expected version 1, got {created.version}"
        assert created.is_current == True, f"Expected is_current=True, got {created.is_current}"
        
    except Exception as e:
        print(f"✗ Error creating assignment: {e}")
        return False
    
    # Test 2: Modify assignment (should create version 2, mark version 1 as historical)
    print("\nTest 2: Modifying assignment...")
    try:
        modified_data = Assignment(
            percentage=1.0,  # Change percentage
            valid_from=date.today() + timedelta(days=1)
        )
        
        modified = service.modify_assignment(1, 1, 1, modified_data)
        print(f"✓ Modified assignment: ID={modified.id}, version={modified.version}, is_current={modified.is_current}")
        assert modified.version == 2, f"Expected version 2, got {modified.version}"
        assert modified.is_current == True, f"Expected is_current=True, got {modified.is_current}"
        
        # Check that previous version is now historical
        history = service.get_assignment_history(1, 1, 1)
        print(f"✓ Assignment history has {len(history)} versions")
        
        version_1 = next((h for h in history if h.version == 1), None)
        if version_1:
            print(f"✓ Version 1 is_current={version_1.is_current}, valid_to={version_1.valid_to}")
            assert version_1.is_current == False, f"Expected version 1 is_current=False, got {version_1.is_current}"
        
    except Exception as e:
        print(f"✗ Error modifying assignment: {e}")
        return False
    
    # Test 3: Terminate assignment (should set is_current=False, valid_to=date)
    print("\nTest 3: Terminating assignment...")
    try:
        current = service._get_current_assignment(1, 1, 1)
        if current:
            termination_date = date.today() + timedelta(days=2)
            success = service.terminate_assignment(current.id, termination_date)
            print(f"✓ Terminated assignment: success={success}")
            
            # Verify termination
            terminated = service.get_by_id(current.id)
            print(f"✓ Terminated assignment: is_current={terminated.is_current}, valid_to={terminated.valid_to}")
            assert terminated.is_current == False, f"Expected is_current=False, got {terminated.is_current}"
            assert terminated.valid_to == termination_date, f"Expected valid_to={termination_date}, got {terminated.valid_to}"
        
    except Exception as e:
        print(f"✗ Error terminating assignment: {e}")
        return False
    
    # Test 4: Test current assignments filtering
    print("\nTest 4: Testing current assignments filtering...")
    try:
        current_assignments = service.get_current_assignments()
        print(f"✓ Found {len(current_assignments)} current assignments")
        
        # All should have is_current=True
        for assignment in current_assignments:
            assert assignment.is_current == True, f"Found non-current assignment in current list: {assignment.id}"
        
        print("✓ All current assignments have is_current=True")
        
    except Exception as e:
        print(f"✗ Error testing current assignments: {e}")
        return False
    
    # Test 5: Test version consistency validation
    print("\nTest 5: Testing version consistency validation...")
    try:
        consistency_errors = service.validate_all_version_consistency()
        if consistency_errors:
            print(f"⚠ Found version consistency issues: {consistency_errors}")
        else:
            print("✓ No version consistency issues found")
        
    except Exception as e:
        print(f"✗ Error validating version consistency: {e}")
        return False
    
    print("\n=== All tests passed! ===")
    return True

if __name__ == "__main__":
    success = test_versioning_system()
    sys.exit(0 if success else 1)