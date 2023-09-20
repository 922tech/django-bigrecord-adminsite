"""
To create fake records in the database write this command:
    `python manage.py fake_record <how_many>`
    e.g.
    `python manage.py fake_record 1000` :
    would create 1000 fake records in the database
"""

from django.core.management.base import BaseCommand
from ...utils import  fake_field_creator
from time import time

class Command(BaseCommand):
    help = 'Description of your custom command'

    def add_arguments(self, parser):
        parser.add_argument("--how_many", nargs="+", type=int)

    def handle(self, *args, **options):
        self.stdout.write("Creating fake records...")
        if options['how_many']:
            how_many = options['how_many'][0]
        else:
            how_many = 100
        t0 = time()
        fake_field_creator(how_many)
        delta = round(time() - t0 ,2)
        self.stdout.write(f"{how_many} records created successfully in {delta} seconds!")
