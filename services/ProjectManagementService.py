import os
from datetime import datetime
import shutil
from pathlib import Path
import zipfile


def create_project_dir(name):
    now = datetime.now()
    dt_string = name + '_' + now.strftime("%d%m%Y%H%M%S")
    project_path = os.getcwd() + '/' + dt_string
    if not os.path.exists(project_path):
        os.makedirs(project_path)
    return project_path


def list_projects():
    dirs = os.listdir(os.getcwd())
    project_dirs = [a for a in dirs if '_' in a]
    projects = []
    for itm in project_dirs:
        parts = itm.split("_")
        projects.append({
            'name': parts[0],
            'date': datetime.strptime(parts[1], "%d%m%Y%H%M%S").timestamp(),
            'path': os.getcwd() + '/' + itm
        })
    return projects


def package_project(files_path):
    file_name = os.path.basename(os.path.normpath(files_path))
    print(file_name)
    file = os.getcwd() + "/" + file_name
    shutil.make_archive(file, 'zip', files_path)
    p = Path(file + '.zip')
    p.rename(p.with_suffix('.dip'))
    return file + ".dip"


def extract_project(files_path):
    p = Path(files_path)
    zip_file = p.with_suffix('.zip')
    output = p.with_suffix('')
    p.rename(zip_file)
    if not os.path.exists(output):
        print('path ' + str(output) + ' does not exist, extracting')
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(output)

    os.remove(zip_file)

    name = os.path.basename(os.path.normpath(output))
    parts = name.split("_")
    return {
        'name': parts[0],
        'date': datetime.strptime(parts[1], "%d%m%Y%H%M%S").timestamp(),
        'path': str(output)
    }
