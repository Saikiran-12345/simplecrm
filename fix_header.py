with open('templates/base/base.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("<h2>SimpleCRM</h2>", "<h2>{{ global_settings.get('company_name', 'SimpleCRM') }}</h2>")

with open('templates/base/base.html', 'w', encoding='utf-8') as f:
    f.write(content)
