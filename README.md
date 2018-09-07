OLC Webportal V2
================

A web portal for accessing CFIA genomic data, with some tools included.

The portal itself runs via docker-compose, and submits jobs to Azure Batch Service.

## Installing

You will need to: 

- clone this repository
- have docker-compose installed and working on your system
- have an azure storage and azure batch account

## Setup

#### Azure Setup
- create a custom VM image with tools you want to be able to run through the portal installed, and have it registered
as an app through the azure portal that has access to batch service. This image must be in the same subscription as
your Azure Batch account
- The VM should have a `/databases` folder with any resources you need to run assembly pipeline/other things,
and a `/envs` folder where conda environments are stored - see the `tasks.py` of various apps to see the commands that
the VM actually runs
- create a container called `raw-data` in your Azure storage account and store .fastq.gz files there - it's assumed that
they're MiSeq files that start with SEQIDs
- create a container called `processed-data` in your Azure storage account and put your illumina assemblies there. It's 
assumed that they're named in the format seqid.fasta


#### Making Your Env File

Create a file called `env` that has the following variables that the portal will use:

```
DB_NAME=yourpostgresdbname
DB_USER=yourpostgresdbuser
DB_PASS=yourdbpassword
DB_SERVICE=postgres
DB_PORT=5432
SECRET_KEY=yourdjangosecretkey
AZURE_ACCOUNT_NAME=yourazurestorageaccount
AZURE_ACCOUNT_KEY=yourazurestoragekey
BATCH_ACCOUNT_NAME=azurebatchaccountname
BATCH_ACCOUNT_URL=https://azurebatchaccountname.canadacentral.batch.azure.com
BATCH_ACCOUNT_KEY=batchaccountkey
EMAIL_HOST_USER=youremail@gmail.com
EMAIL_HOST_PASSWORD=emailpassword
VM_IMAGE=/subscriptions/subscription_id/resourceGroups/subscription/providers/Microsoft.Compute/images/image_name
VM_CLIENT_ID=vm_client_id
VM_SECRET=vm_secret_key
VM_TENANT=vm_tenant_id
```

#### Booting up the portal

Add your IP address to ALLOWED_HOSTS in `prod.yml`, and make a directory called
`postgres-data` in the root of your cloned dir. You should now be able to boot up the portal. You'll need the following commands (in this order, run in the root
of the directory you cloned):

- `docker-compose build`
- `docker-compose up`

At this point, the portal should be up. To make it fully functional, you'll need to attach into the running container twice
(`docker exec -it olc_webportalv2_web_1 /bin/bash`).

In the first attached instance, run:

- `python3 manage.py makemigrations`
- `python3 manage.py migrate`
- `python3 manage.py process_tasks > /dev/null &`

Then, disown the process started (command should be `disown %1`) and do the same thing with the `monitor_tasks` command.

- `python3 manage.py monitor_tasks > /dev/null &`
- `disown %1`

This way, if you lose connection to the VM hosting the site, tasks should still run.



