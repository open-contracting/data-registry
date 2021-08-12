import requests

response = requests.post('https://flatten.open-contracting.org/api/urls/', {
                         'urls': 'file:///data/exporter_dumps/zambia/154/2020_02.jsonl.gz',
                         'country': 'United Kingdom',
                         'period': 'Last 6 months',
                         'source': 'OCP Kingfisher Database'
                         },
                         headers={'Accept-Language': 'en_US|es'})

print(response.json())
print("https://flatten.open-contracting.org//#/upload-file?lang=en_US|es&url={}".format(response.json()["id"]))
