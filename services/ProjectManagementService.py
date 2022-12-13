import os
from datetime import datetime
import shutil
from pathlib import Path
import zipfile
import json
import glob
import requests


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
        try:
            ortho_path = os.path.join(os.getcwd(), itm, 'rgb', 'odm_orthophoto', 'odm_orthophoto.png')
            ortho_thumb_path = os.path.join(os.getcwd(), itm, 'rgb', 'odm_orthophoto', 'odm_orthophoto_thumb.png')
            ortho_path = ortho_path if os.path.exists(ortho_path) else None
            ortho_thumb_path = ortho_thumb_path if os.path.exists(ortho_thumb_path) else None

            data = None
            if os.path.exists(itm + '/avg_coordinates.json'):
                with open(itm + '/avg_coordinates.json') as json_file:
                    data = json.load(json_file)

            index_data = []
            for img in glob.glob(itm + "/*.png"):
                img_parts = img.split("_")
                thresh_parts = img.split("threshold")
                index_data.append({
                    'path': os.path.join(os.getcwd(), img),
                    'index': img_parts[len(img_parts) - 1][:-4] if len(thresh_parts) <= 1 else str(img_parts[len(img_parts) - 4][:-1] + '_' + img_parts[len(img_parts) - 2] + '-' + img_parts[len(img_parts) - 1][:-4]),
                    'vector': os.path.join(os.getcwd(), img[:-3] + 'npy') if len(thresh_parts) <= 1 else None
                })

            parts = itm.split("_")
            projects.append({
                'name': parts[0],
                'date': datetime.strptime(parts[1], "%d%m%Y%H%M%S").timestamp(),
                'path': os.path.join(os.getcwd(), itm),
                'orthophoto_path':  ortho_path,
                'orthophoto_thumb_path': ortho_thumb_path,
                "avg_coordinates": data,
                "indexes": index_data
            })
        except Exception:
            print('Could not open project at:', itm)
    projects.sort(key=get_date, reverse=True)
    return projects


def get_date(project):
    return project.get('date')


def export_as_zip(files_path):
    downloads_path = str(Path.home() / "Downloads")
    file_name = os.path.basename(os.path.normpath(files_path))
    file = os.path.join(downloads_path, file_name)
    shutil.make_archive(file, 'zip', files_path)
    return file + ".zip"


def package_project(files_path):
    file_name = os.path.basename(os.path.normpath(files_path))
    file = os.getcwd() + "/" + file_name
    if not os.path.exists(file + '.dip'):
        shutil.make_archive(file, 'zip', files_path)
        p = Path(file + '.zip')
        p.rename(p.with_suffix('.dip'))
    return file + ".dip"


def download_dip(url, file_name):
    response = requests.get(url)
    open(file_name, "wb").write(response.content)
    extract_project(os.getcwd() + "/" + file_name)
    return 'ok'


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
