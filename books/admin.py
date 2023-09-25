
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.utils.translation import gettext as _

from .models import Book
from .utils import get_sql_searchparams


class SearchOnlyChangeList(ChangeList):
    """
    This class provides an optimized way to make a change list for a django app.
    It shows am empty table that gets filled on search.
    It also uses raw SQL queries for optimization purposes.
    """

    def get_ordering_kwargs(self) -> str:
        """
        returns an `ORDER BY ...` SQL clause.
        Indirectly uses the `o` parameter of changelist request.GET
        (using `get_ordering_field_columns` method). 
        """

        order_enum = self.get_ordering_field_columns()
        kwargs = {self.list_display[i]:order_enum[i] for i in order_enum}
        kwargs_string = 'ORDER BY ' + ', '.join([f'{i} {kwargs[i]}' for i in kwargs])
        return kwargs_string

    def get_sql(self, querystring_dict: dict, order_code: str='') -> str:
        """
        param querystring_dict: a dictionary extracted form querystring
        param oreder_code: a django coding for changelist ordering
        returns a complete sql query
        """

        searchparams = get_sql_searchparams(
            self.model, self.search_fields, querystring_dict, delim='OR')

        if order_code:
            ordering_params = self.get_ordering_kwargs()
        else:
            ordering_params = ''

        sql = str(self.root_queryset.query) + f' {self.model._meta.db_table}' + \
            ' WHERE ' + searchparams + ordering_params  # + ' LIMIT 100'
        return sql

    def get_queryset(self, request):
        """
        The main logic of the class is here.
        """
        request_data = request.GET
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
