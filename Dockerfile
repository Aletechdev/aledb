
FROM python:3.5

# Ensure that Python outputs everything that's printed inside
# the application rather than buffering it.
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY . /app

VOLUME /app/static
VOLUME /app/settings

ENV DJANGO_SETTINGS_MODULE=aleinfo.settings_private
RUN python manage.py collectstatic --no-input

#EXPOSE 80

#CMD ["./docker-runserver.sh"]

