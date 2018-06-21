from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
import mimetypes
import os
from olc_webportalv2.cowbat.forms import RunNameForm
from olc_webportalv2.cowbat.models import SequencingRun, DataFile
from olc_webportalv2.cowbat.tasks import run_cowbat
from django.contrib.auth.decorators import login_required
import logging

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
    return render(request,
                  'cowbat/cowbat_processing.html',
                  {
                      'sequencing_run': sequencing_run,
                  })


@login_required
def download_run_info(request, run_folder):
    # Found at: http://voorloopnul.com/blog/serving-large-and-small-files-with-django/
    filepath = '/static/{run_folder}/{run_folder}.zip'.format(run_folder=run_folder)
    with open(filepath, 'r') as f:
        data = f.read()

    response = HttpResponse(data, content_type=mimetypes.guess_type(filepath)[0])
    response['Content-Disposition'] = 'attachment; filename={}.zip'.format(run_folder)
    response['Content-Length'] = os.path.getsize(filepath)
    return response
