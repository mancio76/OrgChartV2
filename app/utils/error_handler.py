"""
Enhanced Error Handling System - Task 8.2
Organigramma Web App
"""

import logging
import traceback
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import sqlite3

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="templates")

class ErrorHandler:
    """Centralized error handling system"""
    
    @staticmethod
    def log_error(error: Exception, request: Request, error_id: str = None) -> str:
        """Log error with detailed information"""
        if not error_id:
            error_id = str(uuid.uuid4())[:8]
        
        error_info = {
            'error_id': error_id,
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'request_url': str(request.url),
            'request_method': request.method,
            'user_agent': request.headers.get('user-agent', 'Unknown'),
            'client_ip': request.client.host if request.client else 'Unknown',
            'traceback': traceback.format_exc()
        }
        
        # Log structured error information
        logger.error(
            f"Error {error_id}: {error_info['error_type']} - {error_info['error_message']}",
            extra=error_info
        )
        
        return error_id
    
    @staticmethod
    def log_database_error(error: Exception, operation: str, error_id: str = None) -> str:
        """Log database-specific errors with transaction context"""
        if not error_id:
            error_id = str(uuid.uuid4())[:8]
        
        db_error_info = {
            'error_id': error_id,
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'database_operation': operation,
            'is_database_error': True,
            'traceback': traceback.format_exc()
        }
        
        # Specific handling for SQLite errors
        if isinstance(error, sqlite3.Error):
            db_error_info.update({
                'sqlite_error_code': getattr(error, 'sqlite_errorcode', None),
                'sqlite_error_name': getattr(error, 'sqlite_errorname', None)
            })
        
        logger.error(
            f"Database Error {error_id}: {operation} - {db_error_info['error_message']}",
            extra=db_error_info
        )
        
        return error_id
    
    @staticmethod
    def create_safe_error_response(error: Exception, request: Request, status_code: int = 500) -> Dict[str, Any]:
        """Create safe error response without exposing sensitive information"""
        error_id = ErrorHandler.log_error(error, request)
        
        # Safe error messages for different error types
        safe_messages = {
            404: "La risorsa richiesta non è stata trovata.",
            403: "Non hai i permessi necessari per accedere a questa risorsa.",
            400: "La richiesta non è valida. Controlla i dati inseriti.",
            422: "I dati forniti non sono validi.",
            500: "Si è verificato un errore interno del server.",
            503: "Il servizio non è temporaneamente disponibile."
        }
        
        return {
            'error_id': error_id,
            'status_code': status_code,
            'message': safe_messages.get(status_code, "Si è verificato un errore."),
            'timestamp': datetime.now().isoformat(),
            'support_message': f"Se il problema persiste, contatta il supporto con il codice errore: {error_id}"
        }
    
    @staticmethod
    async def handle_404_error(request: Request, exc: HTTPException) -> HTMLResponse:
        """Handle 404 Not Found errors"""
        error_id = ErrorHandler.log_error(exc, request)
        
        context = {
            'request': request,
            'error_id': error_id,
            'timestamp': datetime.now().isoformat(),
            'requested_url': str(request.url),
            'page_title': 'Pagina non trovata',
            'error_code': 404
        }
        
        return templates.TemplateResponse(
            "errors/404.html",
            context,
            status_code=404
        )
    
    @staticmethod
    async def handle_500_error(request: Request, exc: Exception) -> HTMLResponse:
        """Handle 500 Internal Server Error"""
        error_id = ErrorHandler.log_error(exc, request)
        
        context = {
            'request': request,
            'error_id': error_id,
            'timestamp': datetime.now().isoformat(),
            'page_title': 'Errore del server',
            'error_code': 500,
            'support_message': f"Codice errore: {error_id}"
        }
        
        return templates.TemplateResponse(
            "errors/500.html",
            context,
            status_code=500
        )
    
    @staticmethod
    async def handle_api_error(request: Request, exc: Exception, status_code: int = 500) -> JSONResponse:
        """Handle API errors with JSON response"""
        error_response = ErrorHandler.create_safe_error_response(exc, request, status_code)
        
        return JSONResponse(
            status_code=status_code,
            content={
                'success': False,
                'error': error_response,
                'data': None
            }
        )
    
    @staticmethod
    async def handle_validation_error(request: Request, exc: Exception) -> HTMLResponse:
        """Handle validation errors"""
        error_id = ErrorHandler.log_error(exc, request)
        
        context = {
            'request': request,
            'error_id': error_id,
            'timestamp': datetime.now().isoformat(),
            'page_title': 'Errore di validazione',
            'error_code': 422,
            'validation_errors': getattr(exc, 'errors', [])
        }
        
        return templates.TemplateResponse(
            "errors/validation.html",
            context,
            status_code=422
        )
    
    @staticmethod
    async def handle_database_error(request: Request, exc: Exception, operation: str = "database operation") -> HTMLResponse:
        """Handle database-specific errors"""
        error_id = ErrorHandler.log_database_error(exc, operation)
        
        # Determine if this is a user-facing error or system error
        user_friendly_errors = {
            'UNIQUE constraint failed': 'Un record con questi dati esiste già.',
            'FOREIGN KEY constraint failed': 'Impossibile completare l\'operazione: esistono dipendenze.',
            'NOT NULL constraint failed': 'Tutti i campi obbligatori devono essere compilati.',
            'CHECK constraint failed': 'I dati inseriti non rispettano i vincoli di validità.'
        }
        
        error_message = "Si è verificato un errore durante l'operazione sul database."
        for constraint, message in user_friendly_errors.items():
            if constraint in str(exc):
                error_message = message
                break
        
        context = {
            'request': request,
            'error_id': error_id,
            'timestamp': datetime.now().isoformat(),
            'page_title': 'Errore database',
            'error_code': 500,
            'error_message': error_message,
            'operation': operation
        }
        
        return templates.TemplateResponse(
            "errors/database.html",
            context,
            status_code=500
        )

class DatabaseTransactionManager:
    """Database transaction manager with automatic rollback on errors"""
    
    def __init__(self, connection):
        self.connection = connection
        self.transaction_started = False
    
    def __enter__(self):
        """Start transaction"""
        try:
            self.connection.execute("BEGIN TRANSACTION")
            self.transaction_started = True
            logger.debug("Database transaction started")
            return self
        except Exception as e:
            logger.error(f"Failed to start transaction: {e}")
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Commit or rollback transaction based on exception status"""
        try:
            if exc_type is None:
                # No exception occurred, commit the transaction
                self.connection.execute("COMMIT")
                logger.debug("Database transaction committed successfully")
            else:
                # Exception occurred, rollback the transaction
                self.connection.execute("ROLLBACK")
                logger.warning(f"Database transaction rolled back due to error: {exc_val}")
                
                # Log the database error
                ErrorHandler.log_database_error(
                    exc_val, 
                    "transaction_rollback",
                    str(uuid.uuid4())[:8]
                )
        except Exception as e:
            logger.error(f"Error during transaction cleanup: {e}")
        finally:
            self.transaction_started = False

def handle_database_operation(operation_name: str):
    """Decorator for database operations with automatic error handling"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except sqlite3.IntegrityError as e:
                error_id = ErrorHandler.log_database_error(e, operation_name)
                raise HTTPException(
                    status_code=400,
                    detail=f"Integrity constraint violation in {operation_name}. Error ID: {error_id}"
                )
            except sqlite3.OperationalError as e:
                error_id = ErrorHandler.log_database_error(e, operation_name)
                raise HTTPException(
                    status_code=500,
                    detail=f"Database operational error in {operation_name}. Error ID: {error_id}"
                )
            except sqlite3.Error as e:
                error_id = ErrorHandler.log_database_error(e, operation_name)
                raise HTTPException(
                    status_code=500,
                    detail=f"Database error in {operation_name}. Error ID: {error_id}"
                )
            except Exception as e:
                error_id = str(uuid.uuid4())[:8]
                logger.error(f"Unexpected error in {operation_name} (ID: {error_id}): {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Unexpected error in {operation_name}. Error ID: {error_id}"
                )
        return wrapper
    return decorator

# Global exception handler for unhandled exceptions
def setup_global_exception_handler():
    """Setup global exception handler for unhandled exceptions"""
    import sys
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle unhandled exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow keyboard interrupt to work normally
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_id = str(uuid.uuid4())[:8]
        logger.critical(
            f"Unhandled exception {error_id}: {exc_type.__name__} - {exc_value}",
            extra={
                'error_id': error_id,
                'error_type': exc_type.__name__,
                'error_message': str(exc_value),
                'traceback': ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            }
        )
    
    sys.excepthook = handle_exception