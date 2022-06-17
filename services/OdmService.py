import glob
import subprocess
import time
import docker
import os
from pyodm import Node
from pyodm.types import TaskStatus
import cv2
from utils.OdmUtils import get_rgb_config, get_multispectral_config
from services.ProjectManagementService import create_project_dir
from osgeo import gdal
from concurrent.futures import ThreadPoolExecutor
import zipfile
from pathlib import Path
import shutil
import requests


client = docker.from_env()


def startup():
    containers = client.containers.list()
    if not any(container.attrs['Config']['Image'] == 'opendronemap/nodeodm' for container in containers):
        subprocess.Popen(["docker", "run", "-ti", "-p", "3000:3000", "opendronemap/nodeodm"])


def stop_odm():
    client.containers.prune()


def odm_running():
    containers = client.containers.list()
    for container in containers:
        if container.attrs['Config']['Image'] == 'opendronemap/nodeodm':
            return True

    return False


def odm_progress():
    try:
        tasks = requests.get('http://localhost:3000/task/list').json()
        if len(tasks) != 0:
            map = {}
            for task in tasks:
                info = requests.get('http://localhost:3000/task/' + task['uuid'] + '/info').json()
                progress = info['progress']
                status = info['status']['code']
                map[task['uuid']] = {'progress': progress, 'status': status}
            return map, 'ok'
        return None, 'No tasks running'
    except:
        return None, 'No tasks running'


def start_odm(img_path, project_name):
    project_dir = create_project_dir(project_name)
    print('Will save results at:', project_dir)
    multispectral = glob.glob(img_path + '/*.tif')
    rgb = glob.glob(img_path + '/*.jpg')
    names = normalize_multispectral_images(multispectral)
    normalize_rgb_images(rgb)
    main_band = names[0][:-4][-3:]
    print(main_band)

    node = Node('localhost', 3000)

    run_tasks_in_parallel([
        lambda: create_task(node, glob.glob(img_path + '/*.tif'), get_multispectral_config('RED'), 'multispectral', project_dir),
        lambda: create_task(node, glob.glob(img_path + '/*.jpg'), get_rgb_config(), 'rgb', project_dir)])


def create_task(node, imgs, config, img_type, project_dir):
    print('Starting task for', img_type, 'images...')
    task = node.create_task(imgs, config)
    flag = True
    while flag:
        try:
            info = task.info()

            print({
                'image_type': img_type,
                'status': info.status,
                'progress': info.progress,
                'output': info.output,
                'processing_time': str(round(int(info.processing_time)/60000, 2)) + ' minutes',
            })

            if info.status == TaskStatus.COMPLETED:
                flag = False

            time.sleep(5)
        except Exception as exc:
            print('error:', exc)

    try:
        final_dir = project_dir + '/' + img_type
        if not os.path.exists(final_dir):
            os.makedirs(final_dir)
        zip_dir = task.download_zip(final_dir, parallel_downloads=16)
        unzip_file(zip_dir, final_dir)
        if img_type == 'multispectral':
            convert_single_channel_tif_to_png(final_dir + '/odm_orthophoto')
    except Exception as exc:
        print('error saving results:', exc)


def normalize_multispectral_images(imgs):
    imgs.sort(key=lambda x: x[:-4][-3:])
    green = list(filter(lambda x: x[:-4][-3:] == 'GRE', imgs))
    nir = list(filter(lambda x: x[:-4][-3:] == 'NIR', imgs))
    red = list(filter(lambda x: x[:-4][-3:] == 'RED', imgs))
    reg = list(filter(lambda x: x[:-4][-3:] == 'REG', imgs))
    ret = clean_multispectral(green)
    clean_multispectral(nir)
    clean_multispectral(red)
    clean_multispectral(reg)
    return ret


def clean_multispectral(imgs):
    ret = []
    for i, filename in enumerate(imgs):
        print('RENAMING ', filename)
        new_filename = filename.replace('_', '')[:-4]
        final_name = new_filename[:-3] + '_' + new_filename[-3:] + '.tif'
        print(final_name)
        os.rename(filename, final_name)
        ret.append(final_name)

    return ret


def normalize_rgb_images(imgs):
    for i, filename in enumerate(imgs):
        final_name = filename[:-4] + '_RGB.jpg'
        print(final_name)
        os.rename(filename, final_name)


def convert_single_channel_tif_to_png(img_path):
    multispectral = glob.glob(img_path + '/*.tif')
    for img in multispectral:
        print(img)
        dataset = gdal.Open(img)
        image = dataset.ReadAsArray()
        if image.shape[2] == 6:
            green = cv2.merge([image[0], image[0], image[0], image[5]])
            red = cv2.merge([image[1], image[1], image[1], image[5]])
            reg = cv2.merge([image[2], image[2], image[2], image[5]])
            nir = cv2.merge([image[3], image[3], image[3], image[5]])
            blue = cv2.merge([image[4], image[4], image[4], image[5]])

            cv2.imwrite(img[:-4] + '_BLU.tif', blue)
        else:
            green = cv2.merge([image[0], image[0], image[0], image[4]])
            red = cv2.merge([image[1], image[1], image[1], image[4]])
            reg = cv2.merge([image[2], image[2], image[2], image[4]])
            nir = cv2.merge([image[3], image[3], image[3], image[4]])

        cv2.imwrite(img[:-4] + '_GRE.tif', green)
        cv2.imwrite(img[:-4] + '_RED.tif', red)
        cv2.imwrite(img[:-4] + '_REG.tif', reg)
        cv2.imwrite(img[:-4] + '_NIR.tif', nir)


def run_tasks_in_parallel(tasks):
    with ThreadPoolExecutor() as executor:
        running_tasks = [executor.submit(task) for task in tasks]
        for running_task in running_tasks:
            running_task.result()


def unzip_file(file, output):
    p = Path(file)
    zip_file = p.with_suffix('.zip')
    print(zip_file)
    p.rename(zip_file)
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(output)
    os.remove(zip_file)


def package_file(files_path, output):
    shutil.make_archive(output, 'zip', files_path)
    p = Path(output + '.zip')
    print(p)
    p.rename(p.with_suffix('.dip'))
