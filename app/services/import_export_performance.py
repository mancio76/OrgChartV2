"""
Performance optimization service for import/export operations.

This module provides performance optimizations for handling large datasets including:
- Streaming for large file processing
- Memory management and batch processing
- Parallel processing for independent operations

Implements Requirements 1.1, 2.1, 5.1, 5.2 performance optimizations.
"""

import logging
import os
import asyncio
import threading
import time
import gc
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator, Callable, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from contextlib import contextmanager
import psutil

logger = logging.getLogger(__name__)


@dataclass
class PerformanceConfig:
    """Configuration for performance optimizations"""
    # Memory management
    max_memory_usage_mb: int = 512  # Maximum memory usage in MB
    memory_check_interval: int = 100  # Check memory every N records
    gc_threshold: int = 1000  # Force garbage collection every N records
    
    # Batch processing
    default_batch_size: int = 100
    max_batch_size: int = 1000
    min_batch_size: int = 10
    adaptive_batching: bool = True
    
    # Streaming
    stream_threshold_mb: int = 50  # Stream files larger than this
    read_buffer_size: int = 8192  # Buffer size for file reading
    
    # Parallel processing
    max_workers: int = 4  # Maximum number of worker threads/processes
    use_process_pool: bool = False  # Use process pool for CPU-intensive tasks
    parallel_threshold: int = 1000  # Use parallel processing for datasets larger than this
    
    # Performance monitoring
    enable_profiling: bool = False
    log_performance_metrics: bool = True


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations"""
    start_time: float
    end_time: Optional[float] = None
    records_processed: int = 0
    memory_peak_mb: float = 0.0
    cpu_time: float = 0.0
    io_time: float = 0.0
    batch_count: int = 0
    average_batch_time: float = 0.0
    
    @property
    def total_time(self) -> float:
        """Get total processing time"""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    @property
    def records_per_second(self) -> float:
        """Get processing rate"""
        total_time = self.total_time
        if total_time > 0:
            return self.records_processed / total_time
        return 0.0


class MemoryManager:
    """Memory management utilities for large dataset processing"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.process = psutil.Process()
        self.initial_memory = self.get_memory_usage_mb()
        self.peak_memory = self.initial_memory
    
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB"""
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / 1024 / 1024  # Convert to MB
        except Exception:
            return 0.0
    
    def check_memory_usage(self) -> bool:
        """Check if memory usage is within limits"""
        current_memory = self.get_memory_usage_mb()
        self.peak_memory = max(self.peak_memory, current_memory)
        
        if current_memory > self.config.max_memory_usage_mb:
            logger.warning(f"Memory usage ({current_memory:.1f}MB) exceeds limit ({self.config.max_memory_usage_mb}MB)")
            return False
        
        return True
    
    def force_garbage_collection(self) -> None:
        """Force garbage collection to free memory"""
        try:
            collected = gc.collect()
            logger.debug(f"Garbage collection freed {collected} objects")
        except Exception as e:
            logger.warning(f"Error during garbage collection: {e}")
    
    @contextmanager
    def memory_monitor(self):
        """Context manager for monitoring memory usage"""
        start_memory = self.get_memory_usage_mb()
        try:
            yield self
        finally:
            end_memory = self.get_memory_usage_mb()
            memory_delta = end_memory - start_memory
            logger.debug(f"Memory usage delta: {memory_delta:+.1f}MB (peak: {self.peak_memory:.1f}MB)")


class StreamingProcessor:
    """Streaming processor for large files"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
    
    def should_stream_file(self, file_path: str) -> bool:
        """Determine if file should be processed using streaming"""
        try:
            file_size_mb = os.path.getsize(file_path) / 1024 / 1024
            return file_size_mb > self.config.stream_threshold_mb
        except Exception:
            return False
    
    def stream_csv_records(self, file_path: str) -> Iterator[Dict[str, Any]]:
        """Stream CSV records one at a time"""
        import csv
        
        try:
            with open(file_path, 'r', encoding='utf-8', buffering=self.config.read_buffer_size) as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    # Add line number for error reporting
                    row['_line_number'] = row_num
                    yield row
        
        except Exception as e:
            logger.error(f"Error streaming CSV file {file_path}: {e}")
            raise
    
    def stream_json_records(self, file_path: str) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """Stream JSON records by entity type"""
        import json
        
        try:
            with open(file_path, 'r', encoding='utf-8', buffering=self.config.read_buffer_size) as f:
                data = json.load(f)
                
                # Stream each entity type's records
                for entity_type, records in data.items():
                    if entity_type == 'metadata':
                        continue
                    
                    if isinstance(records, list):
                        for record_num, record in enumerate(records):
                            # Add line number for error reporting
                            record['_line_number'] = record_num + 1
                            yield entity_type, record
        
        except Exception as e:
            logger.error(f"Error streaming JSON file {file_path}: {e}")
            raise
    
    def batch_stream_records(self, record_iterator: Iterator[Any], 
                           batch_size: int) -> Iterator[List[Any]]:
        """Batch streaming records for efficient processing"""
        batch = []
        
        for record in record_iterator:
            batch.append(record)
            
            if len(batch) >= batch_size:
                yield batch
                batch = []
        
        # Yield remaining records
        if batch:
            yield batch


class AdaptiveBatchProcessor:
    """Adaptive batch processor that adjusts batch size based on performance"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.current_batch_size = config.default_batch_size
        self.batch_times: List[float] = []
        self.memory_manager = MemoryManager(config)
    
    def get_optimal_batch_size(self, total_records: int) -> int:
        """Calculate optimal batch size based on dataset size and performance"""
        if not self.config.adaptive_batching:
            return self.config.default_batch_size
        
        # Adjust based on total records
        if total_records < 100:
            return min(total_records, self.config.min_batch_size)
        elif total_records > 10000:
            return self.config.max_batch_size
        
        # Adjust based on recent performance
        if len(self.batch_times) >= 3:
            avg_time = sum(self.batch_times[-3:]) / 3
            
            # If batches are taking too long, reduce batch size
            if avg_time > 5.0:  # 5 seconds
                self.current_batch_size = max(
                    self.config.min_batch_size,
                    int(self.current_batch_size * 0.8)
                )
            # If batches are very fast, increase batch size
            elif avg_time < 1.0:  # 1 second
                self.current_batch_size = min(
                    self.config.max_batch_size,
                    int(self.current_batch_size * 1.2)
                )
        
        return self.current_batch_size
    
    def process_batch(self, batch: List[Any], processor_func: Callable, 
                     *args, **kwargs) -> Any:
        """Process a batch and track performance metrics"""
        start_time = time.time()
        
        try:
            # Check memory before processing
            if not self.memory_manager.check_memory_usage():
                self.memory_manager.force_garbage_collection()
            
            # Process the batch
            result = processor_func(batch, *args, **kwargs)
            
            # Track timing
            batch_time = time.time() - start_time
            self.batch_times.append(batch_time)
            
            # Keep only recent batch times
            if len(self.batch_times) > 10:
                self.batch_times = self.batch_times[-10:]
            
            logger.debug(f"Processed batch of {len(batch)} records in {batch_time:.2f}s")
            return result
        
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            raise


class ParallelProcessor:
    """Parallel processor for independent operations"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.executor = None
    
    def should_use_parallel_processing(self, total_records: int) -> bool:
        """Determine if parallel processing should be used"""
        return total_records >= self.config.parallel_threshold
    
    def get_executor(self):
        """Get appropriate executor for parallel processing"""
        if self.executor is None:
            if self.config.use_process_pool:
                self.executor = ProcessPoolExecutor(max_workers=self.config.max_workers)
            else:
                self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        return self.executor
    
    def process_batches_parallel(self, batches: List[List[Any]], 
                               processor_func: Callable, *args, **kwargs) -> List[Any]:
        """Process multiple batches in parallel"""
        if len(batches) <= 1:
            # Not worth parallelizing
            if batches:
                return [processor_func(batches[0], *args, **kwargs)]
            return []
        
        executor = self.get_executor()
        results = []
        
        try:
            # Submit all batches for processing
            future_to_batch = {
                executor.submit(processor_func, batch, *args, **kwargs): i
                for i, batch in enumerate(batches)
            }
            
            # Collect results in order
            batch_results = [None] * len(batches)
            for future in as_completed(future_to_batch):
                batch_index = future_to_batch[future]
                try:
                    result = future.result()
                    batch_results[batch_index] = result
                except Exception as e:
                    logger.error(f"Error processing batch {batch_index}: {e}")
                    raise
            
            return batch_results
        
        except Exception as e:
            logger.error(f"Error in parallel batch processing: {e}")
            raise
    
    def process_entities_parallel(self, entity_data: Dict[str, List[Any]], 
                                processor_func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Process different entity types in parallel"""
        if len(entity_data) <= 1:
            # Not worth parallelizing
            results = {}
            for entity_type, records in entity_data.items():
                results[entity_type] = processor_func(entity_type, records, *args, **kwargs)
            return results
        
        executor = self.get_executor()
        
        try:
            # Submit each entity type for processing
            future_to_entity = {
                executor.submit(processor_func, entity_type, records, *args, **kwargs): entity_type
                for entity_type, records in entity_data.items()
            }
            
            # Collect results
            results = {}
            for future in as_completed(future_to_entity):
                entity_type = future_to_entity[future]
                try:
                    result = future.result()
                    results[entity_type] = result
                except Exception as e:
                    logger.error(f"Error processing entity type {entity_type}: {e}")
                    raise
            
            return results
        
        except Exception as e:
            logger.error(f"Error in parallel entity processing: {e}")
            raise
    
    def cleanup(self):
        """Clean up executor resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None


class ImportExportPerformanceService:
    """
    Performance optimization service for import/export operations.
    
    Provides comprehensive performance optimizations including:
    - Streaming for large file processing
    - Memory management and batch processing
    - Parallel processing for independent operations
    """
    
    def __init__(self, config: Optional[PerformanceConfig] = None):
        """Initialize performance service with configuration."""
        self.config = config or PerformanceConfig()
        self.memory_manager = MemoryManager(self.config)
        self.streaming_processor = StreamingProcessor(self.config)
        self.batch_processor = AdaptiveBatchProcessor(self.config)
        self.parallel_processor = ParallelProcessor(self.config)
        
        logger.info("ImportExportPerformanceService initialized")
    
    def create_performance_metrics(self) -> PerformanceMetrics:
        """Create new performance metrics tracker"""
        return PerformanceMetrics(start_time=time.time())
    
    def optimize_import_processing(self, file_path: str, file_format: str, 
                                 total_records: int) -> Dict[str, Any]:
        """
        Determine optimal processing strategy for import operation.
        
        Args:
            file_path: Path to the import file
            file_format: Format of the file (csv/json)
            total_records: Total number of records to process
            
        Returns:
            Dictionary with optimization recommendations
        """
        recommendations = {
            'use_streaming': False,
            'use_parallel': False,
            'batch_size': self.config.default_batch_size,
            'memory_monitoring': True,
            'processing_strategy': 'standard'
        }
        
        # Check if streaming should be used
        if self.streaming_processor.should_stream_file(file_path):
            recommendations['use_streaming'] = True
            recommendations['processing_strategy'] = 'streaming'
            logger.info(f"Recommending streaming processing for large file: {file_path}")
        
        # Check if parallel processing should be used
        if self.parallel_processor.should_use_parallel_processing(total_records):
            recommendations['use_parallel'] = True
            recommendations['processing_strategy'] = 'parallel'
            logger.info(f"Recommending parallel processing for {total_records} records")
        
        # Determine optimal batch size
        recommendations['batch_size'] = self.batch_processor.get_optimal_batch_size(total_records)
        
        # Memory management recommendations
        file_size_mb = os.path.getsize(file_path) / 1024 / 1024
        if file_size_mb > 100:  # Files larger than 100MB
            recommendations['memory_monitoring'] = True
            recommendations['gc_frequency'] = max(100, self.config.gc_threshold // 2)
        
        logger.info(f"Performance optimization recommendations: {recommendations}")
        return recommendations
    
    def stream_file_records(self, file_path: str, file_format: str) -> Iterator[Any]:
        """
        Stream records from file for memory-efficient processing.
        
        Args:
            file_path: Path to the file to stream
            file_format: Format of the file
            
        Yields:
            Individual records or (entity_type, record) tuples
        """
        if file_format.lower() == 'csv':
            yield from self.streaming_processor.stream_csv_records(file_path)
        elif file_format.lower() == 'json':
            yield from self.streaming_processor.stream_json_records(file_path)
        else:
            raise ValueError(f"Unsupported file format for streaming: {file_format}")
    
    def process_records_in_batches(self, records: List[Any], processor_func: Callable,
                                 batch_size: Optional[int] = None, *args, **kwargs) -> List[Any]:
        """
        Process records in optimized batches.
        
        Args:
            records: List of records to process
            processor_func: Function to process each batch
            batch_size: Optional batch size override
            
        Returns:
            List of processing results
        """
        if batch_size is None:
            batch_size = self.batch_processor.get_optimal_batch_size(len(records))
        
        results = []
        
        # Process records in batches
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            # Process batch with performance tracking
            result = self.batch_processor.process_batch(batch, processor_func, *args, **kwargs)
            results.append(result)
            
            # Memory management
            if i % (batch_size * self.config.memory_check_interval) == 0:
                if not self.memory_manager.check_memory_usage():
                    self.memory_manager.force_garbage_collection()
        
        return results
    
    def process_entities_optimized(self, entity_data: Dict[str, List[Any]], 
                                 processor_func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Process multiple entity types with optimal strategy.
        
        Args:
            entity_data: Dictionary mapping entity types to record lists
            processor_func: Function to process each entity type
            
        Returns:
            Dictionary of processing results by entity type
        """
        total_records = sum(len(records) for records in entity_data.values())
        
        # Determine if parallel processing is beneficial
        if self.parallel_processor.should_use_parallel_processing(total_records):
            logger.info("Using parallel processing for entity types")
            return self.parallel_processor.process_entities_parallel(
                entity_data, processor_func, *args, **kwargs
            )
        else:
            # Sequential processing with batch optimization
            results = {}
            for entity_type, records in entity_data.items():
                logger.debug(f"Processing {len(records)} records for {entity_type}")
                results[entity_type] = processor_func(entity_type, records, *args, **kwargs)
            return results
    
    def monitor_performance(self, metrics: PerformanceMetrics, 
                          operation_name: str = "import_export") -> None:
        """
        Monitor and log performance metrics.
        
        Args:
            metrics: Performance metrics to monitor
            operation_name: Name of the operation being monitored
        """
        if not self.config.log_performance_metrics:
            return
        
        # Update peak memory
        current_memory = self.memory_manager.get_memory_usage_mb()
        metrics.memory_peak_mb = max(metrics.memory_peak_mb, current_memory)
        
        # Log performance information
        if metrics.end_time:
            logger.info(f"Performance metrics for {operation_name}:")
            logger.info(f"  Total time: {metrics.total_time:.2f}s")
            logger.info(f"  Records processed: {metrics.records_processed}")
            logger.info(f"  Processing rate: {metrics.records_per_second:.1f} records/sec")
            logger.info(f"  Peak memory usage: {metrics.memory_peak_mb:.1f}MB")
            logger.info(f"  Batches processed: {metrics.batch_count}")
            if metrics.batch_count > 0:
                logger.info(f"  Average batch time: {metrics.average_batch_time:.2f}s")
    
    def cleanup(self):
        """Clean up performance service resources"""
        try:
            self.parallel_processor.cleanup()
            logger.info("Performance service cleanup completed")
        except Exception as e:
            logger.error(f"Error during performance service cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.cleanup()


# Global performance service instance
_performance_service = None


def get_import_export_performance_service() -> ImportExportPerformanceService:
    """Get the global import/export performance service instance."""
    global _performance_service
    if _performance_service is None:
        _performance_service = ImportExportPerformanceService()
    return _performance_service