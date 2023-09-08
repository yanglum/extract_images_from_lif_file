#!/usr/bin/env python

# environment = readlif
# 
# https://pypi.org/project/readlif/

from readlif.reader import LifFile
import os
import numpy as np
import cv2
from skimage.exposure import rescale_intensity

def convert_and_scale(image, convert_16_to_8bit, scale_image, auto_scale, scale_min, scale_max):
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

#def auto_z_slices(img_list):
#
#	 use laplacian variance to determine which z slices are good
#	 
#	 return same output as make_max_projection

def make_max_projection(img_list, start_slice, end_slice):
	if end_slice == 'end':
		img_list = img_list[start_slice:]
	else:
		img_list = img_list[start_slice:end_slice]
	return np.max(img_list, axis=0)

def get_single_z(image, convert_16_to_8bit, scale_image, auto_scale, scale_min, scale_max, z_stack, find_best_z, max_projection, auto_slice, start_slice, end_slice, time):
	"takes LifImage and outputs numpy array of best z plane for each channel inside a dictionary where keys = tiles (dimension s in Lif); this is the key function"
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
				#if auto_slice:
					#best_z = auto_z_slices(z_list)
				best_z = make_max_projection(z_list, start_slice, end_slice)
				composites[j][:,:,i] = best_z

		composites[j] = convert_and_scale(composites[j], convert_16_to_8bit, scale_image, auto_scale, scale_min, scale_max)
	
	return composites

def extract_from_lif(filename, inpath, convert_16_to_8bit, scale_image, auto_scale, scale_min, scale_max, z_stack, find_best_z, max_projection, auto_slice, start_slice, end_slice, return_composite, channel_order, return_channels, extension):
	# Append output file name with settings
	name_addon = ''
	if convert_16_to_8bit:
		name_addon += '_8bit'
	else:
		name_addon += '_16bit'
	if scale_image:
		if auto_scale:
			name_addon += '_autoScale'
		else:
			min_string = ''
			max_string = ''
			for no in scale_min:
				min_string += '-'+str(no)
			for no in scale_max:
				max_string += '-'+str(no)
			name_addon += '_manScale_'+min_string+'_'+max_string
	if z_stack:
		if find_best_z:
			name_addon += '_bestZ'
		elif max_projection:
			name_addon += '_maxProj_'+str(start_slice)+'-'+str(end_slice)
			
	new = LifFile(os.path.join(inpath, filename))
	dir_name = filename[:-4]
	if os.path.exists(os.path.join(inpath, dir_name))==False:
		os.mkdir(os.path.join(inpath, dir_name))

	count = 0
	for img in new.get_iter_image(): # each image could be mosaic or single image (single z or z stack) with or without timelapse (TileScan or Position in Lif language)
		for k in range(img.dims.t): # each time in timelapse (dimension t in Lif)
			if img.dims.t == 1:
				time_addon = ''
			else:
				time_addon = '_time'+str(k)
			comp = get_single_z(img, convert_16_to_8bit, scale_image, auto_scale, scale_min, scale_max, z_stack, find_best_z, max_projection, auto_slice, start_slice, end_slice, time=k)
			if return_channels:
				for j in comp.keys(): # each tile for tiled images (dimension s in Lif)
					if len(comp.keys()) == 1:
						tile_addon = ''
					else:
						tile_addon = '_tile'+str(j)
					for i in range(comp[j].shape[2]):
						cv2.imwrite(os.path.join(inpath, dir_name, 'image'+str(count)+time_addon+tile_addon+'_channel'+str(i)+name_addon+extension), comp[j][:,:,i])
					if j%10==0:
						print('.', end='', flush=True)
			if return_composite:
				channel_dict = {'red':2, 'green':1, 'blue':0} # default channel order is BGR
				channel_order_translated = [channel_dict[x] for x in channel_order]
				for j in comp.keys(): # each tile for tiled images (dimension s in Lif)
					if len(comp.keys()) == 1:
						tile_addon = ''
					else:
						tile_addon = '_tile'+str(j)
					if comp[j].dtype=='uint16':
						composite = np.full((comp[j].shape[0], comp[j].shape[1], 3), 0, dtype=np.uint16)
					elif comp[j].dtype=='uint8':
						composite = np.full((comp[j].shape[0], comp[j].shape[1], 3), 0, dtype=np.uint8)
					for i in range(min(comp[j].shape[2], 3)):
						composite[:,:,channel_order_translated[i]] = comp[j][:,:,i]
					cv2.imwrite(os.path.join(inpath, dir_name, 'image'+str(count)+time_addon+tile_addon+'_composite'+name_addon+extension), composite)
					if j%10==0:
						print('.', end='', flush=True)
		count+=1
		if count%10==0:
			print('.', end='', flush=True)
	# if name is too long, won't output file
	print('images saved to', os.path.join(inpath, dir_name), end='', flush=True)