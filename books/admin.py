from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.utils.functional import cached_property
from django.core.paginator import Paginator

from .models import Book

from .utils import get_field_verbose_names, get_field_names


class NonPaginator(Paginator):
    @cached_property
    def count(self):
        return 10


class SearchOnlyChangeList(ChangeList):
    """
    This class provides an optimized way to make a change list for a django app.
    It shows am empty table that gets filled on search.
    It also uses raw SQL queries for optimization purposes.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_fields = [self.all_fields[0]]

    @property
    def all_fields(self):
        """
        Returns all field names no a model in a list
        """
        return get_field_names(self.model)

    @property
    def all_fields_verbose_names(self):
        return get_field_verbose_names(self.model)

    @property
    def fields_enumeration(self):
        return enumerate(self.all_fields_verbose_names)

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
        kwargs_string = 'ORDER BY ' + \
            ', '.join([f'{i} {kwargs[i]}' for i in kwargs])

        return kwargs_string

    def get_sql(self, order_code: str = '', page_number=1) -> str:
        """
        param `order_code`: a django coding for changelist ordering
        returns a complete sql query
        """

        searchparams = self.get_sql_searchparams()
        if order_code:
            ordering_params = self.get_ordering_kwargs()
        else:
            ordering_params = 'ORDER BY id asc'

        sql = str(self.root_queryset.query) + f' {self.opts.db_table}' + \
            ' WHERE ' + searchparams + ordering_params \
            + f' LIMIT {self.list_per_page}' + \
            f' OFFSET { self.list_per_page * (page_number - 1) }'

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
        if 'mf' in request_data:
            search_field_index = int(request_data['mf'])
            self.set_search_fields(search_field_index)

        if 'q' in request_data:
            if 'o' in request_data:
                order_code = request_data['o']
            else:
                order_code = 0

            if 'p' in request_data:
                page_number = int(request_data['p'])
            else:
                page_number = 1
            sql_string = self.get_sql(order_code, page_number)
            queryset = self.get_search_queryset(sql_string, request_data)
            return queryset

        else:
            return self.root_queryset.none()

    def pagination_required(self, request):
        return


class OptimizedAdminSearchMixin:

    show_full_result_count = False
    list_per_page = 15  # to get rid of the count query
    _paginator_cls = NonPaginator
    _paginator_cls.count = list_per_page
    paginator = _paginator_cls
    # the value of list_per_page should be equal to the value of NonPaginator.count
    change_list_template = 'admin/bigrecord_change_list.html'

    def get_changelist(self, request, **kwargs):
        return SearchOnlyChangeList


@admin.register(Book)
class MyAdmin(OptimizedAdminSearchMixin, admin.ModelAdmin):
    # The preceedance of the parent classes is important
    list_display = ['id', 'title']
