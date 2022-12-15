# extract_lif_file
Extracts images from Lif files and outputs in common image formats

Requirements:
python 3.9.12
readlif 0.6.5
numpy 1.21.5
opencv-python 4.5.5.64
scikit-image 0.19.2
PyYAML 6.0

Takes Lif file and extracts each image (TileScan, Position, etc) and outputs the image (one for each tile in dimension "s" for mosaic images and one for each time in dimension "t" for timelapse images) with user-defined histogram and z project adjustment.

Currently doesn't really support 16 bit images (converting to 8 bit is preferred)
Currently doesn't support more than 3 channels for outputing composites
Currently only outputs channels in the pre-determined order blue, green, red for outputing composites
