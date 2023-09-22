from typing import Any
from urllib.parse import quote as urlquote
from pprint import pprint as print


from django.contrib import admin, messages
from django.contrib.admin import helpers, utils
from django.contrib.admin.options import (IS_POPUP_VAR, TO_FIELD_VAR,
                                          IncorrectLookupParameters)
# from django.contrib.admin.options import modelform_factory
# import django.http.request
# from django.contrib import messages
# from django.contrib.admin.decorators import display
# from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
# from django.core.exceptions import PermissionDenied
from django.contrib.admin.views.main import ChangeList
from django.core.exceptions import (FieldDoesNotExist, ImproperlyConfigured,
                                    PermissionDenied, SuspiciousOperation)
from django.core.paginator import InvalidPage
from django.core.serializers import serialize
from django.db.models import Exists, F, Field, ManyToOneRel, OrderBy, OuterRef
from django.db.models.expressions import Combinable
from django.db.models.query import QuerySet
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.template.response import (HttpResponse, SimpleTemplateResponse,
                                      TemplateResponse)
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.utils.http import urlencode
from django.utils.timezone import make_aware
from django.utils.translation import gettext
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import redirect

from .models import Book
from .utils import get_field_names, get_sql_queryparams

csrf_protect_m = method_decorator(csrf_protect)


class SearchOnlyChangeList(ChangeList):
    def get_queryset(self, request):
        try:
            request.GET['q']
        except:
            return self.root_queryset.none()
        return super().get_queryset(request)


@admin.register(Book)
class Admin(admin.ModelAdmin):
    list_display = ['id', 'title', 'serial_number']
    lookup_fields = search_fields = ['title', 'serial_number']

    def get_changelist0(self, request, **kwargs):
        """
        This logic renders an empty table that gets filled by searching.
        Does not need to override the changelist_view method.
        """
        return SearchOnlyChangeList

    def changelist_view(self, request, extra_context=None):
        """
        This logic displays a form like django changeform 
        by which a single record can be retrievd and the 
        client will be redirected to the change form of that
        particular object.
        """
        # TODO: exception handling while more than one value is fetched
        # TODO: raw the queries
        # TODO: refactor
        error = False
        message = None
        obj = self.model()
        cl = self.get_changelist_instance(request)

        if not any(request.POST):
            self.fields = self.lookup_fields

        else:
            kwargs = {i: request.POST[i]
                      for i in self.lookup_fields if i in request.POST}
            print(get_sql_queryparams(self.model, self.lookup_fields))

            try:
                obj = self.model.objects.get(**kwargs)
                self.fields = get_field_names(self.model)
                return redirect("%s/change" % (obj.id))

            except self.model.DoesNotExist:
                obj = self.model()
                message = 'No record found with %s!' % kwargs
                error = True

        fieldsets = self.get_fieldsets(request, obj)
        ModelForm = self.get_form(
            request, obj, change=False, fields=utils.flatten_fieldsets(fieldsets)
        )
        form = ModelForm(instance=obj)
        admin_form = helpers.AdminForm(
            form,
            list(fieldsets),
            self.get_prepopulated_fields(request, obj)
            if self.has_change_permission(request, obj)
            else {},
            [],
            model_admin=self,
        )

        cl.formset = None
        context = {
            **self.admin_site.each_context(request),
            "cl": cl,
            "title": cl.title,
            "opts": cl.opts,
            "adminform": admin_form,
            "model_name": self.model._meta.verbose_name,
            "module_name": str(self.opts.verbose_name_plural),
            "has_view_permission": self.has_view_permission(request),
            "not_found_message": message,
            "errors": error
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
