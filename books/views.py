from django.shortcuts import render
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.options import modelform_factory
from django.forms import ModelForm
from .models import Book


class AdminForm(ModelForm):
    class Meta:
        model = Book
        fields = "__all__"


def index(request):

    formset = modelform_factory(Book, fields='__all__')
    print(formset)
    return render(request, 'custome_changelist.html', {'form': AdminForm(), 'message': 1111})
# Create your views here.
