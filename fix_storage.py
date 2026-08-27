with open('app/utils/storage.py', 'r', encoding='utf-8') as f:
    content = f.read()

search_method = """
    def search_records(self, **kwargs):
        data = self._read_data()
        results = []
        for record in data:
            match = True
            for k, v in kwargs.items():
                if record.get(k) != v:
                    match = False
                    break
            if match:
                results.append(record)
        return results

    def get_all_records(self):
"""

content = content.replace("    def get_all_records(self):", search_method)

with open('app/utils/storage.py', 'w', encoding='utf-8') as f:
    f.write(content)
