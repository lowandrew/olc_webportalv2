from .models import Project
import django_tables2 as tables


class ProjectTable(tables.Table):
    class Meta:
        model = Project
        attrs = {'class': 'paleblue'}

