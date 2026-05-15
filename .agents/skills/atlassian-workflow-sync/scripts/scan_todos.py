import os
import re
import json

def scan_todos(directory):
    todo_pattern = re.compile(r'#\s*(TODO|FIXME|BUG):\s*(.*)', re.IGNORECASE)
    results = []
    
    for root, dirs, files in os.walk(directory):
        if '.git' in dirs:
            dirs.remove('.git')
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
            
        for file in files:
            if file.endswith('.py') or file.endswith('.md'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f, 1):
                            match = todo_pattern.search(line)
                            if match:
                                type_ = match.group(1).upper()
                                message = match.group(2).strip()
                                results.append({
                                    'file': os.path.relpath(path, directory),
                                    'line': i,
                                    'type': type_,
                                    'message': message
                                })
                except Exception as e:
                    print(f"Error reading {path}: {e}")
                    
    return results

if __name__ == "__main__":
    import sys
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    todos = scan_todos(repo_path)
    print(json.dumps(todos, indent=2))
