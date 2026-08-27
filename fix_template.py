with open('templates/sales/view.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("{% for item in sale.items %}", "{% for item in sale.get('items', []) %}")

with open('templates/sales/view.html', 'w', encoding='utf-8') as f:
    f.write(content)
