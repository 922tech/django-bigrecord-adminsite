from django.contrib import admin

from books.admin import SearchOnlyChangeList
from .models import Post


@admin.register(Post)
class Admin(admin.ModelAdmin):

    list_display = ['id', 'title', 'author']
    lookup_fields = search_fields = ['title', 'author']
    list_per_page = 2
    list_filter = ['id']
