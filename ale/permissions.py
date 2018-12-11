from guardian.models import GroupObjectPermission, UserObjectPermission

VIEW_PROJECT = 'view_project'


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


def can_view_project(user, project):
    ok = user.is_superuser or project.is_public or user.id == project.user_id
    if not ok and user.is_staff:
        if _project_has_permissions(project, VIEW_PROJECT):
            ok = user.has_perm(VIEW_PROJECT, project)
        else:
            ok = True
    return ok


def can_add_global_filter(user):
    return user.is_superuser


def can_add_project_filter(user, project):
    return user.is_superuser or user.id == project.user_id

