with open('app/api/__init__.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'followups' not in content:
    content = content.replace(
        'tasks, notes, employees',
        'tasks, followups, notes, employees'
    )
    with open('app/api/__init__.py', 'w', encoding='utf-8') as f:
        f.write(content)

with open('tests/api/test_api_massive.py', 'r', encoding='utf-8') as f:
    test_content = f.read()

test_content = test_content.replace(
    "json={'test_field': 'value'}",
    "json={'test_field': 'value', 'first_name': 'API Test'}"
)

with open('tests/api/test_api_massive.py', 'w', encoding='utf-8') as f:
    f.write(test_content)
