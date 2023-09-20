from django.shortcuts import render
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.options import modelform_factory
from .models import Book

def index(request):
    formset = modelform_factory(Book, fields='__all__')

    return render(request, 'custome_changelist.html', {'form':formset, 'message':1111})
# Create your views here.
