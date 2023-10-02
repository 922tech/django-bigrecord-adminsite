import re
import random
import time
from faker import Faker
from .models import Book
from django.db import models
from typing import Any, Callable, Union, Sequence
import xxhash


def count_results(self):
    """
    separates everything that comes after 'FROM' including `FROM`
    from an SQL query. useful for purifying the django base query
    for a given queryset.
    """
    pattern = r'(?=FROM)(.*)'
    clause = re.findall(pattern, str(self.root_queryset.query))


def get_field_names(model: models.Model) -> list[str]:
    """
    returns name of all the fields on a model class except
    for `id` field
    """
    return [field.name for field in model._meta.get_fields()]


def get_field_verbose_names(model: models.Model) -> list[str]:
    """
    returns name of all the fields on a model class except
    for `id` field
    """
    return [field.verbose_name for field in model._meta.get_fields()]

def generate_random_string():
    x = xxhash.xxh64()
    data = f"Hello, World!{time.time()}".encode()
    x.update(data)
    return x.hexdigest()


def get_fields(model: models.Model):
    table = model._meta.db_table


def get_sql_queryparams(model: models.Model, lookup_dict: dict, delim='AND') -> str:
    """
    accepts a dictionary of kwargs and returns a string contains query
    parameters. It is indented to  use in creation of a SQL WHERE clause.

    param `model`: the django model
    param `lookup_dict`: a dictionary containing the kwargs.
    param `delim`: a string containing keywords like `AND` , `OR` etc. that
                 comes amongst the conditions.

    example:
    ```
    >>> get_sql_queryparams(Book,{'col1':'something', 'col2':'other_thing'})
    >>> 'books_book.col1=$$something$$ AND books_book.col2=$$other_thing$$ '
    ```
    """
    table = model._meta.db_table
    q = [f"{table}.{i}=%$${j}$$% " for (i, j) in lookup_dict.items()]
    length = len(q)
    for i in range(length):
        if i < length - 1:
            q[i] += delim+' '
    return ''.join(q)


def get_sql_searchparams(model: models.Model, search_fields: Sequence, search_param: Any, delim: str = 'AND') -> str:
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
    >>> get_sql_searchparams(Book, ['col1', 'col2'], 'plant')
    >>> 'UPPER(books_book.col1::text) LIKE %s AND UPPER(books_book.col2::text) LIKE %s '
    ```
    """
    table = model._meta.db_table
    q = [f"LOWER({table}.{i}::text) LIKE LOWER(%s::text) " for i in search_fields]
    # Using LIKE was more efficient than ILIKE in the tests
    # Use of lowercasing along with  `LIKE` was a more efficient way than using `ILIKE`
    length = len(q)
    for i in range(length):
        if i < length - 1:
            q[i] += delim+' '
    return ''.join(q)


def get_sql_ordering(fields: dict[str, str]):
    args = [f" {i} {fields[i]}" for i in fields]
    for i in range(len(args)-1):
        args[i] += ','

    return 'ORDER BY' + ''.join(args)


class FakeModelFactory:
    """
    The tool to create fake data.

    model: table in which the data will be persisted
    fake_field_creator: the function which returns
            a dictionary containing fields and faker implementations
    """

    def __init__(
            self,
            model: models.Model,
            fake_field_creator:  Callable[[], dict[str, Any]]
    ):
        self.model = model
        self.fake_field_creator = fake_field_creator

    def create_fake_record(self, how_many: int):
        objs = (self.model(**self.fake_field_creator())
                for _ in range(how_many))
        self.model.objects.bulk_create(objs)


def fake_creator() -> dict[str, Any]:
    faker = Faker('en_US')
    DATE = faker.date()
    return {
        'title': generate_random_string(),
        'publication_date': DATE,
        'price': random.randint(10, 10000),
        'serial_number': generate_random_string(),
        'description': faker.text(random.randint(10, 100)),
    }


def fake_field_creator(how_many=100):
    fake_category_factory = FakeModelFactory(Book, fake_creator)
    fake_category_factory.create_fake_record(how_many)
