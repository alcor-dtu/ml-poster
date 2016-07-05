# -*- coding: utf-8 -*-
"""
Created on Tue Jul 05 10:52:47 2016

@author: alcor
"""

#!/usr/bin/env python
import inspect
import os
import sys
import argparse
from numpy import fromfile
import numpy as np 
import scipy.misc
import pickle

import errno

def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
            
def get_script_dir(follow_symlinks=True):
    if getattr(sys, 'frozen', False): # py2exe, PyInstaller, cx_Freeze
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)

def get_script_complete_path(follow_symlinks = True):
    return get_script_dir(follow_symlinks) + "\\" + sys.argv[0]

path = get_script_dir()
parser = argparse.ArgumentParser()
parser.add_argument('-i','--input', required=False, default=".", dest="input_folder", help='The input folder where to find the images.')
parser.add_argument('-o','--out', required=False, default="output", dest="output_folder", help='The output file.')
parser.add_argument('-n','--patch-size', required=False, nargs=2, default="32 32", dest="patch_size", help='The patch size for the image.')
parser.add_argument('-p','--padding-size', required=False, nargs=2, default="2 2", dest="pad_size", help='The overlapping size for each patch.')

args = parser.parse_args(sys.argv[1:])

tuples = []
print("Scanning for files...")
for root, dirs, files in os.walk(args.input_folder):
    for name in files:
        if name.endswith((".txt")):
            full_path = os.path.join(root, name)
            name_only = name
            raw_name = os.path.join(root, name[:-4] + ".raw")
            if(os.path.isfile(raw_name)) :
                print("Found raw file: " + name + " " +  name[:-4] + ".txt")    
                tuples.append((full_path, raw_name, name[:-4]))
    
output = args.output_folder
print("Starting processing of files...")

names = ["r", "g", "b"]

patch_size = np.array([int(s) for s in args.patch_size.split()])
pad_size = np.array([int(s) for s in args.pad_size.split()])

step = patch_size - pad_size
make_sure_path_exists(output)

for t in tuples:
    path = output
    print("Processing " + t[0] +" in folder "+ path + "...")
    f = open(t[0])
    lines = [line.rstrip('\n') for line in f]    
    frame = int(lines[0])
    width, height = [int(i) for i in lines[1].split(' ')]      
    n_patches = np.array([width, height]) // step

    print("Found file with w=" + str(width) + ", h=" + str(height) + ", frame=" + str(frame))
    f.close()
    raw_f = open(t[1])
    size = width * height * 3
    data = fromfile(raw_f, np.float32, -1)
    raw_f.close()
    colors = [data[range(i,data.size,3)] for i in range(3)]
    colors = [np.reshape(r, (width, height)) for r in colors]
    d = {}
    for i in range(3):
        color = np.flipud(colors[i])
        name = names[i]
        file_base = path + "/" + t[2] + "_" + name 
        patches = np.zeros((n_patches[0]*n_patches[1], patch_size[0]*patch_size[1]))
        for j in range(n_patches[0]):
            for k in range(n_patches[1]):
                initial_pixel = np.array([j,k])*step
                final_pixel = initial_pixel + patch_size
                patch = color[initial_pixel[0]:final_pixel[0],:][:,initial_pixel[1]:final_pixel[1]]
                #scipy.misc.toimage(patch, cmin=0.0, cmax=1.0).save(file_base+ "_" + str(j) + "_" + str(k) + ".png")
                patch = np.reshape(patch, patch.size)
                patches[j * n_patches[1] + k] = patch
        d[name] = {"data" : patches}
    ff = open(path + "/" + t[2] + ".dat", "w+")
    pickle.dump(d, ff)
    ff.close()