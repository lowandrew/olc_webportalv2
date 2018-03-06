from django.shortcuts import render, get_object_or_404
import os

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from django_tables2 import RequestConfig
from .models import ProjectMulti, Sample, SendsketchResult
from .forms import ProjectForm, JobForm
from . import tasks
from .table import SendsketchTable
# Create your views here.


@login_required
def new_multisample(request):
    project_list = ProjectMulti.objects.filter(user=request.user)
    form = ProjectForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            print('Form is valid.\n')

            # Have to do this in order to set the user to current logged in user
            new_entry = form.save(commit=False)

            # Pull active user
            new_entry.user = request.user

            # Save the form
            new_entry = form.save()

    return render(request,
                  'new_multisample/new_multisample.html',
                  {'project_list': project_list,
                   'form': form,
                   'project_id': ProjectMulti.pk,
                   'user': request.user
                   }
                  )


@login_required
def upload_samples(request, project_id):
    project = get_object_or_404(ProjectMulti, pk=project_id)
    # try:
    #     project_id = ProjectMulti.objects.get(pk=project_id)
    # except ProjectMulti.DoesNotExist:
    #     raise Http404("Project ID {} does not exist.".format(project_id))

    if request.method == 'POST':
        # form = SampleForm(request.POST)
        files = request.FILES.getlist('files')
        filenames = list()
        file_dict = dict()
        for item in files:
            if item.name.endswith('.fastq') or item.name.endswith('.fastq.gz'):
                filenames.append(item.name)
                file_dict[item.name] = item
            # TODO: Need to parse through names to try to get samples.
            # instance = Attachment(attachment=item)
            # instance.save()
        pairs = find_paired_reads(filenames)
        for pair in pairs:
            sample_name = pair[0].split('_R1')[0]
            instance = Sample(file_R1=file_dict[pair[0]],
                              file_R2=file_dict[pair[1]],
                              title=sample_name,
                              project=project)
            instance.save()

        form = JobForm(request.POST)
        return render(request,
                      'new_multisample/project_detail.html',
                      {'project': project,
                       'form': form,
                       'user': request.user},
                      )
    else:
        return render(request,
                      'new_multisample/upload_samples.html',
                      {'project': project}
                       )

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(ProjectMulti, pk=project_id)
    form = JobForm(request.POST)
    # try:
    #     project_id = ProjectMulti.objects.get(pk=project_id)
    # except ProjectMulti.DoesNotExist:
    #     raise Http404("Project ID {} does not exist.".format(project_id))
    if request.method == 'POST':
        # Save the form
        if form.is_valid():
            jobs_to_run = form.cleaned_data.get('jobs')
            print(jobs_to_run)
            if 'sendsketch' in jobs_to_run:
                for sample in project.samples.all():
                    file_path = os.path.dirname(str(sample.file_R1))
                    tasks.run_sendsketch(read1=sample.file_R1.name,
                                         read2=sample.file_R2.name,
                                         sample_pk=sample.pk,
                                         file_path=file_path)

    # else:
    #     form = SampleForm()
    return render(request,
                  'new_multisample/project_detail.html',
                  {'project': project,
                   'form': form,
                   'user': request.user},
                  )


def sample_detail(request, sample_id):
    sample = get_object_or_404(Sample, pk=sample_id)
    return render(request,
                  'new_multisample/sample_detail.html',
                  {'sample': sample},
                  )

@login_required
def sendsketch_results_table(request, sample_id):
    try:
        sample = SendsketchResult.objects.filter(sample=Sample.objects.get(pk=sample_id)).exclude(rank='N/A')
        sendsketch_results_table_ = SendsketchTable(SendsketchResult.objects.all())
        base_project = Sample.objects.get(pk=sample_id)
        RequestConfig(request).configure(sendsketch_results_table_)
    except ObjectDoesNotExist:
        sendsketch_results_table_ = None
        sample = None
        base_project = None

    return render(request,
                  'new_multisample/sendsketch_results_table.html',
                  {'sendsketch_results_table': sendsketch_results_table_,
                   'project': sample,
                   'base_project': base_project
                   }
                  )


def find_paired_reads(filelist):
    pairs = list()
    for filename in filelist:
        if '_R1' in filename and filename.replace('_R1', '_R2') in filelist:
            pairs.append([filename, filename.replace('_R1', '_R2')])
    return pairs
