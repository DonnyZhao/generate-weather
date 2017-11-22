#/bin/bash

#####Python environment setup ######

##prepare to install python 2.7

##step 1: install a few necessary packages that contain python27
## "-y" implies "yes" choice 'Yes' automatically
sodu yum -y install centos-release-scl

##step 2: install python version 2.7
sodu yum install python27

## step 4: enable python version 2.7 to override older version
sodu scl enable python27 bash

## step 5: install pip
sodu wget https://bootstrap.pypa.io/get-pip.py
sodu python  get-pip.py

## step 6: install a few necessrery libary
pip install GDAL
pip install requests
pip install Pillow
pip install rasterio
pip install affine
pip install pyproj
pip install numpy
scl enable python27 bash
