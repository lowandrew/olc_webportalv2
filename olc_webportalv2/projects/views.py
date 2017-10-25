import os

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from django_tables2 import RequestConfig

from . import tasks
from .forms import ProjectForm
from .models import Project, \
    GenesipprResults, \
    SendsketchResults, \
    GenesipprResultsSixteens, \
    GenesipprResultsGDCS, \
    GenesipprResultsSerosippr

from .table import ProjectTable, \
    GenesipprTable, \
    SendsketchTable, \
    GDCSTable, \
    SixteensTable, \
    SerosipprTable


@login_required
def projects(request):
    project_list = Project.objects.all()
    form = ProjectForm(request.POST, request.FILES)

    # Create new project
    if request.method == 'POST':
        if form.is_valid():
            print('Form is valid.\n')

            # Have to do this in order to set the user to current logged in user
            new_entry = form.save(commit=False)

            # Pull active user
            new_entry.user = request.user

            # Save the form
            new_entry = form.save()

            # Debug
            print('PK: {}, User: {}'.format(new_entry.pk, new_entry.user))
            print('File 1: {}\nFile 2: {}'.format(new_entry.file_R1, new_entry.file_R2))
            print('Requested jobs: {} for project {}'.format(new_entry.requested_jobs, new_entry.pk))

            # Check jobs
            if 'genesipprv2' in new_entry.requested_jobs:
                print('\nGenesipprV2 job detected.')

                # Create Genesippr entries entry
                GenesipprResults.objects.get_or_create(project=Project.objects.get(id=new_entry.pk))
                GenesipprResultsGDCS.objects.get_or_create(project=Project.objects.get(id=new_entry.pk))
                GenesipprResultsSixteens.objects.get_or_create(project=Project.objects.get(id=new_entry.pk))
                GenesipprResultsSerosippr.objects.get_or_create(project=Project.objects.get(id=new_entry.pk))
                print('\nCreated GenesipprV2 table entries for project {}'.format(new_entry.pk))

                # Set file path
                file_path = os.path.dirname(str(new_entry.file_R1))

                # Set status
                Project.objects.filter(pk=new_entry.pk).update(genesippr_status="Processing")

                # Queue genesippr task
                tasks.run_genesippr(file_path=file_path,
                                    proj_pk=new_entry.pk)

            if 'sendsketch' in new_entry.requested_jobs:
                print('\nSendsketch job detected.')

                # Create SendsketchResults entry
                SendsketchResults.objects.get_or_create(project=Project.objects.get(id=new_entry.pk))
                print('\nCreated SendsketchResults entry for project {}'.format(new_entry.pk))

                file_path = os.path.dirname(str(new_entry.file_R1))

                Project.objects.filter(pk=new_entry.pk).update(sendsketch_status="Processing")

                # Queue sendsketch task
                tasks.run_sendsketch(read1=new_entry.file_R1.name,
                                     read2=new_entry.file_R1.name,
                                     proj_pk=new_entry.pk,
                                     file_path=file_path)

            return redirect('project/{}'.format(new_entry.pk))
        else:
            raise ValidationError(
                'Form is not valid. Please ensure the file type for your reads are fastq or fastq.gz.'
            )

    return render(request,
                  'projects/projects.html',
                  {'project_list': project_list,
                   'form': form,
                   'project_id': Project.pk,
                   'user': request.user,
                   }
                  )


@login_required
def project_detail(request, project_id):
    try:
        project_id = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        raise Http404("Project ID {} does not exist.".format(project_id))

    return render(request,
                  'projects/detail.html',
                  {'project_id': project_id,
                   }
                  )


@login_required
def project_table(request, project_id):
    project_id = Project.objects.get(pk=project_id)
    project_table_ = ProjectTable(Project.objects.all())
    try:
        RequestConfig(request).configure(project_table)
    except AttributeError:
        pass

    return render(request,
                  'projects/project_table.html',
                  {'project_table': project_table_,
                   'project_id': project_id,
                   }
                  )


@login_required
def job_status_table(request, project_id):

    project_id = Project.objects.get(pk=project_id)
    job_status_table_ = ProjectTable(Project.objects.all())
    try:
        RequestConfig(request).configure(job_status_table_)
    except AttributeError:
        pass

    return render(request,
                  'projects/job_status_table.html',
                  {'job_status_table': job_status_table_,
                   'project_id': project_id,
                   }
                  )


@login_required
def genesippr_results_table(request, project_id):
    try:
        # Grab the base project
        base_project = Project.objects.get(pk=project_id)

        # Get GenesipprResults project
        genesippr_project = GenesipprResults.objects.get(project=base_project)
        gdcs_project = GenesipprResultsGDCS.objects.get(project=base_project)
        sixteens_project = GenesipprResultsSixteens.objects.get(project=base_project)
        serosippr_project = GenesipprResultsSerosippr.objects.get(project=base_project)

        # Genesippr Multi-table setup
        genesippr_results_table_ = GenesipprTable(GenesipprResults.objects.all())
        gdcs_results_table_ = GDCSTable(GenesipprResultsGDCS.objects.all())
        sixteens_results_table_ = SixteensTable(GenesipprResultsSixteens.objects.all())
        serosippr_results_table_ = SerosipprTable(GenesipprResultsSerosippr.objects.all())

        # Config tables
        RequestConfig(request).configure(genesippr_results_table_)
        RequestConfig(request).configure(gdcs_results_table_)
        RequestConfig(request).configure(sixteens_results_table_)
        RequestConfig(request).configure(serosippr_results_table_)

    except ObjectDoesNotExist:
        genesippr_results_table_ = gdcs_results_table_ = sixteens_results_table_ = serosippr_results_table_ = None
        genesippr_project = gdcs_project = sixteens_project = serosippr_project = None
        base_project = None

    return render(request,
                  'projects/genesippr_results_table.html',
                  {'genesippr_results_table': genesippr_results_table_,
                   'gdcs_results_table': gdcs_results_table_,
                   'sixteens_results_table': sixteens_results_table_,
                   'serosippr_results_table': serosippr_results_table_,
                   'genesippr_project': genesippr_project,
                   'gdcs_project': gdcs_project,
                   'sixteens_project': sixteens_project,
                   'serosippr_project': serosippr_project,
                   'base_project': base_project
                   }
                  )


@login_required
def sendsketch_results_table(request, project_id):
    # TODO: Sort the project queryset by ANI

    try:
        project = SendsketchResults.objects.filter(project=Project.objects.get(pk=project_id))
        sendsketch_results_table_ = SendsketchTable(SendsketchResults.objects.all())
        base_project = Project.objects.get(pk=project_id)
        RequestConfig(request).configure(sendsketch_results_table_)
    except ObjectDoesNotExist:
        sendsketch_results_table_ = None
        project = None
        base_project = None

    return render(request,
                  'projects/sendsketch_results_table.html',
                  {'sendsketch_results_table': sendsketch_results_table_,
                   'project': project,
                   'base_project': base_project
                   }
                  )
