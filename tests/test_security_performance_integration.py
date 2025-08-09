"""
Integration tests for security and performance optimizations in import/export system.

This module tests the integration of security measures and performance optimizations
to ensure they work together correctly and meet all requirements.

Tests Requirements 1.1, 2.1, 5.1, 5.2, 7.1 security and performance measures.
"""

import pytest
import tempfile
import json
import csv
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException, UploadFile, Request
from io import BytesIO, StringIO

from app.services.import_export_security import ImportExportSecurityService, FileSecurityConfig
from app.services.import_export_performance import ImportExportPerformanceService, PerformanceConfig
from app.services.import_export import ImportExportService
from app.models.import_export import ImportOptions, ExportOptions, FileFormat, ConflictResolutionStrategy


class TestSecurityPerformanceIntegration:
    """Integration tests for security and performance optimizations."""
    
    @pytest.fixture
    def security_service(self):
        """Create security service for testing."""
        config = FileSecurityConfig(
            max_file_size=10 * 1024 * 1024,  # 10MB for testing
            max_files_per_hour=10,
            max_total_size_per_hour=50 * 1024 * 1024  # 50MB for testing
        )
        return ImportExportSecurityService(config)
    
    @pytest.fixture
    def performance_service(self):
        """Create performance service for testing."""
        config = PerformanceConfig(
            max_memory_usage_mb=256,  # 256MB for testing
            default_batch_size=50,
            stream_threshold_mb=5,  # 5MB for testing
            parallel_threshold=100
        )
        return ImportExportPerformanceService(config)
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request for testing."""
        request = Mock(spec=Request)
        request.headers = {'user-agent': 'test-browser/1.0'}
        request.client = Mock()
        request.client.host = '127.0.0.1'
        return request
    
    def create_test_csv_file(self, size_mb: float = 1.0) -> str:
        """Create a test CSV file of specified size."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        
        # Write CSV header
        temp_file.write('id,name,email,first_name,last_name\n')
        
        # Calculate number of rows needed for target size
        row_size = len('1,Test User,test@example.com,Test,User\n')
        target_bytes = size_mb * 1024 * 1024
        num_rows = max(1, int(target_bytes / row_size))
        
        # Write data rows
        for i in range(num_rows):
            temp_file.write(f'{i+1},Test User {i+1},test{i+1}@example.com,Test,User\n')
        
        temp_file.close()
        return temp_file.name
    
    def create_test_json_file(self, size_mb: float = 1.0) -> str:
        """Create a test JSON file of specified size."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        
        # Calculate number of records needed for target size
        sample_record = {
            "id": 1,
            "name": "Test User",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        }
        record_size = len(json.dumps(sample_record))
        target_bytes = size_mb * 1024 * 1024
        num_records = max(1, int(target_bytes / record_size))
        
        # Create data structure
        data = {
            "metadata": {
                "export_date": "2024-01-01T00:00:00Z",
                "version": "1.0"
            },
            "persons": []
        }
        
        # Add records
        for i in range(num_records):
            data["persons"].append({
                "id": i + 1,
                "name": f"Test User {i + 1}",
                "email": f"test{i + 1}@example.com",
                "first_name": "Test",
                "last_name": "User"
            })
        
        json.dump(data, temp_file, indent=2)
        temp_file.close()
        return temp_file.name
    
    def create_malicious_csv_file(self) -> str:
        """Create a CSV file with malicious content."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write('id,name,email\n')
        temp_file.write('1,"<script>alert(\'xss\')</script>","test@example.com"\n')
        temp_file.write('2,"Normal User","normal@example.com"\n')
        temp_file.write('3,"<?php echo \'injection\'; ?>","php@example.com"\n')
        temp_file.close()
        return temp_file.name
    
    def test_file_upload_security_validation(self, security_service, mock_request):
        """Test comprehensive file upload security validation."""
        # Test valid file
        valid_file_path = self.create_test_csv_file(0.1)  # 100KB file
        
        try:
            with open(valid_file_path, 'rb') as f:
                file_content = f.read()
            
            upload_file = UploadFile(
                filename="test.csv",
                file=BytesIO(file_content),
                size=len(file_content),
                headers={'content-type': 'text/csv'}
            )
            
            # Should not raise exception
            security_service.validate_file_upload(upload_file, mock_request, "import")
        
        finally:
            os.unlink(valid_file_path)
    
    def test_file_upload_security_rejection(self, security_service, mock_request):
        """Test security rejection of malicious files."""
        malicious_file_path = self.create_malicious_csv_file()
        
        try:
            with open(malicious_file_path, 'rb') as f:
                file_content = f.read()
            
            upload_file = UploadFile(
                filename="malicious.csv",
                file=BytesIO(file_content),
                size=len(file_content),
                headers={'content-type': 'text/csv'}
            )
            
            # Should raise HTTPException due to malicious content
            with pytest.raises(HTTPException) as exc_info:
                security_service.validate_file_upload(upload_file, mock_request, "import")
            
            assert exc_info.value.status_code == 400
            assert "contenuto potenzialmente pericoloso" in exc_info.value.detail
        
        finally:
            os.unlink(malicious_file_path)
    
    def test_file_size_limit_enforcement(self, security_service, mock_request):
        """Test file size limit enforcement."""
        # Create file larger than limit (10MB limit in test config)
        large_file_path = self.create_test_csv_file(15.0)  # 15MB file
        
        try:
            with open(large_file_path, 'rb') as f:
                file_content = f.read()
            
            upload_file = UploadFile(
                filename="large.csv",
                file=BytesIO(file_content),
                size=len(file_content),
                headers={'content-type': 'text/csv'}
            )
            
            # Should raise HTTPException due to size limit
            with pytest.raises(HTTPException) as exc_info:
                security_service.validate_file_upload(upload_file, mock_request, "import")
            
            assert exc_info.value.status_code == 413
            assert "File troppo grande" in exc_info.value.detail
        
        finally:
            os.unlink(large_file_path)
    
    def test_rate_limiting_enforcement(self, security_service, mock_request):
        """Test upload rate limiting enforcement."""
        # Upload multiple files to trigger rate limit
        for i in range(12):  # Exceed limit of 10 files per hour
            file_path = self.create_test_csv_file(0.1)
            
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                upload_file = UploadFile(
                    filename=f"test{i}.csv",
                    file=BytesIO(file_content),
                    size=len(file_content),
                    headers={'content-type': 'text/csv'}
                )
                
                if i < 10:
                    # First 10 should succeed
                    security_service.validate_file_upload(upload_file, mock_request, "import")
                else:
                    # 11th and 12th should fail due to rate limit
                    with pytest.raises(HTTPException) as exc_info:
                        security_service.validate_file_upload(upload_file, mock_request, "import")
                    
                    assert exc_info.value.status_code == 429
                    assert "Limite di upload superato" in exc_info.value.detail
            
            finally:
                os.unlink(file_path)
    
    def test_data_sanitization(self, security_service):
        """Test input data sanitization."""
        # Test data with safe content that should be sanitized but not rejected
        safe_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'description': 'Normal text description',
            'notes': 'Some notes about the user'
        }
        
        sanitized_data = security_service.sanitize_import_data(safe_data, 'persons')
        
        # Check that safe content is preserved
        assert sanitized_data['name'] == 'Test User'
        assert sanitized_data['email'] == 'test@example.com'
        assert sanitized_data['description'] == 'Normal text description'
        assert sanitized_data['notes'] == 'Some notes about the user'
        
        # Test that malicious content is properly rejected
        malicious_data = {
            'name': '<script>alert("xss")</script>',
            'email': 'test@example.com'
        }
        
        # Should raise ImportExportValidationError for malicious content
        with pytest.raises(Exception):  # Could be ImportExportValidationError or SecurityValidationError
            security_service.sanitize_import_data(malicious_data, 'persons')
    
    def test_performance_streaming_threshold(self, performance_service):
        """Test performance streaming is triggered for large files."""
        # Create file larger than streaming threshold (5MB in test config)
        large_file_path = self.create_test_csv_file(7.0)  # 7MB file
        
        try:
            # Should recommend streaming
            should_stream = performance_service.streaming_processor.should_stream_file(large_file_path)
            assert should_stream == True
            
            # Test streaming functionality
            record_count = 0
            for record in performance_service.stream_file_records(large_file_path, 'csv'):
                record_count += 1
                if record_count >= 10:  # Test first 10 records
                    break
            
            assert record_count == 10
        
        finally:
            os.unlink(large_file_path)
    
    def test_performance_batch_optimization(self, performance_service):
        """Test adaptive batch size optimization."""
        # Test with different dataset sizes
        small_dataset = list(range(50))
        medium_dataset = list(range(500))
        large_dataset = list(range(5000))
        
        # Small dataset should use smaller batch size
        small_batch_size = performance_service.batch_processor.get_optimal_batch_size(len(small_dataset))
        assert small_batch_size <= 50
        
        # Medium dataset should use default batch size
        medium_batch_size = performance_service.batch_processor.get_optimal_batch_size(len(medium_dataset))
        assert medium_batch_size == performance_service.config.default_batch_size
        
        # Large dataset should use larger batch size
        large_batch_size = performance_service.batch_processor.get_optimal_batch_size(len(large_dataset))
        assert large_batch_size >= performance_service.config.default_batch_size
    
    def test_performance_parallel_processing_threshold(self, performance_service):
        """Test parallel processing is triggered for large datasets."""
        # Small dataset should not use parallel processing
        small_dataset = list(range(50))
        should_parallel_small = performance_service.parallel_processor.should_use_parallel_processing(len(small_dataset))
        assert should_parallel_small == False
        
        # Large dataset should use parallel processing
        large_dataset = list(range(1500))  # Above threshold of 1000
        should_parallel_large = performance_service.parallel_processor.should_use_parallel_processing(len(large_dataset))
        assert should_parallel_large == True
    
    def test_memory_management(self, performance_service):
        """Test memory management functionality."""
        memory_manager = performance_service.memory_manager
        
        # Test memory usage monitoring
        initial_memory = memory_manager.get_memory_usage_mb()
        assert initial_memory > 0
        
        # Test memory check
        memory_ok = memory_manager.check_memory_usage()
        assert memory_ok == True  # Should be OK for test environment
        
        # Test garbage collection
        memory_manager.force_garbage_collection()  # Should not raise exception
    
    @patch('app.services.import_export.ImportExportService')
    def test_integrated_security_performance_workflow(self, mock_import_service, 
                                                    security_service, performance_service, mock_request):
        """Test integrated security and performance workflow."""
        # Create test file
        test_file_path = self.create_test_csv_file(2.0)  # 2MB file
        
        try:
            # Step 1: Security validation
            with open(test_file_path, 'rb') as f:
                file_content = f.read()
            
            upload_file = UploadFile(
                filename="test.csv",
                file=BytesIO(file_content),
                size=len(file_content),
                headers={'content-type': 'text/csv'}
            )
            
            # Security validation should pass
            security_service.validate_file_upload(upload_file, mock_request, "import")
            
            # Step 2: Performance optimization
            optimization_config = performance_service.optimize_import_processing(
                test_file_path, 'csv', 1000
            )
            
            # Should recommend appropriate optimizations
            assert 'batch_size' in optimization_config
            assert 'use_streaming' in optimization_config
            assert 'memory_monitoring' in optimization_config
            
            # Step 3: Access control validation
            security_service.validate_access_permissions(mock_request, "import", ['persons'])
            
            # Step 4: Data sanitization (simulate)
            test_data = {
                'name': 'Test User',
                'email': 'test@example.com'
            }
            sanitized_data = security_service.sanitize_import_data(test_data, 'persons')
            assert sanitized_data['name'] == 'Test User'
            assert sanitized_data['email'] == 'test@example.com'
        
        finally:
            os.unlink(test_file_path)
    
    def test_security_headers_generation(self, security_service):
        """Test security headers are properly generated."""
        headers = security_service.get_security_headers()
        
        # Check required security headers
        assert 'X-Content-Type-Options' in headers
        assert headers['X-Content-Type-Options'] == 'nosniff'
        assert 'X-Frame-Options' in headers
        assert headers['X-Frame-Options'] == 'DENY'
        assert 'X-XSS-Protection' in headers
        assert 'Cache-Control' in headers
        assert 'no-cache' in headers['Cache-Control']
    
    def test_performance_metrics_collection(self, performance_service):
        """Test performance metrics collection."""
        metrics = performance_service.create_performance_metrics()
        
        # Simulate processing
        time.sleep(0.1)  # Small delay
        metrics.records_processed = 100
        metrics.batch_count = 5
        metrics.end_time = time.time()
        
        # Test metrics calculation
        assert metrics.total_time > 0
        assert metrics.records_per_second > 0
        
        # Test performance monitoring (should not raise exception)
        performance_service.monitor_performance(metrics, "test_operation")
    
    def test_quarantine_functionality(self, security_service, mock_request):
        """Test file quarantine functionality."""
        # Create malicious file
        malicious_file_path = self.create_malicious_csv_file()
        
        try:
            with open(malicious_file_path, 'rb') as f:
                file_content = f.read()
            
            upload_file = UploadFile(
                filename="malicious.csv",
                file=BytesIO(file_content),
                size=len(file_content),
                headers={'content-type': 'text/csv'}
            )
            
            # Should quarantine the file and raise exception
            with pytest.raises(HTTPException):
                security_service.validate_file_upload(upload_file, mock_request, "import")
            
            # Check that quarantine directory exists
            assert security_service.quarantine_dir.exists()
        
        finally:
            os.unlink(malicious_file_path)
    
    def test_cleanup_functionality(self, security_service, performance_service):
        """Test cleanup functionality."""
        # Test security service cleanup
        cleaned_count = security_service.cleanup_quarantine(days_old=0)
        assert cleaned_count >= 0  # Should not raise exception
        
        # Test performance service cleanup
        performance_service.cleanup()  # Should not raise exception
    
    def teardown_method(self):
        """Clean up after each test."""
        # Clean up any temporary files that might have been left behind
        import glob
        temp_files = glob.glob('/tmp/tmp*')
        for temp_file in temp_files:
            try:
                if os.path.isfile(temp_file) and (temp_file.endswith('.csv') or temp_file.endswith('.json')):
                    os.unlink(temp_file)
            except:
                pass  # Ignore cleanup errors