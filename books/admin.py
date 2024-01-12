from typing import Sequence
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.utils.functional import cached_property
from django.core.paginator import Paginator
from django.db import connection
from django.core.paginator import InvalidPage
from django.contrib.admin.options import IncorrectLookupParameters
from .models import Book, Author
from .utils import get_field_verbose_names, get_field_names


class SearchOnlyChangeList(ChangeList):
    """
    This class provides an optimized way to make a change list for a django app.
    It shows am empty table that gets filled on search.
    It also uses raw SQL queries for optimization purposes.
    """

    def __init__(self, *args, **kwargs):
        self.search_result_count = 0
        super().__init__(*args, **kwargs)
        self.lookup_field = None

    @property
    def related_fields(self):
        return [
            i.split('__') for i in self.search_fields if '__' in i
        ]

    @staticmethod
    def get_join_clause(seq: Sequence):
        """
        param seq: sequence of related fields to join
        e.g. 
        >>> get_join_clause([''])
        """
        return ' '.join('JOIN ')

    @property
    def all_fields(self):
        """
        Returns all field names on a model in a list
        """
        return get_field_names(self.model)

    @property
    def all_fields_verbose_names(self):
        return get_field_verbose_names(self.model)

    @property
    def fields_enumeration(self):
        return enumerate(self.search_fields)

    def set_search_fields(self, search_field_index=0):
        self.search_fields = [self.all_fields[search_field_index]]
        self.model_admin.search_fields = [self.all_fields[search_field_index]]

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
        >>> 'LOWER(books_book.col1::text) LIKE %s AND LOWER(books_book.col2::text) LIKE %s '
        ```
        """

        table = self.opts.db_table
        search_fields = self.search_fields
        q = [
            f"LOWER({table}.{i}::text) LIKE LOWER(%s::text) " for i in search_fields]
        # Using LIKE was more efficient than ILIKE in the benchmark
        # Use of lower-casing along with  `LIKE` was a more efficient way than using `ILIKE`
        length = len(q)
        for i in range(length):
            if i < length - 1:
                q[i] += delim + ' '
        return ''.join(q)

    def get_search_clause(self, field):
        table = self.opts.db_table
        return f"LOWER({table}.{field}::text) LIKE LOWER(%s::text) "

    def get_ordering_kwargs(self) -> str:
        """
        returns an `ORDER BY ...` SQL clause.
        Indirectly uses the `o` parameter of changelist request.GET
        (using `get_ordering_field_columns` method).

        sample output for a model that has fields: id, author, name:
        >>> "ORDER BY id asc, author asc, title asc"
        """

        order_enum = self.get_ordering_field_columns()
        kwargs = {self.list_display[i]: order_enum[i] for i in order_enum}
        kwargs_string = 'ORDER BY ' + \
            ', '.join([f'{i} {kwargs[i]}' for i in kwargs])

        return kwargs_string

    def get_sql(self, order_code: str = '', page_number: int = 1) -> str:
        """
        param `order_code`: a django coding for changelist ordering
        returns a complete sql query with limit & offset
        """
        root_query = str(self.root_queryset.query)
        from_clause_index = root_query.capitalize().find('FROM')
        select_clause = root_query[:from_clause_index]

        searchparams = self.get_search_clause(self.lookup_field)
        if order_code:
            ordering_params = self.get_ordering_kwargs()
        else:
            ordering_params = f"""
            ORDER BY {self.model_admin.default_sorting_key} 
            {self.model_admin.default_sorting_order}"""

        sql = root_query + ' WHERE ' + searchparams + ordering_params \
            + f' LIMIT {self.list_per_page}' + \
              f' OFFSET {self.list_per_page * (page_number - 1)}'
        return sql

    def get_search_queryset(self, sql_string: str, searched_data: str):
        queryset = self.model.objects.raw(sql_string, [f'%{searched_data}%'])
        return queryset

    def pagination_required(self, request):
        """deactivating django's default pagination"""
        return

    def count_search_result(self, searched_data: str) -> int:
        searchparams = self.get_search_clause(self.lookup_field)
        sql = f"SELECT COUNT(*) FROM {self.opts.db_table} WHERE {searchparams}"
        cursor = connection.cursor()
        cursor.execute(sql, [f'%{searched_data}%'])
        self.search_result_count = cursor.fetchone()[0]
        return self.search_result_count

    def get_queryset(self, request):
        """
        The main logic of the class lays here.
        """
        request_data = request.GET
        q = request_data.get('q')

        if not q:
            return self.root_queryset.none()

        if 'mf' in request_data:  # mf: model_field to look up for
            search_field_index = int(request_data['mf'])
            self.lookup_field = self.search_fields[search_field_index]

        if request.session.get('search_param') != q + request_data.get('mf'):
            request.session['search_param'] = q + request_data.get('mf')
            self.model_admin.paginator.count = \
                request.session['count'] = self.count_search_result(q)
        else:
            self.search_result_count = request.session['count']

        order_code = request_data.get('o')
        page_number = request_data.get('p') if request_data.get('p') else 1

        if '__' in self.lookup_field:
            sql_string = ''
        else:
            sql_string = self.get_sql(order_code, page_number)

        queryset = self.get_search_queryset(sql_string, q)
        return queryset

    def get_results(self, request):
        paginator = self.model_admin.get_paginator(
            request, self.queryset, self.list_per_page
        )
        # Get the number of objects, with admin filters applied.
        result_count = self.search_result_count
        # Get the total number of objects, with no admin filters applied.
        if self.model_admin.show_full_result_count:
            full_result_count = self.root_queryset.count()
        else:
            full_result_count = None
        can_show_all = result_count <= self.list_max_show_all
        multi_page = result_count > self.list_per_page

        try:
            result_list = self.queryset._clone()
        except InvalidPage:
            raise IncorrectLookupParameters

        self.result_count = result_count
        self.show_full_result_count = self.model_admin.show_full_result_count
        # Admin actions are shown if there is at least one entry
        # or if entries are not counted because show_full_result_count is disabled
        self.show_admin_actions = not self.show_full_result_count or bool(
            full_result_count
        )
        self.full_result_count = full_result_count
        self.result_list = result_list
        self.can_show_all = can_show_all
        self.multi_page = multi_page
        self.paginator = paginator


class OptimizedAdminSearchMixin:
    """
    Wraps the whole optimized django admin site logic.
    To use, inherit this class in your admin class along with django's ModelAdmin.
    """
    default_sorting_key = 'id'
    search_fields = ['id']
    default_sorting_order = 'ASC'  # or 'DESC'
    list_per_page = 15
    change_list_template = 'admin/bigrecord_change_list.html'
    show_full_result_count = False

    def get_changelist(self, request, **kwargs):
        return SearchOnlyChangeList


@admin.register(Book)
class MyAdmin(OptimizedAdminSearchMixin, admin.ModelAdmin):
    list_display = ['id', 'title', 'price']
    default_sorting_key = 'title'
    search_fields = ['id', 'title', 'price', 'author__name']


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    pass
