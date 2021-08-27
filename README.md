# Data Registry

## Development

Install requirements:

```bash
pip install -r requirements.txt
```

Create a database (your user should have access without requiring a password):

```bash
createdb data_registry
```

Prepare the database:

```bash
./manage.py migrate --settings core.settings.github
./manage.py createsuperuser --settings core.settings.github
```

Run the web server, replacing `PASSWORD`:

```bash
env SCRAPY_HOST=https://scrape:PASSWORD@collect.kingfisher.open-contracting.org/ SCRAPY_PROJECT=kingfisher EXPORTER_HOST=http://127.0.0.1:8000/ ./manage.py runserver --settings core.settings.github
```

### Idiosyncracies

- `related_name` is singular, instead of plural
