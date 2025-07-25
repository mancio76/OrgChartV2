"""
End-to-end integration tests for complete CRUD workflows and system functionality.

This module implements Task 11.1 - Perform end-to-end integration testing:
- Test complete CRUD workflows for all entities
- Verify assignment versioning system functionality  
- Validate organizational chart visualization with different data sets
- Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 6.1
"""

import pytest
import sqlite3
from datetime import date, datetime, timedelta
from unittest.mock import patch, Mock

from app.database import DatabaseManager
from app.models.unit_type import UnitType
from app.models.unit import Unit
from app.models.person import Person
from app.models.job_title import JobTitle
from app.models.assignment import Assignment
from app.services.unit import UnitService
from app.services.person import PersonService
from app.services.job_title import JobTitleService
from app.services.assignment import AssignmentService
from app.services.orgchart import OrgchartService


class TestEndToEndCRUDWorkflows:
    """Test complete CRUD workflows for all entities (Requirements 3.1, 3.2, 3.3, 3.4)"""
    
    def test_complete_unit_crud_workflow(self, client, mock_db_manager):
        """Test complete CRUD workflow for units (Requirement 3.1)"""
        # Test data
        unit_data = {
            "name": "Test Department",
            "short_name": "TEST",
            "unit_type_id": 1,
            "parent_unit_id": None,
            "start_date": "2023-01-01"
        }
        
        # Mock the validation method to avoid import issues
        with patch.object(UnitService, '_validate_for_create') as mock_validate:
            
            # 1. CREATE - Test unit creation
            mock_db_manager.execute_query.return_value = Mock(lastrowid=1, rowcount=1)
            mock_created_unit = {
                'id': 1,
                'name': 'Test Department',
                'short_name': 'TEST',
                'unit_type_id': 1,
                'parent_unit_id': None,
                'start_date': '2023-01-01',
                'end_date': None,
                'aliases': '[]',
                'datetime_created': '2023-01-01T10:00:00',
                'datetime_updated': '2023-01-01T10:00:00',
                'parent_name': None,
                'children_count': 0,
                'person_count': 0,
                'level': 0,
                'path': '/Test Department',
                'full_path': 'Test Department'
            }
            
            # Mock validation queries to return no duplicates
            def mock_fetch_one_side_effect(query, params=None):
                if "SELECT id FROM units WHERE name" in query:
                    return None  # No duplicate names
                elif "SELECT id FROM unit_types WHERE id" in query:
                    return {'id': 1}  # Unit type exists
                else:
                    return mock_created_unit
            
            mock_db_manager.fetch_one.side_effect = mock_fetch_one_side_effect
            
            create_response = client.post("/api/units", json=unit_data)
            assert create_response.status_code == 201
            create_data = create_response.json()
            assert create_data['success'] is True
            assert create_data['data']['name'] == 'Test Department'
            unit_id = create_data['data']['id']
            
            # 2. READ - Test unit retrieval
            read_response = client.get(f"/api/units/{unit_id}")
            assert read_response.status_code == 200
            read_data = read_response.json()
            assert read_data['success'] is True
            assert read_data['data']['name'] == 'Test Department'
            
            # 3. UPDATE - Test unit modification
            updated_unit_data = {
                "name": "Updated Department",
                "short_name": "UPD",
                "unit_type_id": 1,
                "parent_unit_id": None,
                "start_date": "2023-01-01"
            }
            
            mock_updated_unit = mock_created_unit.copy()
            mock_updated_unit['name'] = 'Updated Department'
            mock_updated_unit['short_name'] = 'UPD'
            mock_db_manager.fetch_one.return_value = mock_updated_unit
            
            update_response = client.put(f"/api/units/{unit_id}", json=updated_unit_data)
            assert update_response.status_code == 200
            update_data = update_response.json()
            assert update_data['success'] is True
            assert update_data['data']['name'] == 'Updated Department'
            
            # 4. LIST - Test unit listing
            mock_db_manager.fetch_all.return_value = [mock_updated_unit]
            list_response = client.get("/api/units")
            assert list_response.status_code == 200
            list_data = list_response.json()
            assert list_data['success'] is True
            assert len(list_data['data']) == 1
            assert list_data['data'][0]['name'] == 'Updated Department'
            
            # 5. DELETE - Test unit deletion
            mock_db_manager.fetch_one.return_value = None  # No dependent records
            delete_response = client.delete(f"/api/units/{unit_id}")
            assert delete_response.status_code == 200
            delete_data = delete_response.json()
            assert delete_data['success'] is True
            assert 'deleted successfully' in delete_data['message']
    
    def test_complete_person_crud_workflow(self, client, mock_db_manager):
        """Test complete CRUD workflow for persons (Requirement 3.2)"""
        # Test data
        person_data = {
            "name": "Mario Rossi",
            "short_name": "M. Rossi",
            "email": "mario.rossi@example.com"
        }
        
        # 1. CREATE - Test person creation
        mock_db_manager.execute_query.return_value = Mock(lastrowid=1, rowcount=1)
        mock_created_person = {
            'id': 1,
            'name': 'Mario Rossi',
            'short_name': 'M. Rossi',
            'email': 'mario.rossi@example.com',
            'datetime_created': '2023-01-01T10:00:00',
            'datetime_updated': '2023-01-01T10:00:00',
            'current_assignments_count': 0,
            'total_assignments_count': 0
        }
        mock_db_manager.fetch_one.return_value = mock_created_person
        
        create_response = client.post("/api/persons", json=person_data)
        assert create_response.status_code == 201
        create_data = create_response.json()
        assert create_data['success'] is True
        assert create_data['data']['name'] == 'Mario Rossi'
        assert create_data['data']['email'] == 'mario.rossi@example.com'
        person_id = create_data['data']['id']
        
        # 2. READ - Test person retrieval
        read_response = client.get(f"/api/persons/{person_id}")
        assert read_response.status_code == 200
        read_data = read_response.json()
        assert read_data['success'] is True
        assert read_data['data']['name'] == 'Mario Rossi'
        
        # 3. UPDATE - Test person modification
        updated_person_data = {
            "name": "Mario Bianchi",
            "short_name": "M. Bianchi",
            "email": "mario.bianchi@example.com"
        }
        
        mock_updated_person = mock_created_person.copy()
        mock_updated_person['name'] = 'Mario Bianchi'
        mock_updated_person['email'] = 'mario.bianchi@example.com'
        mock_db_manager.fetch_one.return_value = mock_updated_person
        
        update_response = client.put(f"/api/persons/{person_id}", json=updated_person_data)
        assert update_response.status_code == 200
        update_data = update_response.json()
        assert update_data['success'] is True
        assert update_data['data']['name'] == 'Mario Bianchi'
        assert update_data['data']['email'] == 'mario.bianchi@example.com'
        
        # 4. LIST - Test person listing with search
        mock_db_manager.fetch_all.return_value = [mock_updated_person]
        list_response = client.get("/api/persons?search=Mario")
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert list_data['success'] is True
        assert len(list_data['data']) == 1
        assert list_data['data'][0]['name'] == 'Mario Bianchi'
        
        # 5. DELETE - Test person deletion
        mock_db_manager.fetch_one.return_value = None  # No dependent records
        delete_response = client.delete(f"/api/persons/{person_id}")
        assert delete_response.status_code == 200
        delete_data = delete_response.json()
        assert delete_data['success'] is True
    
    def test_complete_job_title_crud_workflow(self, client, mock_db_manager):
        """Test complete CRUD workflow for job titles (Requirement 3.3)"""
        # Test data
        job_title_data = {
            "name": "Software Engineer",
            "short_name": "SW Eng",
            "start_date": "2023-01-01",
            "assignable_unit_ids": [1, 2]
        }
        
        # 1. CREATE - Test job title creation
        mock_db_manager.execute_query.return_value = Mock(lastrowid=1, rowcount=1)
        mock_created_job_title = {
            'id': 1,
            'name': 'Software Engineer',
            'short_name': 'SW Eng',
            'aliases': '[]',
            'start_date': '2023-01-01',
            'end_date': None,
            'datetime_created': '2023-01-01T10:00:00',
            'datetime_updated': '2023-01-01T10:00:00',
            'current_assignments_count': 0,
            'total_assignments_count': 0
        }
        mock_db_manager.fetch_one.return_value = mock_created_job_title
        
        create_response = client.post("/api/job-titles", json=job_title_data)
        assert create_response.status_code == 201
        create_data = create_response.json()
        assert create_data['success'] is True
        assert create_data['data']['name'] == 'Software Engineer'
        job_title_id = create_data['data']['id']
        
        # 2. READ - Test job title retrieval
        read_response = client.get(f"/api/job-titles/{job_title_id}")
        assert read_response.status_code == 200
        read_data = read_response.json()
        assert read_data['success'] is True
        assert read_data['data']['name'] == 'Software Engineer'
        
        # 3. LIST - Test job title listing
        mock_db_manager.fetch_all.return_value = [mock_created_job_title]
        list_response = client.get("/api/job-titles")
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert list_data['success'] is True
        assert len(list_data['data']) == 1
        assert list_data['data'][0]['name'] == 'Software Engineer'
        
        # 4. SEARCH - Test job title search
        search_response = client.get("/api/job-titles?search=Software")
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data['success'] is True
        assert len(search_data['data']) == 1
    
    def test_complete_assignment_crud_workflow(self, client, mock_db_manager):
        """Test complete CRUD workflow for assignments (Requirement 3.4)"""
        # Test data
        assignment_data = {
            "person_id": 1,
            "unit_id": 1,
            "job_title_id": 1,
            "percentage": 100.0,
            "is_ad_interim": False,
            "is_unit_boss": False,
            "valid_from": "2023-01-01"
        }
        
        # 1. CREATE - Test assignment creation
        mock_db_manager.execute_query.return_value = Mock(lastrowid=1, rowcount=1)
        mock_created_assignment = {
            'id': 1,
            'person_id': 1,
            'unit_id': 1,
            'job_title_id': 1,
            'version': 1,
            'percentage': 1.0,
            'is_ad_interim': 0,
            'is_unit_boss': 0,
            'notes': None,
            'flags': None,
            'valid_from': '2023-01-01',
            'valid_to': None,
            'is_current': 1,
            'datetime_created': '2023-01-01T10:00:00',
            'datetime_updated': '2023-01-01T10:00:00',
            'person_name': 'Mario Rossi',
            'person_short_name': 'M. Rossi',
            'unit_name': 'IT Department',
            'unit_short_name': 'IT',
            'job_title_name': 'Software Engineer',
            'job_title_short_name': 'SW Eng'
        }
        mock_db_manager.fetch_one.return_value = mock_created_assignment
        
        create_response = client.post("/api/assignments", json=assignment_data)
        assert create_response.status_code == 201
        create_data = create_response.json()
        assert create_data['success'] is True
        assert create_data['data']['person_id'] == 1
        assert create_data['data']['version'] == 1
        assert create_data['data']['is_current'] == 1
        assignment_id = create_data['data']['id']
        
        # 2. READ - Test assignment retrieval
        read_response = client.get(f"/api/assignments/{assignment_id}")
        assert read_response.status_code == 200
        read_data = read_response.json()
        assert read_data['success'] is True
        assert read_data['data']['person_name'] == 'Mario Rossi'
        
        # 3. LIST - Test assignment listing
        mock_db_manager.fetch_all.return_value = [mock_created_assignment]
        list_response = client.get("/api/assignments")
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert list_data['success'] is True
        assert len(list_data['data']) == 1
        assert list_data['data'][0]['person_name'] == 'Mario Rossi'
        
        # 4. HISTORY - Test assignment history retrieval
        history_response = client.get(f"/api/assignments/{assignment_id}/history")
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert history_data['success'] is True
        
        # 5. TERMINATE - Test assignment termination
        terminate_response = client.post(f"/api/assignments/{assignment_id}/terminate", 
                                       json={"termination_date": "2023-12-31"})
        assert terminate_response.status_code == 200
        terminate_data = terminate_response.json()
        assert terminate_data['success'] is True


class TestAssignmentVersioningSystem:
    """Test assignment versioning system functionality (Requirements 4.1, 4.2, 4.3)"""
    
    def test_assignment_versioning_workflow(self, client, mock_db_manager):
        """Test complete assignment versioning workflow (Requirements 4.1, 4.2, 4.3)"""
        # Setup mock responses for versioning
        mock_db_manager.execute_query.return_value = Mock(lastrowid=1, rowcount=1)
        
        # 1. CREATE INITIAL ASSIGNMENT (Version 1)
        initial_assignment = {
            'id': 1,
            'person_id': 1,
            'unit_id': 1,
            'job_title_id': 1,
            'version': 1,
            'percentage': 1.0,
            'is_ad_interim': 0,
            'is_unit_boss': 0,
            'valid_from': '2023-01-01',
            'valid_to': None,
            'is_current': 1,
            'datetime_created': '2023-01-01T10:00:00',
            'datetime_updated': '2023-01-01T10:00:00',
            'person_name': 'Mario Rossi',
            'unit_name': 'IT Department',
            'job_title_name': 'Software Engineer'
        }
        mock_db_manager.fetch_one.return_value = initial_assignment
        
        assignment_data = {
            "person_id": 1,
            "unit_id": 1,
            "job_title_id": 1,
            "percentage": 100.0,
            "is_ad_interim": False,
            "is_unit_boss": False,
            "valid_from": "2023-01-01"
        }
        
        create_response = client.post("/api/assignments", json=assignment_data)
        assert create_response.status_code == 201
        create_data = create_response.json()
        assert create_data['data']['version'] == 1
        assert create_data['data']['is_current'] == 1
        
        # 2. CREATE MODIFIED ASSIGNMENT (Version 2)
        modified_assignment = initial_assignment.copy()
        modified_assignment.update({
            'id': 2,
            'version': 2,
            'percentage': 0.8,
            'valid_from': '2023-06-01',
            'datetime_created': '2023-06-01T10:00:00',
            'datetime_updated': '2023-06-01T10:00:00'
        })
        mock_db_manager.fetch_one.return_value = modified_assignment
        
        modified_assignment_data = {
            "person_id": 1,
            "unit_id": 1,
            "job_title_id": 1,
            "percentage": 80.0,  # Changed percentage
            "is_ad_interim": False,
            "is_unit_boss": False,
            "valid_from": "2023-06-01"
        }
        
        modify_response = client.post("/api/assignments", json=modified_assignment_data)
        assert modify_response.status_code == 201
        modify_data = modify_response.json()
        assert modify_data['data']['version'] == 2
        assert modify_data['data']['percentage'] == 0.8
        assert modify_data['data']['is_current'] == 1
        
        # 3. TEST VERSION HISTORY
        version_history = [
            modified_assignment,  # Version 2 (current)
            {
                **initial_assignment,
                'is_current': 0,
                'valid_to': '2023-05-31'
            }  # Version 1 (historical)
        ]
        mock_db_manager.fetch_all.return_value = version_history
        
        history_response = client.get("/api/assignments/2/history")
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert history_data['success'] is True
        assert len(history_data['data']) == 2
        
        # Verify version ordering (latest first)
        versions = history_data['data']
        assert versions[0]['version'] == 2
        assert versions[0]['is_current'] == 1
        assert versions[1]['version'] == 1
        assert versions[1]['is_current'] == 0
        
        # 4. TEST CURRENT ASSIGNMENTS FILTERING
        current_assignments = [modified_assignment]  # Only current version
        mock_db_manager.fetch_all.return_value = current_assignments
        
        current_response = client.get("/api/assignments?current_only=true")
        assert current_response.status_code == 200
        current_data = current_response.json()
        assert current_data['success'] is True
        assert len(current_data['data']) == 1
        assert current_data['data'][0]['is_current'] == 1
        assert current_data['data'][0]['version'] == 2
        
        # 5. TEST ASSIGNMENT TERMINATION
        terminate_response = client.post("/api/assignments/2/terminate", 
                                       json={"termination_date": "2023-12-31"})
        assert terminate_response.status_code == 200
        terminate_data = terminate_response.json()
        assert terminate_data['success'] is True
        assert 'terminated successfully' in terminate_data['message']
    
    def test_assignment_version_consistency(self, client, mock_db_manager):
        """Test assignment version consistency validation (Requirement 4.2)"""
        # Mock version history with consistent versioning
        consistent_history = [
            {
                'id': 3,
                'person_id': 1,
                'unit_id': 1,
                'job_title_id': 1,
                'version': 3,
                'percentage': 0.5,
                'is_current': 1,
                'valid_from': '2023-09-01',
                'valid_to': None,
                'datetime_created': '2023-09-01T10:00:00'
            },
            {
                'id': 2,
                'person_id': 1,
                'unit_id': 1,
                'job_title_id': 1,
                'version': 2,
                'percentage': 0.8,
                'is_current': 0,
                'valid_from': '2023-06-01',
                'valid_to': '2023-08-31',
                'datetime_created': '2023-06-01T10:00:00'
            },
            {
                'id': 1,
                'person_id': 1,
                'unit_id': 1,
                'job_title_id': 1,
                'version': 1,
                'percentage': 1.0,
                'is_current': 0,
                'valid_from': '2023-01-01',
                'valid_to': '2023-05-31',
                'datetime_created': '2023-01-01T10:00:00'
            }
        ]
        
        mock_db_manager.fetch_all.return_value = consistent_history
        
        # Test version history consistency
        history_response = client.get("/api/assignments/3/history")
        assert history_response.status_code == 200
        history_data = history_response.json()
        
        versions = history_data['data']
        assert len(versions) == 3
        
        # Verify version sequence
        assert versions[0]['version'] == 3
        assert versions[1]['version'] == 2
        assert versions[2]['version'] == 1
        
        # Verify only one current version
        current_versions = [v for v in versions if v['is_current'] == 1]
        assert len(current_versions) == 1
        assert current_versions[0]['version'] == 3
    
    def test_assignment_percentage_validation(self, client, mock_db_manager):
        """Test assignment percentage validation in versioning (Requirement 4.1)"""
        # Test invalid percentage values
        invalid_assignment_data = {
            "person_id": 1,
            "unit_id": 1,
            "job_title_id": 1,
            "percentage": 150.0,  # Invalid: > 100%
            "is_ad_interim": False,
            "is_unit_boss": False,
            "valid_from": "2023-01-01"
        }
        
        # Should return validation error
        response = client.post("/api/assignments", json=invalid_assignment_data)
        assert response.status_code == 422  # Validation error
        
        # Test validation endpoint
        validation_response = client.get(
            "/api/validate/assignment?person_id=1&unit_id=1&job_title_id=1&percentage=150"
        )
        assert validation_response.status_code == 200
        validation_data = validation_response.json()
        assert validation_data['data']['is_valid'] is False
        assert len(validation_data['data']['errors']) > 0


class TestOrganizationalChartVisualization:
    """Test organizational chart visualization with different data sets (Requirement 6.1)"""
    
    def test_orgchart_tree_visualization_simple(self, client, mock_db_manager):
        """Test orgchart tree visualization with simple hierarchy"""
        # Mock simple organizational structure
        simple_tree = {
            'id': 1,
            'name': 'CEO Office',
            'unit_type_id': 1,  # Function unit
            'children': [
                {
                    'id': 2,
                    'name': 'IT Department',
                    'unit_type_id': 2,  # Organizational unit
                    'children': [],
                    'persons': [
                        {
                            'id': 1,
                            'name': 'Mario Rossi',
                            'job_title': 'IT Manager',
                            'is_unit_boss': True
                        }
                    ]
                },
                {
                    'id': 3,
                    'name': 'HR Department',
                    'unit_type_id': 2,
                    'children': [],
                    'persons': [
                        {
                            'id': 2,
                            'name': 'Anna Bianchi',
                            'job_title': 'HR Manager',
                            'is_unit_boss': True
                        }
                    ]
                }
            ],
            'persons': [
                {
                    'id': 3,
                    'name': 'Giuseppe Verdi',
                    'job_title': 'CEO',
                    'is_unit_boss': True
                }
            ]
        }
        
        with patch('app.services.orgchart.OrgchartService.get_complete_tree') as mock_tree:
            mock_tree.return_value = simple_tree
            
            response = client.get("/api/orgchart/tree")
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            
            tree_data = data['data']
            assert tree_data['name'] == 'CEO Office'
            assert len(tree_data['children']) == 2
            assert len(tree_data['persons']) == 1
            
            # Verify unit type rendering requirements
            assert tree_data['unit_type_id'] == 1  # Function unit (bold-framed)
            assert tree_data['children'][0]['unit_type_id'] == 2  # Organizational unit (normal-framed)
            assert tree_data['children'][1]['unit_type_id'] == 2
    
    def test_orgchart_tree_visualization_complex(self, client, mock_db_manager):
        """Test orgchart tree visualization with complex multi-level hierarchy"""
        # Mock complex organizational structure
        complex_tree = {
            'id': 1,
            'name': 'Company HQ',
            'unit_type_id': 1,
            'children': [
                {
                    'id': 2,
                    'name': 'Technology Division',
                    'unit_type_id': 2,
                    'children': [
                        {
                            'id': 4,
                            'name': 'Software Development',
                            'unit_type_id': 2,
                            'children': [
                                {
                                    'id': 6,
                                    'name': 'Frontend Team',
                                    'unit_type_id': 2,
                                    'children': [],
                                    'persons': [
                                        {'id': 4, 'name': 'Developer 1', 'job_title': 'Frontend Developer'},
                                        {'id': 5, 'name': 'Developer 2', 'job_title': 'Frontend Developer'}
                                    ]
                                },
                                {
                                    'id': 7,
                                    'name': 'Backend Team',
                                    'unit_type_id': 2,
                                    'children': [],
                                    'persons': [
                                        {'id': 6, 'name': 'Developer 3', 'job_title': 'Backend Developer'},
                                        {'id': 7, 'name': 'Developer 4', 'job_title': 'Backend Developer'}
                                    ]
                                }
                            ],
                            'persons': [
                                {'id': 3, 'name': 'Tech Lead', 'job_title': 'Technical Lead', 'is_unit_boss': True}
                            ]
                        },
                        {
                            'id': 5,
                            'name': 'DevOps',
                            'unit_type_id': 2,
                            'children': [],
                            'persons': [
                                {'id': 8, 'name': 'DevOps Engineer', 'job_title': 'DevOps Engineer'}
                            ]
                        }
                    ],
                    'persons': [
                        {'id': 2, 'name': 'CTO', 'job_title': 'Chief Technology Officer', 'is_unit_boss': True}
                    ]
                },
                {
                    'id': 3,
                    'name': 'Business Division',
                    'unit_type_id': 2,
                    'children': [
                        {
                            'id': 8,
                            'name': 'Sales',
                            'unit_type_id': 2,
                            'children': [],
                            'persons': [
                                {'id': 9, 'name': 'Sales Manager', 'job_title': 'Sales Manager', 'is_unit_boss': True},
                                {'id': 10, 'name': 'Sales Rep', 'job_title': 'Sales Representative'}
                            ]
                        }
                    ],
                    'persons': [
                        {'id': 11, 'name': 'Business Director', 'job_title': 'Business Director', 'is_unit_boss': True}
                    ]
                }
            ],
            'persons': [
                {'id': 1, 'name': 'CEO', 'job_title': 'Chief Executive Officer', 'is_unit_boss': True}
            ]
        }
        
        with patch('app.services.orgchart.OrgchartService.get_complete_tree') as mock_tree:
            mock_tree.return_value = complex_tree
            
            response = client.get("/api/orgchart/tree")
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            
            tree_data = data['data']
            assert tree_data['name'] == 'Company HQ'
            assert len(tree_data['children']) == 2
            
            # Verify multi-level hierarchy
            tech_division = tree_data['children'][0]
            assert tech_division['name'] == 'Technology Division'
            assert len(tech_division['children']) == 2
            
            # Verify deep nesting
            software_dev = tech_division['children'][0]
            assert software_dev['name'] == 'Software Development'
            assert len(software_dev['children']) == 2
            
            # Verify leaf nodes have persons
            frontend_team = software_dev['children'][0]
            assert frontend_team['name'] == 'Frontend Team'
            assert len(frontend_team['persons']) == 2
            assert len(frontend_team['children']) == 0
    
    def test_orgchart_statistics_integration(self, client, mock_db_manager):
        """Test orgchart statistics with different data sets"""
        # Mock organizational statistics
        mock_statistics = {
            'total_units': 8,
            'total_persons': 11,
            'total_assignments': 11,
            'units_by_type': {
                'function': 1,
                'organizational': 7
            },
            'persons_by_unit': {
                'Company HQ': 1,
                'Technology Division': 1,
                'Software Development': 1,
                'Frontend Team': 2,
                'Backend Team': 2,
                'DevOps': 1,
                'Business Division': 1,
                'Sales': 2
            },
            'vacant_positions': 0,
            'average_span_of_control': 2.5,
            'max_hierarchy_depth': 4
        }
        
        with patch('app.services.orgchart.OrgchartService.get_organization_overview') as mock_overview, \
             patch('app.services.orgchart.OrgchartService.get_organization_metrics') as mock_metrics:
            
            mock_overview.return_value = {
                'total_units': 8,
                'total_persons': 11,
                'total_assignments': 11
            }
            mock_metrics.return_value = {
                'units_by_type': {'function': 1, 'organizational': 7},
                'persons_by_unit': mock_statistics['persons_by_unit'],
                'vacant_positions': 0,
                'average_span_of_control': 2.5,
                'max_hierarchy_depth': 4
            }
            
            response = client.get("/api/orgchart/statistics")
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            
            stats = data['data']
            assert stats['total_units'] == 8
            assert stats['total_persons'] == 11
            assert stats['units_by_type']['function'] == 1
            assert stats['units_by_type']['organizational'] == 7
            assert stats['average_span_of_control'] == 2.5
            assert stats['max_hierarchy_depth'] == 4
    
    def test_orgchart_vacant_positions(self, client, mock_db_manager):
        """Test orgchart vacant positions detection"""
        # Mock vacant positions
        mock_vacant_positions = [
            {
                'unit_id': 5,
                'unit_name': 'DevOps',
                'job_title_id': 3,
                'job_title_name': 'Senior DevOps Engineer',
                'required_count': 2,
                'current_count': 1,
                'vacant_count': 1
            },
            {
                'unit_id': 8,
                'unit_name': 'Sales',
                'job_title_id': 4,
                'job_title_name': 'Sales Representative',
                'required_count': 3,
                'current_count': 1,
                'vacant_count': 2
            }
        ]
        
        with patch('app.services.orgchart.OrgchartService.get_vacant_positions') as mock_vacant:
            mock_vacant.return_value = mock_vacant_positions
            
            response = client.get("/api/orgchart/vacant-positions")
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            
            vacant_positions = data['data']
            assert len(vacant_positions) == 2
            assert vacant_positions[0]['unit_name'] == 'DevOps'
            assert vacant_positions[0]['vacant_count'] == 1
            assert vacant_positions[1]['unit_name'] == 'Sales'
            assert vacant_positions[1]['vacant_count'] == 2
    
    def test_orgchart_subtree_visualization(self, client, mock_db_manager):
        """Test orgchart subtree visualization for specific units"""
        # Mock subtree for specific unit
        subtree_data = {
            'id': 2,
            'name': 'Technology Division',
            'unit_type_id': 2,
            'children': [
                {
                    'id': 4,
                    'name': 'Software Development',
                    'unit_type_id': 2,
                    'children': [],
                    'persons': [
                        {'id': 3, 'name': 'Tech Lead', 'job_title': 'Technical Lead'}
                    ]
                }
            ],
            'persons': [
                {'id': 2, 'name': 'CTO', 'job_title': 'Chief Technology Officer'}
            ]
        }
        
        with patch('app.services.orgchart.OrgchartService.get_subtree') as mock_subtree:
            mock_subtree.return_value = subtree_data
            
            response = client.get("/api/orgchart/tree?unit_id=2")
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            
            tree_data = data['data']
            assert tree_data['id'] == 2
            assert tree_data['name'] == 'Technology Division'
            assert len(tree_data['children']) == 1
            assert len(tree_data['persons']) == 1


class TestGlobalSearchIntegration:
    """Test global search functionality across all entities"""
    
    def test_global_search_integration(self, client, mock_db_manager):
        """Test global search across all entity types"""
        # Mock search results for different entity types
        def mock_fetch_all(query, params=None):
            if 'units' in query.lower():
                return [{
                    'id': 1, 'name': 'IT Department', 'short_name': 'IT', 'unit_type_id': 1,
                    'parent_unit_id': None, 'start_date': '2023-01-01', 'end_date': None,
                    'aliases': '[]', 'datetime_created': '2023-01-01T10:00:00',
                    'datetime_updated': '2023-01-01T10:00:00', 'parent_name': None,
                    'children_count': 0, 'person_count': 2, 'level': 0, 'path': '/IT',
                    'full_path': 'IT Department'
                }]
            elif 'persons' in query.lower():
                return [{
                    'id': 1, 'name': 'Mario Rossi', 'short_name': 'M. Rossi',
                    'email': 'mario@example.com', 'datetime_created': '2023-01-01T10:00:00',
                    'datetime_updated': '2023-01-01T10:00:00', 'current_assignments_count': 1,
                    'total_assignments_count': 1
                }]
            elif 'job_titles' in query.lower():
                return [{
                    'id': 1, 'name': 'Software Engineer', 'short_name': 'SW Eng',
                    'aliases': '[]', 'start_date': '2023-01-01', 'end_date': None,
                    'datetime_created': '2023-01-01T10:00:00', 'datetime_updated': '2023-01-01T10:00:00',
                    'current_assignments_count': 1, 'total_assignments_count': 1
                }]
            return []
        
        mock_db_manager.fetch_all.side_effect = mock_fetch_all
        
        response = client.get("/api/search?query=test&entity_types=units&entity_types=persons&entity_types=job_titles")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        
        search_results = data['data']
        assert 'units' in search_results
        assert 'persons' in search_results
        assert 'job_titles' in search_results
        
        assert len(search_results['units']) == 1
        assert len(search_results['persons']) == 1
        assert len(search_results['job_titles']) == 1
        
        assert search_results['units'][0]['name'] == 'IT Department'
        assert search_results['persons'][0]['name'] == 'Mario Rossi'
        assert search_results['job_titles'][0]['name'] == 'Software Engineer'


class TestSystemHealthAndValidation:
    """Test system health checks and validation endpoints"""
    
    def test_api_health_check(self, client):
        """Test API health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['status'] == 'healthy'
        assert 'timestamp' in data['data']
        assert data['message'] == 'API is healthy'
    
    def test_assignment_validation_endpoint(self, client):
        """Test assignment validation endpoint"""
        # Test valid assignment
        response = client.get("/api/validate/assignment?person_id=1&unit_id=1&job_title_id=1&percentage=100")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'is_valid' in data['data']
        assert 'warnings' in data['data']
        assert 'errors' in data['data']
        
        # Test invalid assignment (percentage > 100)
        response = client.get("/api/validate/assignment?person_id=1&unit_id=1&job_title_id=1&percentage=150")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['is_valid'] is False
        assert len(data['data']['errors']) > 0
    
    def test_global_statistics_endpoint(self, client):
        """Test global statistics endpoint"""
        with patch('app.services.unit.UnitService.count') as mock_unit_count, \
             patch('app.services.person.PersonService.count') as mock_person_count, \
             patch('app.services.job_title.JobTitleService.count') as mock_job_title_count, \
             patch('app.services.assignment.AssignmentService.get_current_assignments') as mock_assignments, \
             patch('app.services.assignment.AssignmentService.get_statistics') as mock_stats:
            
            mock_unit_count.return_value = 5
            mock_person_count.return_value = 10
            mock_job_title_count.return_value = 8
            mock_assignments.return_value = [Mock()] * 12  # 12 active assignments
            mock_stats.return_value = {
                'total_versions': 15,
                'average_assignment_duration': 365,
                'most_common_job_title': 'Software Engineer'
            }
            
            response = client.get("/api/stats")
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            
            stats = data['data']
            assert stats['units'] == 5
            assert stats['persons'] == 10
            assert stats['job_titles'] == 8
            assert stats['active_assignments'] == 12
            assert 'total_versions' in stats
            assert 'average_assignment_duration' in stats