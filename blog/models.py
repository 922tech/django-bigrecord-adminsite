from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=32)
    author = models.CharField(max_length=32)

# Create your models here.
