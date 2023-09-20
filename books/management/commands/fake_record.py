from django.core.management.base import BaseCommand
from ...utils import  fake_field_creator
from time import time
_HOW_MANY = 1000


class Command(BaseCommand):
    help = 'Description of your custom command'

    def handle(self, *args, **options):
        self.stdout.write("Creating fake records...")
        t0 = time()
        fake_field_creator(_HOW_MANY)
        delta = round(time() - t0 ,2)

        self.stdout.write(f"{_HOW_MANY} records created successfully in {delta} seconds!")
