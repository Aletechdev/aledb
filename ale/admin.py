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


# Each FrozenPopulation should display related Isolates
@add_link_field()
class IsolateList(admin.TabularInline):
    model = Isolate
    extra = 1
    show_edit_link = True

class FrozenPopulationAdmin(admin.ModelAdmin):
    inlines = [IsolateList]

# each AleId should display related FrozenPopulations
@add_link_field()
class FrozenPopulationList(admin.TabularInline):
    model = FrozenPopulation
    extra = 0

class AleIdAdmin(admin.ModelAdmin):
    inlines = [FrozenPopulationList]
    list_display = ("__unicode__", "ale_experiment", "parent_strain")
    list_filter = ("ale_experiment", "parent_strain")
    search_fields = ["ale_experiment__ale_id"]

# each AleExperiment should display related AleId's
@add_link_field()
class AleIdList(admin.TabularInline):
    model = AleId
    extra = 9

class AleExperimentAdmin(admin.ModelAdmin):
    inlines = [AleIdList]


admin.site.register(AleExperiment, AleExperimentAdmin)
admin.site.register(Instrument)
admin.site.register(Media)
admin.site.register(FrozenPopulation, FrozenPopulationAdmin)
admin.site.register(Isolate)
admin.site.register(AleId, AleIdAdmin)
