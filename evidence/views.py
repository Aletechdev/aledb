from django.shortcuts import get_object_or_404, render
from django.shortcuts import redirect
from .utils import get_user_projects, get_all_user_exps
from .permissions import can_view_project
import logging


logger = logging.getLogger(__name__)


def evidence(request):
    file_to_serve = get_all_user_exps(request.path)
    path_of_file = "/data/aledata/" + file_to_serve

    template_name = "ale/evidence.html"
    return render(request, template_name, {'file_to_serve': file_to_serve})
