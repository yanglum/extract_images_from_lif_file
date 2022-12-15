#!/usr/bin/env python

# environment = readlif
# 
# https://pypi.org/project/readlif/

from readlif.reader import LifFile
import os
import numpy as np
import cv2
from skimage.exposure import rescale_intensity
import yaml

# load settings from YAML file
config = open("config_v10.yml")
var = yaml.load(config, Loader=yaml.FullLoader)['settings']
filename = var['filename']
inpath = var['directory']

convert_16_to_8bit = var['convert_16_to_8bit']
scale_image = var['scale_image']
auto_scale = var['auto_scale']
scale_min = var['min']
scale_max = var['max']

z_stack = var['z_stack']
find_best_z = var['find_best_z_plane']
max_projection = var['max_projection']

return_composite = var['return_composite']
return_channels = var['return_channels']
extension = var['output_file_type']

if z_stack:
	if find_best_z and max_projection:
		print("Please only set either find_best_z or max_projection as 'True', not both!")
		exit()

# Append output file name with settings
name_addon = ''
if convert_16_to_8bit:
	name_addon += '_8bit'
else:
	name_addon += '_16bit'
if scale_image:
	if auto_scale:
		name_addon += '_autoScaled'
	else:
		min_string = ''
		max_string = ''
		for no in scale_min:
			min_string += '-'+str(no)
		for no in scale_max:
			max_string += '-'+str(no)
		name_addon += '_manualScaled_min'+min_string+'_max'+max_string
if z_stack:
	if find_best_z:
		name_addon += '_bestZ'
	elif max_projection:
		name_addon += '_maxProj'

### Functions ###
def convert_and_scale(image):
	"converts 16bit image to 8bit and applies scaling factors"
	if convert_16_to_8bit:
		image = (image/256).astype('uint8')
	if scale_image and auto_scale:
		for i in range(image.shape[2]): # scale each channel
			image[:,:,i] = rescale_intensity(image[:,:,i], in_range='image', out_range='dtype')
	elif scale_image:
		for i in range(image.shape[2]): # scale each channel
			image[:,:,i] = rescale_intensity(image[:,:,i], in_range=(scale_min[i], scale_max[i]), out_range='dtype')
	return image
	
def laplacian_variance(img):
	return np.var(cv2.Laplacian(img, cv2.CV_64F, ksize=21))

def find_best_z_plane_id(img_list):
	if len(img_list) == 1: # if single z, just return the z plane
		max_var = 0
	else:
		lap_vars = []
		for img in img_list:
			lap_vars.append(laplacian_variance(img))
		max_var = lap_vars.index(max(lap_vars)) # z plane with max laplacian variance = most in focus (sharpest edges)
	return max_var

def make_max_projection(img_list):
	return np.max(img_list, axis=0)

def get_single_z(image, time):
	"takes LifImage and outputs numpy array of best z plane for each channel inside a dictionary where keys = tiles (dimension s in Lif)"
	composites = {}
	for j in range(image.dims[4]): # tiles for tiled images (dimension s in Lif)
		if image.bit_depth[0]==16:
			composites[j] = np.full((image.dims[0], image.dims[1], image.channels), 0, dtype=np.uint16)
		elif image.bit_depth[0]==8:
			composites[j] = np.full((image.dims[0], image.dims[1], image.channels), 0, dtype=np.uint8)
			
		for i in range(image.channels): # for each channel of image or z-stack
			if image.bit_depth[0]==16:
				z_list = [np.uint16(np.array(z)) for z in image.get_iter_z(t=time, c=i, m=j)] # convert to numpy array
			elif image.bit_depth[0]==8:
				z_list = [np.uint8(np.array(z)) for z in image.get_iter_z(t=time, c=i, m=j)] # convert to numpy array
			if z_stack==False or find_best_z:				   
				best_z = find_best_z_plane_id(z_list)
				composites[j][:,:,i] = z_list[best_z]
			elif max_projection:
				best_z = make_max_projection(z_list)
				composites[j][:,:,i] = best_z

		if image.bit_depth[0]==16: # only outputs 8 bit currently
			composites[j] = convert_and_scale(composites[j])
	
	return composites
##############

### Script ###
new = LifFile(os.path.join(inpath, filename))
dir_name = filename[:-4]
if os.path.exists(os.path.join(inpath, dir_name))==False:
	os.mkdir(os.path.join(inpath, dir_name))

count = 0
for img in new.get_iter_image(): # each image could be mosaic or single image (single z or z stack) with or without timelapse (TileScan or Position in Lif language)
	for k in range(img.dims.t): # each time in timelapse (dimension t in Lif)
		comp = get_single_z(img, time=k)
		if return_channels:
			for j in comp.keys(): # each tile for tiled images (dimension s in Lif)
				for i in range(comp[j].shape[2]):
					cv2.imwrite(os.path.join(inpath, dir_name, 'image'+str(count)+'_time'+str(k)+'_tile'+str(j)+'_channel'+str(i)+name_addon+extension), comp[j][:,:,i])
				if j%10==0:
					print('.')
		if return_composite:
			for j in comp.keys(): # each tile for tiled images (dimension s in Lif)	  
				if comp[j].dtype=='uint16':
					composite = np.full((comp[j].shape[0], comp[j].shape[1], 3), 0, dtype=np.uint16)
				elif comp[j].dtype=='uint8':
					composite = np.full((comp[j].shape[0], comp[j].shape[1], 3), 0, dtype=np.uint8)
				for i in range(min(comp[j].shape[2], 3)):
					composite[:,:,i] = comp[j][:,:,i]
				cv2.imwrite(os.path.join(inpath, dir_name, 'image'+str(count)+'_time'+str(k)+'_tile'+str(j)+'_composite'+name_addon+extension), composite)
				if j%10==0:
					print('.')
	count+=1
	if count%10==0:
		print('.')

print('images saved to', os.path.join(inpath, dir_name))