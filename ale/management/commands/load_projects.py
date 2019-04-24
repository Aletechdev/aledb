import pandas as pd
from ale.models import AleExperiment, Project
from django.contrib.auth.models import User
from django.core.management import BaseCommand
from django.contrib.auth.hashers import make_password
from datetime import datetime


class Command(BaseCommand):
    # command: manage.py load_projects "/Users/rcai/Downloads/ALEdb exp proj map.xlsx"
    help = "This function is used to load projects and associate exeperiments from file"

    def add_arguments(self, parser):
        parser.add_argument('file', help='path to input file')

    def handle(self, *args, **options):
        filename = options['file']
        df = pd.read_excel(filename)
        print(df.columns)

        experiment_name_map = {exp.name.strip().lower(): exp for exp in AleExperiment.objects.all()}
        project_name_map = {proj.name.lower(): proj for proj in Project.objects.all()}
        user_name_map = {user.get_full_name(): user for user in User.objects.filter(first_name__isnull=False)}

        for index, row in df.iterrows():
            exp_name = row['experiment'].strip()
            experiment = experiment_name_map.get(exp_name.lower())
            if experiment:
                owner = row['owner'].strip()
                proj_name = row['project'].strip()
                email = str(row['email'])
                pub_flag = row['public']
                if email is None or email =='nan':
                    email = ''
                print("row", index, exp_name)

                user = user_name_map.get(owner)
                if user is None:
                    user = _create_user(owner, email)
                    user_name_map[owner] = user

                project = project_name_map.get(proj_name.lower())
                if project is None:
                    project = _create_project(proj_name, user, pub_flag)
                    project_name_map[proj_name.lower()] = project
                experiment.project = project
                experiment.save()
            else:
                print("experiment does not exit: ", exp_name)


def _create_user(user_full_name: str, email: str):
    default_password = make_password("aledb changeme")
    idx = user_full_name.rfind(' ')
    firstname = user_full_name[0:idx]
    lastname = user_full_name[idx+1:]
    username = (firstname[0] + lastname).lower()
    return User.objects.create(username=username, password=default_password,
                               first_name=firstname, last_name=lastname, email=email,
                               is_active=True, is_staff=True, date_joined=datetime.now())


def _create_project(project_name: str, owner: User, pub_flag):
    is_pub = (pub_flag == 1)
    return Project.objects.create(name=project_name, user=owner, date=datetime.now(),
                                  status="In progress", is_public=is_pub)
