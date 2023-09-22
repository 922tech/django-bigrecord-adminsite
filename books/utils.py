
import random
import time
from faker import Faker
from .models import Book
from django.db import models
from typing import Any, Callable
import xxhash


def get_field_names(model: models.base.ModelBase) -> list[str]:
    """
    returns name of all the fields on a model class except
    for `id` field
    """
    return [field.name for field in Book._meta.get_fields()
            if field.name != 'id']


def generate_random_string():
    x = xxhash.xxh64()
    data = f"Hello, World!{time.time()}".encode()
    x.update(data)
    return x.hexdigest()


def get_sql_queryparams(model: models.base.ModelBase, lookup_dict: dict) -> str:
    """
    accepts a dictionary of kwargs and returns a string contains query
    parameters.
    example:
    get_sql_queryparams(Book,{'col1':'something', 'col2':'other_thing'})
    >>> 'books_book.col1=$$something$$ AND books_book.col2=$$other_thing$$ '
    """
    table = model._meta.db_table
    q = [f"{table}.{i}=$${j}$$ " for (i, j) in lookup_dict.items()]
    length = len(q)
    for i in range(length):
        if i < length - 1:
            q[i] += 'AND '
    return ''.join(q)


class FakeModelFactory:
    """
    The tool to create fake data.

    model: table in which the data will be persisted
    fake_field_creator: the function which returns
            a dictionary containing fields and faker implementations
    """

    def __init__(
            self,
            model: models.base.ModelBase,
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
