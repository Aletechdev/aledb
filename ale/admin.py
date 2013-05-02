from ale.models import *
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import mark_safe

def add_link_field(target_model = None, field = '', link_text = unicode):
    def add_link(cls):
        reverse_name = target_model or cls.model.__name__.lower()
        def link(self, instance):
            app_name = instance._meta.app_label
            reverse_path = "admin:%s_%s_change" % (app_name, reverse_name)
            link_obj = getattr(instance, field, None) or instance
            url = reverse(reverse_path, args = (link_obj.id,))
            return mark_safe("<a href='%s'>%s</a>" % (url, link_text(link_obj)))
        link.allow_tags = True
        link.short_description = reverse_name + ' link'
        cls.link = link
        cls.readonly_fields = list(getattr(cls, 'readonly_fields', [])) + ['link']
        return cls
    return add_link


# Each Flask should display related Isolates
@add_link_field()
class IsolateList(admin.TabularInline):
    model = Isolate
    extra = 1
    show_edit_link = True

    
class FlaskAdmin(admin.ModelAdmin):
    inlines = [IsolateList]
    extra = 0
    list_display = ("__unicode__", "ale_experiment", "ale_id", "flask_number", "media")
    list_filter = ("ale_id__ale_experiment", "ale_id", "flask_number")

# each AleId should display related Flasks
@add_link_field()
class FlaskList(admin.TabularInline):
    model = Flask
    extra = 0

class IsolateAdmin(admin.ModelAdmin):
    inlines = [FlaskList]
    list_display = ("__unicode__","isolate_number","flask")

class AleIdAdmin(admin.ModelAdmin):
    inlines = [FlaskList]
    list_display = ("__unicode__", "ale_experiment", "description")
    list_filter = ("ale_experiment", "description")
    #search_fields = ["ale_experiment__ale_id"]

# each AleExperiment should display related AleId's
@add_link_field()
class AleIdList(admin.TabularInline):
    model = AleId
    extra = 0

class AleExperimentAdmin(admin.ModelAdmin):
    inlines = [AleIdList]
    list_display = ("__unicode__", "ale_id", "date", "person", "instrument", "simulation", "notes")
    list_filter = ("simulation","instrument","person")
    search_fields = ["ale_id"]


class FreezerBoxAdmin(admin.ModelAdmin):
    inlines = [IsolateList]

admin.site.register(AleExperiment, AleExperimentAdmin)
admin.site.register(Instrument)
admin.site.register(Media)
admin.site.register(Flask, FlaskAdmin)
admin.site.register(Isolate, IsolateAdmin)
admin.site.register(AleId, AleIdAdmin)
admin.site.register(FreezerBox, FreezerBoxAdmin)
