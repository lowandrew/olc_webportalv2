from background_task import background
from olc_webportalv2.cowbat.models import SequencingRun
from subprocess import Popen, check_output


@background(schedule=1)
def run_cowbat(sequencing_run_pk):
    sequencing_run = SequencingRun.objects.get(pk=sequencing_run_pk)
    cmd = 'docker exec ' \
          'olcwebportalv2_cowbat ' \
          '/bin/bash -c "source activate cowbat && assembly_pipeline.py -s /sequences/{run_name} ' \
          '-r /mnt/nas2/databases/assemblydatabases/0.3.2"'.format(run_name=str(sequencing_run))
    try:
        p = check_output(cmd, shell=True)
    except:
        SequencingRun.objects.filter(pk=sequencing_run_pk).update(status='Error')
        return

    SequencingRun.objects.filter(pk=sequencing_run_pk).update(status='Complete')


