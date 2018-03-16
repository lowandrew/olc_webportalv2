OLC Webportal V2
================

A portal to commonly used CFIA-OLC genomics tools.

### Requirements
WIP

### Installation
WIP

### Usage
WIP

### Developer Notes
- Registering model changes

```
docker-compose -f dev.yml run django python manage.py makemigrations
```
After making your first set of migrations, add the following line to your 0001_initial.py
in new_multisample, in the `operations` section:
`migrations.RunSQL("CREATE EXTENSION IF NOT EXISTS hstore")`
With that done, you're able to migrate: 
```
docker-compose -f dev.yml run django python manage.py migrate
```

- Running background tasks

```
docker-compose -f dev.yml run django python manage.py process_tasks
```
