# Image Processing

Local Python backend for drone image processing

## Requirements

* Docker
* Python

## Installation Guide

1. Create a virtual environment using venv
   ```
   pip install virtualenv
   python3 -m venv image-processing
   . image-processing/bin/activate (for windows use: image-processing\Scripts\activate)
   ```
2. Install project dependencies
   ```
   pip install -r requirements.txt
   ```
   _If an error comes up while installing gdal, windows wheels are provided_
   ```
   pip install GDAL-3.4.3-cp39-cp39-win_amd64.whl
   ```
4. Run project
   ```
   for port 5000:
   export FLASK_APP=app.py (for windows use: setx FLASK_APP "app.py")
   flask run
   
   // or
   for port 5001:
   python app.py
   ```

## Common errors

1. ModuleNotFoundError: No module named 'osgeo'. Solution: run the following line:
   ```
   pip install --global-option=build_ext --global-option="-I/usr/include/gdal" GDAL==`gdal-config --version`    
   ```