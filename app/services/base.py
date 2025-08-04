"""
Base service class with common CRUD operations, search functionality, and validation integration
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Type, TypeVar, Union
from app.database import get_db_manager
from app.models.base import BaseModel, ModelValidationException, ValidationError

T = TypeVar('T', bound=BaseModel)

logger = logging.getLogger(__name__)


class ServiceException(Exception):
    """Base exception for service layer operations"""
    pass


class ServiceValidationException(ServiceException):
    """Exception raised when service-level validation fails"""
    
    def __init__(self, message: str, errors: List[ValidationError] = None):
        self.errors = errors or []
        super().__init__(message)


class ServiceNotFoundException(ServiceException):
    """Exception raised when requested resource is not found"""
    pass


class ServiceIntegrityException(ServiceException):
    """Exception raised when referential integrity constraints are violated"""
    pass


class BaseService(ABC):
    """
    Abstract base service class providing common CRUD operations, search functionality,
    and validation integration for all domain services.
    
    This class implements the Service Layer pattern, encapsulating business logic
    separate from route handlers as required by Requirement 7.2.
    """
    
    def __init__(self, model_class: Type[T], table_name: str):
        self.model_class = model_class
        self.table_name = table_name
        self.db_manager = get_db_manager()
        logger.debug(f"Initialized {self.__class__.__name__} for table {table_name}")
    
    @abstractmethod
    def get_list_query(self) -> str:
        """Get query for listing all records"""
        pass
    
    @abstractmethod
    def get_by_id_query(self) -> str:
        """Get query for fetching single record by ID"""
        pass
    
    @abstractmethod
    def get_insert_query(self) -> str:
        """Get query for inserting new record"""
        pass
    
    @abstractmethod
    def get_update_query(self) -> str:
        """Get query for updating existing record"""
        pass
    
    @abstractmethod
    def get_delete_query(self) -> str:
        """Get query for deleting record"""
        pass
    
    @abstractmethod
    def model_to_insert_params(self, model: T) -> tuple:
        """Convert model to parameters for insert query"""
        pass
    
    @abstractmethod
    def model_to_update_params(self, model: T) -> tuple:
        """Convert model to parameters for update query"""
        pass
    
    def get_all(self, **kwargs) -> List[T]:
        """
        Get all records with optional filtering parameters.
        
        Args:
            **kwargs: Optional filtering parameters (implementation-specific)
            
        Returns:
            List of model instances
            
        Raises:
            ServiceException: If database operation fails
        """
        try:
            logger.debug(f"Fetching all records from {self.table_name}")
            rows = self.db_manager.fetch_all(self.get_list_query())
            results = [self.model_class.from_sqlite_row(row) for row in rows]
            logger.debug(f"Retrieved {len(results)} records from {self.table_name}")
            return results
        except Exception as e:
            logger.error(f"Error fetching all {self.table_name}: {e}")
            raise ServiceException(f"Failed to retrieve {self.table_name} records") from e
    
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Get single record by ID.
        
        Args:
            id: Primary key of the record
            
        Returns:
            Model instance if found, None otherwise
            
        Raises:
            ServiceException: If database operation fails
        """
        try:
            logger.debug(f"Fetching {self.table_name} with id {id}")
            row = self.db_manager.fetch_one(self.get_by_id_query(), (id,))
            result = self.model_class.from_sqlite_row(row)
            logger.debug(f"{'Found' if result else 'Not found'} {self.table_name} with id {id}")
            return result
        except Exception as e:
            logger.error(f"Error fetching {self.table_name} with id {id}: {e}")
            raise ServiceException(f"Failed to retrieve {self.table_name} with id {id}") from e
    
    def create(self, model: T) -> T:
        """
        Create new record with validation and audit field management.
        
        Args:
            model: Model instance to create
            
        Returns:
            Created model instance with assigned ID
            
        Raises:
            ServiceValidationException: If validation fails
            ServiceException: If database operation fails
        """
        try:
            logger.debug(f"Creating new {self.table_name} record")
            
            # Set audit fields for creation
            model.set_audit_fields(is_update=False)
            
            # Validate model
            errors = model.validate()
            if errors:
                logger.warning(f"Validation failed for {self.table_name}: {[e.message for e in errors]}")
                raise ServiceValidationException(
                    f"Validation failed for {self.table_name}",
                    errors
                )
            
            # Perform additional service-level validation
            self._validate_for_create(model)
            
            # Insert record
            cursor = self.db_manager.execute_query(
                self.get_insert_query(),
                self.model_to_insert_params(model)
            )
            
            # Get created record with assigned ID
            if hasattr(model, 'id') and cursor.lastrowid:
                model.id = cursor.lastrowid
                created_record = self.get_by_id(cursor.lastrowid)
                logger.info(f"Successfully created {self.table_name} with id {cursor.lastrowid}")
                return created_record
            
            logger.info(f"Successfully created {self.table_name} record")
            return model
            
        except (ServiceValidationException, ModelValidationException):
            raise
        except Exception as e:
            logger.error(f"Error creating {self.table_name}: {e}")
            raise ServiceException(f"Failed to create {self.table_name}") from e
    
    def update(self, model: T) -> T:
        """
        Update existing record with validation and audit field management.
        
        Args:
            model: Model instance to update (must have ID)
            
        Returns:
            Updated model instance
            
        Raises:
            ServiceNotFoundException: If record doesn't exist
            ServiceValidationException: If validation fails
            ServiceException: If database operation fails
        """
        try:
            logger.debug(f"Updating {self.table_name} record")
            
            # Check if record exists
            if not hasattr(model, 'id') or not model.id:
                raise ServiceValidationException(f"Cannot update {self.table_name} without ID")
            
            existing = self.get_by_id(model.id)
            if not existing:
                raise ServiceNotFoundException(f"{self.table_name} with id {model.id} not found")
            
            # Set audit fields for update
            model.set_audit_fields(is_update=True)
            
            # Validate model
            errors = model.validate()
            if errors:
                logger.warning(f"Validation failed for {self.table_name}: {[e.message for e in errors]}")
                raise ServiceValidationException(
                    f"Validation failed for {self.table_name}",
                    errors
                )
            
            # Perform additional service-level validation
            self._validate_for_update(model, existing)
            
            # Update record
            self.db_manager.execute_query(
                self.get_update_query(),
                self.model_to_update_params(model)
            )
            
            # Return updated record
            updated_record = self.get_by_id(model.id)
            logger.info(f"Successfully updated {self.table_name} with id {model.id}")
            return updated_record
            
        except (ServiceNotFoundException, ServiceValidationException, ModelValidationException):
            raise
        except Exception as e:
            logger.error(f"Error updating {self.table_name}: {e}")
            raise ServiceException(f"Failed to update {self.table_name}") from e
    
    def delete(self, id: int) -> bool:
        """
        Delete record by ID with referential integrity checks.
        
        Args:
            id: Primary key of the record to delete
            
        Returns:
            True if record was deleted, False otherwise
            
        Raises:
            ServiceNotFoundException: If record doesn't exist
            ServiceIntegrityException: If referential integrity would be violated
            ServiceException: If database operation fails
        """
        try:
            logger.debug(f"Deleting {self.table_name} with id {id}")
            
            # Check if record exists
            existing = self.get_by_id(id)
            if not existing:
                raise ServiceNotFoundException(f"{self.table_name} with id {id} not found")
            
            # Perform referential integrity checks
            self._validate_for_delete(existing)
            
            # Delete record
            cursor = self.db_manager.execute_query(self.get_delete_query(), (id,))
            
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Successfully deleted {self.table_name} with id {id}")
            else:
                logger.warning(f"No rows affected when deleting {self.table_name} with id {id}")
            
            return success
            
        except (ServiceNotFoundException, ServiceIntegrityException):
            raise
        except Exception as e:
            logger.error(f"Error deleting {self.table_name} with id {id}: {e}")
            raise ServiceException(f"Failed to delete {self.table_name} with id {id}") from e
    
    def exists(self, id: int) -> bool:
        """Check if record exists"""
        try:
            return self.get_by_id(id) is not None
        except Exception:
            return False
    
    def count(self, **kwargs) -> int:
        """
        Get total record count with optional filtering.
        
        Args:
            **kwargs: Optional filtering parameters
            
        Returns:
            Total number of records
        """
        try:
            row = self.db_manager.fetch_one(f"SELECT COUNT(*) as count FROM {self.table_name}")
            count = row['count'] if row else 0
            logger.debug(f"Count for {self.table_name}: {count}")
            return count
        except Exception as e:
            logger.error(f"Error counting {self.table_name}: {e}")
            return 0
    
    def get_paginated(self, page: int = 1, page_size: int = 20, **kwargs) -> Dict[str, Any]:
        """
        Get paginated results.
        
        Args:
            page: Page number (1-based)
            page_size: Number of records per page
            **kwargs: Additional filtering parameters
            
        Returns:
            Dictionary with paginated results and metadata
        """
        try:
            offset = (page - 1) * page_size
            
            # Get total count
            total_count = self.count(**kwargs)
            
            # Get paginated results
            query = f"{self.get_list_query()} LIMIT ? OFFSET ?"
            rows = self.db_manager.fetch_all(query, (page_size, offset))
            results = [self.model_class.from_sqlite_row(row) for row in rows]
            
            # Calculate pagination metadata
            total_pages = (total_count + page_size - 1) // page_size
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                'results': results,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': total_pages,
                    'has_next': has_next,
                    'has_prev': has_prev
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting paginated {self.table_name}: {e}")
            return {
                'results': [],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': 0,
                    'total_pages': 0,
                    'has_next': False,
                    'has_prev': False
                }
            }
    
    def _inject_where_clause(self, sql: str, conditions: str) -> str:
        """Safely inject WHERE conditions into SQL query using regex"""
        # Remove extra whitespace and normalize
        sql = re.sub(r'\s+', ' ', sql.strip())
        
        # Regex patterns for SQL clause detection (case-insensitive)
        patterns = {
            'cte_pattern': r'^(\s*WITH\s+.+?\s+)\s*(SELECT\b.*)',
            'select': r'^(\s*SELECT\s+.+?\s+)\s*(FROM\b.*)',
            'where': r'\bWHERE\b',
            'group_by': r'\bGROUP\s+BY\b',
            'having': r'\bHAVING\b', 
            'order_by': r'\bORDER\s+BY\b',
            'limit': r'\bLIMIT\b',
            'offset': r'\bOFFSET\b'
        }
        
        # Check if WHERE clause already exists
        where_match = re.search(patterns['where'], sql, re.IGNORECASE)
        
        if where_match:
            # WHERE exists - add our conditions with AND
            # Find the position right after WHERE
            where_end = where_match.end()
            
            # Insert our conditions with proper grouping
            new_sql = (sql[:where_end] + 
                    f" ({conditions}) AND " + 
                    sql[where_end:])
            return new_sql
        
        else:
            # No WHERE clause - find the best insertion point
            insertion_point = len(sql)
            
            # Check for clauses that should come after WHERE (in order of precedence)
            for clause_name in ['group_by', 'having', 'order_by', 'limit', 'offset']:
                match = re.search(patterns[clause_name], sql, re.IGNORECASE)
                if match:
                    insertion_point = min(insertion_point, match.start())
            
            # Insert WHERE clause
            new_sql = (sql[:insertion_point].rstrip() + 
                    f" WHERE {conditions} " + 
                    sql[insertion_point:])
            return new_sql

    def search(self, search_term: str, fields: List[str] = None, **kwargs) -> List[T]:
        """
        Search records by term in specified fields with advanced filtering options.
        
        Args:
            search_term: Term to search for
            fields: List of field names to search in (defaults to searchable fields)
            **kwargs: Additional search parameters (implementation-specific)
            
        Returns:
            List of matching model instances
            
        Raises:
            ServiceException: If search operation fails
        """
        if not search_term:
            return self.get_all(**kwargs)
        
        if not fields:
            fields = self.get_searchable_fields()
        
        if not fields:
            logger.warning(f"No searchable fields defined for {self.table_name}")
            return []
        
        try:
            logger.debug(f"Searching {self.table_name} for '{search_term}' in fields: {fields}")
            
            # Build search query
            conditions = []
            params = []
            for field in fields:
                conditions.append(f"{field} LIKE ?")
                params.append(f"%{search_term}%")
            
            where_clause = " OR ".join(conditions)
            base_query = self.get_list_query()

            query = self._inject_where_clause(base_query, search_conditions)
            
            rows = self.db_manager.fetch_all(query, tuple(params))
            results = [self.model_class.from_sqlite_row(row) for row in rows]
            
            logger.debug(f"Search returned {len(results)} results for '{search_term}'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching {self.table_name}: {e}")
            # Return empty list instead of raising exception for search failures
            # This provides graceful degradation as mentioned in the design
            return []
    
    def get_searchable_fields(self) -> List[str]:
        """
        Get list of fields that can be searched.
        Override in subclasses to define searchable fields.
        
        Returns:
            List of field names that support search
        """
        return []
    
    def advanced_search(self, criteria: Dict[str, Any]) -> List[T]:
        """
        Perform advanced search with multiple criteria.
        
        Args:
            criteria: Dictionary of field names and search values
            
        Returns:
            List of matching model instances
            
        Raises:
            ServiceException: If search operation fails
        """
        if not criteria:
            return self.get_all()
        
        try:
            logger.debug(f"Advanced search on {self.table_name} with criteria: {criteria}")
            
            conditions = []
            params = []
            
            for field, value in criteria.items():
                if value is not None:
                    if isinstance(value, str):
                        conditions.append(f"{field} LIKE ?")
                        params.append(f"%{value}%")
                    else:
                        conditions.append(f"{field} = ?")
                        params.append(value)
            
            if not conditions:
                return self.get_all()
            
            where_clause = " AND ".join(conditions)
            query = f"{self.get_list_query()} WHERE {where_clause}"
            
            rows = self.db_manager.fetch_all(query, tuple(params))
            results = [self.model_class.from_sqlite_row(row) for row in rows]
            
            logger.debug(f"Advanced search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in advanced search for {self.table_name}: {e}")
            return []   
 # Validation methods - override in subclasses for specific business rules
    
    def _validate_for_create(self, model: T) -> None:
        """
        Perform additional validation before creating a record.
        Override in subclasses to add specific business rules.
        
        Args:
            model: Model instance to validate
            
        Raises:
            ServiceValidationException: If validation fails
        """
        pass
    
    def _validate_for_update(self, model: T, existing: T) -> None:
        """
        Perform additional validation before updating a record.
        Override in subclasses to add specific business rules.
        
        Args:
            model: Model instance to update
            existing: Current model instance from database
            
        Raises:
            ServiceValidationException: If validation fails
        """
        pass
    
    def _validate_for_delete(self, model: T) -> None:
        """
        Perform validation before deleting a record.
        Override in subclasses to check referential integrity.
        
        Args:
            model: Model instance to delete
            
        Raises:
            ServiceIntegrityException: If referential integrity would be violated
        """
        pass
    
    # Utility methods for common operations
    
    def bulk_create(self, models: List[T]) -> List[T]:
        """
        Create multiple records in a single transaction.
        
        Args:
            models: List of model instances to create
            
        Returns:
            List of created model instances
            
        Raises:
            ServiceValidationException: If any validation fails
            ServiceException: If database operation fails
        """
        if not models:
            return []
        
        try:
            logger.debug(f"Bulk creating {len(models)} {self.table_name} records")
            created_models = []
            
            # Use database transaction for bulk operations
            with self.db_manager.get_connection() as conn:
                for model in models:
                    # Set audit fields
                    model.set_audit_fields(is_update=False)
                    
                    # Validate each model
                    errors = model.validate()
                    if errors:
                        raise ServiceValidationException(
                            f"Validation failed for {self.table_name}",
                            errors
                        )
                    
                    # Perform service-level validation
                    self._validate_for_create(model)
                    
                    # Insert record
                    cursor = conn.cursor()
                    cursor.execute(self.get_insert_query(), self.model_to_insert_params(model))
                    
                    if hasattr(model, 'id') and cursor.lastrowid:
                        model.id = cursor.lastrowid
                    
                    created_models.append(model)
                
                conn.commit()
            
            logger.info(f"Successfully bulk created {len(created_models)} {self.table_name} records")
            return created_models
            
        except (ServiceValidationException, ModelValidationException):
            raise
        except Exception as e:
            logger.error(f"Error bulk creating {self.table_name}: {e}")
            raise ServiceException(f"Failed to bulk create {self.table_name}") from e
    
    def get_by_field(self, field_name: str, value: Any) -> Optional[T]:
        """
        Get single record by field value.
        
        Args:
            field_name: Name of the field to search
            value: Value to search for
            
        Returns:
            Model instance if found, None otherwise
            
        Raises:
            ServiceException: If database operation fails
        """
        try:
            #query = f"{self.get_list_query()} WHERE {field_name} = ?"
            query = self.get_list_query()
            query = self._inject_where_clause(query, f"{field_name} = ?")

            row = self.db_manager.fetch_one(query, (value,))
            return self.model_class.from_sqlite_row(row)
        except Exception as e:
            logger.error(f"Error fetching {self.table_name} by {field_name}={value}: {e}")
            raise ServiceException(f"Failed to retrieve {self.table_name} by {field_name}") from e
    
    def get_all_by_field(self, field_name: str, value: Any) -> List[T]:
        """
        Get all records matching field value.
        
        Args:
            field_name: Name of the field to search
            value: Value to search for
            
        Returns:
            List of matching model instances
            
        Raises:
            ServiceException: If database operation fails
        """
        try:
            query = f"{self.get_list_query()} WHERE {field_name} = ?"
            rows = self.db_manager.fetch_all(query, (value,))
            return [self.model_class.from_sqlite_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching {self.table_name} by {field_name}={value}: {e}")
            raise ServiceException(f"Failed to retrieve {self.table_name} by {field_name}") from e
    
    def validate_model(self, model: T) -> List[ValidationError]:
        """
        Validate model instance including service-level business rules.
        
        Args:
            model: Model instance to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Model-level validation
        errors.extend(model.validate())
        
        # Service-level validation can be added here
        # This method can be overridden in subclasses for additional validation
        
        return errors
    
    def is_valid_model(self, model: T) -> bool:
        """
        Check if model instance is valid.
        
        Args:
            model: Model instance to validate
            
        Returns:
            True if valid, False otherwise
        """
        return len(self.validate_model(model)) == 0