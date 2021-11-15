# Data Registry

## Development

Create a Python 3.8 virtual environment.

Install requirements:

```bash
pip install -r requirements_dev.txt
```

Create a database (your user should have access without requiring a password):

```bash
createdb data_registry
```

Prepare the database:

```bash
./manage.py migrate
./manage.py createsuperuser
```

Run the web server, replacing `PASSWORD`:

```bash
env SCRAPYD_URL=https://scrape:PASSWORD@collect.kingfisher.open-contracting.org EXPORTER_URL=http://127.0.0.1:8000 ./manage.py runserver
```

Note: If you also want to test the integration with Spoonbill to generate Excel/CSVs files, you need to set env SPOONBILL_API_USERNAME=USERNAME and SPOONBILL_API_PASSWORD=PASSWORD

### Translation

See how to [update Django translations](https://ocp-software-handbook.readthedocs.io/en/latest/python/i18n.html) and use [Transifex](https://www.transifex.com/open-contracting-partnership-1/data-registry/).

### Idiosyncracies

#### Django configuration

- `related_name` is singular, instead of plural

#### Word choice

- "collection" has a different meaning in the code than in Kingfisher Collect or Kingfisher Process. It should be "publication", used in the UI and documentation.
