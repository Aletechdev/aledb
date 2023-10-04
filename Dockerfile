
FROM python:3.11

# Ensure that Python outputs everything that's printed inside
# the application rather than buffering it.
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY . /app

#VOLUME /app/static
#VOLUME /app/aleinfo

#ENV DJANGO_SETTINGS_MODULE=aleinfo.settings_private
#RUN python manage.py collectstatic --no-input

#EXPOSE 8000
#
#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

