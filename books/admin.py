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
        kwargs = {self.list_display[i]: order_enum[i] for i in order_enum}
        kwargs_string = 'ORDER BY ' + ', '.join([f'{i} {kwargs[i]}' for i in kwargs])
        return kwargs_string

    def get_sql(self, querystring_dict: dict, order_code: str = '') -> str:
        """
        param `querystring_dict`: a dictionary extracted form querystring
        param `order_code`: a django coding for changelist ordering
        returns a complete sql query
        """

        searchparams = get_sql_searchparams(
            self.model, self.search_fields, querystring_dict, delim='OR')

        if order_code:
            ordering_params = self.get_ordering_kwargs()
        else:
            ordering_params = ''

        sql = str(self.root_queryset.query) + f' {self.opts.db_table}' + \
              ' WHERE ' + searchparams + ordering_params  # + ' LIMIT 100'
        return sql

    def get_queryset(self, request):
        """
        The main logic of the class lays here.
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
                SQL, [f'%{request_data["q"]}%'] * len(self.search_fields))

            return query

        else:
            return self.root_queryset.none()


@admin.register(Book)
class Admin(admin.ModelAdmin):
    list_display = ['id', 'title', 'serial_number', 'publication_date']
    lookup_fields = search_fields = ['title', 'serial_number', 'description', 'publication_date']

    def get_changelist(self, request, **kwargs):
        return SearchOnlyChangeList
