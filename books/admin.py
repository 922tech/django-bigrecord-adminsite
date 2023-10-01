from django.contrib import admin
from django.contrib.admin.views.main import ChangeList

from .models import Book
from django.core.paginator import Paginator
# from .utils import get_sql_searchparams


class BigRecordPaginator(Paginator):
    pass


class SearchOnlyChangeList(ChangeList):
    """
    This class provides an optimized way to make a change list for a django app.
    It shows am empty table that gets filled on search.
    It also uses raw SQL queries for optimization purposes.
    """

    def get_sql_searchparams(self, delim: str = 'OR') -> str:

        """
        This function is intended to be used for creating a query for searchnig in a model.
        param `model`: the django model to be searched. It should represent the db table that
                     will be searched.
        param `search_fields`: the table columns to be searched
        param `search_param`: the thing that you want to find in the db.
        param `delim`: a string containing keywords like `AND` , `OR` etc. that
                     comes amongst the conditions.

        example:
        ```
        get_sql_searchparams(Book, ['col1', 'col2'], 'plant')
        >>> 'UPPER(books_book.col1::text) LIKE %s AND UPPER(books_book.col2::text) LIKE %s '
        ```
        """

        table = self.opts.db_table
        search_fields = self.search_fields
        q = [f"LOWER({table}.{i}::text) LIKE LOWER(%s::text) " for i in search_fields]
        # Using LIKE was more efficient than ILIKE in the tests
        # Use of lower-casing along with  `LIKE` was a more
        # efficient way than using `ILIKE`
        length = len(q)
        for i in range(length):
            if i < length - 1:
                q[i] += delim + ' '
        return ''.join(q)

    def get_ordering_kwargs(self) -> str:
        """
        returns an `ORDER BY ...` SQL clause.
        Indirectly uses the `o` parameter of changelist request.GET
        (using `get_ordering_field_columns` method).

        sample output for a model that has fields:id, author, name:
        >>> "ORDER BY id asc, author asc, title asc"
        """

        order_enum = self.get_ordering_field_columns()
        kwargs = {self.list_display[i]: order_enum[i] for i in order_enum}
        kwargs_string = 'ORDER BY ' + ', '.join([f'{i} {kwargs[i]}' for i in kwargs])

        return kwargs_string

    def get_sql(self, order_code: str = '') -> str:
        """
        param `order_code`: a django coding for changelist ordering
        returns a complete sql query
        """

        searchparams = self.get_sql_searchparams()
        if order_code:
            ordering_params = self.get_ordering_kwargs()
        else:
            ordering_params = ''

        sql = str(self.root_queryset.query) + f' {self.opts.db_table}' + \
              ' WHERE ' + searchparams + ordering_params  # + ' LIMIT 100'
        return sql

    def get_search_queryset(self, sql_string, request_data):
        queryset = self.model.objects.raw(
            sql_string, [f'%{request_data["q"]}%'] * len(self.search_fields)
        )
        return queryset

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

            sql_string = self.get_sql(order_code)
            # query = self.model.objects.raw(
            #     sql_string, [f'%{request_data["q"]}%'] * len(self.search_fields)
            # )
            queryset = self.get_search_queryset(sql_string, request_data)
            return queryset

        else:
            return self.root_queryset.none()


@admin.register(Book)
class Admin(admin.ModelAdmin):
    show_full_result_count = False
    # to get rid of the count query
    list_display = ['id', 'title', 'serial_number', 'publication_date']
    lookup_fields = ['title']
    search_fields = ["title", 'serial_number']

    def get_changelist(self, request, **kwargs):
        # cl = self.get_changelist_instance(request)
        return SearchOnlyChangeList

    def get_changelist_instance(self, request):
        cl = super().get_changelist_instance(request)
        print(cl.queryset)
        return cl

# def get_paginator(
    #     self, request, queryset, per_page, orphans=0, allow_empty_first_page=True
    # ):
    #     cl = self.get_changelist_instance(request)
    #     return self.paginator(queryset, per_page, orphans, allow_empty_first_page)
    #     return self.paginator(cl.get_queryset(request), per_page, orphans, allow_empty_first_page)
