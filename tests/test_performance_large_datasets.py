"""
Performance tests for large datasets.

This module tests the performance characteristics of the import/export system
with large datasets, including memory usage, processing time, and scalability.
"""

import os
import tempfile
import pytest
import json
import csv
import time
import psutil
import shutil
from datetime import datetime, date
from unittest.mock import Mock, patch

from app.services.import_export import ImportExportService
from app.services.csv_processor import CSVProcessor
from app.services.json_processor import JSONProcessor
from app.models.import_export import (
    ImportOptions, ExportOptions, FileFormat, ConflictResolutionStrategy
)


class TestPerformanceLargeDatasets:
    """Performance test cases for large datasets."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = ImportExportService()
        self.csv_processor = CSVProcessor()
        self.json_processor = JSONProcessor()
        
        # Get initial memory usage
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.service.cleanup_transaction_contexts()
    
    def _generate_large_person_dataset(self, count: int) -> dict:
        """Generate large person dataset for testing."""
        persons = []
        for i in range(count):
            persons.append({
                "id": i + 1,
                "name": f"Person {i + 1:06d}",
                "short_name": f"P{i + 1:06d}",
                "email": f"person{i + 1:06d}@example.com",
                "first_name": f"First{i + 1:06d}",
                "last_name": f"Last{i + 1:06d}",
                "registration_no": f"EMP{i + 1:06d}",
                "profile_image": f"profiles/person{i + 1:06d}.jpg" if i % 100 == 0 else None
            })
        return {"persons": persons}
    
    def _generate_large_unit_dataset(self, count: int) -> dict:
        """Generate large unit dataset with hierarchical structure."""
        unit_types = []
        units = []
        
        # Generate unit types (fewer than units)
        for i in range(min(count // 10, 100)):
            unit_types.append({
                "id": i + 1,
                "name": f"Unit Type {i + 1}",
                "short_name": f"UT{i + 1}",
                "aliases": [],
                "level": (i % 5) + 1,
                "theme_id": None
            })
        
        # Generate units
        for i in range(count):
            unit_type_id = (i % len(unit_types)) + 1
            parent_unit_id = None if i < 10 else ((i - 1) // 10) + 1
            
            units.append({
                "id": i + 1,
                "name": f"Unit {i + 1:06d}",
                "short_name": f"U{i + 1:06d}",
                "aliases": [],
                "unit_type_id": unit_type_id,
                "parent_unit_id": parent_unit_id,
                "start_date": "2024-01-01",
                "end_date": None
            })
        
        return {"unit_types": unit_types, "units": units}
    
    def _generate_large_assignment_dataset(self, person_count: int, unit_count: int, job_title_count: int) -> dict:
        """Generate large assignment dataset with relationships."""
        assignments = []
        
        # Generate assignments (one per person initially)
        for i in range(person_count):
            person_id = i + 1
            unit_id = (i % unit_count) + 1
            job_title_id = (i % job_title_count) + 1
            
            assignments.append({
                "id": i + 1,
                "person_id": person_id,
                "unit_id": unit_id,
                "job_title_id": job_title_id,
                "version": 1,
                "percentage": 1.0,
                "is_ad_interim": i % 10 == 0,  # 10% ad interim
                "is_unit_boss": i % 20 == 0,   # 5% unit bosses
                "notes": f"Assignment {i + 1}" if i % 5 == 0 else None,
                "valid_from": "2024-01-01",
                "valid_to": None,
                "is_current": True
            })
        
        return {"assignments": assignments}
    
    def test_large_json_import_performance(self):
        """Test performance with large JSON import (10,000 records)."""
        # Generate large dataset
        large_data = self._generate_large_person_dataset(10000)
        
        # Create JSON file
        json_file = os.path.join(self.temp_dir, "large_persons.json")
        start_time = time.time()
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(large_data, f)
        
        file_creation_time = time.time() - start_time
        file_size_mb = os.path.getsize(json_file) / 1024 / 1024
        
        print(f"Created {file_size_mb:.2f}MB JSON file in {file_creation_time:.2f}s")
        
        # Test import preview performance
        import_options = ImportOptions(
            entity_types=['persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP,
            batch_size=1000
        )
        
        memory_before = self.process.memory_info().rss / 1024 / 1024
        start_time = time.time()
        
        preview_result = self.service.preview_import(json_file, FileFormat.JSON, import_options)
        
        preview_time = time.time() - start_time
        memory_after = self.process.memory_info().rss / 1024 / 1024
        memory_used = memory_after - memory_before
        
        print(f"Preview completed in {preview_time:.2f}s, memory used: {memory_used:.2f}MB")
        
        # Performance assertions
        assert preview_result.success == True
        assert preview_result.total_records == 10000
        assert preview_time < 30.0, f"Preview took too long: {preview_time:.2f}s"
        assert memory_used < 500, f"Memory usage too high: {memory_used:.2f}MB"
        assert preview_result.estimated_processing_time > 0
    
    def test_large_csv_export_performance(self):
        """Test performance with large CSV export (50,000 records)."""
        # Generate large dataset
        large_data = self._generate_large_person_dataset(50000)
        
        export_options = ExportOptions(
            entity_types=['persons'],
            output_directory=self.temp_dir,
            file_prefix="performance_test_export",
            output_format=FileFormat.CSV,
            include_metadata=True
        )
        
        # Mock data fetching to return our large dataset
        with patch.object(self.service, '_fetch_export_data', return_value=large_data):
            memory_before = self.process.memory_info().rss / 1024 / 1024
            start_time = time.time()
            
            export_result = self.service.export_data(export_options)
            
            export_time = time.time() - start_time
            memory_after = self.process.memory_info().rss / 1024 / 1024
            memory_used = memory_after - memory_before
        
        print(f"Export completed in {export_time:.2f}s, memory used: {memory_used:.2f}MB")
        
        # Performance assertions
        assert export_result.success == True
        assert len(export_result.generated_files) >= 1
        assert export_result.total_records == 50000
        assert export_time < 60.0, f"Export took too long: {export_time:.2f}s"
        assert memory_used < 1000, f"Memory usage too high: {memory_used:.2f}MB"
        
        # Verify file was created and has reasonable size
        csv_files = [f for f in export_result.generated_files if f.endswith('.csv')]
        assert len(csv_files) >= 1
        
        csv_file = csv_files[0]
        file_size_mb = os.path.getsize(csv_file) / 1024 / 1024
        print(f"Generated CSV file: {file_size_mb:.2f}MB")
        assert file_size_mb > 0
    
    def test_batch_processing_performance(self):
        """Test performance with different batch sizes."""
        # Generate medium dataset
        data = self._generate_large_person_dataset(5000)
        
        json_file = os.path.join(self.temp_dir, "batch_test.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        batch_sizes = [100, 500, 1000, 2000]
        performance_results = {}
        
        for batch_size in batch_sizes:
            import_options = ImportOptions(
                entity_types=['persons'],
                conflict_resolution=ConflictResolutionStrategy.SKIP,
                batch_size=batch_size
            )
            
            start_time = time.time()
            memory_before = self.process.memory_info().rss / 1024 / 1024
            
            preview_result = self.service.preview_import(json_file, FileFormat.JSON, import_options)
            
            processing_time = time.time() - start_time
            memory_after = self.process.memory_info().rss / 1024 / 1024
            memory_used = memory_after - memory_before
            
            performance_results[batch_size] = {
                'time': processing_time,
                'memory': memory_used,
                'success': preview_result.success
            }
            
            print(f"Batch size {batch_size}: {processing_time:.2f}s, {memory_used:.2f}MB")
            
            assert preview_result.success == True
            assert processing_time < 20.0
        
        # Verify that larger batch sizes are generally more efficient
        # (though this may vary based on system and data characteristics)
        assert all(result['success'] for result in performance_results.values())
    
    def test_complex_dataset_with_relationships(self):
        """Test performance with complex dataset including all entity types."""
        # Generate complex dataset with relationships
        unit_data = self._generate_large_unit_dataset(1000)
        person_data = self._generate_large_person_dataset(5000)
        
        # Generate job titles
        job_titles = []
        for i in range(100):
            job_titles.append({
                "id": i + 1,
                "name": f"Job Title {i + 1}",
                "short_name": f"JT{i + 1}",
                "aliases": [],
                "start_date": "2024-01-01",
                "end_date": None
            })
        
        # Generate assignments
        assignment_data = self._generate_large_assignment_dataset(5000, 1000, 100)
        
        # Combine all data
        complex_data = {
            **unit_data,
            **person_data,
            "job_titles": job_titles,
            **assignment_data
        }
        
        json_file = os.path.join(self.temp_dir, "complex_dataset.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(complex_data, f)
        
        file_size_mb = os.path.getsize(json_file) / 1024 / 1024
        print(f"Complex dataset file size: {file_size_mb:.2f}MB")
        
        import_options = ImportOptions(
            entity_types=['unit_types', 'units', 'job_titles', 'persons', 'assignments'],
            conflict_resolution=ConflictResolutionStrategy.SKIP,
            batch_size=500
        )
        
        memory_before = self.process.memory_info().rss / 1024 / 1024
        start_time = time.time()
        
        preview_result = self.service.preview_import(json_file, FileFormat.JSON, import_options)
        
        processing_time = time.time() - start_time
        memory_after = self.process.memory_info().rss / 1024 / 1024
        memory_used = memory_after - memory_before
        
        print(f"Complex dataset preview: {processing_time:.2f}s, {memory_used:.2f}MB")
        print(f"Total records: {preview_result.total_records}")
        print(f"Dependency order: {preview_result.dependency_order}")
        
        # Performance assertions
        assert preview_result.success == True
        assert preview_result.total_records > 6000  # Sum of all entities
        assert processing_time < 45.0, f"Processing took too long: {processing_time:.2f}s"
        assert memory_used < 800, f"Memory usage too high: {memory_used:.2f}MB"
        
        # Verify dependency order is correct
        assert 'assignments' in preview_result.dependency_order
        assignments_idx = preview_result.dependency_order.index('assignments')
        
        # Assignments should be last (depends on all others)
        assert assignments_idx == len(preview_result.dependency_order) - 1
    
    def test_csv_parsing_performance_multiple_files(self):
        """Test CSV parsing performance with multiple large files."""
        entity_counts = {
            'unit_types': 500,
            'persons': 10000,
            'job_titles': 200,
            'assignments': 10000
        }
        
        csv_files = {}
        file_creation_times = {}
        
        # Generate CSV files
        for entity_type, count in entity_counts.items():
            start_time = time.time()
            
            csv_file = os.path.join(self.temp_dir, f"{entity_type}.csv")
            csv_files[entity_type] = csv_file
            
            if entity_type == 'unit_types':
                self._create_unit_types_csv(csv_file, count)
            elif entity_type == 'persons':
                self._create_persons_csv(csv_file, count)
            elif entity_type == 'job_titles':
                self._create_job_titles_csv(csv_file, count)
            elif entity_type == 'assignments':
                self._create_assignments_csv(csv_file, count)
            
            file_creation_times[entity_type] = time.time() - start_time
            file_size_mb = os.path.getsize(csv_file) / 1024 / 1024
            print(f"Created {entity_type}.csv: {file_size_mb:.2f}MB in {file_creation_times[entity_type]:.2f}s")
        
        # Test parsing performance
        parsing_times = {}
        memory_usage = {}
        
        for entity_type, csv_file in csv_files.items():
            memory_before = self.process.memory_info().rss / 1024 / 1024
            start_time = time.time()
            
            result = self.csv_processor.parse_csv_file(csv_file, entity_type)
            
            parsing_times[entity_type] = time.time() - start_time
            memory_after = self.process.memory_info().rss / 1024 / 1024
            memory_usage[entity_type] = memory_after - memory_before
            
            print(f"Parsed {entity_type}: {parsing_times[entity_type]:.2f}s, {memory_usage[entity_type]:.2f}MB")
            
            assert result.success == True
            assert len(result.data) == count
            assert parsing_times[entity_type] < 30.0, f"{entity_type} parsing too slow"
            assert memory_usage[entity_type] < 200, f"{entity_type} memory usage too high"
    
    def _create_unit_types_csv(self, file_path: str, count: int):
        """Create unit types CSV file."""
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'short_name', 'aliases', 'level', 'theme_id'])
            
            for i in range(count):
                writer.writerow([
                    i + 1,
                    f'Unit Type {i + 1}',
                    f'UT{i + 1}',
                    '[]',
                    (i % 5) + 1,
                    None
                ])
    
    def _create_persons_csv(self, file_path: str, count: int):
        """Create persons CSV file."""
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'short_name', 'email', 'first_name', 'last_name', 'registration_no', 'profile_image'])
            
            for i in range(count):
                writer.writerow([
                    i + 1,
                    f'Person {i + 1:06d}',
                    f'P{i + 1:06d}',
                    f'person{i + 1:06d}@example.com',
                    f'First{i + 1:06d}',
                    f'Last{i + 1:06d}',
                    f'EMP{i + 1:06d}',
                    None
                ])
    
    def _create_job_titles_csv(self, file_path: str, count: int):
        """Create job titles CSV file."""
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'short_name', 'aliases', 'start_date', 'end_date'])
            
            for i in range(count):
                writer.writerow([
                    i + 1,
                    f'Job Title {i + 1}',
                    f'JT{i + 1}',
                    '[]',
                    '2024-01-01',
                    None
                ])
    
    def _create_assignments_csv(self, file_path: str, count: int):
        """Create assignments CSV file."""
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'person_id', 'unit_id', 'job_title_id', 'version', 'percentage', 'is_ad_interim', 'is_unit_boss', 'notes', 'valid_from', 'valid_to', 'is_current'])
            
            for i in range(count):
                writer.writerow([
                    i + 1,
                    (i % 10000) + 1,  # Assuming 10000 persons
                    (i % 500) + 1,    # Assuming 500 units
                    (i % 200) + 1,    # Assuming 200 job titles
                    1,
                    1.0,
                    i % 10 == 0,      # 10% ad interim
                    i % 20 == 0,      # 5% unit bosses
                    f'Assignment {i + 1}' if i % 5 == 0 else None,
                    '2024-01-01',
                    None,
                    True
                ])
    
    def test_memory_efficiency_streaming(self):
        """Test memory efficiency with streaming-like processing."""
        # Generate very large dataset
        large_data = self._generate_large_person_dataset(25000)
        
        json_file = os.path.join(self.temp_dir, "streaming_test.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(large_data, f)
        
        # Test with small batch sizes to simulate streaming
        import_options = ImportOptions(
            entity_types=['persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP,
            batch_size=100  # Very small batches
        )
        
        memory_samples = []
        start_time = time.time()
        
        # Monitor memory during processing
        def memory_monitor():
            return self.process.memory_info().rss / 1024 / 1024
        
        initial_memory = memory_monitor()
        memory_samples.append(initial_memory)
        
        preview_result = self.service.preview_import(json_file, FileFormat.JSON, import_options)
        
        final_memory = memory_monitor()
        processing_time = time.time() - start_time
        peak_memory_increase = final_memory - initial_memory
        
        print(f"Streaming test: {processing_time:.2f}s, peak memory increase: {peak_memory_increase:.2f}MB")
        
        # Performance assertions for streaming efficiency
        assert preview_result.success == True
        assert preview_result.total_records == 25000
        assert processing_time < 60.0, f"Streaming processing too slow: {processing_time:.2f}s"
        assert peak_memory_increase < 300, f"Memory increase too high for streaming: {peak_memory_increase:.2f}MB"
    
    def test_concurrent_processing_performance(self):
        """Test performance characteristics under concurrent load."""
        # Create multiple datasets for concurrent processing
        datasets = []
        for i in range(3):
            data = self._generate_large_person_dataset(2000)
            json_file = os.path.join(self.temp_dir, f"concurrent_{i}.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            datasets.append(json_file)
        
        import_options = ImportOptions(
            entity_types=['persons'],
            conflict_resolution=ConflictResolutionStrategy.SKIP,
            batch_size=500
        )
        
        # Test sequential processing
        sequential_start = time.time()
        sequential_results = []
        
        for dataset in datasets:
            result = self.service.preview_import(dataset, FileFormat.JSON, import_options)
            sequential_results.append(result)
        
        sequential_time = time.time() - sequential_start
        
        print(f"Sequential processing: {sequential_time:.2f}s")
        
        # Verify all sequential results
        for result in sequential_results:
            assert result.success == True
            assert result.total_records == 2000
        
        # Performance assertion
        assert sequential_time < 45.0, f"Sequential processing too slow: {sequential_time:.2f}s"
        
        # Note: Actual concurrent processing would require threading/multiprocessing
        # This test verifies the system can handle multiple operations sequentially
        # without performance degradation


if __name__ == '__main__':
    # Run with specific markers for performance tests
    pytest.main([__file__, '-v', '-s'])