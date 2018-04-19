from django.conf import settings


def global_settings(request):
    return {
        'GOOGLE_ANALYTICS_TAG': settings.GOOGLE_ANALYTICS_TAG,
    }
