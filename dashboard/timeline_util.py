from dashboard.models import TimelineEvent

__author__ = 'dgosting'

MAX_EVENTS = 10


def create_event(title, message, icon, color):

    event = TimelineEvent(title=title, message=message, icon=icon, color=color)

    event.save()

    clean_timeline()


def get_timeline():

    timeline_list = []

    events = TimelineEvent.objects.all().order_by("-timestamp")

    for event in events:

        event_dict = {"title": event.title,
                      "timestamp": event.timestamp,
                      "message": event.message,
                      "icon": event.icon,
                      "color": event.color}

        timeline_list.append(event_dict)

    return timeline_list


def clean_timeline():

    all_events = TimelineEvent.objects.all().order_by("timestamp")

    event_count = all_events.count()

    while event_count > MAX_EVENTS:

        all_events[0].delete()

        all_events = TimelineEvent.objects.all().order_by("timestamp")

        event_count = all_events.count()
