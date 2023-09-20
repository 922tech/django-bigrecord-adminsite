from django.db import models


class Book(models.Model):
    title = models.CharField(max_length=100)
    publication_date = models.DateField()
    price = models.FloatField()
    serial_number = models.CharField(max_length=36, null=True, blank=True)
    description = models.TextField()

    def __str__(self):
        return self.title
    
