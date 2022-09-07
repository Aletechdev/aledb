from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse


def evidence(request):

    return HttpResponse("Here's some evidence")