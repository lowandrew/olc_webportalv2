from django.shortcuts import render, get_object_or_404
import os
import pandas as pd

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

    if request.method == 'POST':
        # form = SampleForm(request.POST)
        files = request.FILES.getlist('files')
        filenames = list()
        file_dict = dict()
        forward_id = request.POST['Forward_ID']
        reverse_id = request.POST['Reverse_ID']
        ProjectMulti.objects.filter(pk=project_id).update(forward_id=forward_id)
        ProjectMulti.objects.filter(pk=project_id).update(reverse_id=forward_id)
        for item in files:
            if item.name.endswith('.fastq') or item.name.endswith('.fastq.gz'):
                filenames.append(item.name)
                file_dict[item.name] = item

        pairs = find_paired_reads(filenames, forward_id=forward_id, reverse_id=reverse_id)
        for pair in pairs:
            sample_name = pair[0].split(forward_id)[0]
            instance = Sample(file_R1=file_dict[pair[0]],
                              file_R2=file_dict[pair[1]],
                              title=sample_name,
                              project=project)
            instance.save()

        return redirect('new_multisample:project_detail', project_id=project_id)
    else:
        return render(request,
                      'new_multisample/upload_samples.html',
                      {'project': project},
                      )


@login_required
def project_detail(request, project_id):
    project = get_object_or_404(ProjectMulti, pk=project_id)
    # try:
    #     project_id = ProjectMulti.objects.get(pk=project_id)
    # except ProjectMulti.DoesNotExist:
    #     raise Http404("Project ID {} does not exist.".format(project_id))
    if request.method == 'POST':
        form = JobForm(request.POST)
        # Save the form
        if form.is_valid():
            jobs_to_run = form.cleaned_data.get('jobs')
            print(jobs_to_run)
            if 'sendsketch' in jobs_to_run:
                for sample in project.samples.all():
                    if sample.sendsketch_status != 'Complete':
                        file_path = os.path.dirname(str(sample.file_R1))
                        Sample.objects.filter(pk=sample.pk).update(sendsketch_status="Processing")
                        tasks.run_sendsketch(read1=sample.file_R1.name,
                                             read2=sample.file_R2.name,
                                             sample_pk=sample.pk,
                                             file_path=file_path)
            if 'genesipprv2' in jobs_to_run:
                for sample in project.samples.all():
                    if sample.genesippr_status != 'Complete':
                        Sample.objects.filter(pk=sample.pk).update(genesippr_status="Processing")
                tasks.run_genesippr(project_id=project.pk)

            if 'confindr' in jobs_to_run:
                for sample in project.samples.all():
                    if sample.confindr_status != 'Complete':
                        Sample.objects.filter(pk=sample.pk).update(confindr_status="Processing")
                tasks.run_confindr(project_id=project.pk)
            form = JobForm()

    else:
         form = JobForm()
    return render(request,
                  'new_multisample/project_detail.html',
                  {'project': project,
                   'form': form,
                   'user': request.user},
                  )

@login_required
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


@login_required
def confindr_results_table(request, project_id):
    project = get_object_or_404(ProjectMulti, pk=project_id)
    return render(request,
                  'new_multisample/confindr_results_table.html',
                  {'project': project},
                  )


@login_required
def display_genesippr_results(request, project_id):
    project = get_object_or_404(ProjectMulti, pk=project_id)
    if project.results_created == 'True':
        genesippr_data = pd.read_csv(project.genesippr_file).dropna(axis=1, how='all').fillna('')
        genesippr_data_html = genesippr_data.to_html(classes=['table', 'table-hover', 'table-bordered'])
        # serosippr_data = pd.read_csv(project.serosippr_file).fillna('')
        # serosippr_data_html = serosippr_data.to_html(classes=['table', 'table-hover', 'table-bordered'])
        gdcs_data = pd.read_csv(project.gdcs_file).fillna('')
        gdcs_data = gdcs_data[['Strain', 'Genus', 'Matches', 'MeanCoverage', 'Pass/Fail']]
        gdcs_data_html = gdcs_data.to_html(classes=['table', 'table-hover', 'table-bordered'])
        sixteens_data = pd.read_csv(project.sixteens_file).fillna('')
        sixteens_data_html = sixteens_data.to_html(classes=['table', 'table-hover', 'table-bordered'])
        return render(request,
                      'new_multisample/display_genesippr_results.html',
                      {'project': project,
                       'genesippr_data': genesippr_data_html,
                       'sixteens_data': sixteens_data_html,
                       'gdcs_data': gdcs_data_html},
                       # 'serosippr_data': serosippr_data_html},
                      )
    else:
        return render(request,
                      'new_multisample/display_genesippr_results.html',
                      {'project': project},
                      )

@login_required
def project_remove(request, project_id):
    project = get_object_or_404(ProjectMulti, pk=project_id)
    project.delete()
    return redirect('new_multisample:new_multisample')


@login_required
def project_remove_confirm(request, project_id):
    project = get_object_or_404(ProjectMulti, pk=project_id)
    return render(request,
                  'new_multisample/confirm_project_delete.html',
                  {'project': project},
                  )


@login_required
def sample_remove(request, sample_id):
    sample = get_object_or_404(Sample, pk=sample_id)
    project = get_object_or_404(ProjectMulti, pk=sample.project.id)
    sample.delete()
    return redirect('new_multisample:project_detail', project_id=project.id)


@login_required
def sample_remove_confirm(request, sample_id):
    sample = get_object_or_404(Sample, pk=sample_id)
    project = get_object_or_404(ProjectMulti, pk=sample.project.id)
    return render(request,
                  'new_multisample/confirm_sample_delete.html',
                  {'sample': sample,
                   'project': project},
                  )


def find_paired_reads(filelist, forward_id='_R1', reverse_id='_R2'):
    pairs = list()
    for filename in filelist:
        if forward_id in filename and filename.replace(forward_id, reverse_id) in filelist:
            pairs.append([filename, filename.replace(forward_id, reverse_id)])
    return pairs
