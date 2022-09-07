from guardian.models import GroupObjectPermission, UserObjectPermission
from guardian.shortcuts import assign_perm

from ale.models import AleExperiment
from seq.models import ResequencingExperiment
import logging

VIEW_PROJECT = 'view_project'

logger = logging.getLogger(__name__)


def _project_has_permissions(project, permission_codename):
    """
    Define if a project has permissions set
    :param project:
    :return:
    """
    if project.is_public:
        return False
    group_permissions = GroupObjectPermission.objects.filter(content_type__app_label='ale',
                                                             content_type__model='project',
                                                             object_pk=project.id,
                                                             permission__codename=permission_codename)
    if group_permissions:
        return True
    user_permissions = UserObjectPermission.objects.filter(content_type__app_label='ale',
                                                           content_type__model='project',
                                                           object_pk=project.id,
                                                           permission__codename=permission_codename)
    if user_permissions:
        return True
    return False


def get_users_with_access_to_project(project):
    users = set([])
    permissions = UserObjectPermission.objects.filter(object_pk=project.id)
    for permission in permissions:
        users.add(permission.user)
    return users


def grant_access_to_project(project, user_list):
    for user in user_list:
        assign_perm(VIEW_PROJECT, user, project)
    return


def can_view_project(user, project):
    ok = user.is_superuser or project.is_public or user.has_perm(VIEW_PROJECT, project)
    if not ok and user.is_staff:
        if _project_has_permissions(project, VIEW_PROJECT):
            ok = user.has_perm(VIEW_PROJECT, project)
        else:
            ok = True
    return ok


def can_view_experiment(user, resequence_data_location):
    #Return true until we figure ot the rest
    return True
    reseqs = ResequencingExperiment.objects.filter(location=resequence_data_location).select_related("tech_rep__isolate__flask__ale_id__ale_experiment__project")
    #reseqs = ResequencingExperiment.objects.all()
    if reseqs:
        for reseq in reseqs:
            project = reseq.ale_experiment.project
            ok = can_view_project(user, project)
            if ok:
                return True
    return False


def can_add_global_filter(user):
    return user.is_superuser


def can_add_experiment_filter(user, experiment):
    if experiment:
        return user.is_superuser or user.has_perm(VIEW_PROJECT, experiment.project)
    return False
