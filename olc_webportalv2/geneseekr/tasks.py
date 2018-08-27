import os
import subprocess

from background_task import background
from django.conf import settings
from olc_webportalv2.geneseekr.models import GeneSeekrRequest, AzureGeneSeekrTask


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

        # Once that's done, create a config file for use with AzureBatch and submit job.
        # The monitor_tasks command will watch for an exit file and upload results files
        batch_config_file = os.path.join(geneseekr_dir, 'batch_config.txt')
        # TODO: Change VM size, geneseekr shouldn't need anything too big
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
            for seqid in geneseekr_request.seqids:
                f.write('CLOUD_IN:=processed-data/{}.fasta\n'.format(seqid))
            f.write('OUTPUT:=reports/\n')  # Figure out exactly what outputs we need from
            # The CLARK part of the pipeline needs absolute path specified, so the $AZ_BATCH_TASK_WORKING_DIR has to
            # be specifiec as part of the command in order to have the absolute path of our sequences propagate to it.
            f.write('COMMAND:=source $CONDA/activate /envs/geneseekr && GeneSeekr blastn -s {} '
                    '-t {} -r reports\n')
        # TODO: Uncomment once I have VM image updated with GeneSeekr
        # subprocess.Popen('AzureBatch -e {run_folder}/exit_codes.txt -c {run_folder}/batch_config.txt '
        #                  '-o {run_folder}'.format(run_folder=geneseekr_dir), shell=True)
        # AzureGeneSeekrTask.objects.create(geneseekr_request=geneseekr_request,
        #                                   exit_code_file=os.path.join(geneseekr_dir, 'exit_codes.txt'))
    except:
        geneseekr_request.status = 'Error'
        geneseekr_request.save()
