# Django-related imports
from django.core.mail import send_mail  # To be used eventually, only works in cloud
from background_task import background
from olc_webportalv2.cowbat.models import SequencingRun, AzureTask
# For some reason settings get imported from base.py - in views they come from prod.py. Weird.
from django.conf import settings  # To access azure credentials
# Standard python stuff
import subprocess
import shutil
import time
import glob
import os
# Other (azure related)

# Not quite working yet. Run tomorrow.
@background(schedule=1)
def run_cowbat_batch(sequencing_run_pk):
    try:
        sequencing_run = SequencingRun.objects.get(pk=sequencing_run_pk)
        # Wait for all the files to actually be present.
        all_files_present = False
        run_folder = 'olc_webportalv2/media/{run_name}'.format(run_name=str(sequencing_run))
        while all_files_present is False:
            all_files_present = True
            for seqid in sequencing_run.seqids:
                if len(glob.glob('olc_webportalv2/media/{run_name}/{seqid}*.fastq.gz'.format(run_name=str(sequencing_run), seqid=seqid))) != 2:
                    all_files_present = False
            time.sleep(60)

        container_name = str(sequencing_run).replace('_', '-').lower()

        # Create a configuration file to be used by my Azure batch script.
        batch_config_file = os.path.join(run_folder, 'batch_config.txt')
        with open(batch_config_file, 'w') as f:
            f.write('BATCH_ACCOUNT_NAME:={}\n'.format(settings.BATCH_ACCOUNT_NAME))
            f.write('BATCH_ACCOUNT_KEY:={}\n'.format(settings.BATCH_ACCOUNT_KEY))
            f.write('BATCH_ACCOUNT_URL:={}\n'.format(settings.BATCH_ACCOUNT_URL))
            f.write('STORAGE_ACCOUNT_NAME:={}\n'.format(settings.AZURE_ACCOUNT_NAME))
            f.write('STORAGE_ACCOUNT_KEY:={}\n'.format(settings.AZURE_ACCOUNT_KEY))
            f.write('JOB_NAME:={}\n'.format(container_name))
            f.write('VM_IMAGE:={}\n'.format(settings.VM_IMAGE))
            f.write('VM_CLIENT_ID:={}\n'.format(settings.VM_CLIENT_ID))
            f.write('VM_SECRET:={}\n'.format(settings.VM_SECRET))
            f.write('VM_TENANT:={}\n'.format(settings.VM_TENANT))
            f.write('INPUT:={} {}\n'.format(os.path.join(run_folder, '*.fastq.gz'), str(sequencing_run)))
            f.write('INPUT:={} {}\n'.format(os.path.join(run_folder, '*.xml'), str(sequencing_run)))
            f.write('INPUT:={} {}\n'.format(os.path.join(run_folder, '*.csv'), str(sequencing_run)))
            f.write('INPUT:={} {}\n'.format(os.path.join(run_folder, 'InterOp', '*'), os.path.join(str(sequencing_run), 'InterOp')))
            f.write('OUTPUT:={}\n'.format(os.path.join(run_folder, 'reports', '*')))
            f.write('OUTPUT:={}\n'.format(os.path.join(run_folder, 'BestAssemblies', '*')))
            # The CLARK part of the pipeline needs absolute path specified, so the $AZ_BATCH_TASK_WORKING_DIR has to
            # be specifiec as part of the command in order to have the absolute path of our sequences propagate to it.
            f.write('COMMAND:=source $CONDA/activate /envs/cowbat && assembly_pipeline.py '
                    '-s $AZ_BATCH_TASK_WORKING_DIR/{run_name} -r /databases/0.3.2\n'.format(run_name=str(sequencing_run)))

        # With that done, we can submit the file to batch with our package.
        # Use Popen to run in background so that task is considered complete.
        subprocess.Popen('AzureBatch -k -e {run_folder}/exit_codes.txt -c {run_folder}/batch_config.txt '
                         '-o olc_webportalv2/media'.format(run_folder=run_folder), shell=True)
        AzureTask.objects.create(sequencing_run=sequencing_run,
                                 exit_code_file=os.path.join(run_folder, 'exit_codes.txt'))
    except:
        """
        send_mail(subject='Assembly Error - Run {} was not successfully submitted to Azure Batch.'.format(str(sequencing_run)),
                  message='Fix it!',
                  from_email=settings.EMAIL_HOST_USER,
                  recipient_list=['andrew.low@canada.ca'])
        """
        SequencingRun.objects.filter(pk=sequencing_run_pk).update(status='Error')


@background(schedule=1)
def cowbat_cleanup(sequencing_run_pk):
    sequencing_run = SequencingRun.objects.get(pk=sequencing_run_pk)
    # With the sequencing run done, need to put create a zipfile with assemblies and reports for user to download.
    # First create a folder.
    if not os.path.isdir('olc_webportalv2/media/{run_name}/reports_and_assemblies'.format(run_name=str(sequencing_run))):
        os.makedirs('olc_webportalv2/media/{run_name}/reports_and_assemblies'.format(run_name=str(sequencing_run)))
    # Now copy the reports and assemblies to the created folder.
    cmd = 'cp -r {best_assemblies} ' \
          '{download_folder}'.format(best_assemblies='olc_webportalv2/media/{run_name}/BestAssemblies'.format(run_name=str(sequencing_run)),
                                     download_folder='olc_webportalv2/media/{run_name}/reports_and_assemblies'.format(run_name=str(sequencing_run)))
    os.system(cmd)
    cmd = 'cp -r {reports} ' \
          '{download_folder}'.format(reports='olc_webportalv2/media/{run_name}/reports'.format(run_name=str(sequencing_run)),
                                     download_folder='olc_webportalv2/media/{run_name}/reports_and_assemblies'.format(run_name=str(sequencing_run)))
    os.system(cmd)

    # With that done, create a zipfile.
    shutil.make_archive('olc_webportalv2/media/{run_name}/{run_name}'.format(run_name=str(sequencing_run)),
                        'zip', 'olc_webportalv2/media/{run_name}/reports_and_assemblies'.format(run_name=str(sequencing_run)))

    # Finally, to save space on storage, get rid of raw data, since that's been uploaded to the cloud.
    os.system = 'rm olc_webportalv2/media/{run_name}/*.fastq.gz'.format(run_name=str(sequencing_run))
    # Run is now considered complete! Update to let user know and send email to people that need to know.
    SequencingRun.objects.filter(pk=sequencing_run_pk).update(status='Complete')
    # Finally (but actually this time) send an email to relevant people to let them know that things have worked.
    # Uncomment this on the cloud where email sending actually works
    """
    send_mail(subject='TEST PLEASE IGNORE - Run {} has finished assembly.'.format(str(sequencing_run)),
              message='If you are Andrew or Adam, please download the blob container to local OLC storage.'
                      ' If you\'re Paul, please add this data to the OLC database.',
              from_email=settings.EMAIL_HOST_USER,
              recipient_list=['paul.manninger@canada.ca', 'andrew.low@canada.ca', 'adam.koziol@canada.ca'])
    """

