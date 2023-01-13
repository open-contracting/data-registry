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

Run the web server, replacing `USERNAME` AND `PASSWORD`:

```bash
env SCRAPYD_URL=https://USERNAME:PASSWORD@collect.kingfisher.open-contracting.org ./manage.py runserver
```

Note: If you also want to test the integration with Spoonbill to generate Excel/CSVs files, you need to set env SPOONBILL_API_USERNAME=USERNAME and SPOONBILL_API_PASSWORD=PASSWORD

### Stylesheets

```bash
npx webpack --watch
```

### Translation

See how to [update Django translations](https://ocp-software-handbook.readthedocs.io/en/latest/python/i18n.html) and use [Transifex](https://www.transifex.com/open-contracting-partnership-1/data-registry/).

### Idiosyncrasies

- `related_name` is singular, instead of plural.
- "collection" has a different meaning in the code than in Kingfisher Collect or Kingfisher Process. It should be "publication", used in the UI and documentation.

## Tasks

### Publish a message

To manually start a task, run, for example:

```python
import os

from exporter.util import publish
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

publish({"job_id": 123}, "flattener_init")
```
