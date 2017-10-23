from .models import Project, GenesipprResults, SendsketchResults
import django_tables2 as tables


class ProjectTable(tables.Table):
    class Meta:
        model = Project
        attrs = {'class': 'paleblue'}


class GenesipprTable(tables.Table):
    class Meta:
        model = GenesipprResults
        attrs = {'class': 'paleblue'}


class SendsketchTable(tables.Table):
    class Meta:
        model = SendsketchResults
        attrs = {'class': 'paleblue'}
