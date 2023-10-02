from django.db import models
from django.urls import reverse


class Book(models.Model):
    title = models.CharField(max_length=100, verbose_name='Book Title')
    publication_date = models.DateField(verbose_name='Published On')
    price = models.FloatField(verbose_name='Price')
    serial_number = models.CharField(max_length=36, null=True, blank=True, verbose_name='Serial Number')
    description = models.TextField(verbose_name='Description')

    def __str__(self):
        return self.title

    # class Meta:
    #     db_table = 'book'

