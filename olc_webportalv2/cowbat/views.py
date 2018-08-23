# Django-related imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
# Standard libraries
import mimetypes
import logging
import re
import os
# Portal-specific things.
from olc_webportalv2.cowbat.models import SequencingRun, DataFile, InterOpFile
from olc_webportalv2.cowbat.forms import RunNameForm
from olc_webportalv2.cowbat.tasks import run_cowbat_batch
# Azure!
import azure.batch.batch_service_client as batch
import azure.batch.batch_auth as batch_auth
import azure.batch.models as batchmodels

log = logging.getLogger(__name__)


def find_percent_complete(sequencing_run):
    try:
        job_id = str(sequencing_run).lower().replace('_', '-')
        credentials = batch_auth.SharedKeyCredentials(settings.BATCH_ACCOUNT_NAME, settings.BATCH_ACCOUNT_KEY)
        batch_client = batch.BatchServiceClient(credentials, base_url=settings.BATCH_ACCOUNT_URL)
        node_files = batch_client.file.list_from_task(job_id=job_id, task_id=job_id, recursive=True)
        seqid_regex = '\d{4}-[A-Z]+-\d{4}'
        final_num_subfolders = len(sequencing_run.seqids) * 20
        current_subfolders = 0
        for node_file in node_files:
            if len(node_file.name.split('/')) == 4 and '.' not in os.path.split(node_file.name)[1] and re.search(seqid_regex, node_file.name) is not None:
                    current_subfolders += 1
        if final_num_subfolders == 0:
            percent_completed = 1
        else:
            percent_completed = int(100.0 * (current_subfolders/final_num_subfolders))

    except batchmodels.BatchErrorException:  # Means task and job have not yet been created
        percent_completed = 1
    return percent_completed


# Create your views here.
@login_required
def cowbat_processing(request, sequencing_run_pk):
    sequencing_run = get_object_or_404(SequencingRun, pk=sequencing_run_pk)
    if sequencing_run.status == 'Unprocessed':
        SequencingRun.objects.filter(pk=sequencing_run.pk).update(status='Processing')
        run_cowbat_batch(sequencing_run_pk=sequencing_run.pk)

    # Find percent complete (approximately). Not sure that having calls to azure batch API in views is a good thing.
    # Will have to see if performance is terrible because of it.
    if sequencing_run.status == 'Processing':
        progress = find_percent_complete(sequencing_run)
    else:
        progress = 1
    return render(request,
                  'cowbat/cowbat_processing.html',
                  {
                      'sequencing_run': sequencing_run,
                      'progress': str(progress)
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


@login_required
def assembly_home(request):
    sequencing_runs = SequencingRun.objects.filter()
    return render(request,
                  'cowbat/assembly_home.html',
                  {
                      'sequencing_runs': sequencing_runs
                  })


@login_required
def upload_metadata(request):
    form = RunNameForm()
    if request.method == 'POST':
        form = RunNameForm(request.POST)
        if form.is_valid():
            if not SequencingRun.objects.filter(run_name=form.cleaned_data.get('run_name')).exists():
                sequencing_run, created = SequencingRun.objects.update_or_create(run_name=form.cleaned_data.get('run_name'),
                                                                                 seqids=list())
            else:
                sequencing_run = SequencingRun.objects.get(run_name=form.cleaned_data.get('run_name'))
            files = [request.FILES.get('file[%d]' % i) for i in range(0, len(request.FILES))]
            for item in files:
                instance = DataFile(sequencing_run=sequencing_run,
                                    data_file=item)
                instance.save()
                log.debug(item.name)
                if item.name == 'SampleSheet.csv':
                    with open('olc_webportalv2/media/{run_name}/SampleSheet.csv'.format(run_name=str(sequencing_run))) as f:
                        lines = f.readlines()
                    seqid_start = False
                    seqid_list = list()
                    for i in range(len(lines)):
                        if seqid_start:
                            seqid = lines[i].split(',')[0]
                            seqid_list.append(seqid)
                        if 'Sample_ID' in lines[i]:
                            seqid_start = True
                    SequencingRun.objects.filter(pk=sequencing_run.pk).update(seqids=seqid_list)
            return redirect('cowbat:upload_interop', sequencing_run_pk=sequencing_run.pk)
    return render(request,
                  'cowbat/upload_metadata.html',
                  {
                      'form': form
                  })


@login_required
def upload_interop(request, sequencing_run_pk):
    sequencing_run = get_object_or_404(SequencingRun, pk=sequencing_run_pk)
    if request.method == 'POST':
            files = [request.FILES.get('file[%d]' % i) for i in range(0, len(request.FILES))]
            for item in files:
                instance = InterOpFile(sequencing_run=sequencing_run,
                                       interop_file=item)
                instance.save()
            return redirect('cowbat:upload_sequence_data', sequencing_run_pk=sequencing_run.pk)
    return render(request,
                  'cowbat/upload_interop.html',
                  {
                      'sequencing_run': sequencing_run
                  })


# TODO: This should be refactored - have one function for uploading and saving the files, and
# a different function that gets called when all have been uploaded that submits the task
@login_required
def upload_sequence_data(request, sequencing_run_pk):
    sequencing_run = get_object_or_404(SequencingRun, pk=sequencing_run_pk)
    if request.method == 'POST':
        # This appears to be creating giant memory usage issues. Files get read into memory by dropzone,
        # and then read into memory again when I call this, which seems horrendously inefficient (and causes
        # crashes when we run OOM). Need to either - get dropzone to write directly to disk (which I don't think
        # can happen since its only client side) OR just put one file at a time to disk.

        # I think this should do the only put one file at a time to disk trick. Commented out code below that
        # is previous bad implementation that read everything into memory again.
        for i in range(0, len(request.FILES)):
            item = request.FILES.get('file[%d]' % i)
            log.debug(item.name)
            instance = DataFile(sequencing_run=sequencing_run,
                                data_file=item)
            instance.save()

        return redirect('cowbat:cowbat_processing', sequencing_run_pk=sequencing_run.pk)
    return render(request,
                  'cowbat/upload_sequence_data.html',
                  {
                      'sequencing_run': sequencing_run,
                  })
