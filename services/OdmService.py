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
from services.ImageClassifier import classify_images
from osgeo import gdal
from concurrent.futures import ThreadPoolExecutor
import zipfile
from pathlib import Path
import requests
import GPUtil


client = docker.from_env()

types = []


def startup():
    containers = client.containers.list()
    if not any((container.attrs['Config']['Image'] == 'opendronemap/nodeodm:2.8.7' or container.attrs['Config']['Image'] == 'opendronemap/nodeodm:gpu') for container in containers):
        if len(GPUtil.getGPUs()) > 0:
            subprocess.Popen(["docker", "run", "-l", "image-processing-odm", "-ti", "-p", "3000:3000", "--gpus", "all", "opendronemap/nodeodm:gpu"])
        else:
            subprocess.Popen(["docker", "run", "-l", "image-processing-odm", "-ti", "-p", "3000:3000", "opendronemap/nodeodm:2.8.7"])


def stop_odm():
    client.containers.prune(filters={"label": "image-processing-odm"})


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
            for idx, task in enumerate(tasks):
                info = requests.get('http://localhost:3000/task/' + task['uuid'] + '/info').json()
                progress = info['progress']
                status = info['status']['code']
                processing_time = info['processingTime']
                map[types[idx]] = {'id': task['uuid'], 'progress': progress, 'status': status, 'processingTime': processing_time}
            return map, 'ok'
        return None, 'No tasks running'
    except:
        return None, 'No tasks running'


def start_odm(img_path, project_name):
    project_dir = create_project_dir(project_name)
    images_map = classify_images(img_path)
    print('Will save results at:', project_dir)
    normalize_multispectral_images(images_map)
    normalize_rgb_images(images_map['rgb_images'])
    main_band = 'Green'
    node = Node('localhost', 3000)

    run_tasks_in_parallel([
        lambda: create_task(node, glob.glob(img_path + '/*.tif'), get_multispectral_config(main_band), 'multispectral', project_dir),
        lambda: create_task(node, glob.glob(img_path + '/*.jpg'), get_rgb_config(), 'rgb', project_dir)])

    return project_dir


def create_task(node, imgs, config, img_type, project_dir):
    print('Starting task for', img_type, 'images')
    task = node.create_task(imgs, config)
    print('started', img_type)
    types.append(img_type)
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

            if info.status == TaskStatus.COMPLETED or info.status == TaskStatus.FAILED:
                print('out', info.status)
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

    requests.post('http://localhost:3000/task/remove', {'uuid': task.uuid}).json() # TODO check if download is finished before removing the task
    types.remove(img_type)


def normalize_multispectral_images(imgs):
    green = imgs['gre_images']
    nir = imgs['nir_images']
    red = imgs['red_images']
    reg = imgs['reg_images']
    blue = imgs['blu_images']
    ret = clean_multispectral(green, 'GRE')
    clean_multispectral(nir, 'NIR')
    clean_multispectral(red, 'RED')
    clean_multispectral(reg, 'REG')
    clean_multispectral(blue, 'BLUE')
    return ret


def clean_multispectral(imgs, band):
    ret = []
    for i, filename in enumerate(imgs):
        if (band == 'BLUE' and filename[-9:] != '_' + band + '.tif') or (band != 'BLUE' and filename[-8:] != '_' + band + '.tif'):
            new_filename = filename.replace('_', '')
            final_name = new_filename[:-4] + '_' + band + '.tif'
            os.rename(filename, final_name)
            print('Renaming ', filename, 'to', final_name)
            ret.append(final_name)
        else:
            ret.append(filename)

    return ret


def normalize_rgb_images(imgs):
    for i, filename in enumerate(imgs):
        if filename[-8:] != '_RGB.jpg':
            final_name = filename[:-4] + '_RGB.jpg'
            os.rename(filename, final_name)


def convert_single_channel_tif_to_png(img_path):
    multispectral = glob.glob(img_path + '/*.tif')
    for img in multispectral:
        dataset = gdal.Open(img)
        image = dataset.ReadAsArray()
        if image.shape[0] == 6:
            green = cv2.merge([image[1], image[1], image[1], image[5]])
            red = cv2.merge([image[2], image[2], image[2], image[5]])
            reg = cv2.merge([image[3], image[3], image[3], image[5]])
            nir = cv2.merge([image[4], image[4], image[4], image[5]])
            blue = cv2.merge([image[0], image[0], image[0], image[5]])
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
