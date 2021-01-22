# SA-Flood-Detection-ALOS2
A Flood Mapping Approach ( Change Thresholding) Using ALOS-2 PALSAR-2 Synthetic Aperture Radar Data with Open Source Python libraries.

# Objective 
This script will give the user access to process ALOS-2 PALSAR-2 (Synthetic Aperture Radar) data to detect water areas after a disaster, especially a flood, typhoon, or storm.


# Functionality
This flood mapping approach gives the user flood water area detection ALOS-2 PALSAR-2 data based on threshold technique and it also capable of getting data from Optemis system which is explained before.


Sentinel Asia and Optemis System

The Sentinel Asia (https://sentinel-asia.org/) is a voluntary basis initiative led by the Asia-Pacific Regional Space Agency Forum (APRSAF) to support disaster management activity Asia-Pacific region by applying the WEB-GIS technology and space-based technology, such as earth observation satellites data. When a disaster occurs, all earth observation data (Specially ALOS-2 PALSAR-2 data) will be available to the Value-Adder Organization through this initiative. In that case, all the satellite data will be provided for a system called Optemis (https://optemis.sentinel-asia.org/) which, is used to share earth observation data and processed results for Sentinel Asia Members.

The following script can also be used to acquire ALOS-2 Data from the Optemis system and process it according to the requirement. (Only post-event data/ Both Pre and Post data)



Then the flood extraction is carried out according to the instruction of the Flood_Module_ALOS2.py file. This file includes the main processing steps such as change image generation, thresholding, majority filtering, and raster polygonization. (For both cases : Pre-Post/ Post only)

# Installation Steps

1. Install anaconda

You can find the installation instruction from this Link.
https://docs.anaconda.com/anaconda/install/

After the installation,install the libraries mentioned below using Anaconda prompt.

    pip install glob2 DateTime GDAL numpy whitebox pathlib rasterio pprint36 zipfile36 paramiko re2 pytest-shutil

2. Running Scripts

The main script (Realtime-Sentinel1-Flood-Mapping.ipynb) runs in jupyter notebook environment and the Flood_OST_S1.py can be placed in the same directory as the main script, or it can be placed in the Lib folder of the working anaconda environment (e.g., " C:\Users\User_name\Anaconda3\Lib"). 
Then you can import the Flood_OST_S1 module to the main script. Sentinel1Flood is the class for the processing of the Sentinel-1 ARD data for flood detection.
 
    from Flood_Module_ALOS2 import ALOS2_pre_post
    
    from Flood_Module_ALOS2 import ALOS2_post

# Methodology

This below graph shows the method adopted in this approach. (Pre-Post/Post only)

<img src="https://github.com/chathumal93/Realtime-Sentinel1-Flood-Mapping/blob/master/Images/Method.png" width="400" height="400" />

# Output
The results will include the following;

* Processed pre-event and post-event tif files. (In Flood_Result Folder)
* Threshold and majority filtered tif files. 
* Detected Flood water shp file.

![](Images/Output_Structure.png)

Result Floder Structure

![](Images/Flood_Result_QGIS.png)

Output visualization on QGIS
