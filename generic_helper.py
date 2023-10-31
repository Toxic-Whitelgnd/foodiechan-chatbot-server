import re

def extract_session_id(sessioncontext):
    match = re.search(r'/sessions/(.*?)/contexts/',sessioncontext)

    if match:
        session_id = match.group(1)
        return session_id
    return ""

def extract_str(food_dict: dict):
    return ', '.join([f"{int(value)} {key} " for key,value in food_dict.items()])
