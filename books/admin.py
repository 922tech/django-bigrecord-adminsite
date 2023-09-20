from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.forms import ModelForm
from django.http.request import HttpRequest
from django.contrib.admin.options import modelform_factory
# import django.http.request
# from django.contrib import messages
# from django.contrib.admin.decorators import display
# from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.core.exceptions import (
    PermissionDenied,
)
from django.http.response import HttpResponse
from django.template.response import TemplateResponse, HttpResponse
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.contrib.admin import helpers, utils
from urllib.parse import quote as urlquote
from django.utils.html import format_html
import json
from django.core.serializers import serialize
from .models import Book


class IncorrectLookupParameters(Exception):
    pass

csrf_protect_m = method_decorator(csrf_protect)

@admin.register(Book)
class Admin(admin.ModelAdmin):
    # fields = ['title', 'serial_number']
    
    lookup_fields = ['title']
    
    

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return Book.objects.none()
    
    def changelist_view(self, request, extra_context=None):
        if not request.POST:

            obj = self.model()
        else:
            kwargs = {i:request.POST[i] for i in self.lookup_fields if request.POST[i]}
            print(kwargs)
            obj = self.model.objects.get(**kwargs)

            

        fieldsets = self.get_fieldsets(request, obj)
        ModelForm = self.get_form(
            request, obj, change=False, fields=utils.flatten_fieldsets(fieldsets)
        )
        form = ModelForm(instance=obj)
        adminForm = helpers.AdminForm(
            form,
            list(fieldsets),
            # Clear prepopulated fields on a view-only form to avoid a crash.
            self.get_prepopulated_fields(request, obj)
            if  self.has_change_permission(request, obj)
            else {},
            [],
            model_admin=self,
        )
        # form = ModelForm(instance=obj)
        add = False
        admin_form  = helpers.AdminForm(
            form,
            list(fieldsets),
            self.get_prepopulated_fields(request, obj)
            if add or self.has_change_permission(request, obj)
            else {},
            [],
            model_admin=self,
        )

        cl = self.get_changelist_instance(request)

        cl.formset = None

        app_label = self.opts.app_label

        selection_note_all = ngettext(
            "%(total_count)s selected", "All %(total_count)s selected", cl.result_count
        )

        context = {
        **self.admin_site.each_context(request),
        "cl": cl,
        "title": cl.title,
        "opts": cl.opts,
        "adminform":admin_form,
        "model_name": self.model._meta.verbose_name,
        "module_name": str(self.opts.verbose_name_plural),
        "has_view_permission": self.has_view_permission(request),

        # "preserved_filters": self.get_preserved_filters(request),
        # "selection_note": _("0 of %(cnt)s selected") % {"cnt": len(cl.result_list)},
        # "selection_note_all": selection_note_all % {"total_count": cl.result_count},
        # "subtitle": None,
        # "is_popup": cl.is_popup,
        # "to_field": cl.to_field,
        # "media": None,
        # "action_form": None,
        # "actions_on_top": self.actions_on_top,
        # "actions_on_bottom": self.actions_on_bottom,
        # "actions_selection_counter": self.actions_selection_counter,

         }

        return TemplateResponse(
            request,
            [
                # "admin/%s/%s/change_list.html" % (app_label, self.opts.model_name),
                # "admin/%s/change_list.html" % app_label,
                "custome_changeform.html",
            ],
            context,
        )



    '''TODO: review `render_change_form` for checking permissions and submit-row'''
