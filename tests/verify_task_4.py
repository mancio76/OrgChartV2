#!/usr/bin/env python3
"""
Verification script for Task 4: Automatic Assignment Versioning System
Tests both subtasks 4.1 and 4.2
"""

import sys
import os
from datetime import date, datetime
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.database import DatabaseManager
from app.services.assignment import AssignmentService
from app.models.assignment import Assignment

def test_version_management_logic():
    """Test Task 4.1: Create version management logic"""
    print("=" * 60)
    print("Testing Task 4.1: Version Management Logic")
    print("=" * 60)
    
    # Initialize services
    db_manager = DatabaseManager()
    assignment_service = AssignmentService()
    
    # Test data - use combination that doesn't exist
    person_id = 1
    unit_id = 2
    job_title_id = 3
    
    # Clean up any existing test data
    try:
        db_manager.execute_query(
            "DELETE FROM person_job_assignments WHERE person_id = ? AND unit_id = ? AND job_title_id = ?",
            (person_id, unit_id, job_title_id)
        )
        print(f"   Cleaned up existing test data for person {person_id}, unit {unit_id}, job_title {job_title_id}")
    except:
        pass
    
    print(f"\n1. Testing automatic version assignment for new assignments")
    print(f"   Creating new assignment for person {person_id}, unit {unit_id}, job_title {job_title_id}")
    
    # Create new assignment
    new_assignment = Assignment(
        person_id=person_id,
        unit_id=unit_id,
        job_title_id=job_title_id,
        percentage=1.0,
        valid_from=date.today(),
        notes="Test assignment - version 1"
    )
    
    try:
        created = assignment_service.create_assignment(new_assignment)
        print(f"   ✓ Created assignment with version {created.version}, is_current={created.is_current}")
        assert created.version == 1, f"Expected version 1, got {created.version}"
        assert created.is_current == True, f"Expected is_current=True, got {created.is_current}"
        
        assignment_id = created.id
        
    except Exception as e:
        print(f"   ✗ Error creating assignment: {e}")
        return False
    
    print(f"\n2. Testing version increment logic for assignment modifications")
    
    # Modify the assignment
    modified_assignment = Assignment(
        person_id=person_id,
        unit_id=unit_id,
        job_title_id=job_title_id,
        percentage=0.8,
        valid_from=date.today(),
        notes="Test assignment - version 2 (modified)"
    )
    
    try:
        modified = assignment_service.modify_assignment(person_id, unit_id, job_title_id, modified_assignment)
        print(f"   ✓ Created new version {modified.version}, is_current={modified.is_current}")
        assert modified.version == 2, f"Expected version 2, got {modified.version}"
        assert modified.is_current == True, f"Expected is_current=True, got {modified.is_current}"
        
        # Check that previous version is now historical
        history = assignment_service.get_assignment_history(person_id, unit_id, job_title_id)
        version_1 = next((a for a in history if a.version == 1), None)
        assert version_1 is not None, "Version 1 should still exist"
        assert version_1.is_current == False, f"Version 1 should be historical, is_current={version_1.is_current}"
        print(f"   ✓ Previous version 1 is now historical (is_current={version_1.is_current})")
        
    except Exception as e:
        print(f"   ✗ Error modifying assignment: {e}")
        return False
    
    print(f"\n3. Testing assignment termination handling")
    
    try:
        # Terminate the current assignment
        termination_date = date.today()
        success = assignment_service.terminate_assignment(modified.id, termination_date)
        print(f"   ✓ Terminated assignment: {success}")
        assert success == True, "Termination should succeed"
        
        # Check that assignment is now terminated
        terminated = assignment_service.get_by_id(modified.id)
        assert terminated.is_current == False, f"Expected is_current=False, got {terminated.is_current}"
        assert terminated.valid_to == termination_date, f"Expected valid_to={termination_date}, got {terminated.valid_to}"
        print(f"   ✓ Assignment marked as terminated (is_current={terminated.is_current}, valid_to={terminated.valid_to})")
        
    except Exception as e:
        print(f"   ✗ Error terminating assignment: {e}")
        return False
    
    print(f"\n✓ Task 4.1 tests completed successfully!")
    return True

def test_assignment_history_tracking():
    """Test Task 4.2: Build assignment history tracking"""
    print("\n" + "=" * 60)
    print("Testing Task 4.2: Assignment History Tracking")
    print("=" * 60)
    
    assignment_service = AssignmentService()
    db_manager = DatabaseManager()
    
    # Test data - use combination that doesn't exist
    person_id = 3
    unit_id = 3
    job_title_id = 4
    
    # Clean up any existing test data
    try:
        db_manager.execute_query(
            "DELETE FROM person_job_assignments WHERE person_id = ? AND unit_id = ? AND job_title_id = ?",
            (person_id, unit_id, job_title_id)
        )
        print(f"   Cleaned up existing test data for person {person_id}, unit {unit_id}, job_title {job_title_id}")
    except:
        pass
    
    print(f"\n1. Testing historical version queries and display")
    
    # Create multiple versions for testing
    try:
        # Version 1
        v1 = Assignment(
            person_id=person_id,
            unit_id=unit_id,
            job_title_id=job_title_id,
            percentage=1.0,
            valid_from=date(2024, 1, 1),
            notes="Version 1"
        )
        created_v1 = assignment_service.create_assignment(v1)
        
        # Version 2
        v2 = Assignment(
            person_id=person_id,
            unit_id=unit_id,
            job_title_id=job_title_id,
            percentage=0.8,
            valid_from=date(2024, 6, 1),
            notes="Version 2"
        )
        created_v2 = assignment_service.modify_assignment(person_id, unit_id, job_title_id, v2)
        
        # Version 3
        v3 = Assignment(
            person_id=person_id,
            unit_id=unit_id,
            job_title_id=job_title_id,
            percentage=0.6,
            valid_from=date(2024, 12, 1),
            notes="Version 3"
        )
        created_v3 = assignment_service.modify_assignment(person_id, unit_id, job_title_id, v3)
        
        print(f"   ✓ Created 3 versions of assignment")
        
    except Exception as e:
        print(f"   ✗ Error creating test versions: {e}")
        return False
    
    # Test history retrieval
    try:
        history = assignment_service.get_assignment_history(person_id, unit_id, job_title_id)
        print(f"   ✓ Retrieved {len(history)} versions from history")
        assert len(history) == 3, f"Expected 3 versions, got {len(history)}"
        
        # Check versions are in descending order
        versions = [a.version for a in history]
        assert versions == [3, 2, 1], f"Expected versions [3, 2, 1], got {versions}"
        print(f"   ✓ Versions returned in correct order: {versions}")
        
        # Check only latest is current
        current_versions = [a for a in history if a.is_current]
        assert len(current_versions) == 1, f"Expected 1 current version, got {len(current_versions)}"
        assert current_versions[0].version == 3, f"Expected current version 3, got {current_versions[0].version}"
        print(f"   ✓ Only latest version is current: version {current_versions[0].version}")
        
    except Exception as e:
        print(f"   ✗ Error testing history queries: {e}")
        return False
    
    print(f"\n2. Testing current assignment filtering (is_current=true only)")
    
    try:
        # Test current assignments filtering
        current_assignments = assignment_service.get_current_assignments()
        current_for_person = assignment_service.get_current_assignments_by_person(person_id)
        current_for_unit = assignment_service.get_current_assignments_by_unit(unit_id)
        
        print(f"   ✓ Retrieved {len(current_assignments)} total current assignments")
        print(f"   ✓ Retrieved {len(current_for_person)} current assignments for person {person_id}")
        print(f"   ✓ Retrieved {len(current_for_unit)} current assignments for unit {unit_id}")
        
        # Verify all returned assignments are current
        for assignment in current_assignments:
            assert assignment.is_current == True, f"Assignment {assignment.id} should be current"
        
        for assignment in current_for_person:
            assert assignment.is_current == True, f"Assignment {assignment.id} should be current"
            assert assignment.person_id == person_id, f"Assignment should be for person {person_id}"
        
        for assignment in current_for_unit:
            assert assignment.is_current == True, f"Assignment {assignment.id} should be current"
            assert assignment.unit_id == unit_id, f"Assignment should be for unit {unit_id}"
        
        print(f"   ✓ All returned assignments are current (is_current=True)")
        
    except Exception as e:
        print(f"   ✗ Error testing current assignment filtering: {e}")
        return False
    
    print(f"\n3. Testing version consistency validation and integrity checks")
    
    try:
        # Test version consistency for specific combination
        consistency_errors = assignment_service._validate_version_consistency(person_id, unit_id, job_title_id)
        print(f"   ✓ Version consistency check completed")
        if consistency_errors:
            print(f"   ⚠ Consistency issues found: {consistency_errors}")
        else:
            print(f"   ✓ No consistency issues found")
        
        # Test system-wide consistency validation
        all_errors = assignment_service.validate_all_version_consistency()
        print(f"   ✓ System-wide consistency check completed")
        if all_errors:
            print(f"   ⚠ Found consistency issues in {len(all_errors)} combinations")
            for key, errors in all_errors.items():
                print(f"     - {key}: {errors}")
        else:
            print(f"   ✓ No system-wide consistency issues found")
        
        # Test version statistics
        stats = assignment_service.get_version_statistics()
        print(f"   ✓ Version statistics:")
        print(f"     - Total versions: {stats.get('total_versions', 0)}")
        print(f"     - Current versions: {stats.get('current_versions', 0)}")
        print(f"     - Historical versions: {stats.get('historical_versions', 0)}")
        print(f"     - Unique combinations: {stats.get('unique_combinations', 0)}")
        print(f"     - Avg versions per combination: {stats.get('avg_versions_per_combination', 0)}")
        
        # Test assignment timeline
        timeline = assignment_service.get_assignment_timeline(person_id, unit_id, job_title_id)
        print(f"   ✓ Retrieved timeline with {len(timeline)} events")
        for event in timeline:
            print(f"     - Version {event['version']}: {event['event_type']} on {event['date']}")
        
    except Exception as e:
        print(f"   ✗ Error testing version consistency: {e}")
        return False
    
    print(f"\n✓ Task 4.2 tests completed successfully!")
    return True

def main():
    """Main test function"""
    print("Verifying Task 4: Automatic Assignment Versioning System")
    print("=" * 80)
    
    try:
        # Initialize database
        db_manager = DatabaseManager()
        db_manager.initialize_database()
        print("✓ Database initialized")
        
        # Run tests
        task_4_1_success = test_version_management_logic()
        task_4_2_success = test_assignment_history_tracking()
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Task 4.1 (Version Management Logic): {'✓ PASSED' if task_4_1_success else '✗ FAILED'}")
        print(f"Task 4.2 (Assignment History Tracking): {'✓ PASSED' if task_4_2_success else '✗ FAILED'}")
        
        if task_4_1_success and task_4_2_success:
            print(f"\n🎉 All Task 4 tests PASSED!")
            return True
        else:
            print(f"\n❌ Some Task 4 tests FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)