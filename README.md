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

Note: If you also want to test the integration with Spoonbill to generate Excel/CSVs files, you need to set env SPOONBILL_API_USERNAME=USERNAME and SPOONBILL_API_PASSWORD=PASSWORD

### Translation

This project uses [Django's translation framework](https://docs.djangoproject.com/en/3.2/topics/i18n/translation/) and [Transifex](https://www.transifex.com/open-contracting-partnership-1/data-registry/). The source language is `en_US`, and the translations are English (`en`), Spanish (`es`) and Russian (`ru`).

#### Configure Transifex

The first time you use Transifex, create a [`~/.transifexrc file`](https://docs.transifex.com/client/client-configuration#~/-transifexrc) (replace `USERNAME` and `PASSWORD`):

```bash
shell sphinx-intl create-transifexrc --transifex-username USERNAME --transifex-password PASSWORD
```

#### Update translations

Whenever text in the interface is added or updated, you must extract the strings to translate from the code files into PO files by running:

```bash
django-admin makemessages -l en_US
```

Then, push the PO files to Transifex with:

```bash
tx push -s
```

When ready, pull the translations from Transifex with:

```bash
tx pull -a
```

Then, compile the PO files to MO files with:

```bash
python manage.py compilemessages
```

### Idiosyncracies

#### Django configuration

- `related_name` is singular, instead of plural

#### Word choice

- "collection" has a different meaning in the code than in Kingfisher Collect or Kingfisher Process. It should be "publication", used in the UI and documentation.
- The "cbom" (central brain of mankind) management command should be "orchestrate".
- "scrape" should be "collect".
