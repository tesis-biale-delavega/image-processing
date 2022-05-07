import os
import subprocess
from pyodm import Node
import docker

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
