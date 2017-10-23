import os

from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from django_tables2 import RequestConfig

from . import tasks
from .forms import ProjectForm
from .models import Project, GenesipprResults
from .table import ProjectTable, GenesipprTable


@login_required
def projects(request):
    project_list = Project.objects.all()
    form = ProjectForm(request.POST, request.FILES)

    # Configure the table
    # project_table = ProjectTable(Project.objects.all())
    # RequestConfig(request).configure(project_table)

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

                # Create GenesipprResults entry
                GenesipprResults.objects.get_or_create(project=Project.objects.get(id=new_entry.pk))
                print('\nCreated GenesipprResults entry for project {}'.format(new_entry.pk))

                # Set file path
                file_path = os.path.dirname(str(new_entry.file_R1))

                # Update model status for the detail.html page
                # This would be nice but I can't get the model in tasks.py to update...
                # Project.objects.filter(pk=new_entry.pk).update(genesippr_status="Queued")
                Project.objects.filter(pk=new_entry.pk).update(genesippr_status="Processing")

                # # Queue genesippr task
                tasks.run_genesippr(file_path=file_path,
                                    proj_pk=new_entry.pk)

            if 'sendsketch' in new_entry.requested_jobs:
                print('\nSendsketch job detected.')

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

    return render(request, 'projects/projects.html', {'project_list': project_list,
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

    return render(request, 'projects/detail.html', {'project_id': project_id,
                                                    }
                  )


@login_required
def project_table(request, project_id):
    # Configure the table
    project_id = Project.objects.get(pk=project_id)
    project_table = ProjectTable(Project.objects.all())
    RequestConfig(request).configure(project_table)

    return render(request, 'projects/project_table.html', {'project_table': project_table,
                                                           'project_id': project_id,
                                                           }
                  )


@login_required
def genesippr_results_table(request, project_id):
    # Configure the table
    project = GenesipprResults.objects.get(project=Project.objects.get(pk=project_id))
    genesippr_results_table = GenesipprTable(GenesipprResults.objects.all())
    RequestConfig(request).configure(genesippr_results_table)

    return render(request, 'projects/genesippr_results_table.html', {'genesippr_results_table': genesippr_results_table,
                                                                     'project': project,
                                                                     }
                  )
