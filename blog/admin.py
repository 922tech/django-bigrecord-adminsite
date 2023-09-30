from django.contrib import admin

from books.admin import SearchOnlyChangeList
from .models import Post


@admin.register(Post)
class Admin(admin.ModelAdmin):

    list_display = ['id', 'title', 'author']
    lookup_fields = search_fields = ['title', 'author', ]

    def get_changelist(self, request, **kwargs):
        return SearchOnlyChangeList

# Register your models here.
