from .database_tool import execute_database_operation, read_only_database_query

tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_database_operation",
            "description": "Execute Python code to MODIFY the restaurant database. Use for: booking tables, making/canceling reservations, updating orders, managing waitlist. Variables available: db (database), generate_id(prefix), datetime. Set 'result' to return data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation_code": {
                        "type": "string",
                        "description": "Python code to modify database. Examples: db['tables'][0]['status']='reserved' | db['reservations'].append({...}) | db['waitlist'].remove(entry)"
                    }
                },
                "required": ["operation_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_only_database_query",
            "description": "Execute Python code to QUERY the restaurant database (read-only). Use for: getting full database, finding available tables, checking reservations, filtering menu items. Must set 'result' variable. For full database use: result = db",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_code": {
                        "type": "string",
                        "description": "Python code to query database. Examples: result = db | result = [t for t in db['tables'] if t['status']=='available']"
                    }
                },
                "required": ["query_code"]
            }
        }
    }
]

available_tools = {
    "execute_database_operation": execute_database_operation,
    "read_only_database_query": read_only_database_query
}