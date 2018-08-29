import os
import shutil
import subprocess

from background_task import background
from django.conf import settings
from olc_webportalv2.geneseekr.models import GeneSeekrRequest, AzureGeneSeekrTask
from azure.storage.blob import BlockBlobService

@background(schedule=1)
def run_geneseekr(geneseekr_request_pk):
    geneseekr_request = GeneSeekrRequest.objects.get(pk=geneseekr_request_pk)
    try:
        geneseekr_dir = 'olc_webportalv2/media/geneseekr-{}'.format(geneseekr_request_pk)
        if not os.path.isdir(geneseekr_dir):
            os.makedirs(geneseekr_dir)
        # Run Geneseekr! Need to write the contents of the query_sequence attribute to a file.
        with open(os.path.join(geneseekr_dir, 'query.tfa'), 'w') as f:
            f.write(geneseekr_request.query_sequence)

        # Azure is not happy when too many (not sure on exact number, seems to be ~100) input files
        # get specfied. If that's the case, we'll need to download all the input files, zip them, and
        # then upload the zip back to blob and unzip it as part of the command. Otherwise,
        # take advantage of the fact that the files are already in the cloud.
        if len(geneseekr_request.seqids) > 75:
            sequence_dir = os.path.join(geneseekr_dir, 'sequences')
            if not os.path.isdir(sequence_dir):
                os.makedirs(sequence_dir)
            blob_client = BlockBlobService(account_key=settings.AZURE_ACCOUNT_KEY,
                                           account_name=settings.AZURE_ACCOUNT_NAME)
            for seqid in geneseekr_request.seqids:
                blob_client.get_blob_to_path(container_name='processed-data',
                                             blob_name='{}.fasta'.format(seqid),
                                             file_path=os.path.join(sequence_dir, '{}.fasta'.format(seqid)))
            shutil.make_archive(sequence_dir, 'zip', sequence_dir)
            batch_config_file = os.path.join(geneseekr_dir, 'batch_config.txt')
            with open(batch_config_file, 'w') as f:
                f.write('BATCH_ACCOUNT_NAME:={}\n'.format(settings.BATCH_ACCOUNT_NAME))
                f.write('BATCH_ACCOUNT_KEY:={}\n'.format(settings.BATCH_ACCOUNT_KEY))
                f.write('BATCH_ACCOUNT_URL:={}\n'.format(settings.BATCH_ACCOUNT_URL))
                f.write('STORAGE_ACCOUNT_NAME:={}\n'.format(settings.AZURE_ACCOUNT_NAME))
                f.write('STORAGE_ACCOUNT_KEY:={}\n'.format(settings.AZURE_ACCOUNT_KEY))
                f.write('JOB_NAME:={}\n'.format('geneseekr-{}'.format(geneseekr_request_pk)))
                f.write('VM_IMAGE:={}\n'.format(settings.VM_IMAGE))
                f.write('VM_CLIENT_ID:={}\n'.format(settings.VM_CLIENT_ID))
                f.write('VM_SECRET:={}\n'.format(settings.VM_SECRET))
                f.write('VM_SIZE:=Standard_D2_v3\n')
                f.write('VM_TENANT:={}\n'.format(settings.VM_TENANT))
                f.write('INPUT:={} targets\n'.format(os.path.join(geneseekr_dir, 'query.tfa')))
                f.write('INPUT:={}\n'.format(sequence_dir + '.zip'))
                f.write('OUTPUT:=reports/*\n')
                # Need to include these exports or click freaks out about python3 ascii encoding.
                # Also, clumsy unzip, but that's OK
                f.write('COMMAND:=unzip sequences.zip && mkdir sequences &&  mv *.fasta sequences && export LC_ALL=C.UTF-8 && export LANG=C.UTF-8 && '
                        'source $CONDA/activate /envs/geneseekr '
                        '&& GeneSeekr blastn -s sequences -t targets -r reports\n')
        else:
            batch_config_file = os.path.join(geneseekr_dir, 'batch_config.txt')
            with open(batch_config_file, 'w') as f:
                f.write('BATCH_ACCOUNT_NAME:={}\n'.format(settings.BATCH_ACCOUNT_NAME))
                f.write('BATCH_ACCOUNT_KEY:={}\n'.format(settings.BATCH_ACCOUNT_KEY))
                f.write('BATCH_ACCOUNT_URL:={}\n'.format(settings.BATCH_ACCOUNT_URL))
                f.write('STORAGE_ACCOUNT_NAME:={}\n'.format(settings.AZURE_ACCOUNT_NAME))
                f.write('STORAGE_ACCOUNT_KEY:={}\n'.format(settings.AZURE_ACCOUNT_KEY))
                f.write('JOB_NAME:={}\n'.format('geneseekr-{}'.format(geneseekr_request_pk)))
                f.write('VM_IMAGE:={}\n'.format(settings.VM_IMAGE))
                f.write('VM_CLIENT_ID:={}\n'.format(settings.VM_CLIENT_ID))
                f.write('VM_SECRET:={}\n'.format(settings.VM_SECRET))
                f.write('VM_SIZE:=Standard_D2_v3\n')
                f.write('VM_TENANT:={}\n'.format(settings.VM_TENANT))
                f.write('INPUT:={} targets\n'.format(os.path.join(geneseekr_dir, 'query.tfa')))
                f.write('CLOUDIN:=')
                for seqid in geneseekr_request.seqids:
                    f.write('processed-data/{}.fasta '.format(seqid))
                f.write('sequences\n')
                f.write('OUTPUT:=reports/*\n')
                # Need to include these exports or click freaks out about python3 ascii encoding.
                f.write('COMMAND:=export LC_ALL=C.UTF-8 && export LANG=C.UTF-8 && source $CONDA/activate /envs/geneseekr '
                        '&& GeneSeekr blastn -s sequences -t targets -r reports\n')
        # Get process running in background, and create an azureTask that looks for the exit code file
        subprocess.Popen('AzureBatch -e {run_folder}/exit_codes.txt -c {run_folder}/batch_config.txt '
                         '-o {run_folder}'.format(run_folder=geneseekr_dir), shell=True)
        AzureGeneSeekrTask.objects.create(geneseekr_request=geneseekr_request,
                                          exit_code_file=os.path.join(geneseekr_dir, 'exit_codes.txt'))
    except:
        geneseekr_request.status = 'Error'
        geneseekr_request.save()
