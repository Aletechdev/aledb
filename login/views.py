from django.contrib.auth import authenticate, login, logout
from seq.views.dashboard import dashboard
from django.template import loader
from django.http import HttpResponse


def login_user(request):
    logout(request)
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return dashboard(request)

    template = loader.get_template('login.html')

    return HttpResponse(template.render())
