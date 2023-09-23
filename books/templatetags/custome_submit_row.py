
from django import template
from django.contrib.admin.templatetags.base import InclusionAdminNode
from django.contrib.admin.templatetags.admin_list import result_list_tag
from django.template.library import InclusionNode


register = template.Library()


def submit_row(context):
    """
    Display the row of buttons for delete and save.
    """
    return {'message': 'salam'}


@register.tag(name="custome_submit_row")
def submit_row_tag(parser, token):
    return InclusionNode(
        func=submit_row, takes_context=True, args=[], kwargs={}, filename="custome_submit_row.html",
    )


@register.tag(name="MYTAG")
def submit_row_tag(parser, token):
    return InclusionNode(
        func=submit_row, takes_context=True, args=[], kwargs={}, filename="custome_submit_row.html",
    )


@register.tag(name="result_list_tag")
def result(parser, token):
    return result_list_tag(parser, token)
