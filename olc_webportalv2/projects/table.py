import django_tables2 as tables

from .models import Project, \
    GenesipprResults, \
    SendsketchResults, \
    GenesipprResultsGDCS, \
    GenesipprResultsSixteens, \
    GenesipprResultsSerosippr


################################
# --------- PROJECTS --------- #
################################
class ProjectTable(tables.Table):
    class Meta:
        model = Project
        attrs = {'class': 'paleblue'}


###################################
# -------- GENESIPPRV2 ---------- #
###################################
class GenesipprTable(tables.Table):
    class Meta:
        model = GenesipprResults
        attrs = {'class': 'paleblue'}


class GDCSTable(tables.Table):
    class Meta:
        model = GenesipprResultsGDCS
        attrs = {'class': 'paleblue'}


class SixteensTable(tables.Table):
    class Meta:
        model = GenesipprResultsSixteens
        attrs = {'class': 'paleblue'}


class SerosipprTable(tables.Table):
    class Meta:
        model = GenesipprResultsSerosippr
        attrs = {'class': 'paleblue'}


###################################
# --------- SENDSKETCH ---------- #
###################################
class SendsketchTable(tables.Table):
    class Meta:
        model = SendsketchResults
        attrs = {'class': 'paleblue'}
