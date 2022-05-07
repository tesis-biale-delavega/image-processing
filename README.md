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
3. Run project
   ```
   export FLASK_APP=app.py (for windows use: setx FLASK_APP "app.py")
   flask run
   ```
