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
```
docker-compose -f dev.yml run django python manage.py migrate
```

- Running background tasks

```
docker-compose -f dev.yml run django python manage.py process_tasks
```

## Deployment
- clone repo, make sure you have docker images loaded from NAS (TODO: put on docker hub so can be pulled form anywhere)
- update `ALLOWED_HOSTS` in `prod.yml` to whatever your domain/IP address is.
- Make a directory in project root called `postgres-data`
- `docker-compose build`
- `docker-compose up`
- Things won't work quite yet. Attach into the web container: `docker exec -it olcwebportalv2_web_1 /bin/bash
` and then make and run migrations `python3 manage.py makemigrations` and then `python3 manage.py migrate`. Finally, get background tasks running - `python3 manage.py process_tasks`

## Running Tests
Follow the instructions in the deployment section. Then, attach into the web container:

`docker exec -it olcwebportalv2_web_1 /bin/bash`. 

From inside the container type:

`python3 manage.py test new_multisample`
