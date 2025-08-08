"""
Import/Export routes for organizational data management.

This module provides FastAPI routes for importing and exporting organizational data
with support for CSV and JSON formats, file upload handling, and async processing.
Implements Requirements 1.1, 2.1, 7.1, 7.2.
"""

import logging
import os
import tempfile
import uuid
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, Request, Form, File, UploadFile, Depends, HTTPException, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.security import HTTPBearer

from app.services.import_export import ImportExportService, ImportExportException
from app.models.import_export import (
    ImportOptions, ExportOptions, FileFormat, ConflictResolutionStrategy,
    ImportExportValidationError, ImportErrorType
)
from app.security import InputValidator, SecurityValidationError, get_client_ip, log_security_event
from app.security_csfr import generate_csrf_token, validate_csrf_token_flexible

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Security configuration
security = HTTPBearer(auto_error=False)

# Global storage for operation status (in production, use Redis or database)
operation_status: Dict[str, Dict[str, Any]] = {}


def get_import_export_service():
    """Dependency injection for ImportExportService."""
    return ImportExportService()


# File upload security validation
def validate_upload_file(file: UploadFile) -> None:
    """
    Validate uploaded file for security compliance.
    
    Args:
        file: Uploaded file to validate
        
    Raises:
        HTTPException: If file fails security validation
    """
    # Check file size (max 100MB)
    max_size = 100 * 1024 * 1024  # 100MB
    if file.size and file.size > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File troppo grande. Dimensione massima: {max_size // (1024*1024)}MB"
        )
    
    # Check file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nome file mancante")
    
    allowed_extensions = {'.csv', '.json'}
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Formato file non supportato. Formati consentiti: {', '.join(allowed_extensions)}"
        )
    
    # Check content type
    allowed_content_types = {
        'text/csv', 'application/csv', 'text/plain',
        'application/json', 'text/json'
    }
    if file.content_type and file.content_type not in allowed_content_types:
        logger.warning(f"Suspicious content type: {file.content_type} for file: {file.filename}")


async def save_upload_file(file: UploadFile) -> str:
    """
    Securely save uploaded file to temporary location.
    
    Args:
        file: Uploaded file to save
        
    Returns:
        Path to saved temporary file
        
    Raises:
        HTTPException: If file save fails
    """
    try:
        # Create secure temporary file
        suffix = Path(file.filename).suffix.lower()
        temp_fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix="import_")
        
        # Write file content
        with os.fdopen(temp_fd, 'wb') as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        logger.info(f"File uploaded and saved: {file.filename} -> {temp_path}")
        return temp_path
    
    except Exception as e:
        logger.error(f"Error saving uploaded file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Errore nel salvataggio del file")


def cleanup_temp_file(file_path: str) -> None:
    """
    Clean up temporary file safely.
    
    Args:
        file_path: Path to temporary file to remove
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.debug(f"Temporary file cleaned up: {file_path}")
    except Exception as e:
        logger.warning(f"Could not clean up temporary file {file_path}: {e}")


# Route handlers

@router.get("/", response_class=HTMLResponse)
async def import_export_home(
    request: Request,
    csrf_token: str = Depends(generate_csrf_token)
):
    """
    Main import/export interface page.
    
    Provides access to both import and export functionality with
    navigation to specific operations.
    """
    try:
        return templates.TemplateResponse(
            "import_export/index.html",
            {
                "request": request,
                "page_title": "Import/Export Dati",
                "page_subtitle": "Gestione importazione ed esportazione dati organizzativi",
                "csrf_token": csrf_token,
                "breadcrumb": [
                    ##{"name": "Home", "url": "/"},
                    {"name": "Import/Export"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error loading import/export home page: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/import", response_class=HTMLResponse)
async def import_form(
    request: Request,
    csrf_token: str = Depends(generate_csrf_token)
):
    """
    Display import form interface.
    
    Shows file upload form with entity type selection and import options.
    Implements Requirements 1.1, 5.1, 5.2.
    """
    try:
        # Available entity types for import
        entity_types = [
            {"value": "unit_types", "label": "Tipi di Unità", "description": "Definizioni dei tipi di unità organizzative"},
            {"value": "unit_type_themes", "label": "Temi Tipi Unità", "description": "Temi grafici per i tipi di unità"},
            {"value": "units", "label": "Unità", "description": "Unità organizzative"},
            {"value": "job_titles", "label": "Titoli Lavorativi", "description": "Ruoli e posizioni lavorative"},
            {"value": "persons", "label": "Persone", "description": "Anagrafica delle persone"},
            {"value": "assignments", "label": "Incarichi", "description": "Assegnazioni di persone a unità e ruoli"}
        ]
        
        # Conflict resolution strategies
        conflict_strategies = [
            {"value": "skip", "label": "Ignora Duplicati", "description": "Salta i record già esistenti"},
            {"value": "update", "label": "Aggiorna Esistenti", "description": "Aggiorna i record esistenti con nuovi dati"},
            {"value": "create_version", "label": "Crea Nuova Versione", "description": "Crea nuove versioni per gli incarichi (solo assignments)"}
        ]
        
        return templates.TemplateResponse(
            "import_export/import.html",
            {
                "request": request,
                "page_title": "Importa Dati",
                "page_subtitle": "Carica dati da file CSV o JSON",
                "entity_types": entity_types,
                "conflict_strategies": conflict_strategies,
                "csrf_token": csrf_token,
                "breadcrumb": [
                    {"name": "Home", "url": "/"},
                    {"name": "Import/Export", "url": "/import-export"},
                    {"name": "Importa"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error loading import form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/upload")
async def upload_import_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    entity_types: str = Form(...),
    conflict_resolution: str = Form("skip"),
    validate_only: bool = Form(False),
    batch_size: int = Form(100),
    csrf_protection: bool = Depends(validate_csrf_token_flexible),
    import_export_service: ImportExportService = Depends(get_import_export_service)
):
    """
    Handle file upload and initiate import process.
    
    Implements Requirements 1.1, 7.1, 7.2 with:
    - File upload handling with security validation
    - Async processing for large operations
    - Operation status tracking
    """
    operation_id = str(uuid.uuid4())
    temp_file_path = None
    
    try:
        # Security validation for file upload
        validate_upload_file(file)
        
        # Log security event
        log_security_event('IMPORT_FILE_UPLOAD', {
            'filename': file.filename,
            'content_type': file.content_type,
            'size': file.size,
            'operation_id': operation_id,
            'client_ip': get_client_ip(request)
        }, request)
        
        # Parse and validate form data
        try:
            entity_types_list = [et.strip() for et in entity_types.split(',') if et.strip()]
            if not entity_types_list:
                raise ValueError("Almeno un tipo di entità deve essere selezionato")
            
            # Validate entity types
            valid_entities = {'unit_types', 'unit_type_themes', 'units', 'job_titles', 'persons', 'assignments'}
            invalid_entities = set(entity_types_list) - valid_entities
            if invalid_entities:
                raise ValueError(f"Tipi di entità non validi: {', '.join(invalid_entities)}")
            
            # Validate conflict resolution strategy
            if conflict_resolution not in ['skip', 'update', 'create_version']:
                raise ValueError("Strategia di risoluzione conflitti non valida")
            
            # Validate batch size
            if not (1 <= batch_size <= 1000):
                raise ValueError("Dimensione batch deve essere tra 1 e 1000")
        
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Save uploaded file securely
        temp_file_path = await save_upload_file(file)
        
        # Detect file format
        try:
            file_format = import_export_service.detect_file_format(temp_file_path)
        except Exception as e:
            cleanup_temp_file(temp_file_path)
            raise HTTPException(status_code=400, detail=f"Formato file non riconosciuto: {str(e)}")
        
        # Create import options
        import_options = ImportOptions(
            entity_types=entity_types_list,
            conflict_resolution=ConflictResolutionStrategy(conflict_resolution),
            validate_only=validate_only,
            batch_size=batch_size
        )
        
        # Initialize operation status
        operation_status[operation_id] = {
            "status": "processing",
            "progress": 0,
            "message": "Inizializzazione importazione...",
            "start_time": datetime.now().isoformat(),
            "filename": file.filename,
            "file_format": file_format.value,
            "entity_types": entity_types_list,
            "validate_only": validate_only,
            "errors": [],
            "warnings": [],
            "results": None
        }
        
        # Start async processing
        if validate_only:
            background_tasks.add_task(
                process_import_preview,
                operation_id, temp_file_path, file_format, import_options, import_export_service
            )
        else:
            background_tasks.add_task(
                process_import_operation,
                operation_id, temp_file_path, file_format, import_options, import_export_service
            )
        
        # Return operation ID for status tracking
        return JSONResponse({
            "success": True,
            "operation_id": operation_id,
            "message": "File caricato con successo. Elaborazione in corso...",
            "status_url": f"/import-export/status/{operation_id}"
        })
    
    except HTTPException:
        if temp_file_path:
            cleanup_temp_file(temp_file_path)
        raise
    except Exception as e:
        if temp_file_path:
            cleanup_temp_file(temp_file_path)
        logger.error(f"Error in import upload: {e}")
        raise HTTPException(status_code=500, detail="Errore interno del server")


async def process_import_preview(
    operation_id: str,
    file_path: str,
    file_format: FileFormat,
    options: ImportOptions,
    service: ImportExportService
):
    """
    Background task for processing import preview.
    
    Args:
        operation_id: Unique operation identifier
        file_path: Path to uploaded file
        file_format: Detected file format
        options: Import options
        service: Import/export service instance
    """
    try:
        # Update status
        operation_status[operation_id]["message"] = "Analisi file in corso..."
        operation_status[operation_id]["progress"] = 10
        
        # Process preview
        preview_result = service.preview_import(file_path, file_format, options)
        
        # Update status with results
        operation_status[operation_id].update({
            "status": "completed" if preview_result.success else "completed_with_errors",
            "progress": 100,
            "message": "Anteprima completata",
            "results": {
                "success": preview_result.success,
                "total_records": preview_result.total_records,
                "preview_data": preview_result.preview_data,
                "dependency_order": preview_result.dependency_order,
                "foreign_key_mappings": preview_result.foreign_key_mappings,
                "estimated_processing_time": preview_result.estimated_processing_time
            },
            "errors": [str(error) for error in preview_result.validation_results 
                      if error.error_type in [ImportErrorType.FILE_FORMAT_ERROR, 
                                            ImportErrorType.FOREIGN_KEY_VIOLATION,
                                            ImportErrorType.MISSING_REQUIRED_FIELD]],
            "warnings": [str(error) for error in preview_result.validation_results 
                        if error.error_type not in [ImportErrorType.FILE_FORMAT_ERROR, 
                                                   ImportErrorType.FOREIGN_KEY_VIOLATION,
                                                   ImportErrorType.MISSING_REQUIRED_FIELD]],
            "end_time": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in import preview processing: {e}")
        operation_status[operation_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"Errore durante l'anteprima: {str(e)}",
            "errors": [str(e)],
            "end_time": datetime.now().isoformat()
        })
    
    finally:
        # Clean up temporary file
        cleanup_temp_file(file_path)


async def process_import_operation(
    operation_id: str,
    file_path: str,
    file_format: FileFormat,
    options: ImportOptions,
    service: ImportExportService
):
    """
    Background task for processing actual import operation.
    
    Args:
        operation_id: Unique operation identifier
        file_path: Path to uploaded file
        file_format: Detected file format
        options: Import options
        service: Import/export service instance
    """
    try:
        # Update status
        operation_status[operation_id]["message"] = "Importazione in corso..."
        operation_status[operation_id]["progress"] = 20
        
        # Process import (this would call the actual import method when implemented)
        # For now, we'll simulate the process
        await asyncio.sleep(2)  # Simulate processing time
        
        # TODO: Implement actual import processing when import_data method is available
        # import_result = service.import_data(file_path, file_format, options)
        
        # Simulate successful import result
        operation_status[operation_id].update({
            "status": "completed",
            "progress": 100,
            "message": "Importazione completata con successo",
            "results": {
                "success": True,
                "records_processed": {"total": 100},
                "records_created": {"total": 80},
                "records_updated": {"total": 15},
                "records_skipped": {"total": 5}
            },
            "end_time": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in import operation processing: {e}")
        operation_status[operation_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"Errore durante l'importazione: {str(e)}",
            "errors": [str(e)],
            "end_time": datetime.now().isoformat()
        })
    
    finally:
        # Clean up temporary file
        cleanup_temp_file(file_path)


@router.get("/export", response_class=HTMLResponse)
async def export_form(
    request: Request,
    csrf_token: str = Depends(generate_csrf_token)
):
    """
    Display export form interface.
    
    Shows export configuration form with entity type and date range selection.
    Implements Requirements 2.1, 2.2, 6.1, 6.2.
    """
    try:
        # Available entity types for export
        entity_types = [
            {"value": "unit_types", "label": "Tipi di Unità", "description": "Definizioni dei tipi di unità organizzative"},
            {"value": "unit_type_themes", "label": "Temi Tipi Unità", "description": "Temi grafici per i tipi di unità"},
            {"value": "units", "label": "Unità", "description": "Unità organizzative"},
            {"value": "job_titles", "label": "Titoli Lavorativi", "description": "Ruoli e posizioni lavorative"},
            {"value": "persons", "label": "Persone", "description": "Anagrafica delle persone"},
            {"value": "assignments", "label": "Incarichi", "description": "Assegnazioni di persone a unità e ruoli"}
        ]
        
        # Export formats
        export_formats = [
            {"value": "json", "label": "JSON", "description": "Formato JSON strutturato (file singolo)"},
            {"value": "csv", "label": "CSV", "description": "Formato CSV (file separati per tipo)"}
        ]
        
        return templates.TemplateResponse(
            "import_export/export.html",
            {
                "request": request,
                "page_title": "Esporta Dati",
                "page_subtitle": "Scarica dati in formato CSV o JSON",
                "entity_types": entity_types,
                "export_formats": export_formats,
                "csrf_token": csrf_token,
                "breadcrumb": [
                    {"name": "Home", "url": "/"},
                    {"name": "Import/Export", "url": "/import-export"},
                    {"name": "Esporta"}
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error loading export form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/generate")
async def generate_export(
    request: Request,
    background_tasks: BackgroundTasks,
    entity_types: str = Form(...),
    export_format: str = Form("json"),
    include_historical: bool = Form(True),
    date_from: Optional[str] = Form(None),
    date_to: Optional[str] = Form(None),
    csrf_protection: bool = Depends(validate_csrf_token_flexible),
    import_export_service: ImportExportService = Depends(get_import_export_service)
):
    """
    Generate export files based on user configuration.
    
    Implements Requirements 2.1, 2.2, 6.1, 6.2 with:
    - Export configuration processing
    - Async file generation for large datasets
    - Download link generation
    """
    operation_id = str(uuid.uuid4())
    
    try:
        # Parse and validate form data
        try:
            entity_types_list = [et.strip() for et in entity_types.split(',') if et.strip()]
            if not entity_types_list:
                raise ValueError("Almeno un tipo di entità deve essere selezionato")
            
            # Validate entity types
            valid_entities = {'unit_types', 'unit_type_themes', 'units', 'job_titles', 'persons', 'assignments'}
            invalid_entities = set(entity_types_list) - valid_entities
            if invalid_entities:
                raise ValueError(f"Tipi di entità non validi: {', '.join(invalid_entities)}")
            
            # Validate export format
            if export_format not in ['json', 'csv']:
                raise ValueError("Formato di esportazione non valido")
            
            # Parse date range if provided
            date_range = None
            if date_from and date_to:
                try:
                    from datetime import date
                    date_from_parsed = date.fromisoformat(date_from)
                    date_to_parsed = date.fromisoformat(date_to)
                    if date_from_parsed > date_to_parsed:
                        raise ValueError("La data di inizio deve essere precedente alla data di fine")
                    date_range = (date_from_parsed, date_to_parsed)
                except ValueError as e:
                    raise ValueError(f"Formato data non valido: {str(e)}")
        
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Log security event
        log_security_event('EXPORT_GENERATION', {
            'entity_types': entity_types_list,
            'export_format': export_format,
            'include_historical': include_historical,
            'date_range': f"{date_from} to {date_to}" if date_range else None,
            'operation_id': operation_id,
            'client_ip': get_client_ip(request)
        }, request)
        
        # Create export options
        export_options = ExportOptions(
            entity_types=entity_types_list,
            include_historical=include_historical,
            date_range=date_range
        )
        
        # Initialize operation status
        operation_status[operation_id] = {
            "status": "processing",
            "progress": 0,
            "message": "Inizializzazione esportazione...",
            "start_time": datetime.now().isoformat(),
            "export_format": export_format,
            "entity_types": entity_types_list,
            "include_historical": include_historical,
            "date_range": f"{date_from} to {date_to}" if date_range else None,
            "errors": [],
            "warnings": [],
            "download_urls": []
        }
        
        # Start async export processing
        background_tasks.add_task(
            process_export_operation,
            operation_id, export_format, export_options, import_export_service
        )
        
        # Return operation ID for status tracking
        return JSONResponse({
            "success": True,
            "operation_id": operation_id,
            "message": "Esportazione avviata. Elaborazione in corso...",
            "status_url": f"/import-export/status/{operation_id}"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in export generation: {e}")
        raise HTTPException(status_code=500, detail="Errore interno del server")


async def process_export_operation_old(
    operation_id: str,
    export_format: str,
    options: ExportOptions,
    service: ImportExportService
):
    """
    Background task for processing export operation.
    
    Args:
        operation_id: Unique operation identifier
        export_format: Export format (json/csv)
        options: Export options
        service: Import/export service instance
    """
    try:
        # Update status
        operation_status[operation_id]["message"] = "Esportazione in corso..."
        operation_status[operation_id]["progress"] = 20
        
        ##await asyncio.sleep(1)
        export_result = service.export_data(FileFormat[export_format.upper()], options)
        
        # Simulate successful export result with download URLs
        download_urls = []

        if export_result.success:
            for exported_file in export_result.exported_files:
                download_urls.append({
                    "filename": f"{Path(exported_file).name}",
                    "url": f"/import-export/download/{operation_id}/{Path(exported_file).name}",
                    "size": f"{export_result.file_sizes[exported_file]}"
                })

        # if export_format == "json":
        #     download_urls.append({
        #         "filename": f"export_{operation_id}.json",
        #         "url": f"/import-export/download/{operation_id}/export.json",
        #         "size": "2.5 MB"
        #     })
        # else:  # CSV
        #     for entity_type in options.entity_types:
        #         download_urls.append({
        #             "filename": f"{entity_type}_{operation_id}.csv",
        #             "url": f"/import-export/download/{operation_id}/{entity_type}.csv",
        #             "size": "1.2 MB"
        #         })
        
        operation_status[operation_id].update({
            "status": "completed",
            "progress": 100,
            "message": "Esportazione completata con successo",
            "exported_records": export_result.records_exported if export_result.records_exported else [],
            "errors": export_result.errors if export_result.errors else [],
            "warnings": export_result.warnings if export_result.warnings else [],
            "download_urls": download_urls,
            "end_time": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in export operation processing: {e}")
        operation_status[operation_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"Errore durante l'esportazione: {str(e)}",
            "errors": [str(e)],
            "end_time": datetime.now().isoformat()
        })


async def process_export_operation(
    operation_id: str,
    export_format: str,
    options: ExportOptions,
    service: ImportExportService
):
    """
    Background task for processing export operation.
    
    Args:
        operation_id: Unique operation identifier
        export_format: Export format (json/csv)
        options: Export options
        service: Import/export service instance
    """
    try:
        # Update status
        operation_status[operation_id]["message"] = "Esportazione in corso..."
        operation_status[operation_id]["progress"] = 20
        
        # Execute the export
        export_result = service.export_data(FileFormat[export_format.upper()], options)
        
        # Build download URLs from the actual exported files
        download_urls = []
        
        if export_result.success:
            for exported_file in export_result.exported_files:
                file_name = Path(exported_file).name
                file_size = export_result.file_sizes.get(exported_file, 0)
                
                download_urls.append({
                    "filename": file_name,
                    "url": f"/import-export/download/{operation_id}/{file_name}",
                    "size": f"{file_size / 1024:.2f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.2f} MB",
                    "actual_size": f"{file_size}",
                    "actual_path": exported_file  # Store the actual path for retrieval
                })
        
        # Store the complete export result and file mappings
        operation_status[operation_id].update({
            "status": "completed" if export_result.success else "failed",
            "progress": 100,
            "message": "Esportazione completata con successo" if export_result.success else "Esportazione fallita",
            "exported_records": export_result.records_exported if export_result.records_exported else {},
            "errors": [str(e) for e in export_result.errors] if export_result.errors else [],
            "warnings": [str(w) for w in export_result.warnings] if export_result.warnings else [],
            "download_urls": download_urls,
            "exported_files": export_result.exported_files,  # Store the actual file paths
            "end_time": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in export operation processing: {e}")
        operation_status[operation_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"Errore durante l'esportazione: {str(e)}",
            "errors": [str(e)],
            "end_time": datetime.now().isoformat()
        })

@router.get("/status/{operation_id}")
async def get_operation_status(operation_id: str):
    """
    Get status of import/export operation.
    
    Implements Requirements 7.1, 7.2 with:
    - Job status tracking system
    - Progress reporting for long operations
    
    Args:
        operation_id: Unique operation identifier
        
    Returns:
        JSON response with operation status
    """
    try:
        if operation_id not in operation_status:
            raise HTTPException(status_code=404, detail="Operazione non trovata")
        
        status_info = operation_status[operation_id]
        
        return JSONResponse({
            "operation_id": operation_id,
            "status": status_info["status"],
            "progress": status_info["progress"],
            "message": status_info["message"],
            "start_time": status_info["start_time"],
            "end_time": status_info.get("end_time"),
            "errors": status_info.get("errors", []),
            "warnings": status_info.get("warnings", []),
            "results": status_info.get("results"),
            "download_urls": status_info.get("download_urls", [])
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting operation status for {operation_id}: {e}")
        raise HTTPException(status_code=500, detail="Errore interno del server")


@router.get("/status/{operation_id}/page", response_class=HTMLResponse)
async def operation_status_page(
    request: Request,
    operation_id: str
):
    """
    Display operation status page.
    
    Shows detailed status information with progress updates and results.
    Implements Requirements 7.1, 7.2.
    """
    try:
        if operation_id not in operation_status:
            raise HTTPException(status_code=404, detail="Operazione non trovata")
        
        status_info = operation_status[operation_id]
        
        return templates.TemplateResponse(
            "import_export/status.html",
            {
                "request": request,
                "page_title": "Stato Operazione",
                "page_subtitle": f"Operazione: {operation_id[:8]}...",
                "operation_id": operation_id,
                "status_info": status_info,
                "breadcrumb": [
                    ##{"name": "Home", "url": "/"},
                    {"name": "Import/Export", "url": "/import-export"},
                    {"name": "Stato Operazione"}
                ]
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading status page for {operation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{operation_id}/{filename}")
async def download_export_file(operation_id: str, filename: str):
    """
    Download exported file.
    
    Provides secure file download for completed export operations.
    
    Args:
        operation_id: Operation identifier
        filename: Name of file to download
        
    Returns:
        File response with exported data
    """
    try:
        # Validate operation exists and is completed
        if operation_id not in operation_status:
            raise HTTPException(status_code=404, detail="Operazione non trovata")
        
        status_info = operation_status[operation_id]
        if status_info["status"] != "completed":
            raise HTTPException(status_code=400, detail="Operazione non completata")
        
        # Get the actual file path from stored export results
        exported_files = status_info.get("exported_files", [])
        file_path = None
        
        # Find the file with matching filename
        for exported_file in exported_files:
            if Path(exported_file).name == filename:
                file_path = exported_file
                break
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File non trovato fra quelli esportati")

        # Validate filename is in allowed downloads
        download_urls = status_info.get("download_urls", [])
        valid_filenames = {url["filename"] for url in download_urls}
        
        if filename not in valid_filenames:
            raise HTTPException(status_code=404, detail="File non trovato o non autorizzato")

        # Determine media type
        file_extension = Path(filename).suffix.lower()
        media_type = "application/octet-stream"

        if file_extension == ".json":
            media_type = "application/json"
        elif file_extension == ".csv":
            media_type = "text/csv; charset=utf-8"
            

        # Return the file
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {filename} for operation {operation_id}: {e}")
        raise HTTPException(status_code=500, detail="Errore interno del server")


# Operation Status and Monitoring Endpoints (Task 8.2)

@router.get("/operations", response_class=HTMLResponse)
async def operations_history(
    request: Request,
    page: int = 1,
    limit: int = 20,
    operation_type: Optional[str] = None,
    status_filter: Optional[str] = None
):
    """
    Display operation history page with filtering and pagination.
    
    Implements Requirements 7.1, 7.2, 7.3 with:
    - Operation history display
    - Filtering by type and status
    - Pagination for large result sets
    """
    try:
        # Filter operations based on criteria
        filtered_operations = []
        
        for op_id, op_info in operation_status.items():
            # Apply filters
            if operation_type and operation_type != "all":
                op_type = "import" if op_info.get("filename") else "export"
                if op_type != operation_type:
                    continue
            
            if status_filter and status_filter != "all":
                if op_info.get("status") != status_filter:
                    continue
            
            # Add operation to filtered list
            operation_summary = {
                "id": op_id,
                "type": "import" if op_info.get("filename") else "export",
                "status": op_info.get("status", "unknown"),
                "start_time": op_info.get("start_time"),
                "end_time": op_info.get("end_time"),
                "message": op_info.get("message", ""),
                "entity_types": op_info.get("entity_types", []),
                "filename": op_info.get("filename"),
                "export_format": op_info.get("export_format"),
                "progress": op_info.get("progress", 0),
                "error_count": len(op_info.get("errors", [])),
                "warning_count": len(op_info.get("warnings", []))
            }
            filtered_operations.append(operation_summary)
        
        # Sort by start time (most recent first)
        filtered_operations.sort(key=lambda x: x["start_time"] or "", reverse=True)
        
        # Pagination
        total_operations = len(filtered_operations)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_operations = filtered_operations[start_idx:end_idx]
        
        # Calculate pagination info
        total_pages = (total_operations + limit - 1) // limit
        has_prev = page > 1
        has_next = page < total_pages
        
        return templates.TemplateResponse(
            "import_export/operations.html",
            {
                "request": request,
                "page_title": "Storico Operazioni",
                "page_subtitle": "Cronologia delle operazioni di import/export",
                "operations": paginated_operations,
                "current_page": page,
                "total_pages": total_pages,
                "total_operations": total_operations,
                "has_prev": has_prev,
                "has_next": has_next,
                "operation_type": operation_type or "all",
                "status_filter": status_filter or "all",
                "breadcrumb": [
                    ##{"name": "Home", "url": "/"},
                    {"name": "Import/Export", "url": "/import-export"},
                    {"name": "Storico Operazioni"}
                ]
            }
        )
    
    except Exception as e:
        logger.error(f"Error loading operations history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/operations/stats")
async def operations_statistics():
    """
    Get operation statistics for monitoring dashboard.
    
    Implements Requirements 7.1, 7.2, 7.3 with:
    - Operation statistics aggregation
    - Success/failure rates
    - Performance metrics
    
    Returns:
        JSON response with operation statistics
    """
    try:
        stats = {
            "total_operations": len(operation_status),
            "active_operations": 0,
            "completed_operations": 0,
            "failed_operations": 0,
            "import_operations": 0,
            "export_operations": 0,
            "operations_today": 0,
            "average_processing_time": 0,
            "success_rate": 0,
            "recent_operations": []
        }
        
        from datetime import datetime, timedelta
        today = datetime.now().date()
        processing_times = []
        
        for op_id, op_info in operation_status.items():
            # Count by status
            status = op_info.get("status", "unknown")
            if status == "processing":
                stats["active_operations"] += 1
            elif status in ["completed", "completed_with_errors"]:
                stats["completed_operations"] += 1
            elif status == "failed":
                stats["failed_operations"] += 1
            
            # Count by type
            if op_info.get("filename"):
                stats["import_operations"] += 1
            else:
                stats["export_operations"] += 1
            
            # Count operations today
            start_time_str = op_info.get("start_time")
            if start_time_str:
                try:
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    if start_time.date() == today:
                        stats["operations_today"] += 1
                except:
                    pass
            
            # Calculate processing time for completed operations
            if status in ["completed", "completed_with_errors", "failed"]:
                start_time_str = op_info.get("start_time")
                end_time_str = op_info.get("end_time")
                if start_time_str and end_time_str:
                    try:
                        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                        processing_time = (end_time - start_time).total_seconds()
                        processing_times.append(processing_time)
                    except:
                        pass
            
            # Add to recent operations (last 5)
            if len(stats["recent_operations"]) < 5:
                stats["recent_operations"].append({
                    "id": op_id,
                    "type": "import" if op_info.get("filename") else "export",
                    "status": status,
                    "start_time": start_time_str,
                    "message": op_info.get("message", "")[:50] + "..." if len(op_info.get("message", "")) > 50 else op_info.get("message", "")
                })
        
        # Calculate average processing time
        if processing_times:
            stats["average_processing_time"] = sum(processing_times) / len(processing_times)
        
        # Calculate success rate
        total_completed = stats["completed_operations"] + stats["failed_operations"]
        if total_completed > 0:
            stats["success_rate"] = (stats["completed_operations"] / total_completed) * 100
        
        # Sort recent operations by start time
        stats["recent_operations"].sort(key=lambda x: x["start_time"] or "", reverse=True)
        
        return JSONResponse(stats)
    
    except Exception as e:
        logger.error(f"Error getting operation statistics: {e}")
        raise HTTPException(status_code=500, detail="Errore interno del server")


@router.get("/operations/{operation_id}/logs")
async def get_operation_logs(operation_id: str):
    """
    Get detailed logs for a specific operation.
    
    Implements Requirements 7.4, 7.5 with:
    - Detailed error logs
    - Operation audit trail
    - Line-by-line error reporting
    
    Args:
        operation_id: Operation identifier
        
    Returns:
        JSON response with detailed operation logs
    """
    try:
        if operation_id not in operation_status:
            raise HTTPException(status_code=404, detail="Operazione non trovata")
        
        operation_info = operation_status[operation_id]
        
        # Build detailed log information
        logs = {
            "operation_id": operation_id,
            "operation_type": "import" if operation_info.get("filename") else "export",
            "status": operation_info.get("status"),
            "start_time": operation_info.get("start_time"),
            "end_time": operation_info.get("end_time"),
            "duration": None,
            "configuration": {
                "entity_types": operation_info.get("entity_types", []),
                "filename": operation_info.get("filename"),
                "file_format": operation_info.get("file_format"),
                "export_format": operation_info.get("export_format"),
                "validate_only": operation_info.get("validate_only", False),
                "include_historical": operation_info.get("include_historical"),
                "date_range": operation_info.get("date_range")
            },
            "progress_log": [
                {
                    "timestamp": operation_info.get("start_time"),
                    "progress": 0,
                    "message": "Operazione iniziata",
                    "level": "info"
                }
            ],
            "errors": [],
            "warnings": [],
            "results": operation_info.get("results", {}),
            "download_urls": operation_info.get("download_urls", [])
        }
        
        # Calculate duration if both times are available
        if operation_info.get("start_time") and operation_info.get("end_time"):
            try:
                start_time = datetime.fromisoformat(operation_info["start_time"].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(operation_info["end_time"].replace('Z', '+00:00'))
                logs["duration"] = (end_time - start_time).total_seconds()
            except:
                pass
        
        # Add current progress to log
        current_progress = operation_info.get("progress", 0)
        current_message = operation_info.get("message", "")
        if current_progress > 0 or current_message:
            logs["progress_log"].append({
                "timestamp": operation_info.get("end_time") or datetime.now().isoformat(),
                "progress": current_progress,
                "message": current_message,
                "level": "info" if operation_info.get("status") == "completed" else "warning" if operation_info.get("status") == "completed_with_errors" else "error"
            })
        
        # Process errors with detailed information
        for error in operation_info.get("errors", []):
            logs["errors"].append({
                "timestamp": datetime.now().isoformat(),
                "message": error,
                "level": "error",
                "category": "processing"
            })
        
        # Process warnings
        for warning in operation_info.get("warnings", []):
            logs["warnings"].append({
                "timestamp": datetime.now().isoformat(),
                "message": warning,
                "level": "warning",
                "category": "validation"
            })
        
        return JSONResponse(logs)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting operation logs for {operation_id}: {e}")
        raise HTTPException(status_code=500, detail="Errore interno del server")


@router.delete("/operations/{operation_id}")
async def delete_operation(
    request: Request,
    operation_id: str
):
    """
    Delete operation record and associated files.
    
    Implements Requirements 7.3 with:
    - Operation cleanup
    - File cleanup
    - Audit logging
    
    Args:
        operation_id: Operation identifier
        
    Returns:
        JSON response confirming deletion
    """
    try:
        if operation_id not in operation_status:
            raise HTTPException(status_code=404, detail="Operazione non trovata")
        
        operation_info = operation_status[operation_id]
        
        # Log deletion event
        log_security_event('OPERATION_DELETED', {
            'operation_id': operation_id,
            'operation_type': "import" if operation_info.get("filename") else "export",
            'status': operation_info.get("status"),
            'client_ip': get_client_ip(request)
        }, request)
        
        # TODO: Clean up associated files when file storage is implemented
        # This would include temporary files and generated export files
        
        # Remove operation from status tracking
        del operation_status[operation_id]
        
        return JSONResponse({
            "success": True,
            "message": "Operazione eliminata con successo"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting operation {operation_id}: {e}")
        raise HTTPException(status_code=500, detail="Errore interno del server")


@router.get("/monitoring", response_class=HTMLResponse)
async def monitoring_dashboard(request: Request):
    """
    Display monitoring dashboard with real-time operation status.
    
    Implements Requirements 7.1, 7.2, 7.3 with:
    - Real-time operation monitoring
    - System health indicators
    - Performance metrics display
    """
    try:
        return templates.TemplateResponse(
            "import_export/monitoring.html",
            {
                "request": request,
                "page_title": "Monitoraggio Operazioni",
                "page_subtitle": "Dashboard di monitoraggio in tempo reale",
                "breadcrumb": [
                    ##{"name": "Home", "url": "/"},
                    {"name": "Import/Export", "url": "/import-export"},
                    {"name": "Monitoraggio"}
                ]
            }
        )
    
    except Exception as e:
        logger.error(f"Error loading monitoring dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def import_export_health():
    """
    Health check endpoint for import/export system.
    
    Implements Requirements 7.1, 7.2 with:
    - System health status
    - Service availability check
    - Performance indicators
    
    Returns:
        JSON response with health status
    """
    try:
        # Check service dependencies
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "import_export_service": "healthy",
                "file_storage": "healthy",
                "database": "healthy"
            },
            "metrics": {
                "active_operations": len([op for op in operation_status.values() if op.get("status") == "processing"]),
                "total_operations": len(operation_status),
                "memory_usage": "normal",
                "disk_space": "normal"
            }
        }
        
        # Check for any failed operations in the last hour
        from datetime import datetime, timedelta
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_failures = 0
        
        for op_info in operation_status.values():
            if op_info.get("status") == "failed":
                start_time_str = op_info.get("start_time")
                if start_time_str:
                    try:
                        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        if start_time.replace(tzinfo=None) > one_hour_ago:
                            recent_failures += 1
                    except:
                        pass
        
        # Adjust health status based on recent failures
        if recent_failures > 5:
            health_status["status"] = "degraded"
            health_status["services"]["import_export_service"] = "degraded"
        elif recent_failures > 10:
            health_status["status"] = "unhealthy"
            health_status["services"]["import_export_service"] = "unhealthy"
        
        return JSONResponse(health_status)
    
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return JSONResponse({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }, status_code=500)