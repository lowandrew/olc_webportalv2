from django.contrib import admin
from .models import Project, \
    GenesipprResults, \
    SendsketchResults, \
    GenesipprResultsGDCS, \
    GenesipprResultsSixteens, \
    GenesipprResultsSerosippr

# Register your models here.
admin.site.register(Project)
admin.site.register(GenesipprResults)
admin.site.register(SendsketchResults)
admin.site.register(GenesipprResultsGDCS)
admin.site.register(GenesipprResultsSixteens)
admin.site.register(GenesipprResultsSerosippr)
