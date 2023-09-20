
import string, random, time
from faker import Faker
from .models import Book
from django.db import models 
from typing import  Any, Callable
import xxhash



def get_field_names(klass):
    return [field.name for field in Book._meta.get_fields() if field.name != 'id']


def generate_random_string():
    x = xxhash.xxh64()
    data = f"Hello, World!{time.time()}".encode()
    x.update(data)
    return x.hexdigest()


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
            fake_field_creator:  Callable[[],dict[str, Any]]
            ):
        self.model = model
        self.fake_field_creator = fake_field_creator 

    def create_fake_record(self, how_many: int):
        objs = ( self.model(**self.fake_field_creator()) for _ in range(how_many) )
        self.model.objects.bulk_create(objs)
        


def fake_creator() -> dict[str, Any]:
    faker = Faker('en_US')
    DATE = faker.date()
    return {
    'title':generate_random_string(),
    'publication_date':DATE,
    'price':random.randint(10,10000),
    'serial_number':generate_random_string(),
    'description':faker.text(random.randint(10,100)),
    }


def fake_field_creator(how_many=100):
    fake_category_factory = FakeModelFactory(Book,fake_creator)
    fake_category_factory.create_fake_record(how_many)


