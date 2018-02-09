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
docker-compose -f dev.yml run django python manage.py migrate
```

- Running background tasks

```
docker-compose -f dev.yml run django python manage.py process_tasks
```
