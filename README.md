# extract_images_from_Lif_file
Extracts images from Lif files and outputs in common image formats

Takes Lif file and extracts each image (TileScan, Position, etc) and outputs the image (one for each tile in dimension "s" for mosaic images and one for each time in dimension "t" for timelapse images) with user-defined histogram and z project adjustment.

To run:
1) Adjust settings using the config.yml file
2) Then run the save_lif_as_tif.py script

Requirements:
- python 3.9.12
- readlif 0.6.5
- numpy 1.21.5
- opencv-python 4.5.5.64
- scikit-image 0.19.2
- PyYAML 6.0

Caveats:
1) Currently doesn't support more than 3 channels for outputing composites
2) Currently only outputs channels in the pre-determined order blue, green, red for outputing composites

Change log:
- 02/11/23 (v14): added ability to specify channel color order when returning composites (still only able to return 3 channels)
- 12/15/22 (v13): fully compatible with 16bit
