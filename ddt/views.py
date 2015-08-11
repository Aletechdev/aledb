from django.shortcuts import render


def ddt(request):
    return render(request, 'ddt/index.html')
