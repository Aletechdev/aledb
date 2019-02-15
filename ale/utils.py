from django.contrib.auth.models import User, Group
from ale.models import Project, AleExperiment, RecentExperiments
from guardian.models import GroupObjectPermission, UserObjectPermission
from django.core.exceptions import ObjectDoesNotExist
from ale.permissions import VIEW_PROJECT


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
    if not user.is_staff:
        return Project.objects.filter(is_public=True)
    else:
        restricted_proj_ids = _get_projects_with_permissions(VIEW_PROJECT)
        all_projects = Project.objects.all()
        if restricted_proj_ids is None or len(restricted_proj_ids) == 0:
            return all_projects
        myprojects = []
        for project in all_projects:
            if project.is_public:
                myprojects.append(project)
            elif user.id == project.user_id:
                myprojects.append(project)
            elif str(project.id) not in restricted_proj_ids:
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


def get_recent_ale_exps(ale_experiment_id=None):

    recent, created = RecentExperiments.objects.get_or_create(id=1)

    if ale_experiment_id is not None:
        recent_list = [recent.first, recent.second, recent.third, recent.fourth, recent.fifth]

        if ale_experiment_id not in recent_list:
            recent.fifth = recent.fourth
            recent.fourth = recent.third
            recent.third = recent.second
            recent.second = recent.first
            recent.first = ale_experiment_id
        else:
            temp = [x for x in recent_list if x != ale_experiment_id]
            recent.fifth = temp[3]
            recent.fourth = temp[2]
            recent.third = temp[1]
            recent.second = temp[0]
            recent.first = ale_experiment_id

        recent.save()

    recent_experiments = []
    if recent.first is not None:
        recent_experiments = _ale_exp_exists(recent.first, recent_experiments)

    if recent.second is not None:
        recent_experiments = _ale_exp_exists(recent.second, recent_experiments)

    if recent.third is not None:
        recent_experiments = _ale_exp_exists(recent.third, recent_experiments)

    if recent.fourth is not None:
        recent_experiments = _ale_exp_exists(recent.fourth, recent_experiments)

    if recent.fifth is not None:
        recent_experiments = _ale_exp_exists(recent.fifth, recent_experiments)
    return recent_experiments


def _ale_exp_exists(ale_id, recent_experiments):
    try:
        recent_experiments.append(AleExperiment.objects.get(ale_id=ale_id))
    except ObjectDoesNotExist:
        pass
    return recent_experiments
