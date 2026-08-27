import os

total_lines = 0
file_count = 0

for root, dirs, files in os.walk('.'):
    if 'venv' in dirs:
        dirs.remove('venv')
    if '__pycache__' in dirs:
        dirs.remove('__pycache__')
        
    for file in files:
        if file.endswith(('.py', '.html', '.css', '.js')):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    total_lines += len(lines)
                    file_count += 1
            except Exception as e:
                pass

print(f"Total Lines: {total_lines}")
print(f"Total Files: {file_count}")
