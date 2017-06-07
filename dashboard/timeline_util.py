from dashboard.models import TimelineEvent

__author__ = 'dgosting'


def create_event(title, message, icon, color):

    event = TimelineEvent(title=title, message=message, icon=icon, color=color)

    event.save()
