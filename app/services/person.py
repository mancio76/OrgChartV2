"""
Person service for business logic
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime
from app.services.base import BaseService
from app.models.person import Person
from app.models.assignment import Assignment

logger = logging.getLogger(__name__)


class PersonService(BaseService):
    """Person service class"""
    
    def __init__(self):
        super().__init__(Person, "persons")
    
    def get_list_query(self) -> str:
        """Get query for listing all persons with computed fields"""
        return """
        SELECT p.*,
               COUNT(DISTINCT pja_current.id) as current_assignments_count,
               COUNT(DISTINCT pja_all.id) as total_assignments_count
        FROM persons p
        LEFT JOIN person_job_assignments pja_current ON p.id = pja_current.person_id AND pja_current.is_current = 1
        LEFT JOIN person_job_assignments pja_all ON p.id = pja_all.person_id
        GROUP BY p.id, p.name, p.short_name, p.email, p.datetime_created, p.datetime_updated
        ORDER BY p.name
        """
    
    def get_by_id_query(self) -> str:
        """Get query for fetching single person by ID"""
        return """
        SELECT p.*,
               COUNT(DISTINCT pja_current.id) as current_assignments_count,
               COUNT(DISTINCT pja_all.id) as total_assignments_count
        FROM persons p
        LEFT JOIN person_job_assignments pja_current ON p.id = pja_current.person_id AND pja_current.is_current = 1
        LEFT JOIN person_job_assignments pja_all ON p.id = pja_all.person_id
        WHERE p.id = ?
        GROUP BY p.id, p.name, p.short_name, p.email, p.datetime_created, p.datetime_updated
        """
    
    def get_insert_query(self) -> str:
        return """
        INSERT INTO persons (name, short_name, email)
        VALUES (?, ?, ?)
        """
    
    def get_update_query(self) -> str:
        return """
        UPDATE persons 
        SET name = ?, short_name = ?, email = ?
        WHERE id = ?
        """
    
    def get_delete_query(self) -> str:
        return "DELETE FROM persons WHERE id = ?"
    
    def model_to_insert_params(self, person: Person) -> tuple:
        """Convert person to parameters for insert query"""
        return (
            person.name,
            person.short_name,
            person.email
        )
    
    def model_to_update_params(self, person: Person) -> tuple:
        """Convert person to parameters for update query"""
        return (
            person.name,
            person.short_name,
            person.email,
            person.id
        )
    
    def can_delete(self, person_id: int) -> tuple[bool, str]:
        """Check if person can be deleted"""
        try:
            # Check for current assignments
            current_assignments_query = """
            SELECT COUNT(*) as count 
            FROM person_job_assignments 
            WHERE person_id = ? AND is_current = 1
            """
            row = self.db_manager.fetch_one(current_assignments_query, (person_id,))
            if row and row['count'] > 0:
                return False, f"La persona ha {row['count']} incarichi correnti"
            
            # Check for historical assignments (allow deletion but warn)
            all_assignments_query = """
            SELECT COUNT(*) as count 
            FROM person_job_assignments 
            WHERE person_id = ?
            """
            row = self.db_manager.fetch_one(all_assignments_query, (person_id,))
            if row and row['count'] > 0:
                return True, f"Attenzione: la persona ha {row['count']} incarichi storici che verranno eliminati"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error checking if person {person_id} can be deleted: {e}")
            return False, "Errore durante il controllo delle dipendenze"
    
    def get_person_statistics(self, person_id: int) -> Dict[str, Any]:
        """Get statistics for a specific person"""
        try:
            stats = {}
            
            # Current assignments count
            current_query = """
            SELECT COUNT(*) as count 
            FROM person_job_assignments 
            WHERE person_id = ? AND is_current = 1
            """
            row = self.db_manager.fetch_one(current_query, (person_id,))
            stats['current_assignments'] = row['count'] if row else 0
            
            # Total assignments count
            total_query = """
            SELECT COUNT(*) as count 
            FROM person_job_assignments 
            WHERE person_id = ?
            """
            row = self.db_manager.fetch_one(total_query, (person_id,))
            stats['total_assignments'] = row['count'] if row else 0
            
            # Different units worked in
            units_query = """
            SELECT COUNT(DISTINCT unit_id) as count 
            FROM person_job_assignments 
            WHERE person_id = ?
            """
            row = self.db_manager.fetch_one(units_query, (person_id,))
            stats['units_worked'] = row['count'] if row else 0
            
            # Different job titles held
            jobs_query = """
            SELECT COUNT(DISTINCT job_title_id) as count 
            FROM person_job_assignments 
            WHERE person_id = ?
            """
            row = self.db_manager.fetch_one(jobs_query, (person_id,))
            stats['job_titles_held'] = row['count'] if row else 0
            
            # Current workload (sum of percentages)
            workload_query = """
            SELECT SUM(percentage) as total_percentage 
            FROM person_job_assignments 
            WHERE person_id = ? AND is_current = 1
            """
            row = self.db_manager.fetch_one(workload_query, (person_id,))
            stats['current_workload'] = float(row['total_percentage']) if row and row['total_percentage'] else 0.0
            
            # Interim assignments count
            interim_query = """
            SELECT COUNT(*) as count 
            FROM person_job_assignments 
            WHERE person_id = ? AND ad_interim = 1 AND is_current = 1
            """
            row = self.db_manager.fetch_one(interim_query, (person_id,))
            stats['interim_assignments'] = row['count'] if row else 0
            
            # Average assignment duration (for terminated assignments)
            duration_query = """
            SELECT AVG(julianday(valid_to) - julianday(valid_from)) as avg_duration
            FROM person_job_assignments 
            WHERE person_id = ? AND valid_from IS NOT NULL AND valid_to IS NOT NULL
            """
            row = self.db_manager.fetch_one(duration_query, (person_id,))
            stats['avg_assignment_duration'] = round(row['avg_duration']) if row and row['avg_duration'] else 0
            
            # First assignment date
            first_assignment_query = """
            SELECT MIN(datetime_created) as first_assignment
            FROM person_job_assignments 
            WHERE person_id = ?
            """
            row = self.db_manager.fetch_one(first_assignment_query, (person_id,))
            if row and row['first_assignment']:
                try:
                    first_date = datetime.fromisoformat(row['first_assignment'].replace('Z', '+00:00'))
                    stats['first_assignment_date'] = first_date.date()
                    stats['tenure_days'] = (date.today() - first_date.date()).days
                except:
                    stats['first_assignment_date'] = None
                    stats['tenure_days'] = 0
            else:
                stats['first_assignment_date'] = None
                stats['tenure_days'] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error fetching person statistics for {person_id}: {e}")
            return {}
    
    def create_assignment_timeline(self, person_id: int, assignments: List[Assignment]) -> List[Dict[str, Any]]:
        """Create timeline data for person assignments"""
        try:
            timeline = []
            
            # Sort assignments by start date and version
            sorted_assignments = sorted(assignments, key=lambda x: (x.valid_from or date.min, x.version))
            
            for assignment in sorted_assignments:
                timeline_item = {
                    'id': assignment.id,
                    'title': f"{assignment.job_title_name} - {assignment.unit_name}",
                    'start_date': assignment.valid_from,
                    'end_date': assignment.valid_to,
                    'is_current': assignment.is_current,
                    'ad_interim': assignment.ad_interim,
                    'percentage': assignment.percentage,
                    'version': assignment.version,
                    'notes': assignment.notes,
                    'duration_days': assignment.duration_days,
                    'status': assignment.status,
                    'unit_name': assignment.unit_name,
                    'job_title_name': assignment.job_title_name
                }
                timeline.append(timeline_item)
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error creating timeline for person {person_id}: {e}")
            return []
    
    def get_career_progression(self, person_id: int) -> List[Dict[str, Any]]:
        """Get career progression analysis for person"""
        try:
            query = """
            SELECT pja.*,
                   u.name as unit_name,
                   u.type as unit_type,
                   jt.name as job_title_name,
                   jt.short_name as job_title_short_name
            FROM person_job_assignments pja
            JOIN units u ON pja.unit_id = u.id
            JOIN job_titles jt ON pja.job_title_id = jt.id
            WHERE pja.person_id = ?
            ORDER BY pja.valid_from ASC, pja.datetime_created ASC
            """
            
            rows = self.db_manager.fetch_all(query, (person_id,))
            progression = []
            
            for i, row in enumerate(rows):
                assignment = Assignment.from_sqlite_row(row)
                
                # Determine progression type
                progression_type = "lateral"  # Default
                if i > 0:
                    prev_assignment = progression[i-1]['assignment']
                    
                    # Simple heuristics for progression detection
                    if "chief" in assignment.job_title_name.lower() or "director" in assignment.job_title_name.lower():
                        if not ("chief" in prev_assignment.job_title_name.lower() or "director" in prev_assignment.job_title_name.lower()):
                            progression_type = "promotion"
                    elif "head" in assignment.job_title_name.lower():
                        if "manager" in prev_assignment.job_title_name.lower() or "specialist" in prev_assignment.job_title_name.lower():
                            progression_type = "promotion"
                    elif assignment.unit_id != prev_assignment.unit_id:
                        progression_type = "transfer"
                
                progression.append({
                    'assignment': assignment,
                    'progression_type': progression_type,
                    'order': i + 1
                })
            
            return progression
            
        except Exception as e:
            logger.error(f"Error getting career progression for person {person_id}: {e}")
            return []
    
    def get_competency_areas(self, person_id: int) -> List[Dict[str, Any]]:
        """Get competency areas based on assignments"""
        try:
            query = """
            SELECT u.type as unit_type,
                   u.name as unit_name,
                   jt.name as job_title_name,
                   COUNT(*) as assignment_count,
                   SUM(CASE WHEN pja.is_current = 1 THEN 1 ELSE 0 END) as current_count,
                   MAX(pja.datetime_created) as last_assignment_date
            FROM person_job_assignments pja
            JOIN units u ON pja.unit_id = u.id
            JOIN job_titles jt ON pja.job_title_id = jt.id
            WHERE pja.person_id = ?
            GROUP BY u.type, u.name, jt.name
            ORDER BY assignment_count DESC, last_assignment_date DESC
            """
            
            rows = self.db_manager.fetch_all(query, (person_id,))
            competencies = []
            
            for row in rows:
                competency = {
                    'area': f"{row['unit_name']} ({row['unit_type']})",
                    'role': row['job_title_name'],
                    'experience_level': self._calculate_experience_level(row['assignment_count']),
                    'assignment_count': row['assignment_count'],
                    'is_current': row['current_count'] > 0,
                    'last_assignment': row['last_assignment_date']
                }
                competencies.append(competency)
            
            return competencies
            
        except Exception as e:
            logger.error(f"Error getting competency areas for person {person_id}: {e}")
            return []
    
    def get_organizational_relationships(self, person_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """Get organizational relationships (colleagues, supervisors, subordinates)"""
        try:
            # Get current assignments of the person
            current_units_query = """
            SELECT DISTINCT unit_id, u.name as unit_name, u.parent_unit_id
            FROM person_job_assignments pja
            JOIN units u ON pja.unit_id = u.id
            WHERE pja.person_id = ? AND pja.is_current = 1
            """
            person_units = self.db_manager.fetch_all(current_units_query, (person_id,))
            
            relationships = {
                'colleagues': [],
                'potential_supervisors': [],
                'potential_subordinates': []
            }
            
            for unit_row in person_units:
                unit_id = unit_row['unit_id']
                parent_unit_id = unit_row['parent_unit_id']
                
                # Colleagues (same unit)
                colleagues_query = """
                SELECT DISTINCT p.id, p.name, p.short_name,
                       jt.name as job_title_name,
                       u.name as unit_name
                FROM person_job_assignments pja
                JOIN persons p ON pja.person_id = p.id
                JOIN job_titles jt ON pja.job_title_id = jt.id
                JOIN units u ON pja.unit_id = u.id
                WHERE pja.unit_id = ? AND pja.is_current = 1 AND p.id != ?
                """
                colleagues = self.db_manager.fetch_all(colleagues_query, (unit_id, person_id))
                relationships['colleagues'].extend([dict(row) for row in colleagues])
                
                # Potential supervisors (parent unit)
                if parent_unit_id:
                    supervisors_query = """
                    SELECT DISTINCT p.id, p.name, p.short_name,
                           jt.name as job_title_name,
                           u.name as unit_name
                    FROM person_job_assignments pja
                    JOIN persons p ON pja.person_id = p.id
                    JOIN job_titles jt ON pja.job_title_id = jt.id
                    JOIN units u ON pja.unit_id = u.id
                    WHERE pja.unit_id = ? AND pja.is_current = 1
                    """
                    supervisors = self.db_manager.fetch_all(supervisors_query, (parent_unit_id,))
                    relationships['potential_supervisors'].extend([dict(row) for row in supervisors])
                
                # Potential subordinates (child units)
                subordinates_query = """
                SELECT DISTINCT p.id, p.name, p.short_name,
                       jt.name as job_title_name,
                       u.name as unit_name
                FROM person_job_assignments pja
                JOIN persons p ON pja.person_id = p.id
                JOIN job_titles jt ON pja.job_title_id = jt.id
                JOIN units u ON pja.unit_id = u.id
                WHERE pja.unit_id IN (SELECT id FROM units WHERE parent_unit_id = ?) 
                AND pja.is_current = 1
                """
                subordinates = self.db_manager.fetch_all(subordinates_query, (unit_id,))
                relationships['potential_subordinates'].extend([dict(row) for row in subordinates])
            
            # Remove duplicates
            for key in relationships:
                seen = set()
                unique_relationships = []
                for rel in relationships[key]:
                    if rel['id'] not in seen:
                        seen.add(rel['id'])
                        unique_relationships.append(rel)
                relationships[key] = unique_relationships
            
            return relationships
            
        except Exception as e:
            logger.error(f"Error getting organizational relationships for person {person_id}: {e}")
            return {'colleagues': [], 'potential_supervisors': [], 'potential_subordinates': []}
    
    def calculate_workload(self, person_id: int, current_assignments: List[Assignment]) -> Dict[str, Any]:
        """Calculate current workload analysis"""
        try:
            workload = {
                'total_percentage': 0.0,
                'assignments_count': len(current_assignments),
                'interim_count': 0,
                'units_count': 0,
                'job_titles_count': 0,
                'workload_status': 'normal',
                'workload_color': 'success',
                'assignments_by_unit': {},
                'recommendations': []
            }
            
            units = set()
            job_titles = set()
            
            for assignment in current_assignments:
                workload['total_percentage'] += assignment.percentage
                
                if assignment.ad_interim:
                    workload['interim_count'] += 1
                
                units.add(assignment.unit_id)
                job_titles.add(assignment.job_title_id)
                
                # Group by unit
                unit_name = assignment.unit_name
                if unit_name not in workload['assignments_by_unit']:
                    workload['assignments_by_unit'][unit_name] = []
                workload['assignments_by_unit'][unit_name].append({
                    'job_title': assignment.job_title_name,
                    'percentage': assignment.percentage,
                    'ad_interim': assignment.ad_interim
                })
            
            workload['units_count'] = len(units)
            workload['job_titles_count'] = len(job_titles)
            
            # Determine workload status
            if workload['total_percentage'] > 1.5:
                workload['workload_status'] = 'overloaded'
                workload['workload_color'] = 'danger'
                workload['recommendations'].append("Carico di lavoro eccessivo (>150%)")
            elif workload['total_percentage'] > 1.2:
                workload['workload_status'] = 'high'
                workload['workload_color'] = 'warning'
                workload['recommendations'].append("Carico di lavoro elevato (>120%)")
            elif workload['total_percentage'] < 0.5:
                workload['workload_status'] = 'low'
                workload['workload_color'] = 'info'
                workload['recommendations'].append("Carico di lavoro basso (<50%)")
            
            if workload['interim_count'] > 2:
                workload['recommendations'].append(f"Numero elevato di incarichi ad interim ({workload['interim_count']})")
            
            if workload['units_count'] > 3:
                workload['recommendations'].append(f"Persona distribuita su molte unità ({workload['units_count']})")
            
            return workload
            
        except Exception as e:
            logger.error(f"Error calculating workload for person {person_id}: {e}")
            return {}
    
    def get_workload_history(self, person_id: int) -> List[Dict[str, Any]]:
        """Get workload history over time"""
        try:
            # This is a simplified version - in a real system you might want to 
            # calculate workload for specific time periods
            query = """
            SELECT DATE(pja.valid_from) as date,
                   SUM(pja.percentage) as total_percentage,
                   COUNT(*) as assignments_count
            FROM person_job_assignments pja
            WHERE pja.person_id = ? 
            AND pja.valid_from IS NOT NULL
            GROUP BY DATE(pja.valid_from)
            ORDER BY pja.valid_from DESC
            LIMIT 12
            """
            
            rows = self.db_manager.fetch_all(query, (person_id,))
            history = []
            
            for row in rows:
                history.append({
                    'date': row['date'],
                    'total_percentage': float(row['total_percentage']),
                    'assignments_count': row['assignments_count'],
                    'percentage_display': f"{float(row['total_percentage']) * 100:.0f}%"
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting workload history for person {person_id}: {e}")
            return []
    
    def find_potential_duplicates(self) -> List[Dict[str, Any]]:
        """Find potential duplicate persons based on name similarity"""
        try:
            # Simple approach: find persons with very similar names
            query = """
            SELECT p1.id as id1, p1.name as name1, p1.email as email1,
                   p2.id as id2, p2.name as name2, p2.email as email2,
                   CASE 
                       WHEN p1.email = p2.email AND p1.email IS NOT NULL THEN 'email_match'
                       WHEN LOWER(TRIM(p1.name)) = LOWER(TRIM(p2.name)) THEN 'exact_name_match'
                       ELSE 'similar_name'
                   END as match_type
            FROM persons p1
            JOIN persons p2 ON p1.id < p2.id
            WHERE (
                LOWER(TRIM(p1.name)) = LOWER(TRIM(p2.name)) OR
                (p1.email = p2.email AND p1.email IS NOT NULL AND p1.email != '') OR
                (LENGTH(p1.name) > 5 AND LENGTH(p2.name) > 5 AND 
                 SUBSTR(LOWER(p1.name), 1, LENGTH(p1.name)-1) = SUBSTR(LOWER(p2.name), 1, LENGTH(p2.name)-1))
            )
            ORDER BY match_type, p1.name
            """
            
            rows = self.db_manager.fetch_all(query)
            duplicates = []
            
            for row in rows:
                duplicate = {
                    'person1': {
                        'id': row['id1'],
                        'name': row['name1'],
                        'email': row['email1']
                    },
                    'person2': {
                        'id': row['id2'],
                        'name': row['name2'],
                        'email': row['email2']
                    },
                    'match_type': row['match_type'],
                    'confidence': self._calculate_duplicate_confidence(row)
                }
                duplicates.append(duplicate)
            
            return duplicates
            
        except Exception as e:
            logger.error(f"Error finding potential duplicates: {e}")
            return []
    
    def merge_persons(self, source_person_id: int, target_person_id: int) -> bool:
        """Merge two persons (move all assignments from source to target)"""
        try:
            with self.db_manager.get_connection() as conn:
                # Update all assignments to point to target person
                conn.execute("""
                    UPDATE person_job_assignments 
                    SET person_id = ? 
                    WHERE person_id = ?
                """, (target_person_id, source_person_id))
                
                # Delete source person
                conn.execute("DELETE FROM persons WHERE id = ?", (source_person_id,))
                
                conn.commit()
                logger.info(f"Successfully merged person {source_person_id} into {target_person_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error merging persons {source_person_id} -> {target_person_id}: {e}")
            return False
    
    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """Get comprehensive person statistics"""
        try:
            stats = {}
            
            # Basic counts
            stats['total_persons'] = self.count()
            
            # Persons with assignments
            with_assignments_query = """
            SELECT COUNT(DISTINCT person_id) as count 
            FROM person_job_assignments 
            WHERE is_current = 1
            """
            row = self.db_manager.fetch_one(with_assignments_query)
            stats['persons_with_assignments'] = row['count'] if row else 0
            stats['persons_without_assignments'] = stats['total_persons'] - stats['persons_with_assignments']
            
            # Assignment distribution
            assignment_dist_query = """
            SELECT 
                SUM(CASE WHEN assignment_count = 1 THEN 1 ELSE 0 END) as single_assignment,
                SUM(CASE WHEN assignment_count = 2 THEN 1 ELSE 0 END) as dual_assignment,
                SUM(CASE WHEN assignment_count >= 3 THEN 1 ELSE 0 END) as multiple_assignment
            FROM (
                SELECT person_id, COUNT(*) as assignment_count
                FROM person_job_assignments 
                WHERE is_current = 1
                GROUP BY person_id
            ) t
            """
            row = self.db_manager.fetch_one(assignment_dist_query)
            if row:
                stats['single_assignment_persons'] = row['single_assignment'] or 0
                stats['dual_assignment_persons'] = row['dual_assignment'] or 0
                stats['multiple_assignment_persons'] = row['multiple_assignment'] or 0
            
            # Workload statistics
            workload_query = """
            SELECT 
                AVG(total_percentage) as avg_workload,
                MAX(total_percentage) as max_workload,
                SUM(CASE WHEN total_percentage > 1.0 THEN 1 ELSE 0 END) as overloaded_count
            FROM (
                SELECT person_id, SUM(percentage) as total_percentage
                FROM person_job_assignments 
                WHERE is_current = 1
                GROUP BY person_id
            ) t
            """
            row = self.db_manager.fetch_one(workload_query)
            if row:
                stats['avg_workload'] = round(float(row['avg_workload']) * 100) if row['avg_workload'] else 0
                stats['max_workload'] = round(float(row['max_workload']) * 100) if row['max_workload'] else 0
                stats['overloaded_persons'] = row['overloaded_count'] or 0
            
            # Interim assignments
            interim_query = """
            SELECT COUNT(DISTINCT person_id) as count 
            FROM person_job_assignments 
            WHERE ad_interim = 1 AND is_current = 1
            """
            row = self.db_manager.fetch_one(interim_query)
            stats['persons_with_interim'] = row['count'] if row else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting comprehensive statistics: {e}")
            return {}
    
    def _calculate_experience_level(self, assignment_count: int) -> str:
        """Calculate experience level based on assignment count"""
        if assignment_count >= 5:
            return "Expert"
        elif assignment_count >= 3:
            return "Experienced"  
        elif assignment_count >= 2:
            return "Intermediate"
        else:
            return "Beginner"
    
    def _calculate_duplicate_confidence(self, row: Dict[str, Any]) -> float:
        """Calculate confidence score for duplicate detection"""
        if row['match_type'] == 'email_match':
            return 0.95
        elif row['match_type'] == 'exact_name_match':
            return 0.85
        else:
            return 0.60
    
    def get_searchable_fields(self) -> List[str]:
        """Get list of fields that can be searched for persons"""
        return ["name", "short_name", "email"]
    
    def _validate_for_create(self, person: Person) -> None:
        """Perform additional validation before creating a person"""
        # Check for duplicate email if provided
        if person.email:
            existing = self.db_manager.fetch_one(
                "SELECT id FROM persons WHERE email = ? AND id != ?",
                (person.email, person.id or -1)
            )
            if existing:
                from app.services.base import ServiceValidationException
                raise ServiceValidationException(f"Person with email '{person.email}' already exists")
    
    def _validate_for_update(self, person: Person, existing: Person) -> None:
        """Perform additional validation before updating a person"""
        # Check for duplicate email (excluding current person)
        if person.email:
            duplicate = self.db_manager.fetch_one(
                "SELECT id FROM persons WHERE email = ? AND id != ?",
                (person.email, person.id)
            )
            if duplicate:
                from app.services.base import ServiceValidationException
                raise ServiceValidationException(f"Person with email '{person.email}' already exists")
    
    def _validate_for_delete(self, person: Person) -> None:
        """Perform validation before deleting a person"""
        can_delete, message = self.can_delete(person.id)
        if not can_delete:
            from app.services.base import ServiceIntegrityException
            raise ServiceIntegrityException(message)