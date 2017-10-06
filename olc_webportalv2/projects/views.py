import os

from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import render, redirect
from django_tables2 import RequestConfig

from . import tasks
from .forms import ProjectForm
from .models import Project, GenesipprResults
from .table import ProjectTable, GenesipprTable


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
            print('Requested jobs: {} for project {}\n'.format(new_entry.requested_jobs, new_entry.pk))

            # Check jobs
            if 'genesipprv2' in new_entry.requested_jobs:
                file_path = os.path.dirname(str(new_entry.file_R1))

                # Update model status for the detail.html page

                # This would be nice but I can't get the model in tasks.py to update...
                # Project.objects.filter(pk=new_entry.pk).update(genesippr_status="Queued")

                Project.objects.filter(pk=new_entry.pk).update(genesippr_status="Processing")

                # Queue up the genesippr job
                tasks.run_genesippr(file_path, new_entry.pk)

            return redirect('project/{}'.format(new_entry.pk))
        else:
            raise ValidationError(
                'Form is not valid. Try again.'
            )

    return render(request, 'projects/projects.html', {'project_list': project_list,
                                                      'form': form,
                                                      'project_id': Project.pk,
                                                      'user': request.user,
                                                      }
                  )


def project_detail(request, project_id):
    try:
        project_id = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        raise Http404("Project ID {} does not exist.".format(project_id))

    return render(request, 'projects/detail.html', {'project_id': project_id,
                                                    }
                  )


def project_table(request, project_id):
    # Configure the table
    project_id = Project.objects.get(pk=project_id)
    project_table = ProjectTable(Project.objects.all())
    RequestConfig(request).configure(project_table)

    return render(request, 'projects/project_table.html', {'project_table': project_table,
                                                           'project_id': project_id,
                                                           }
                  )


def genesippr_results_table(request, project_id):
    # Configure the table
    project = GenesipprResults.objects.get(project=Project.objects.get(pk=project_id))
    genesippr_results_table = GenesipprTable(GenesipprResults.objects.all())
    RequestConfig(request).configure(genesippr_results_table)

    return render(request, 'projects/genesippr_results_table.html', {'genesippr_results_table': genesippr_results_table,
                                                                     'project': project,
                                                                     }
                  )
