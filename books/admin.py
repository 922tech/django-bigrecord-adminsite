
from pprint import pprint
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.utils.translation import gettext as _

from .models import Book
from .utils import get_sql_searchparams, get_sql_ordering


class SearchOnlyChangeList(ChangeList):

    def get_ordering_kwargs(self, order_code):

        kwargs = {}
        for i in order_code.split('.'):
            index = abs(int(i))
            if i.startswith('-'):

                kwargs.update({self.list_display[index]: 'DESC'})
            else:
                kwargs.update({self.list_display[index]: 'ASC'})
        return kwargs

    def get_sql(self, querystring_dict, order_code=0):
        searchparams = get_sql_searchparams(
            self.model, self.search_fields, querystring_dict, delim='OR')

        if order_code:
            ordering_enum = self.get_ordering_kwargs(order_code)
            ordering_params = get_sql_ordering(ordering_enum)
        else:
            ordering_params = ''

        sql = str(self.root_queryset.query) + f' {self.model._meta.db_table}' + \
            ' WHERE ' + searchparams + ordering_params  # + ' LIMIT 100'
        return sql

    def get_queryset(self, request):
        request_data = request.GET
        print(self.get_ordering_field_columns())
        if 'q' in request_data:
            querystring_dict = request_data['q']

            if 'o' in request_data:
                order_code = request_data['o']
            else:
                order_code = 0

            SQL = self.get_sql(querystring_dict, order_code)
            query = self.model.objects.raw(
                SQL, [f'%{request_data["q"]}%']*len(self.search_fields))

            return query

        else:
            return self.root_queryset.none()


@admin.register(Book)
class Admin(admin.ModelAdmin):

    list_display = ['id', 'title', 'serial_number']
    lookup_fields = search_fields = ['title', 'serial_number', 'description']

    def get_changelist(self, request, **kwargs):
        """
        This logic cause rendering an empty table  on the app page
        in django admin site that gets filled by searching.
        Does not need to override the changelist_view method.
        """
        return SearchOnlyChangeList

    # def changelist_view0(self, request, extra_context=None):
    #     """
    #     This logic displays a form like django changeform
    #     by which a single record can be retrievd and the
    #     client will be redirected to the change form of that
    #     particular object.
    #     """

    #     error = False
    #     message = None
    #     obj = self.model()
    #     cl = self.get_changelist_instance(request)

    #     if not any(request.POST):
    #         self.fields = self.lookup_fields

    #     else:
    #         kwargs = {i: request.POST[i]
    #                   for i in self.lookup_fields if i in request.POST}
    #         print(get_sql_queryparams(self.model, kwargs))

    #         try:

    #             obj = self.model.objects.get(**kwargs)
    #             self.fields = get_field_names(self.model)
    #             object_id = obj.id

    #             # raw querying
    #             queryparams = get_sql_queryparams(self.model, kwargs)
    #             SQL = self.model.objects.raw
    #             l = SQL(
    #                 f'SELECT * FROM {self.model._meta.db_table} WHERE ' + queryparams
    #             )
    #             object_id = list(l)[0].id
    #             return redirect("%s/change" % object_id)

    #         except self.model.DoesNotExist:
    #             print(f'No record found with {kwargs}!')
    #             obj = self.model()
    #             message = 'No record found with %s!' % kwargs
    #             error = True

    #     fieldsets = self.get_fieldsets(request, obj)
    #     ModelForm = self.get_form(
    #         request, obj, change=False, fields=utils.flatten_fieldsets(fieldsets)
    #     )
    #     form = ModelForm(instance=obj)
    #     admin_form = helpers.AdminForm(
    #         form,
    #         list(fieldsets),
    #         self.get_prepopulated_fields(request, obj)
    #         if self.has_change_permission(request, obj)
    #         else {},
    #         [],
    #         model_admin=self,
    #     )

    #     cl.formset = None

    #     context = {
    #         **self.admin_site.each_context(request),
    #         "cl": cl,
    #         "title": cl.title,
    #         "opts": cl.opts,
    #         "adminform": admin_form,
    #         "model_name": self.model._meta.verbose_name,
    #         "module_name": str(self.opts.verbose_name_plural),
    #         "has_view_permission": self.has_view_permission(request),
    #         "not_found_message": message,
    #         "errors": error
    #     }

    #     return TemplateResponse(
    #         request,
    #         [
    #             # "admin/%s/%s/change_list.html" % (app_label, self.opts.model_name),
    #             # "admin/%s/change_list.html" % app_label,
    #             "custome_changeform.html",
    #         ],
    #         context,
    #     )
