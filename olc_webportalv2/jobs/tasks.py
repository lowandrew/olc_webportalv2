import os
import shutil
from subprocess import Popen
from background_task import background


@background(schedule=5)
def run_genesippr(file_path):

    # Set output directory
    output_dir = '/sequences/{0}/output'.format(file_path)
    if os.path.exists(output_dir):
        print('Output directory already exists. Removing existing directory: ' + output_dir)
        shutil.rmtree(output_dir)
    print('Creating ' + output_dir)
    os.makedirs(output_dir)

    print('Running GenesipprV2...')
    cmd = 'docker exec ' \
          'genesipprv2 ' \
          'python3 ' \
          'geneSipprV2/sipprverse/method.py ' \
          '/sequences/{0}/output ' \
          '-t /targets ' \
          '-s /sequences/{0}'.format(file_path)
    p = Popen(cmd, shell=True)
    p.communicate()  # wait until the script completes before resuming the code
    print('\nGenesipprV2 JOB COMPLETE')
