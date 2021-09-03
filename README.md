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
### Technical processes for translation

This project uses [Django's traslation framework](https://docs.djangoproject.com/en/3.2/topics/i18n/translation/) and [Transifex](https://www.transifex.com/) for translations. The source language is configured as en_US, and the available languages for translation are English (en), Spanish (es) and Russian (ru).

#### Translations for Translators

Translators can provide translations for this application by becomming a collaborator on Transifex https://www.transifex.com/open-contracting-partnership-1/data-registry/

#### Configure Transifex

The first time you use Transifex, create a [`~/.transifexrc file`](https://docs.transifex.com/client/client-configuration#~/-transifexrc) (replace `USERNAME` and `PASSWORD`):

```bash
shell sphinx-intl create-transifexrc --transifex-username USERNAME --transifex-password PASSWORD
```

#### Update translations

Whenever a text in the interface is added or updated, you must extract strings to translate from these files into PO files. In the data_registry directory run:

```bash
django-admin makemessages -l en_US
```

Then, you need yo push the PO file to Transifex with 

```bash
tx push -s
```

When the translations are ready, you need to pull them back from Transifex with `tx pull -a`.

Finally, you need to compile the new translated strings, with 

```bash
python manage.py compilemessages
```
### Idiosyncracies

- `related_name` is singular, instead of plural
