# coding: utf-8
from __future__ import unicode_literals

import django_tables2 as tables
from .models import Project, AleExperiment


class ProjectTable(tables.Table):
    name = tables.Column(linkify=True, order_by=("name",))
    owner = tables.Column()
    date = tables.Column(verbose_name="Created Date")
    description = tables.Column()

    class Meta:
        model = Project
        template_name = "django_tables2/bootstrap.html"
        attrs = {"class": "table table-hover"}
        fields = ("name", "owner", "date", "description")


class ExperimentTable(tables.Table):
    select = tables.CheckBoxColumn(empty_values=(), footer="")
    name = tables.Column(linkify=True, order_by=("name",))
    project = tables.Column(linkify=True)

    class Meta:
        model = AleExperiment
        template_name = "django_tables2/bootstrap.html"
        attrs = {"class": "table table-hover"}
        fields = ("select", "name", "project", "person", "date", "notes")
