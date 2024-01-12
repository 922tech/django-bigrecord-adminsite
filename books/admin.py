from typing import Sequence, Union
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.db import connection
from django.db.models.sql.datastructures import Join
from django.db.models.sql.query import Query, get_order_dir
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, InvalidPage
from django.contrib.admin.options import IncorrectLookupParameters
from .models import Book, Author


class EmptyPagePaginator(Paginator):
    """
    Allows the pages to be empty or even the page number be greater
    than the total page count.
    """
    def validate_number(self, number):
        try:
            if isinstance(number, float) and not number.is_integer():
                raise ValueError
            number = int(number)
        except (TypeError, ValueError):
            raise PageNotAnInteger("That page number is not an integer")
        if number < 1:
            raise InvalidPage("That page number is less than 1")
        return number

class SearchOnlyChangeList(ChangeList):
    """
    This class provides an optimized way to make a change list for a django app.
    It shows an empty change list that gets filled after searching.
    It also uses raw SQL queries for optimization purposes.
    This class is tightly coupled with `OptimizedAdminSearchMixin`
    """

    def __init__(self, *args, **kwargs):
        self.search_result_count = 0
        self.join_clause = ''
        super().__init__(*args, **kwargs)
        self.lookup_field = None
        self.lookup_related_table = None
        self.related_query = ''

    @property
    def related_fields(self):
        return [
            i.split('__') for i in self.search_fields if '__' in i
        ]

    def get_join_clause(self, model, seq: Union[list, tuple], join_clause='') -> str:
        """
        Gets a sequence of related fileds in an ordered sequence and creates a complete 
        SQL JOIN clasue and puts it under `join_clause` varaible's name.
        NOTE that `join_clause` should be another variable in an outer scope otherwise
        it will change in every recursion.

        - param model: django model to JOIN
        - param seq: sequence of related fields to join
        This method changes the self.join_clause attr on class
        e.g. 
        >>> get_join_clause(Library, ['book', 'author'], self.join_clause)
        >>> self.join_clause --> 
        ' JOIN book on "books_book"."author_id"="books_author"."id" JOIN author '
        """
        related_field = model._meta.get_field(seq[0])
        related_model = related_field.related_model
        if len(seq) > 1:
            seq.pop(0)
            self.lookup_related_table = related_model._meta.db_table
            self.get_join_clause(related_model, seq, self.join_clause)
            self.join_clause = f''' 
            INNER JOIN {related_model._meta.db_table} 
            ON
            "{model._meta.db_table}"."{related_field.column}" =
            "{related_model._meta.db_table}"."{related_field.target_field.column}" 
            ''' + self.join_clause
            self.related_lookup_table = related_model._meta.db_table
        else:
            return
        return

    def get_related_queries(self, model, seq: Union[list, tuple],search_param):
        related_field = model._meta.get_field(seq[0])
        local_field, reference_field = related_field.related_fields
        related_model = related_field.related_model
        search_clause = self._get_search_clause(model._meta.db_table, related_field.column)

        if first:
            query = f'''
            SELECT {model._meta.pk} FROM {model._meta.db_table}
            WHERE  {search_clause}
            '''
            params = [search_param]
            first_pk = model.objects.raw(query, params)
        else:
            query = f'''
            SELECT {related_field.column} FROM {model._meta.db_table}
            WHERE  {search_param}
            '''
        target_pk = model.objects.raw(f'''
            SELECT {related_field.column} FROM {model._meta.db_table}
            WHERE  {search_param}
        ''')
        if len(seq) > 1:
            seq.pop(0)
            self.lookup_related_table = related_model._meta.db_table
            self.get_join_clause(related_model, seq, self.join_clause)
            self.join_clause = f''' 
            SELECT {related_field.target_field.column}
            INNER JOIN {related_model._meta.db_table} 
            WHERE
            "{model._meta.db_table}"."{related_field.column}" =
            "{related_model._meta.db_table}"."{related_field.target_field.column}" 
            ''' 
        
        return
    
    @property
    def fields_enumeration(self):
        return enumerate(self.search_fields)

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
        q = [self._get_search_clause(table, i) for i in search_fields]
        # Using LIKE was more efficient than ILIKE in the benchmark
        # Use of lower-casing along with  `LIKE` was a more efficient way than using `ILIKE`
        length = len(q)
        for i in range(length):
            if i < length - 1:
                q[i] += delim + ' '
        return ''.join(q)

    @staticmethod
    def _get_search_clause(table: str, field: str):
        return f"""LOWER("{table}"."{field}"::text) LIKE LOWER(%s::text) """

    def get_search_clause(self):
        if not '__' in self.lookup_field:
            return self._get_search_clause(self.opts.db_table, self.lookup_field)
        else:
            return self._get_search_clause(
                self.lookup_related_table, self.lookup_field.split('__')[-1])

    @staticmethod
    def get_last_joined_table(table, field):
        pass

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
        kwargs_string = ', '.join([f'{i} {kwargs[i]}' for i in kwargs])

        return kwargs_string

    def get_sql(self, order_code: str = '', page_number: int = 1) -> str:
        """
        param `order_code`: a django coding for changelist ordering
        returns a complete sql query with limit & offset
        """

        if '__' in self.lookup_field:
            seq = self.lookup_field.split('__')
            if self.model_admin.use_join_query:
                self.get_join_clause(self.model, seq)

        search_clause = self.get_search_clause()
        self.search_clause = search_clause
        if order_code:
            ordering_params = self.get_ordering_kwargs()
        else:
            default_ordering = get_order_dir(
                self.model_admin.default_sorting_key
            )
            ordering_params = ' '.join(default_ordering)

        root_query = str(self.root_queryset.query)
        
        next_offset = self.list_per_page * (page_number - 1)
        sql = f"""
                {root_query} {self.join_clause} 
                WHERE {search_clause}
                ORDER BY {ordering_params}
                LIMIT {self.list_per_page}
                OFFSET {next_offset}
                """
        self.from_record = next_offset
        self.to_record = next_offset + self.list_per_page
        return sql

    def get_search_queryset(self, sql_string: str, searched_data: str):
        queryset = self.model.objects.raw(sql_string, [f'%{searched_data}%'])
        return queryset

    def pagination_required(self, request):
        """deactivating django's default pagination"""
        return

    def count_search_result(self, searched_data: str) -> int:
        sql = f"""SELECT COUNT(*) FROM {self.opts.db_table}
                  {self.join_clause} WHERE {self.search_clause}"""
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

        # mf: model_field index in search_fields to look up
        search_field_index = int(request_data.get('mf', 0))
        self.lookup_field = self.search_fields[search_field_index]

        order_code = request_data.get('o')
        page_number = int(request_data.get('p', 1))
        sql_string = self.get_sql(order_code, page_number)
        queryset = self.get_search_queryset(sql_string, q)

        if request.session.get('search_param') != q + request_data.get('mf'):
            request.session['search_param'] = q + request_data.get('mf')
            self.model_admin.paginator.count = \
                request.session['count'] = self.count_search_result(q)
        else:
            self.search_result_count = request.session['count']

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
            result_list = list(self.queryset._clone())
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
    Wraps the whole optimized admin site logic for searching.
    To use, inherit this class in your admin class along with django's ModelAdmin.
    """
    default_sorting_key = '-id'
    search_fields = ['id']
    list_per_page = 15
    change_list_template = 'admin/bigrecord_change_list.html'
    show_full_result_count = False
    paginator = EmptyPagePaginator
    use_join_query = True

    def get_changelist(self, request, **kwargs):
        return SearchOnlyChangeList



@admin.register(Book)
class MyAdmin(OptimizedAdminSearchMixin, admin.ModelAdmin):
    list_display = ['id', 'title', 'price']
    default_sorting_key = '-title'
    search_fields = ['id', 'title', 'price',
                     'author__user__username', 'author__name']


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['id', 'user']
    search_fields = ['user__username']
    pass
