#!/usr/bin/env python

import os
import yaml
from utils_v15 import *

# load settings from YAML file
config = open("config_v15.yml")
var = yaml.load(config, Loader=yaml.FullLoader)['settings']
to_extract = var['filename']
inpath = var['directory']

convert_16_to_8bit = var['convert_16_to_8bit']
scale_image = var['scale_image']
auto_scale = var['auto_scale']
scale_min = var['min']
scale_max = var['max']

z_stack = var['z_stack']
find_best_z = var['find_best_z_plane']
max_projection = var['max_projection']
auto_slice = var['auto_slice']
start_slice = var['start_slice']
end_slice = var['end_slice']

return_composite = var['return_composite']
channel_order = var['channel_order']
return_channels = var['return_channels']
extension = var['output_file_type']

if z_stack:
	if find_best_z and max_projection:
		print("Please only set either find_best_z or max_projection as 'True', not both!")
		exit()

if type(to_extract) == str:
	if to_extract == 'ALL':
		filelist = os.listdir(inpath)
	elif to_extract.endswith('.lif'):
		filelist = [to_extract]
	else:
		print("Please make sure the input file is a '.lif' file")
		exit()
elif type(to_extract) == list:
	for file in to_extract:
		if type(file) != str:
			print("Please make sure all files in the input list are strings")
			exit()
		elif not file.endswith('.lif'):
			print("Please make sure all files in the input list are '.lif' files")
			exit()
	filelist = to_extract
else:
	print("Please make sure input file is written as a string or a list of strings")
	exit()

filelist = [x for x in filelist if x.endswith('.lif')]
print('initiating...', end='')
for filename in filelist:
	print('\nextracting from ', filename, end='', flush=True)
	extract_from_lif(filename, inpath, convert_16_to_8bit, scale_image, auto_scale, scale_min, scale_max, z_stack, find_best_z, max_projection, auto_slice, start_slice, end_slice, return_composite, channel_order, return_channels, extension)