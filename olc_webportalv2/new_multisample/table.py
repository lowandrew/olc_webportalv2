import django_tables2 as tables

from .models import SendsketchResult


class SendsketchTable(tables.Table):
    class Meta:
        model = SendsketchResult
        attrs = {'class': 'paleblue'}
