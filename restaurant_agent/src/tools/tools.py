import json

def get_restaurant_info():
    #get enrite database
    with open("/Users/natelevinson/Desktop/practice/restaurant_agent/restaurant_database.json", "r") as f:
        return json.load(f)
    
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_restaurant_info",
            "description": "Fetch the JSON database of the restaurant containing all the information about the restaurant (name, opening hours, capacity, staff on duty, menu, etc.)",
            "parameters": {
                "type": "object",
                "properties": {},
            }
        }
    }
]

available_tools = {
    "get_restaurant_info": get_restaurant_info
}