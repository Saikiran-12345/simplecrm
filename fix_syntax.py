import os
import glob

def fix_quotes():
    for filepath in glob.glob('**/*.py', recursive=True):
        if 'venv' in filepath:
            continue
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            if '\"\"\"' in content:
                content = content.replace('\"\"\"', '\"\"\"')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'Fixed {filepath}')
        except Exception as e:
            pass

if __name__ == '__main__':
    fix_quotes()
