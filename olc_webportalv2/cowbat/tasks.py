from background_task import background
from olc_webportalv2.cowbat.models import SequencingRun
from subprocess import Popen, check_output


@background(schedule=1)
def run_cowbat(sequencing_run_pk):
    sequencing_run = SequencingRun.objects.get(pk=sequencing_run_pk)
    # TODO: Docker exec a cowbat container that will have to be added to docker-compose.yml
