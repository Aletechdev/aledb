"""
Check active users and login activity.
Run via: sudo docker exec -i aledb-web python manage.py shell < scripts/check_active_users.py
"""
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.contrib.auth.models import User

now = timezone.now()

# Active sessions
active_sessions = Session.objects.filter(expire_date__gte=now)
print(f"Active sessions: {active_sessions.count()}")
print()

# Extract user IDs from sessions
user_ids = []
for s in active_sessions:
    data = s.get_decoded()
    uid = data.get("_auth_user_id")
    if uid:
        user_ids.append(uid)

users = User.objects.filter(id__in=user_ids)
print(f"Logged-in users: {users.count()}")
for u in users:
    print(f"  - {u.username} ({u.email}) | Last login: {u.last_login}")

# Total registered users
total = User.objects.count()
active = User.objects.filter(is_active=True).count()
print(f"\nTotal registered users: {total}")
print(f"Active accounts: {active}")

# Recent logins (last 7 days)
week_ago = now - timezone.timedelta(days=7)
recent = User.objects.filter(last_login__gte=week_ago).order_by("-last_login")
print(f"\nUsers who logged in the last 7 days: {recent.count()}")
for u in recent:
    print(f"  - {u.username} ({u.email}) | Last login: {u.last_login}")
