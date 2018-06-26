# Django-related imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
# Standard libraries
import mimetypes
import logging
import glob
import re
import os
# Portal-specific things.
from olc_webportalv2.cowbat.models import SequencingRun, DataFile
from olc_webportalv2.cowbat.forms import RunNameForm
from olc_webportalv2.cowbat.tasks import run_cowbat

log = logging.getLogger(__name__)


# Create your views here.
@login_required
def cowbat_home(request):
    form = RunNameForm()
    if request.method == 'POST':
        log.debug(request.FILES)
        form = RunNameForm(request.POST)
        if form.is_valid():
            log.debug('VALID FORM')
            sequencing_run, created = SequencingRun.objects.update_or_create(run_name=form.cleaned_data.get('run_name'))
            files = [request.FILES.get('file[%d]' % i) for i in range(0, len(request.FILES))]
            for item in files:
                instance = DataFile(sequencing_run=sequencing_run,
                                    data_file=item)
                instance.save()
                log.debug(item.name)
            if sequencing_run.status == 'Unprocessed':
                SequencingRun.objects.filter(pk=sequencing_run.pk).update(status='Processing')
                run_cowbat(sequencing_run_pk=sequencing_run.pk)
            return redirect('cowbat:cowbat_processing', sequencing_run_pk=sequencing_run.pk)
        else:
            log.debug('INVALID FORM')
    else:
        log.debug('NOT A POST REQUEST')
    return render(request,
                  'cowbat/cowbat_home.html',
                  {
                      'form': form,
                  })


@login_required
def cowbat_processing(request, sequencing_run_pk):
    sequencing_run = get_object_or_404(SequencingRun, pk=sequencing_run_pk)
    number_of_samples = len(glob.glob('olc_webportalv2/media/{run_folder}/*_R1*.fastq.gz'.format(run_folder=str(sequencing_run))))
    # Each sample ends up with its own folder that has 17 analysis-related subfolders (except for undetermined? Might have to
    # factor that in). To get rough idea of progress, figure out total number of folders we should end up with,
    # which is number of samples * 17, and do a check on how many subfolders we have
    total_num_folders = number_of_samples * 17
    num_subfolders = 0
    seqid_regex = '\d{4}-[A-Z]+-\d{4}'
    # Get list of all folders in sequencing directory. Use regex to figure out which ones to look into(they should be formatted
    # as seqids.
    folders = glob.glob('olc_webportalv2/media/{run_folder}/*/'.format(run_folder=str(sequencing_run)))
    for folder in folders:
        log.debug(folder)
        # Count number of subfolders if folder we're looking at is a seqid
        if re.search(seqid_regex, folder) is not None:
            num_subfolders += len(next(os.walk(folder))[1])
    # Use this as our marker of progress.
    log.debug(str(num_subfolders))
    if total_num_folders != 0:
        progress = 100.0 * (float(num_subfolders)/float(total_num_folders))
    else:
        progress = 0
    progress = int(progress)
    log.debug(str(progress))
    return render(request,
                  'cowbat/cowbat_processing.html',
                  {
                      'sequencing_run': sequencing_run,
                      'progress': str(progress),
                  })


@login_required
def download_run_info(request, run_folder):
    # Found at: http://voorloopnul.com/blog/serving-large-and-small-files-with-django/
    # Note that this is probably not optimal, but given how few people should be accessing the web portal,
    # this shouldn't matter too much.
    filepath = 'olc_webportalv2/media/{run_folder}/{run_folder}.zip'.format(run_folder=run_folder)
    with open(filepath, 'rb') as f:
        data = f.read()

    response = HttpResponse(data, content_type=mimetypes.guess_type(filepath)[0])
    response['Content-Disposition'] = 'attachment; filename={}.zip'.format(run_folder)
    response['Content-Length'] = os.path.getsize(filepath)
    return response
