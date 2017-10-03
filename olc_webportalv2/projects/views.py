from django.shortcuts import render, redirect
from django.http import Http404
from .models import Project
from django.core.exceptions import ValidationError
from .forms import ProjectForm
from .table import ProjectTable
from django_tables2 import RequestConfig
from ..jobs import tasks
import os


def projects(request):
    project_list = Project.objects.all()
    form = ProjectForm(request.POST, request.FILES)

    # Configure the table
    project_table = ProjectTable(Project.objects.all())
    RequestConfig(request).configure(project_table)

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
            print('Requested jobs: {}'.format(new_entry.requested_jobs))

            # Check jobs
            if 'genesipprv2' in new_entry.requested_jobs:
                print('Requested GenesipprV2 job on project {}'.format(new_entry.pk))
                file_path = os.path.dirname(str(new_entry.file_R1))
                print("File path: " + file_path)
                tasks.run_genesippr.now(file_path)

            return redirect('project/{}'.format(new_entry.pk))
        else:
            raise ValidationError(
                'Form is not valid. Try again.'
            )

    return render(request, 'projects/projects.html', {'project_list': project_list,
                                                      'form': form,
                                                      'project_id': Project.pk,
                                                      'user': request.user,
                                                      'project_table': project_table
                                                      }
                  )


def project_detail(request, project_id):
    try:
        project_id = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        raise Http404("Project ID {} does not exist.".format(project_id))

    return render(request, 'projects/detail.html', {'project_id': project_id})
