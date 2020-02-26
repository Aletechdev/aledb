from django.contrib.auth.models import User, Group
from ale.models import Project, AleExperiment, RecentExperiments, AleId
from guardian.models import GroupObjectPermission, UserObjectPermission
from django.core.exceptions import ObjectDoesNotExist
from ale.permissions import VIEW_PROJECT, can_view_project


def _get_projects_with_permissions(permission_codename):
    """
    get set of projects that have object-level permissions set
    :return: set of project ids (set of str)
    """
    group_permissions = GroupObjectPermission.objects.filter(content_type__app_label='ale',
                                                             content_type__model='project',
                                                             permission__codename=permission_codename)
    user_permissions = UserObjectPermission.objects.filter(content_type__app_label='ale',
                                                           content_type__model='project',
                                                           permission__codename=permission_codename)
    project_ids = {p.object_pk for p in group_permissions} | {p.object_pk for p in user_permissions}
    return project_ids


def get_user_projects(user: User):
    """
    get projects based on user permissions
    :param user: the login user
    :return: list of projects that the user can view
    """
    if user.is_superuser:
        return Project.objects.all()
    else:
        restricted_proj_ids = _get_projects_with_permissions(VIEW_PROJECT)
        all_projects = Project.objects.all()
        if restricted_proj_ids is None or len(restricted_proj_ids) == 0:
            return all_projects
        myprojects = []
        for project in all_projects:
            if project.is_public:
                myprojects.append(project)
            elif can_view_project(user, project):
                myprojects.append(project)
            elif user.has_perm(VIEW_PROJECT, project):
                myprojects.append(project)
        return myprojects


def get_all_user_exps(user):
    """
    Get all experiments that the user can view
    :param user: given login user
    :return: experiment queryset
    """
    projects = get_user_projects(user)
    return AleExperiment.objects.filter(project_id__in=projects).order_by('name')


def _ale_exp_exists(ale_id, recent_experiments):
    try:
        recent_experiments.append(AleExperiment.objects.get(ale_id=ale_id))
    except ObjectDoesNotExist:
        pass
    return recent_experiments


def get_strains():
    """return list of sorted strains"""
    ale_ids = AleId.objects.all()
    strain_sets = {obj.strain for obj in ale_ids}
    strains = [strain for strain in strain_sets if strain]
    return sorted(strains)

