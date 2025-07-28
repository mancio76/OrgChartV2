#!/usr/bin/env python3
"""Check existing assignments in the database"""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.database import DatabaseManager

def main():
    db = DatabaseManager()
    db.initialize_database()
    
    rows = db.fetch_all('''
        SELECT person_id, unit_id, job_title_id, version, is_current 
        FROM person_job_assignments 
        ORDER BY person_id, unit_id, job_title_id, version
    ''')
    
    print('Existing assignments:')
    for r in rows:
        print(f'Person {r["person_id"]}, Unit {r["unit_id"]}, JobTitle {r["job_title_id"]}, Version {r["version"]}, Current {r["is_current"]}')
    
    print(f'\nTotal assignments: {len(rows)}')

if __name__ == "__main__":
    main()