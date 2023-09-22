from django.db import models
from django.urls import reverse


class Book(models.Model):
    title = models.CharField(max_length=100)
    publication_date = models.DateField()
    price = models.FloatField()
    serial_number = models.CharField(max_length=36, null=True, blank=True)
    description = models.TextField()

    def __str__(self):
        return self.title

    # def get_absolute_url(self):
    #     return reverse('book-detail', args=[self.id])
