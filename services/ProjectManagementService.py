import os
from datetime import datetime


def create_project_dir(name):
    now = datetime.now()
    dt_string = name + '_' + now.strftime("%d%m%Y_%H%M%S")
    project_path = os.getcwd() + '/' + dt_string
    if not os.path.exists(project_path):
        os.makedirs(project_path)
    return project_path


def list_projects(src):
    return ''