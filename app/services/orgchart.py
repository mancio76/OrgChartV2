"""
Orgchart service for organizational analysis and visualization
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime, timedelta
from app.database import get_db_manager
from app.models.unit import Unit
from app.models.person import Person
from app.models.assignment import Assignment
from app.models.job_title import JobTitle

logger = logging.getLogger(__name__)


class OrgchartService:
    """Orgchart service for organizational visualization and analysis"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
    
    def get_organization_overview(self) -> Dict[str, Any]:
        """Get high-level organization overview"""
        try:
            overview = {}
            
            # Basic structure counts
            overview['total_units'] = self.db_manager.fetch_one(
                "SELECT COUNT(*) as count FROM units"
            )['count']
            
            overview['total_persons'] = self.db_manager.fetch_one(
                "SELECT COUNT(*) as count FROM persons"
            )['count']
            
            overview['total_job_titles'] = self.db_manager.fetch_one(
                "SELECT COUNT(*) as count FROM job_titles"
            )['count']
            
            overview['active_assignments'] = self.db_manager.fetch_one(
                "SELECT COUNT(*) as count FROM person_job_assignments WHERE is_current = 1"
            )['count']
            
            # Organizational depth
            depth_query = """
            WITH RECURSIVE unit_depth AS (
                SELECT id, name, parent_unit_id, 0 as depth
                FROM units 
                WHERE parent_unit_id IS NULL OR parent_unit_id = -1
                
                UNION ALL
                
                SELECT u.id, u.name, u.parent_unit_id, ud.depth + 1
                FROM units u
                JOIN unit_depth ud ON u.parent_unit_id = ud.id
            )
            SELECT MAX(depth) as max_depth FROM unit_depth
            """
            overview['organizational_depth'] = self.db_manager.fetch_one(depth_query)['max_depth'] or 0
            
            # Span of control (average direct reports)
            span_query = """
            SELECT AVG(child_count) as avg_span
            FROM (
                SELECT parent_unit_id, COUNT(*) as child_count
                FROM units 
                WHERE parent_unit_id IS NOT NULL AND parent_unit_id != -1
                GROUP BY parent_unit_id
            ) spans
            """
            row = self.db_manager.fetch_one(span_query)
            overview['avg_span_of_control'] = round(row['avg_span']) if row and row['avg_span'] else 0
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting organization overview: {e}")
            return {}
    
    def get_organization_metrics(self) -> Dict[str, Any]:
        """Get key organizational metrics"""
        try:
            metrics = {}
            
            # Workload distribution
            workload_query = """
            SELECT 
                SUM(CASE WHEN total_percentage > 1.5 THEN 1 ELSE 0 END) as overloaded,
                SUM(CASE WHEN total_percentage BETWEEN 1.0 AND 1.5 THEN 1 ELSE 0 END) as optimal,
                SUM(CASE WHEN total_percentage < 1.0 THEN 1 ELSE 0 END) as underutilized,
                AVG(total_percentage) as avg_workload
            FROM (
                SELECT person_id, SUM(percentage) as total_percentage
                FROM person_job_assignments 
                WHERE is_current = 1
                GROUP BY person_id
            ) workloads
            """
            workload_data = self.db_manager.fetch_one(workload_query)
            metrics['workload_distribution'] = {
                'overloaded': workload_data['overloaded'] or 0,
                'optimal': workload_data['optimal'] or 0,
                'underutilized': workload_data['underutilized'] or 0,
                'avg_workload': round(float(workload_data['avg_workload']) * 100) if workload_data['avg_workload'] else 0
            }
            
            # Interim assignments ratio
            interim_query = """
            SELECT 
                COUNT(CASE WHEN is_ad_interim = 1 THEN 1 END) as interim_count,
                COUNT(*) as total_count
            FROM person_job_assignments 
            WHERE is_current = 1
            """
            interim_data = self.db_manager.fetch_one(interim_query)
            interim_ratio = (interim_data['interim_count'] / interim_data['total_count'] * 100) if interim_data['total_count'] > 0 else 0
            metrics['interim_ratio'] = round(interim_ratio, 1)
            
            # Vacancy rate (units without assignments)
            vacancy_query = """
            SELECT 
                COUNT(CASE WHEN pja.unit_id IS NULL THEN 1 END) as vacant_units,
                COUNT(u.id) as total_units
            FROM units u
            LEFT JOIN person_job_assignments pja ON u.id = pja.unit_id AND pja.is_current = 1
            """
            vacancy_data = self.db_manager.fetch_one(vacancy_query)
            vacancy_rate = (vacancy_data['vacant_units'] / vacancy_data['total_units'] * 100) if vacancy_data['total_units'] > 0 else 0
            metrics['vacancy_rate'] = round(vacancy_rate, 1)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting organization metrics: {e}")
            return {}
    
    def get_complete_tree(self, show_persons: bool = True) -> List[Dict[str, Any]]:
        """Get complete organizational tree structure"""
        try:
            # Get hierarchical structure
            tree_query = """
            WITH RECURSIVE unit_tree AS (
                SELECT id, name, short_name, unit_type_id, parent_unit_id, 
                       0 as level,
                       CAST(id AS TEXT) as path
                FROM units 
                WHERE parent_unit_id IS NULL OR parent_unit_id = -1
                
                UNION ALL
                
                SELECT u.id, u.name, u.short_name, u.unit_type_id, u.parent_unit_id, ut.level + 1,
                       ut.path || '/' || CAST(u.id AS TEXT)
                FROM units u
                JOIN unit_tree ut ON u.parent_unit_id = ut.id
            )
            SELECT ut.*, 
                   COUNT(DISTINCT pja.person_id) as person_count,
                   COUNT(DISTINCT child_units.id) as children_count
            FROM unit_tree ut
            LEFT JOIN person_job_assignments pja ON ut.id = pja.unit_id AND pja.is_current = 1
            LEFT JOIN units child_units ON child_units.parent_unit_id = ut.id
            GROUP BY ut.id, ut.name, ut.short_name, ut.unit_type_id, ut.parent_unit_id, ut.level, ut.path
            ORDER BY ut.path
            """
            ##tree_query = "select id, name, short_name, unit_type_id, parent_unit_id, level, path from get_complete_tree order by path"
            units = self.db_manager.fetch_all(tree_query, ('YOUSHALLPASS',))
            
            # Build tree structure
            tree_nodes = {}
            root_nodes = []
            
            for unit_row in units:
                node = {
                    'id': unit_row['id'],
                    'name': unit_row['name'],
                    'short_name': unit_row['short_name'],
                    'unit_type_id': unit_row['unit_type_id'],
                    'level': unit_row['level'],
                    'person_count': unit_row['person_count'],
                    'children_count': unit_row['children_count'],
                    'children': [],
                    'persons': [] if show_persons else None
                }
                
                # Add persons if requested
                if show_persons:
                    persons_query = """
                    SELECT p.id, p.name, p.short_name, jt.name as job_title_name,
                           pja.is_ad_interim, pja.is_unit_boss, pja.percentage
                    FROM person_job_assignments pja
                    JOIN persons p ON pja.person_id = p.id
                    JOIN job_titles jt ON pja.job_title_id = jt.id
                    WHERE pja.unit_id = ? AND pja.is_current = 1
                    ORDER BY p.name
                    """
                    persons = self.db_manager.fetch_all(persons_query, (unit_row['id'],))
                    node['persons'] = [dict(person) for person in persons]
                
                tree_nodes[unit_row['id']] = node
                
                if unit_row['parent_unit_id'] is None or unit_row['parent_unit_id'] == -1:
                    root_nodes.append(node)
                else:
                    if unit_row['parent_unit_id'] in tree_nodes:
                        tree_nodes[unit_row['parent_unit_id']]['children'].append(node)
            
            return root_nodes
            
        except Exception as e:
            logger.error(f"Error getting complete tree: {e}")
            return []
    
    def get_subtree(self, root_unit_id: int, show_persons: bool = True) -> List[Dict[str, Any]]:
        """Get subtree starting from specific unit"""
        try:
            # Get subtree structure
            subtree_query = """
            WITH RECURSIVE unit_subtree AS (
                SELECT id, name, short_name, unit_type_id, parent_unit_id, 0 as level,
                       CAST(id AS TEXT) as path
                FROM units 
                WHERE id = ?
                
                UNION ALL
                
                SELECT u.id, u.name, u.short_name, u.unit_type_id, u.parent_unit_id, us.level + 1,
                       us.path || '/' || CAST(u.id AS TEXT)
                FROM units u
                JOIN unit_subtree us ON u.parent_unit_id = us.id
            )
            SELECT us.*, 
                   COUNT(DISTINCT pja.person_id) as person_count,
                   COUNT(DISTINCT child_units.id) as children_count
            FROM unit_subtree us
            LEFT JOIN person_job_assignments pja ON us.id = pja.unit_id AND pja.is_current = 1
            LEFT JOIN units child_units ON child_units.parent_unit_id = us.id
            GROUP BY us.id, us.name, us.short_name, us.unit_type_id, us.parent_unit_id, us.level, us.path
            ORDER BY us.path
            """
            
            units = self.db_manager.fetch_all(subtree_query, (root_unit_id, 'YOUSHALLPASS'))
            
            if not units:
                return []
            
            # Build tree structure (similar to complete tree but starting from root_unit_id)
            tree_nodes = {}
            root_node = None
            
            for unit_row in units:
                node = {
                    'id': unit_row['id'],
                    'name': unit_row['name'],
                    'short_name': unit_row['short_name'],
                    'unit_type_id': unit_row['unit_type_id'],
                    'level': unit_row['level'],
                    'person_count': unit_row['person_count'],
                    'children_count': unit_row['children_count'],
                    'children': [],
                    'persons': [] if show_persons else None
                }
                
                # Add persons if requested
                if show_persons:
                    persons_query = """
                    SELECT p.id, p.name, p.short_name, jt.name as job_title_name,
                           pja.is_ad_interim, pja.is_unit_boss, pja.percentage
                    FROM person_job_assignments pja
                    JOIN persons p ON pja.person_id = p.id
                    JOIN job_titles jt ON pja.job_title_id = jt.id
                    WHERE pja.unit_id = ? AND pja.is_current = 1
                    ORDER BY p.name
                    """
                    persons = self.db_manager.fetch_all(persons_query, (unit_row['id'],))
                    node['persons'] = [dict(person) for person in persons]
                
                tree_nodes[unit_row['id']] = node
                
                if unit_row['id'] == root_unit_id:
                    root_node = node
                else:
                    if unit_row['parent_unit_id'] in tree_nodes:
                        tree_nodes[unit_row['parent_unit_id']]['children'].append(node)
            
            return [root_node] if root_node else []
            
        except Exception as e:
            logger.error(f"Error getting subtree for unit {root_unit_id}: {e}")
            return []
    
    def get_unit(self, unit_id: int) -> Optional[Dict[str, Any]]:
        """Get unit with full details"""
        try:
            unit_query = """
            SELECT u.* --, 
                   --p.name as parent_name,
                   --COUNT(DISTINCT c.id) as children_count,
                   --COUNT(DISTINCT pja.person_id) as person_count
            FROM units u
            LEFT JOIN units p ON u.parent_unit_id = p.id
            LEFT JOIN units c ON c.parent_unit_id = u.id
            LEFT JOIN person_job_assignments pja ON u.id = pja.unit_id AND pja.is_current = 1
            WHERE u.id = ?
            GROUP BY u.id
            """
            
            unit_row = self.db_manager.fetch_one(unit_query, (unit_id,))
            if not unit_row:
                return None
            
            unit_data = dict(unit_row)

            return unit_data
            
        except Exception as e:
            logger.error(f"Error getting unit for {unit_id}: {e}")
            return None
    
    def get_unit_with_details(self, unit_id: int) -> Optional[Dict[str, Any]]:
        """Get unit with full details"""
        try:
            unit_query = """
            SELECT u.* --, 
                   --p.name as parent_name,
                   --COUNT(DISTINCT c.id) as children_count,
                   --COUNT(DISTINCT pja.person_id) as person_count
            FROM units u
            LEFT JOIN units p ON u.parent_unit_id = p.id
            LEFT JOIN units c ON c.parent_unit_id = u.id
            LEFT JOIN person_job_assignments pja ON u.id = pja.unit_id AND pja.is_current = 1
            WHERE u.id = ?
            GROUP BY u.id
            """
            
            unit_row = self.db_manager.fetch_one(unit_query, (unit_id,))
            if not unit_row:
                return None
            
            unit_data = dict(unit_row)
            
            # Get current assignments
            assignments_query = """
            SELECT p.id as person_id, p.name as person_name, p.short_name as person_short_name,
                   jt.name as job_title_name, pja.is_ad_interim, pja.is_unit_boss, pja.percentage
            FROM person_job_assignments pja
            JOIN persons p ON pja.person_id = p.id
            JOIN job_titles jt ON pja.job_title_id = jt.id
            WHERE pja.unit_id = ? AND pja.is_current = 1
            ORDER BY p.name
            """
            assignments = self.db_manager.fetch_all(assignments_query, (unit_id,))
            unit_data['assignments'] = [dict(assignment) for assignment in assignments]
            
            # Get children units
            children_query = """
            SELECT u.id, u.name, u.short_name, u.unit_type_id,
                   COUNT(DISTINCT pja.person_id) as person_count
            FROM units u
            LEFT JOIN person_job_assignments pja ON u.id = pja.unit_id AND pja.is_current = 1
            WHERE u.parent_unit_id = ?
            GROUP BY u.id, u.name, u.short_name, u.unit_type_id
            ORDER BY u.name
            """
            children = self.db_manager.fetch_all(children_query, (unit_id,))
            unit_data['children'] = [dict(child) for child in children]
            
            return unit_data
            
        except Exception as e:
            logger.error(f"Error getting unit details for {unit_id}: {e}")
            return None
    
    def get_vacant_positions(self) -> List[Dict[str, Any]]:
        """Get units without current assignments (vacant positions)"""
        try:
            vacant_query = """
            SELECT u.id, u.name, u.short_name, u.unit_type_id, pu.name as parent_name
            FROM units u
            LEFT JOIN units pu ON u.parent_unit_id = pu.id
            LEFT JOIN person_job_assignments pja ON u.id = pja.unit_id AND pja.is_current = 1
            WHERE pja.unit_id IS NULL
            ORDER BY u.name
            """
            
            vacant_units = self.db_manager.fetch_all(vacant_query)
            return [dict(unit) for unit in vacant_units]
            
        except Exception as e:
            logger.error(f"Error getting vacant positions: {e}")
            return []
    
    def calculate_tree_statistics(self, tree_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for tree data"""
        try:
            stats = {
                'total_units': 0,
                'total_persons': 0,
                'max_depth': 0,
                'avg_span_of_control': 0,
                'vacant_units': 0
            }
            
            def traverse_tree(nodes: List[Dict[str, Any]], depth: int = 0) -> None:
                for node in nodes:
                    stats['total_units'] += 1
                    stats['total_persons'] += node.get('person_count', 0)
                    stats['max_depth'] = max(stats['max_depth'], depth)
                    
                    if node.get('person_count', 0) == 0:
                        stats['vacant_units'] += 1
                    
                    if node.get('children'):
                        traverse_tree(node['children'], depth + 1)
            
            traverse_tree(tree_data)
            
            # Calculate average span of control
            if stats['total_units'] > 1:
                non_leaf_units = stats['total_units'] - sum(1 for node in self._get_leaf_nodes(tree_data))
                if non_leaf_units > 0:
                    stats['avg_span_of_control'] = round((stats['total_units'] - 1) / non_leaf_units, 1)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating tree statistics: {e}")
            return {}
    
    def get_unit_path(self, unit_id: int) -> List[Dict[str, Any]]:
        """Get breadcrumb path to unit"""
        try:
            path_query = """
            WITH RECURSIVE unit_path AS (
                SELECT id, name, parent_unit_id, 0 as level
                FROM units WHERE id = ?
                
                UNION ALL
                
                SELECT u.id, u.name, u.parent_unit_id, up.level + 1
                FROM units u
                JOIN unit_path up ON u.id = up.parent_unit_id
            )
            SELECT id, name FROM unit_path WHERE level > 0 ORDER BY level DESC
            """
            
            path_rows = self.db_manager.fetch_all(path_query, (unit_id, 'YOUSHALLPASS',))
            return [{'id': row['id'], 'name': row['name']} for row in path_rows]
            
        except Exception as e:
            logger.error(f"Error getting unit path for {unit_id}: {e}")
            return []
    
    def get_unit_type(self, unit_id: int) -> List[Dict[str, Any]]:
        """Get the type of the unit"""
        try:
            type_query = """
            SELECT ut.id, ut.name, ut.short_name
            FROM unit_types ut
            JOIN units u ON ut.id = u.unit_type_id
            WHERE u.id = ?
            """
            
            type_rows = self.db_manager.fetch_all(type_query, (unit_id,))
            return [{'id': row['id'], 'name': row['name'], 'short_name': row['short_name']} for row in type_rows]
            
        except Exception as e:
            logger.error(f"Error getting unit path for {unit_id}: {e}")
            return []

    def get_unit_organizational_context(self, unit_id: int) -> Optional[Dict[str, Any]]:
        """Get unit with full organizational context"""
        try:
            unit = self.get_unit_with_details(unit_id)
            if not unit:
                return None
            
            unit_type = self.get_unit_type(unit_id)
            unit['unit_type'] = unit_type[0]['name']

            context = {
                'unit': Unit.from_dict(unit),
                'assignments': unit.get('assignments', []),
                'children': unit.get('children', []),
                'path': self.get_unit_path(unit_id)
            }
            
            # Add sibling units
            if unit.get('parent_unit_id'):
                siblings_query = """
                SELECT u.id, u.name, u.short_name, u.unit_type_id,
                       COUNT(DISTINCT pja.person_id) as person_count
                FROM units u
                LEFT JOIN person_job_assignments pja ON u.id = pja.unit_id AND pja.is_current = 1
                WHERE u.parent_unit_id = ? AND u.id != ?
                GROUP BY u.id, u.name, u.short_name, u.unit_type_id
                ORDER BY u.name
                """
                siblings = self.db_manager.fetch_all(siblings_query, (unit['parent_unit_id'], unit_id))
                context['siblings'] = [dict(sibling) for sibling in siblings]
            else:
                context['siblings'] = []
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting organizational context for unit {unit_id}: {e}")
            return None
    
    def get_recent_organizational_changes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent organizational changes"""
        try:
            changes_query = """
            SELECT 'assignment' as change_type,
                   'Nuovo incarico: ' || p.name || ' - ' || jt.name || ' in ' || u.name as description,
                   pja.datetime_created as change_date,
                   p.name as person_name,
                   u.name as unit_name,
                   jt.name as job_title_name
            FROM person_job_assignments pja
            JOIN persons p ON pja.person_id = p.id
            JOIN units u ON pja.unit_id = u.id
            JOIN job_titles jt ON pja.job_title_id = jt.id
            WHERE pja.is_current = 1
            ORDER BY pja.datetime_created DESC
            LIMIT ?
            """
            
            changes = self.db_manager.fetch_all(changes_query, (limit, 'YOUSHALLPASS',))
            return [dict(change) for change in changes]
            
        except Exception as e:
            logger.error(f"Error getting recent organizational changes: {e}")
            return []
    
    def get_workload_matrix(self) -> Dict[str, Any]:
        """Get workload matrix view"""
        try:
            matrix_query = """
            SELECT p.id as person_id,
                   p.name as person_name,
                   p.short_name as person_short_name,
                   u.name as unit_name,
                   jt.name as job_title_name,
                   pja.percentage,
                   pja.is_ad_interim,
                   pja.is_unit_boss,
                   ut.theme_id as unit_theme_id,
                   utt.icon_class as unit_theme_icon_class,
                   utt.primary_color as unit_theme_primary_color,
                   utt.display_label as unit_theme_display_label
            FROM person_job_assignments pja
            JOIN persons p ON pja.person_id = p.id
            JOIN units u ON pja.unit_id = u.id
            JOIN job_titles jt ON pja.job_title_id = jt.id
            JOIN unit_types ut ON u.unit_type_id = ut.id
            LEFT JOIN unit_type_themes utt ON ut.theme_id = utt.id
            WHERE pja.is_current = 1
            ORDER BY p.name, u.name
            """
            
            assignments = self.db_manager.fetch_all(matrix_query)
            
            # Build matrix structure
            matrix = {}
            for assignment in assignments:
                person_name = assignment['person_name']
                if person_name not in matrix:
                    matrix[person_name] = {
                        'person_id': assignment['person_id'],
                        'person_short_name': assignment['person_short_name'],
                        'total_percentage': 0,
                        'assignments': []
                    }
                
                matrix[person_name]['total_percentage'] += assignment['percentage']
                matrix[person_name]['assignments'].append(dict(assignment))
            
            # Add workload classification
            for person_data in matrix.values():
                percentage = person_data['total_percentage']
                if percentage > 1.2:
                    person_data['workload_status'] = 'overloaded'
                    person_data['workload_color'] = 'danger'
                elif percentage > 1.0:
                    person_data['workload_status'] = 'high'
                    person_data['workload_color'] = 'warning'
                elif percentage >= 0.8:
                    person_data['workload_status'] = 'optimal'
                    person_data['workload_color'] = 'success'
                else:
                    person_data['workload_status'] = 'low'
                    person_data['workload_color'] = 'info'
            
            return matrix
            
        except Exception as e:
            logger.error(f"Error getting workload matrix: {e}")
            return {}
    
    def get_skills_matrix(self) -> Dict[str, Any]:
        """Get skills/competency matrix"""
        try:
            # This is a simplified version - in a real system you'd have skills data
            skills_query = """
            SELECT p.id as person_id,
                   p.name as person_name,
                   jt.name as job_title_name,
                   u.name as unit_name,
                   ut.name as unit_type,
                   COUNT(*) as experience_count,
                   ut.theme_id as unit_theme_id,
                   utt.icon_class as unit_theme_icon_class,
                   utt.primary_color as unit_theme_primary_color,
                   utt.display_label as unit_theme_display_label
            FROM person_job_assignments pja
            JOIN persons p ON pja.person_id = p.id
            JOIN job_titles jt ON pja.job_title_id = jt.id
            JOIN units u ON pja.unit_id = u.id
            JOIN unit_types ut ON u.unit_type_id = ut.id
            LEFT JOIN unit_type_themes utt ON ut.theme_id = utt.id
            GROUP BY p.id, p.name, jt.name, u.name, ut.name, ut.theme_id, utt.icon_class, utt.primary_color, utt.display_label
            ORDER BY p.name, experience_count DESC
            """
            
            skills_data = self.db_manager.fetch_all(skills_query)
            
            # Build skills matrix
            matrix = {}
            for row in skills_data:
                person_name = row['person_name']
                if person_name not in matrix:
                    matrix[person_name] = {'skills': []}
                
                skill_level = "Expert" if row['experience_count'] > 3 else "Experienced" if row['experience_count'] > 1 else "Beginner"
                matrix[person_name]['skills'].append({
                    'person_id' : row['person_id'],
                    'area': f"{row['unit_name']} ({row['unit_type']})",
                    'role': row['job_title_name'],
                    'level': skill_level,
                    'experience_count': row['experience_count'],
                    'unit_name': row['unit_name'],
                    'unit_theme_id': row['unit_theme_id'],
                    'unit_theme_icon_class': row['unit_theme_icon_class'],
                    'unit_theme_primary_color': row['unit_theme_primary_color'],
                    'unit_theme_display_label': row['unit_theme_display_label']
                })
            
            return matrix
            
        except Exception as e:
            logger.error(f"Error getting skills matrix: {e}")
            return {}
    
    def get_hierarchy_matrix(self) -> Dict[str, Any]:
        """Get hierarchy matrix view"""
        try:
            hierarchy_query = """
            WITH RECURSIVE unit_hierarchy AS (
                SELECT id,
                    name,
                    parent_unit_id,
                    0 as level
                FROM units WHERE parent_unit_id IS NULL OR parent_unit_id = -1
                
                UNION ALL
                
                SELECT u.id,
                    u.name,
                    u.parent_unit_id,
                    uh.level + 1
                FROM units u
                JOIN unit_hierarchy uh ON u.parent_unit_id = uh.id
            )
            SELECT uh.*,
                COUNT(DISTINCT pja.person_id) as person_count,
                ut.theme_id,
                utt.icon_class,
                utt.primary_color,
                utt.secondary_color,
                utt.text_color,
                utt.display_label
            FROM unit_hierarchy uh
            LEFT JOIN person_job_assignments pja ON uh.id = pja.unit_id AND pja.is_current = 1
            LEFT JOIN units u ON uh.id = u.id
            LEFT JOIN unit_types ut ON u.unit_type_id = ut.id
            LEFT JOIN unit_type_themes utt ON ut.theme_id = utt.id
            GROUP BY uh.id, uh.name, uh.parent_unit_id, uh.level, ut.theme_id, utt.icon_class, utt.primary_color, utt.secondary_color, utt.text_color, utt.display_label
            ORDER BY uh.level, uh.name
            """
            
            units = self.db_manager.fetch_all(hierarchy_query)
            
            # Group by level
            matrix = {}
            for unit in units:
                level = unit['level']
                if level not in matrix:
                    matrix[level] = []
                matrix[level].append(dict(unit))
            
            return matrix
            
        except Exception as e:
            logger.error(f"Error getting hierarchy matrix: {e}")
            return {}
    
    def _get_leaf_nodes(self, tree_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get leaf nodes from tree data"""
        leaf_nodes = []
        
        def find_leaves(nodes: List[Dict[str, Any]]) -> None:
            for node in nodes:
                if not node.get('children') or len(node['children']) == 0:
                    leaf_nodes.append(node)
                else:
                    find_leaves(node['children'])
        
        find_leaves(tree_data)
        return leaf_nodes
    
    # Placeholder methods for advanced features - implement based on specific requirements
    
    def get_unit_performance_metrics(self, unit_id: int, period: str = "current") -> Dict[str, Any]:
        """Get performance metrics for unit"""
        # Placeholder - implement based on your performance criteria
        return {
            'efficiency_score': 85,
            'workload_balance': 'Good',
            'assignment_stability': 'High',
            'interim_ratio': 10
        }
    
    def get_reporting_relationships(self, unit_id: int) -> Dict[str, Any]:
        """Get reporting relationships for unit"""
        # Placeholder - implement based on your reporting structure
        return {
            'reports_to': [],
            'direct_reports': [],
            'matrix_relationships': []
        }
    
    def get_unit_change_history(self, unit_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get change history for unit"""
        # Placeholder - implement based on your audit requirements
        return []
    
    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """Get comprehensive organizational statistics"""
        overview = self.get_organization_overview()
        metrics = self.get_organization_metrics()
        return {**overview, **metrics}
    
    def get_distribution_analytics(self) -> Dict[str, Any]:
        """Get distribution analytics"""
        # Placeholder - implement distribution analysis
        return {}
    
    def get_organizational_trends(self) -> Dict[str, Any]:
        """Get organizational trends"""
        # Placeholder - implement trend analysis
        return {}
    
    def get_efficiency_metrics(self) -> Dict[str, Any]:
        """Get efficiency metrics"""
        # Placeholder - implement efficiency calculations
        return {}
    
    def perform_gap_analysis(self) -> Dict[str, Any]:
        """Perform organizational gap analysis"""
        # Placeholder - implement gap analysis
        return {}
    
    def get_organizational_recommendations(self) -> List[Dict[str, Any]]:
        """Get organizational recommendations"""
        # Placeholder - implement recommendation engine
        return []
    
    def get_simulation_baseline(self) -> Dict[str, Any]:
        """Get baseline for simulation"""
        # Placeholder - implement simulation baseline
        return {}
    
    def get_simulation_scenarios(self) -> List[Dict[str, Any]]:
        """Get predefined simulation scenarios"""
        # Placeholder - implement scenarios
        return []
    
    def analyze_span_of_control(self) -> Dict[str, Any]:
        """Analyze span of control"""
        # Placeholder - implement span analysis
        return {}
    
    def assess_organizational_health(self) -> Dict[str, Any]:
        """Assess organizational health"""
        # Placeholder - implement health assessment
        return {}
    
    def search_organizational_units(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search organizational units"""
        try:
            search_query = """
            SELECT id, name, short_name, unit_type_id
            FROM units
            WHERE name LIKE ? OR short_name LIKE ?
            LIMIT ?
            """
            results = self.db_manager.fetch_all(search_query, (f"%{query}%", f"%{query}%", limit))
            return [dict(result) for result in results]
        except Exception as e:
            logger.error(f"Error searching units: {e}")
            return []
    
    def simulate_organizational_change(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate organizational change"""
        # Placeholder - implement simulation logic
        return {"status": "simulated", "results": {}}
    
    def generate_export(self, tree_data: List[Dict[str, Any]], format_type: str) -> bytes:
        """Generate export in various formats"""
        # Placeholder - implement export generation
        if format_type == "svg":
            return b"<svg>Placeholder SVG</svg>"
        elif format_type == "pdf":
            return b"Placeholder PDF content"
        elif format_type == "png":
            return b"Placeholder PNG content"
        return b""
    
    def compare_organizational_structures(self, date1: date, date2: date) -> Dict[str, Any]:
        """Compare organizational structures between dates"""
        try:
            # Get structure data for both dates
            # For now, we'll use current data as a placeholder since we don't have historical data
            current_structure_query = """
            SELECT u.id, u.name, u.parent_unit_id,
                   COUNT(DISTINCT pja.person_id) as person_count,
                   ut.theme_id,
                   utt.icon_class,
                   utt.primary_color,
                   utt.display_label
            FROM units u
            LEFT JOIN person_job_assignments pja ON u.id = pja.unit_id AND pja.is_current = 1
            LEFT JOIN unit_types ut ON u.unit_type_id = ut.id
            LEFT JOIN unit_type_themes utt ON ut.theme_id = utt.id
            GROUP BY u.id, u.name, u.parent_unit_id, ut.theme_id, utt.icon_class, utt.primary_color, utt.display_label
            ORDER BY u.name
            """
            
            current_units = self.db_manager.fetch_all(current_structure_query)
            
            # For demonstration, create mock previous data by modifying current data
            previous_units = []
            for unit in current_units:
                unit_dict = dict(unit)
                # Simulate some changes for demo
                if unit_dict['name'] == 'Digital Innovation':
                    continue  # This unit was "added"
                elif unit_dict['name'] == 'IT Department':
                    unit_dict['person_count'] = max(0, unit_dict['person_count'] - 3)  # "modified"
                    unit_dict['change_type'] = 'modified'
                previous_units.append(unit_dict)
            
            # Add change types to current units
            current_units_with_changes = []
            for unit in current_units:
                unit_dict = dict(unit)
                if unit_dict['name'] == 'Digital Innovation':
                    unit_dict['change_type'] = 'added'
                elif unit_dict['name'] == 'IT Department':
                    unit_dict['change_type'] = 'modified'
                current_units_with_changes.append(unit_dict)
            
            return {
                'date1': date1,
                'date2': date2,
                'previous_structure_data': previous_units,
                'current_structure_data': current_units_with_changes,
                'changes': [],
                'summary': {
                    'total_changes': 3,
                    'additions': 1,
                    'modifications': 1,
                    'removals': 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error comparing organizational structures: {e}")
            return {
                'date1': date1,
                'date2': date2,
                'previous_structure_data': [],
                'current_structure_data': [],
                'changes': [],
                'summary': {}
            }