import yaml
data = {
            'Авторка': {
                'singular': {
                    'nominative': {'spelling': 'Авторка', 'suffix': 'к', 'flexion': 'а'},
                    'genitive': {'spelling': 'Авторки', 'suffix': 'к', 'flexion': 'и'},
                    'dative': {'spelling': 'Авторці', 'suffix': 'ц', 'flexion': 'і'},
                    'accusative': {'spelling': 'Авторку', 'suffix': 'к', 'flexion': 'у'},
                    'instrumental': {'spelling': 'Авторкою', 'suffix': 'к', 'flexion': 'ою'}
                },
                'plural': {
                    'instrumental': {'spelling': 'Авторками', 'suffix': 'к', 'flexion': 'ами'}
                }
            },
            'Абонентка': {
                'singular': {
                    'nominative': {'spelling': 'Абонентка', 'suffix': 'к', 'flexion': 'а'},
                    'genitive': {'spelling': 'Абоненток', 'suffix': 'к', 'flexion': None}
                }
            }
}
with open('./test.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(data, f, allow_unicode=True)