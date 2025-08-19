import json
import copy
from typing import Dict, Any
import os

def execute_database_operation(operation_code: str) -> Dict[str, Any]:
    """
    Execute Python code to modify the restaurant database.
    
    The code has access to:
    - 'db': The full database dictionary
    - Standard Python functions and libraries (json, datetime, etc.)
    
    The code should modify 'db' in place and can return a custom result.
    
    Examples:
    - Book a table: db['tables'][2]['status'] = 'reserved'
    - Add reservation: db['reservations'].append({...})
    - Check availability: return [t for t in db['tables'] if t['status'] == 'available']
    """
    
    # Load the current database
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'restaurant_database.json')
    
    try:
        with open(db_path, 'r') as f:
            db = json.load(f)
    except FileNotFoundError:
        return {"error": "Database file not found", "success": False}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON in database file", "success": False}
    
    # Create a backup for safety
    original_db = copy.deepcopy(db)
    
    # Create execution context with useful imports
    exec_context = {
        'db': db,
        'json': json,
        'copy': copy,
        'result': None,  # Variable for the code to store return values
    }
    
    # Import datetime for reservation management
    exec_code = """
import datetime
from datetime import datetime, timedelta
import random
import string

# Helper function to generate IDs
def generate_id(prefix=''):
    return prefix + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Your code starts here
""" + operation_code
    
    try:
        # Execute the provided code
        exec(exec_code, exec_context)
        
        # Get the modified database
        modified_db = exec_context['db']
        
        # Save the modified database back to file
        with open(db_path, 'w') as f:
            json.dump(modified_db, f, indent=2)
        
        # Prepare the response
        response = {
            "success": True,
            "message": "Database operation completed successfully",
            "modified_db": modified_db,
        }
        
        # If the code set a custom result, include it
        if exec_context.get('result') is not None:
            response['result'] = exec_context['result']
            
        return response
        
    except Exception as e:
        # Restore original database on error
        with open(db_path, 'w') as f:
            json.dump(original_db, f, indent=2)
            
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "message": "Database operation failed, changes rolled back"
        }


def read_only_database_query(query_code: str) -> Dict[str, Any]:
    """
    Execute Python code to query the restaurant database (read-only).
    
    Similar to execute_database_operation but doesn't save changes.
    Useful for complex queries and data analysis.
    """
    
    # Load the current database
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'restaurant_database.json')
    
    try:
        with open(db_path, 'r') as f:
            db = json.load(f)
    except FileNotFoundError:
        return {"error": "Database file not found", "success": False}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON in database file", "success": False}
    
    # Create execution context
    exec_context = {
        'db': db,
        'json': json,
        'result': None,
    }
    
    # Import datetime for queries
    exec_code = """
import datetime
from datetime import datetime, timedelta

# Your query starts here
""" + query_code
    
    try:
        # Execute the provided code
        exec(exec_code, exec_context)
        
        # Return the result
        return {
            "success": True,
            "result": exec_context.get('result', "Query executed but no result was set. Use 'result = ...' to return data.")
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "message": "Query failed"
        }