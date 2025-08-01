"""
Company service for business logic
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime
from app.services.base import BaseService, ServiceValidationException, ServiceIntegrityException
from app.models.company import Company

logger = logging.getLogger(__name__)


class CompanyService(BaseService):
    """Company service class for managing organizational relationships (Requirements 3.1-3.8)"""
    
    def __init__(self):
        super().__init__(Company, "companies")
    
    def get_list_query(self) -> str:
        """Get query for listing all companies with contact information"""
        return """
        SELECT c.*,
               p1.name as main_contact_name,
               p2.name as financial_contact_name
        FROM companies c
        LEFT JOIN persons p1 ON c.main_contact_id = p1.id
        LEFT JOIN persons p2 ON c.financial_contact_id = p2.id
        ORDER BY c.name
        """
    
    def get_by_id_query(self) -> str:
        """Get query for fetching single company by ID with contact information"""
        return """
        SELECT c.*,
               p1.name as main_contact_name,
               p2.name as financial_contact_name
        FROM companies c
        LEFT JOIN persons p1 ON c.main_contact_id = p1.id
        LEFT JOIN persons p2 ON c.financial_contact_id = p2.id
        WHERE c.id = ?
        """
    
    def get_insert_query(self) -> str:
        return """
        INSERT INTO companies (
            name, short_name, registration_no, address, city, postal_code, country,
            phone, email, website, main_contact_id, financial_contact_id,
            valid_from, valid_to, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    
    def get_update_query(self) -> str:
        return """
        UPDATE companies 
        SET name = ?, short_name = ?, registration_no = ?, address = ?, city = ?, 
            postal_code = ?, country = ?, phone = ?, email = ?, website = ?,
            main_contact_id = ?, financial_contact_id = ?, valid_from = ?, 
            valid_to = ?, notes = ?
        WHERE id = ?
        """
    
    def get_delete_query(self) -> str:
        return "DELETE FROM companies WHERE id = ?"
    
    def model_to_insert_params(self, company: Company) -> tuple:
        """Convert company to parameters for insert query"""
        return (
            company.name,
            company.short_name,
            company.registration_no,
            company.address,
            company.city,
            company.postal_code,
            company.country,
            company.phone,
            company.email,
            company.website,
            company.main_contact_id,
            company.financial_contact_id,
            company.valid_from.isoformat() if company.valid_from else None,
            company.valid_to.isoformat() if company.valid_to else None,
            company.notes
        )
    
    def model_to_update_params(self, company: Company) -> tuple:
        """Convert company to parameters for update query"""
        return (
            company.name,
            company.short_name,
            company.registration_no,
            company.address,
            company.city,
            company.postal_code,
            company.country,
            company.phone,
            company.email,
            company.website,
            company.main_contact_id,
            company.financial_contact_id,
            company.valid_from.isoformat() if company.valid_from else None,
            company.valid_to.isoformat() if company.valid_to else None,
            company.notes,
            company.id
        )
    
    def get_active_companies(self, as_of_date: Optional[date] = None) -> List[Company]:
        """Get companies that are active as of a specific date (Requirement 3.4)"""
        try:
            if as_of_date is None:
                as_of_date = date.today()
            
            query = """
            SELECT c.*,
                   p1.name as main_contact_name,
                   p2.name as financial_contact_name
            FROM companies c
            LEFT JOIN persons p1 ON c.main_contact_id = p1.id
            LEFT JOIN persons p2 ON c.financial_contact_id = p2.id
            WHERE (c.valid_from IS NULL OR c.valid_from <= ?)
              AND (c.valid_to IS NULL OR c.valid_to >= ?)
            ORDER BY c.name
            """
            
            rows = self.db_manager.fetch_all(query, (as_of_date.isoformat(), as_of_date.isoformat()))
            return [Company.from_sqlite_row(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error fetching active companies: {e}")
            return []
    
    def get_companies_by_contact(self, person_id: int) -> List[Company]:
        """Get companies where a person is a contact (Requirement 3.5)"""
        try:
            query = """
            SELECT c.*,
                   p1.name as main_contact_name,
                   p2.name as financial_contact_name
            FROM companies c
            LEFT JOIN persons p1 ON c.main_contact_id = p1.id
            LEFT JOIN persons p2 ON c.financial_contact_id = p2.id
            WHERE c.main_contact_id = ? OR c.financial_contact_id = ?
            ORDER BY c.name
            """
            
            rows = self.db_manager.fetch_all(query, (person_id, person_id))
            return [Company.from_sqlite_row(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error fetching companies by contact {person_id}: {e}")
            return []
    
    def can_delete(self, company_id: int) -> Tuple[bool, str]:
        """Check if company can be deleted (Requirement 3.7)"""
        try:
            # For now, companies can generally be deleted
            # In the future, this might check for dependencies like contracts, etc.
            company = self.get_by_id(company_id)
            if not company:
                return False, "Company not found"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error checking if company {company_id} can be deleted: {e}")
            return False, "Error during dependency check"
    
    def get_contact_persons(self) -> List[Dict[str, Any]]:
        """Get list of persons that can be used as company contacts (Requirement 3.6)"""
        try:
            query = """
            SELECT id, 
                   COALESCE(
                       CASE 
                           WHEN first_name IS NOT NULL AND last_name IS NOT NULL 
                           THEN last_name || ', ' || first_name
                           ELSE name
                       END, 
                       name
                   ) as display_name,
                   email
            FROM persons
            ORDER BY display_name
            """
            
            rows = self.db_manager.fetch_all(query)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error fetching contact persons: {e}")
            return []
    
    def get_company_statistics(self) -> Dict[str, Any]:
        """Get comprehensive company statistics"""
        try:
            stats = {}
            
            # Total companies
            stats['total_companies'] = self.count()
            
            # Active companies
            active_companies = self.get_active_companies()
            stats['active_companies'] = len(active_companies)
            stats['inactive_companies'] = stats['total_companies'] - stats['active_companies']
            
            # Companies with contacts
            with_main_contact_query = """
            SELECT COUNT(*) as count FROM companies WHERE main_contact_id IS NOT NULL
            """
            row = self.db_manager.fetch_one(with_main_contact_query)
            stats['companies_with_main_contact'] = row['count'] if row else 0
            
            with_financial_contact_query = """
            SELECT COUNT(*) as count FROM companies WHERE financial_contact_id IS NOT NULL
            """
            row = self.db_manager.fetch_one(with_financial_contact_query)
            stats['companies_with_financial_contact'] = row['count'] if row else 0
            
            # Companies without any contacts
            without_contacts_query = """
            SELECT COUNT(*) as count FROM companies 
            WHERE main_contact_id IS NULL AND financial_contact_id IS NULL
            """
            row = self.db_manager.fetch_one(without_contacts_query)
            stats['companies_without_contacts'] = row['count'] if row else 0
            
            # Companies by country
            country_query = """
            SELECT country, COUNT(*) as count 
            FROM companies 
            GROUP BY country 
            ORDER BY count DESC
            """
            rows = self.db_manager.fetch_all(country_query)
            stats['companies_by_country'] = [dict(row) for row in rows]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting company statistics: {e}")
            return {}
    
    def search_companies(self, search_term: str) -> List[Company]:
        """Search companies by name, registration number, or contact information"""
        try:
            if not search_term or not search_term.strip():
                return []
            
            search_pattern = f"%{search_term.strip()}%"
            
            query = """
            SELECT DISTINCT c.*,
                   p1.name as main_contact_name,
                   p2.name as financial_contact_name
            FROM companies c
            LEFT JOIN persons p1 ON c.main_contact_id = p1.id
            LEFT JOIN persons p2 ON c.financial_contact_id = p2.id
            WHERE c.name LIKE ? 
               OR c.short_name LIKE ?
               OR c.registration_no LIKE ?
               OR c.email LIKE ?
               OR p1.name LIKE ?
               OR p2.name LIKE ?
            ORDER BY c.name
            """
            
            params = (search_pattern,) * 6
            rows = self.db_manager.fetch_all(query, params)
            return [Company.from_sqlite_row(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error searching companies with term '{search_term}': {e}")
            return []
    
    def get_searchable_fields(self) -> List[str]:
        """Get list of fields that can be searched for companies"""
        return ["name", "short_name", "registration_no", "email", "city", "country"]
    
    def _validate_for_create(self, company: Company) -> None:
        """Perform additional validation before creating a company"""
        # Check for duplicate registration number if provided
        if company.registration_no:
            existing = self.db_manager.fetch_one(
                "SELECT id FROM companies WHERE registration_no = ? AND id != ?",
                (company.registration_no, company.id or -1)
            )
            if existing:
                raise ServiceValidationException(f"Company with registration number '{company.registration_no}' already exists")
        
        # Validate contact person IDs exist (Requirement 3.6)
        if company.main_contact_id:
            contact = self.db_manager.fetch_one(
                "SELECT id FROM persons WHERE id = ?",
                (company.main_contact_id,)
            )
            if not contact:
                raise ServiceValidationException(f"Main contact person with ID {company.main_contact_id} does not exist")
        
        if company.financial_contact_id:
            contact = self.db_manager.fetch_one(
                "SELECT id FROM persons WHERE id = ?",
                (company.financial_contact_id,)
            )
            if not contact:
                raise ServiceValidationException(f"Financial contact person with ID {company.financial_contact_id} does not exist")
    
    def _validate_for_update(self, company: Company, existing: Company) -> None:
        """Perform additional validation before updating a company"""
        # Check for duplicate registration number (excluding current company)
        if company.registration_no:
            duplicate = self.db_manager.fetch_one(
                "SELECT id FROM companies WHERE registration_no = ? AND id != ?",
                (company.registration_no, company.id)
            )
            if duplicate:
                raise ServiceValidationException(f"Company with registration number '{company.registration_no}' already exists")
        
        # Validate contact person IDs exist (Requirement 3.6)
        if company.main_contact_id:
            contact = self.db_manager.fetch_one(
                "SELECT id FROM persons WHERE id = ?",
                (company.main_contact_id,)
            )
            if not contact:
                raise ServiceValidationException(f"Main contact person with ID {company.main_contact_id} does not exist")
        
        if company.financial_contact_id:
            contact = self.db_manager.fetch_one(
                "SELECT id FROM persons WHERE id = ?",
                (company.financial_contact_id,)
            )
            if not contact:
                raise ServiceValidationException(f"Financial contact person with ID {company.financial_contact_id} does not exist")
    
    def _validate_for_delete(self, company: Company) -> None:
        """Perform validation before deleting a company"""
        can_delete, message = self.can_delete(company.id)
        if not can_delete:
            raise ServiceIntegrityException(message)
    
    def handle_person_deletion(self, person_id: int) -> None:
        """Handle foreign key constraints when a person is deleted (Requirement 3.7)"""
        try:
            # Update companies to remove the deleted person as contact
            # The database foreign key constraint should handle this with SET NULL,
            # but we can also do it explicitly for better control
            
            update_main_contact_query = """
            UPDATE companies SET main_contact_id = NULL WHERE main_contact_id = ?
            """
            self.db_manager.execute_query(update_main_contact_query, (person_id,))
            
            update_financial_contact_query = """
            UPDATE companies SET financial_contact_id = NULL WHERE financial_contact_id = ?
            """
            self.db_manager.execute_query(update_financial_contact_query, (person_id,))
            
            logger.info(f"Updated companies to remove person {person_id} as contact")
            
        except Exception as e:
            logger.error(f"Error handling person deletion {person_id} for companies: {e}")
            raise ServiceIntegrityException(f"Failed to handle person deletion for companies: {e}")
    
    def get_companies_expiring_soon(self, days_ahead: int = 30) -> List[Company]:
        """Get companies that will expire within the specified number of days"""
        try:
            future_date = date.today().replace(day=date.today().day + days_ahead)
            
            query = """
            SELECT c.*,
                   p1.name as main_contact_name,
                   p2.name as financial_contact_name
            FROM companies c
            LEFT JOIN persons p1 ON c.main_contact_id = p1.id
            LEFT JOIN persons p2 ON c.financial_contact_id = p2.id
            WHERE c.valid_to IS NOT NULL 
              AND c.valid_to <= ?
              AND c.valid_to >= ?
            ORDER BY c.valid_to, c.name
            """
            
            rows = self.db_manager.fetch_all(query, (future_date.isoformat(), date.today().isoformat()))
            return [Company.from_sqlite_row(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error fetching companies expiring soon: {e}")
            return []
    
    def get_companies_by_status(self, status: str) -> List[Company]:
        """Get companies filtered by status (active, expired, future)"""
        try:
            today = date.today().isoformat()
            
            if status == "active":
                query = """
                SELECT c.*,
                       p1.name as main_contact_name,
                       p2.name as financial_contact_name
                FROM companies c
                LEFT JOIN persons p1 ON c.main_contact_id = p1.id
                LEFT JOIN persons p2 ON c.financial_contact_id = p2.id
                WHERE (c.valid_from IS NULL OR c.valid_from <= ?)
                  AND (c.valid_to IS NULL OR c.valid_to >= ?)
                ORDER BY c.name
                """
                params = (today, today)
            elif status == "expired":
                query = """
                SELECT c.*,
                       p1.name as main_contact_name,
                       p2.name as financial_contact_name
                FROM companies c
                LEFT JOIN persons p1 ON c.main_contact_id = p1.id
                LEFT JOIN persons p2 ON c.financial_contact_id = p2.id
                WHERE c.valid_to IS NOT NULL AND c.valid_to < ?
                ORDER BY c.valid_to DESC, c.name
                """
                params = (today,)
            elif status == "future":
                query = """
                SELECT c.*,
                       p1.name as main_contact_name,
                       p2.name as financial_contact_name
                FROM companies c
                LEFT JOIN persons p1 ON c.main_contact_id = p1.id
                LEFT JOIN persons p2 ON c.financial_contact_id = p2.id
                WHERE c.valid_from IS NOT NULL AND c.valid_from > ?
                ORDER BY c.valid_from, c.name
                """
                params = (today,)
            else:
                return self.get_all()
            
            rows = self.db_manager.fetch_all(query, params)
            return [Company.from_sqlite_row(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error fetching companies by status '{status}': {e}")
            return []