import os
import shutil
import datetime
import subprocess
import pandas as pd
import multiprocessing
from background_task import background
from django.conf import settings
from olc_webportalv2.geneseekr.models import GeneSeekrRequest, GeneSeekrDetail

from azure.storage.blob import BlockBlobService
from azure.storage.blob import BlobPermissions


@background(schedule=1)
def run_geneseekr(geneseekr_request_pk):
    geneseekr_request = GeneSeekrRequest.objects.get(pk=geneseekr_request_pk)
    try:
        # Running GeneSeekr via batch is not ideal, as it's not really a big job - results should be relatively instant,
        # no need for a 5ish minute delay.

        # Step 1: Make a directory for our things.
        geneseekr_dir = 'olc_webportalv2/media/geneseekr-{}'.format(geneseekr_request_pk)
        if not os.path.isdir(geneseekr_dir):
            os.makedirs(geneseekr_dir)
        # If we're going to run things NOT via batch, all of our files to BLAST against should be stored locally.
        # Need to create links to all those files in our geneseekr_dir.
        sequence_dir = '/sequences'  # TODO: Figure out where you'll actually store these.
        geneseekr_sequence_dir = os.path.join(geneseekr_dir, 'sequences')
        if not os.path.isdir(geneseekr_sequence_dir):
            os.makedirs(geneseekr_sequence_dir)
        for seqid in geneseekr_request.seqids:
            if not os.path.exists(os.path.join(geneseekr_sequence_dir, '{}.fasta'.format(seqid))):
                os.symlink(src=os.path.join(sequence_dir, '{}.fasta'.format(seqid)), dst=os.path.join(geneseekr_sequence_dir, '{}.fasta'.format(seqid)))
        # With our symlinks created, also create our query file.
        geneseekr_query_dir = os.path.join(geneseekr_dir, 'targets')
        if not os.path.isdir(geneseekr_query_dir):
            os.makedirs(geneseekr_query_dir)

        with open(os.path.join(geneseekr_query_dir, 'query.tfa'), 'w') as f:
            f.write(geneseekr_request.query_sequence)

        # With query and sequence done, can go ahead and call GeneSeekr
        geneseekr_report_dir = os.path.join(geneseekr_dir, 'reports')
        if multiprocessing.cpu_count() > 1:
            threads_to_use = multiprocessing.cpu_count() - 1
        else:
            threads_to_use = 1
        cmd = 'GeneSeekr blastn -s {sequences} -t {targets} -r {reports} -n {threads}'.format(sequences=os.path.abspath(geneseekr_sequence_dir),
                                                                                              targets=os.path.abspath(geneseekr_query_dir),
                                                                                              reports=os.path.abspath(geneseekr_report_dir),
                                                                                              threads=threads_to_use)
        subprocess.call(cmd, shell=True)
        print('Reading geneseekr results')
        get_geneseekr_results(geneseekr_result_file='olc_webportalv2/media/geneseekr-{}/reports/geneseekr_blastn.csv'.format(geneseekr_request.pk),
                              geneseekr_task=geneseekr_request)
        get_geneseekr_detail(geneseekr_result_file='olc_webportalv2/media/geneseekr-{}/reports/geneseekr_blastn.csv'.format(geneseekr_request.pk),
                             geneseekr_task=geneseekr_request)

        print('Uploading result files')
        shutil.make_archive('olc_webportalv2/media/geneseekr-{}/reports'.format(geneseekr_request.pk),
                            'zip',
                            'olc_webportalv2/media/geneseekr-{}/reports'.format(geneseekr_request.pk))
        blob_client = BlockBlobService(account_key=settings.AZURE_ACCOUNT_KEY,
                                       account_name=settings.AZURE_ACCOUNT_NAME)
        geneseekr_result_container = 'geneseekr-{}'.format(geneseekr_request.pk)
        blob_client.create_container(geneseekr_result_container)
        blob_name = os.path.split('olc_webportalv2/media/geneseekr-{}/reports.zip'.format(geneseekr_request.pk))[1]
        blob_client.create_blob_from_path(container_name=geneseekr_result_container,
                                          blob_name=blob_name,
                                          file_path='olc_webportalv2/media/geneseekr-{}/reports.zip'.format(geneseekr_request.pk))
        # Generate an SAS url with read access that users will be able to use to download their sequences.
        print('Creating Download Link')
        sas_token = blob_client.generate_container_shared_access_signature(container_name=geneseekr_result_container,
                                                                           permission=BlobPermissions.READ,
                                                                           expiry=datetime.datetime.utcnow() + datetime.timedelta(days=8))
        sas_url = blob_client.make_blob_url(container_name=geneseekr_result_container,
                                            blob_name=blob_name,
                                            sas_token=sas_token)
        geneseekr_request.download_link = sas_url
        shutil.rmtree('olc_webportalv2/media/geneseekr-{}/'.format(geneseekr_request.pk))
        geneseekr_request.status = 'Complete'
        geneseekr_request.save()
    except:
        geneseekr_request.status = 'Error'
        geneseekr_request.save()


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
