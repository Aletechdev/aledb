# Optimize `get_user_projects()` — N+1 Permission Queries

## Current behavior

`ale/utils.py:get_user_projects()` loops over all projects and calls `can_view_project()` per project, which triggers a guardian `user.has_perm()` DB query each time.

## Permission logic

A user can see a project if:
- It's **public**, OR
- User is **superuser**, OR
- User is **staff** and the project has no explicit permissions set, OR
- User has explicit `view_project` permission on it (via `guardian`)

## Proposed fix

Replace the N+1 loop with 2-3 fixed queries:

```python
from django.db.models import Q

def get_user_projects(user):
    if user.is_superuser:
        return Project.objects.all()

    # Projects with explicit view_project permissions for this user
    user_permitted_ids = UserObjectPermission.objects.filter(
        user=user, permission__codename=VIEW_PROJECT,
        content_type__model='project'
    ).values_list('object_pk', flat=True)

    # Public projects + user's permitted projects
    projects = Project.objects.filter(
        Q(is_public=True) | Q(pk__in=user_permitted_ids)
    )

    # Staff can also see projects with no permissions set
    if user.is_staff:
        restricted_ids = _get_projects_with_permissions(VIEW_PROJECT)
        projects = projects | Project.objects.exclude(pk__in=restricted_ids)

    return projects.distinct()
```

## Risks

- Permission logic is delicate — needs thorough testing across superuser, staff, and regular user roles
- Guardian group permissions (not just user permissions) may also need handling
- `can_view_project()` in `ale/permissions.py` is used elsewhere — changing `get_user_projects()` should not affect those call sites, but verify

## Also applies to

Once this is optimized, the same approach should be used to filter `get_strains()` and `get_ref_sequences()` to only return values from user-accessible experiments (currently they return all values with no permission check).
