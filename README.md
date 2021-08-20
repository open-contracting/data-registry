# Data Registry

## Development

```bash
pip install -r requirements.txt
./manage.py migrate --settings core.settings.base
./manage.py createsuperuser --settings core.settings.base
```

Run the web server:

```bash
env DEBUG=True ./manage.py runserver --settings core.settings.base
```
