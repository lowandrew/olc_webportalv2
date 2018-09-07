from django.core.management.base import BaseCommand
from olc_webportalv2.cowbat.models import AzureTask, SequencingRun
from olc_webportalv2.geneseekr.models import GeneSeekrRequest, AzureGeneSeekrTask, GeneSeekrDetail
from django.core.mail import send_mail  # To be used eventually, only works in cloud
from django.conf import settings
from olc_webportalv2.cowbat.tasks import cowbat_cleanup
import pandas as pd
import datetime
import shutil
import time
import os

from azure.storage.blob import BlockBlobService
from azure.storage.blob import BlobPermissions


def monitor_tasks():
    while True:
        # Check for completed cowbat runs
        azure_tasks = AzureTask.objects.filter()
        for task in azure_tasks:
            if os.path.isfile(task.exit_code_file):
                sequencing_run = SequencingRun.objects.get(pk=task.sequencing_run.pk)
                # Read exit code. Update status to 'Error' if non-zero, 'Completed' if zero.
                # Run any tasks necessary to clean things up/have reports run.
                with open(task.exit_code_file) as f:
                    lines = f.readlines()
                for line in lines:
                    line = line.rstrip()
                    if int(line.split(',')[1]) != 0:
                        SequencingRun.objects.filter(pk=sequencing_run.pk).update(status='Error')
                        AzureTask.objects.filter(id=task.id).delete()
                        """
                        send_mail(subject='Assembly Error - Run {} was successfully submitted Azure Batch, but did not complete assembly'.format(str(sequencing_run)),
                                  message='Fix it!',
                                  from_email=settings.EMAIL_HOST_USER,
                                  recipient_list=['andrew.low@canada.ca'])
                        """
                    else:
                        cowbat_cleanup(sequencing_run_pk=sequencing_run.pk)  # This also sets task to complete
                        # Delete task so we don't have to keep checking up on it.
                        AzureTask.objects.filter(id=task.id).delete()

        # Also check for GeneSeekr completion.
        geneseekr_tasks = AzureGeneSeekrTask.objects.filter()
        for task in geneseekr_tasks:
            if os.path.isfile(task.exit_code_file):
                geneseekr_task = GeneSeekrRequest.objects.get(pk=task.geneseekr_request.pk)
                # Read exit code. Update status to 'Error' if non-zero, 'Completed' if zero.
                # Run any tasks necessary to clean things up/have reports run.
                with open(task.exit_code_file) as f:
                    lines = f.readlines()
                for line in lines:
                    line = line.rstrip()
                    if int(line.split(',')[1]) != 0:
                        GeneSeekrRequest.objects.filter(pk=geneseekr_task.pk).update(status='Error')
                        AzureGeneSeekrTask.objects.filter(id=task.id).delete()
                        shutil.rmtree('olc_webportalv2/media/geneseekr-{}/'.format(geneseekr_task.pk))
                    else:
                        # Upload result file to Blob storage, create download link, and clean up files.
                        # Upload entirety of reports folder for now. Maybe add visualisations of results in a bit?
                        print('Reading geneseekr results')
                        get_geneseekr_results(geneseekr_result_file='olc_webportalv2/media/geneseekr-{}/reports/geneseekr_blastn.csv'.format(geneseekr_task.pk),
                                              geneseekr_task=geneseekr_task)
                        get_geneseekr_detail(geneseekr_result_file='olc_webportalv2/media/geneseekr-{}/reports/geneseekr_blastn.csv'.format(geneseekr_task.pk),
                                             geneseekr_task=geneseekr_task)

                        print('Uploading result files')
                        shutil.make_archive('olc_webportalv2/media/geneseekr-{}/reports'.format(geneseekr_task.pk),
                                            'zip',
                                            'olc_webportalv2/media/geneseekr-{}/reports'.format(geneseekr_task.pk))
                        blob_client = BlockBlobService(account_key=settings.AZURE_ACCOUNT_KEY,
                                                       account_name=settings.AZURE_ACCOUNT_NAME)
                        geneseekr_result_container = 'geneseekr-{}'.format(geneseekr_task.pk)
                        blob_client.create_container(geneseekr_result_container)
                        blob_name = os.path.split('olc_webportalv2/media/geneseekr-{}/reports.zip'.format(geneseekr_task.pk))[1]
                        blob_client.create_blob_from_path(container_name=geneseekr_result_container,
                                                          blob_name=blob_name,
                                                          file_path='olc_webportalv2/media/geneseekr-{}/reports.zip'.format(geneseekr_task.pk))
                        # Generate an SAS url with read access that users will be able to use to download their sequences.
                        print('Creating Download Link')
                        sas_token = blob_client.generate_container_shared_access_signature(container_name=geneseekr_result_container,
                                                                                           permission=BlobPermissions.READ,
                                                                                           expiry=datetime.datetime.utcnow() + datetime.timedelta(days=8))
                        sas_url = blob_client.make_blob_url(container_name=geneseekr_result_container,
                                                            blob_name=blob_name,
                                                            sas_token=sas_token)
                        geneseekr_task.download_link = sas_url
                        shutil.rmtree('olc_webportalv2/media/geneseekr-{}/'.format(geneseekr_task.pk))
                        # Delete task so we don't have to keep checking up on it.
                        AzureGeneSeekrTask.objects.filter(id=task.id).delete()
                        geneseekr_task.status = 'Complete'
                        geneseekr_task.save()
        time.sleep(30)


def get_geneseekr_results(geneseekr_result_file, geneseekr_task):
    df = pd.read_csv(geneseekr_result_file)
    for column in df.columns:
        if column != 'Strain':
            hits = 0
            sequences = 0
            for i in df.index:
                sequences += 1
                if df[column][i] != 0:
                    hits += 1
            geneseekr_task.geneseekr_results[column] = 100.0 * float(hits/sequences)
    geneseekr_task.save()


def get_geneseekr_detail(geneseekr_result_file, geneseekr_task):
    df = pd.read_csv(geneseekr_result_file)
    for i in df.index:
        seqid = df['Strain'][i]
        geneseekr_detail = GeneSeekrDetail.objects.create(geneseekr_request=geneseekr_task,
                                                          seqid=seqid)
        geneseekr_results = dict()
        for column in df.columns:
            if column != 'Strain':
                gene = column
                percent_id = df[gene][i]
                if percent_id == 0:
                    percent_id = 0.0
                geneseekr_results[gene] = percent_id
        geneseekr_detail.geneseekr_results = geneseekr_results
        geneseekr_detail.save()


class Command(BaseCommand):
    help = 'Command to monitor cowbat tasks that have been submitted to azure batch'

    def handle(self, *args, **options):
        monitor_tasks()
