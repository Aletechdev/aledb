FROM python:3.5

# Ensure that Python outputs everything that's printed inside
# the application rather than buffering it.
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app

ADD requirements.txt /app
RUN pip install -r requirements.txt

ADD . /app

VOLUME /app/static
VOLUME /app/settings

EXPOSE 80

ENV DJANGO_SETTINGS_MODULE=aleinfo.settings_dockerfile

CMD ["./docker-runserver.sh"]

