
from django.core.management.base import BaseCommand
from ...utils import  fake_field_creator
from time import time

class Command(BaseCommand):
    """
    Command to create fake records in the database as many as passed arguments
    """
    def add_arguments(self, parser):
        parser.add_argument("how_many", nargs="+", type=int)

    def handle(self, *args, **options):
        self.stdout.write("Creating fake records...")
        how_many = options['how_many'][0]

        t0 = time()
        fake_field_creator(how_many)
        delta = round(time() - t0 ,2)
        self.stdout.write(f"{how_many} records created successfully in {delta} seconds!")
