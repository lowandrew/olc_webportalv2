# Django-related imports
from django.core.mail import send_mail  # To be used eventually, only works in cloud
from background_task import background
from olc_webportalv2.cowbat.models import SequencingRun
# For some reason settings get imported from base.py - in views they come from prod.py. Weird.
from django.conf import settings  # To access azure credentials
# Standard python stuff
from subprocess import check_output
import subprocess
import shutil
import time
import glob
import os
# Other (azure related)
from azure.storage.blob import BlockBlobService


@background(schedule=1)
def run_cowbat_batch(sequencing_run_pk):
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

    # Upload the files we've gotten to Azure Blob Storage - to be downloaded to local storage later.
    container_name = str(sequencing_run).replace('_', '-').lower()
    blob_service = BlockBlobService(account_name=settings.AZURE_ACCOUNT_NAME,
                                    account_key=settings.AZURE_ACCOUNT_KEY)
    blob_service.create_container(container_name)
    # List all the files!
    files_to_upload = glob.glob('olc_webportalv2/media/{run_name}/*'.format(run_name=str(sequencing_run)))
    files_to_upload += glob.glob('olc_webportalv2/media/{run_name}/InterOp/*'.format(run_name=str(sequencing_run)))
    for filename in files_to_upload:
        blob_service.create_blob_from_path(container_name,
                                           os.path.split(filename)[-1],
                                           os.path.abspath(filename))

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
        f.write('COMMAND:=source $CONDA/activate /envs/cowbat && assembly_pipeline.py -s {} -r /databases/0.3.3\n'.format(str(sequencing_run)))

    # With that done, we can submit the file to batch with our package.
    # Use Popen to run in background so that task is considered complete.
    subprocess.Popen('AzureBatch -c {}/batch_config.txt')


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
              message='If you are Andrew or Adam, please download blob container {} to local OLC storage.'
                      ' If you\'re Paul, please add this data to the OLC database.'.format(container_name),
              from_email='olcbioinformatics@gmail.com',
              recipient_list=['paul.manninger@canada.ca', 'andrew.low@canada.ca', 'adam.koziol@canada.ca'])
    """


# TODO: Delete once we've tested and verified the batch-related things work.
@background(schedule=1)
def run_cowbat(sequencing_run_pk):
    sequencing_run = SequencingRun.objects.get(pk=sequencing_run_pk)
    # Wait for all the files to actually be present.
    all_files_present = False

    while all_files_present is False:
        all_files_present = True
        for seqid in sequencing_run.seqids:
            if len(glob.glob('olc_webportalv2/media/{run_name}/{seqid}*.fastq.gz'.format(run_name=str(sequencing_run), seqid=seqid))) != 2:
                all_files_present = False
        time.sleep(60)
    # Run COWBAT container - cowbat image is made with user as ubuntu, which causes permission issues
    # when files are uploaded. Hopefully setting user to root fixes that.
    cmd = 'docker exec -u root:root ' \
          'olcwebportalv2_cowbat ' \
          '/bin/bash -c "source activate cowbat && assembly_pipeline.py -s /sequences/{run_name} ' \
          '-r /mnt/nas2/databases/assemblydatabases/0.3.2"'.format(run_name=str(sequencing_run))
    try:
        p = check_output(cmd, shell=True)
    except:
        SequencingRun.objects.filter(pk=sequencing_run_pk).update(status='Error')
        return

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

    # We should now have a file in /sequences/run_name called run_name.zip - this is what we'll upload.

    SequencingRun.objects.filter(pk=sequencing_run_pk).update(status='Complete')

    # Upload results to blob storage and then get rid of everything except for reports and storage.
    # Blobs don't like folders, so create a zip folder out of the whole run.
    shutil.make_archive('olc_webportalv2/media/{run_name}'.format(run_name=str(sequencing_run)),
                        'zip',
                        'olc_webportalv2/media/{run_name}'.format(run_name=str(sequencing_run)))
    # Now login to blob service and upload ye olde zip file as blob to container.
    # Make the container with _ replaced with - and all lower case.
    container_name = str(sequencing_run).replace('_', '-').lower()
    blob_service = BlockBlobService(account_name=settings.AZURE_ACCOUNT_NAME,
                                    account_key=settings.AZURE_ACCOUNT_KEY)
    blob_service.create_container(container_name)
    blob_service.create_blob_from_path(container_name, str(sequencing_run) + '.zip',
                                       'olc_webportalv2/media/{run_name}.zip'.format(run_name=str(sequencing_run)))
    os.remove('olc_webportalv2/media/{run_name}.zip'.format(run_name=str(sequencing_run)))

    # Finally, to save space on storage, get rid of raw data, since that's been uploaded to the cloud.
    os.system = 'rm olc_webportalv2/media/{run_name}/*.fastq.gz'.format(run_name=str(sequencing_run))
    # Finally (but actually this time) send an email to relevant people to let them know that things have worked.
    # Uncomment this on the cloud where email sending actually works
    """
    send_mail(subject='TEST PLEASE IGNORE - Run {} has finished assembly.'.format(str(sequencing_run)),
              message='If you are Andrew or Adam, please download blob container {} to local OLC storage.'
                      ' If you\'re Paul, please add this data to the OLC database.'.format(container_name),
              from_email='olcbioinformatics@gmail.com',
              recipient_list=['paul.manninger@canada.ca', 'andrew.low@canada.ca', 'adam.koziol@canada.ca'])
    """
