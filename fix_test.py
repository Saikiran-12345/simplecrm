with open('tests/test_admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("auth_client.get('/dashboard/')", "auth_client.get('/')")

with open('tests/test_admin.py', 'w', encoding='utf-8') as f:
    f.write(content)
