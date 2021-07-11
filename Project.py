#!/usr/bin/env python
# coding: utf-8

import os
from pathlib import Path 
import pathlib
import numpy as np
from ALOS.process import *


class ALOS2_pre_post():
        
    def __init__(self,directory,project_name):
        self.directory = directory
        self.project_name = project_name
        self.pre_img_list = None
        self.post_img_list = None
        self.pre_img_ccrs_list = None
        self.post_img_ccrs_list = None
        self.img_crs = None
        
    def create_project_dir(self):
        folder_list = [str(self.project_name),
                       str(self.project_name)+"/Pre_Data",
                       str(self.project_name)+"/Pre_Data/Processed",
                       str(self.project_name)+"/Post_Data",
                       str(self.project_name)+"/Post_Data/Processed",
                       str(self.project_name)+"/Results"]
        
        for item in folder_list:
            pathlib.Path(self.directory+'/'+item).mkdir(parents=True, exist_ok=True)
            
    def unzip_imageries(self):
        self.pre_img_list = unzip(str(self.directory)+'/'+str(self.project_name)+"/Pre_Data",
                                    str(self.directory)+'/'+str(self.project_name)+"/Pre_Data/Processed")
        
        print("All pre images have been unzipped.")
        self.post_img_list = unzip(str(self.directory)+'/'+str(self.project_name)+"/Post_Data",
                                     str(self.directory)+'/'+str(self.project_name)+"/Post_Data/Processed")
        
        print("All post images have been unzipped.")

    def common_crs(self):
        ras_list = np.append(self.pre_img_list,self.post_img_list)
        self.img_crs = cordsys_check(ras_list)

    def reproj_sample(self,scale):
        print("Reprojecting to the specified scale...")
        self.pre_img_ccrs_list = resample(self.pre_img_list,
                                              scale,
                                              self.img_crs,
                                              str(self.directory)+'/'+str(self.project_name)+"/Pre_Data/Processed") 
        print("All pre imageries have been reprojected :",self.img_crs)

        self.post_img_ccrs_list = resample(self.post_img_list,
                                               scale,
                                               self.img_crs,
                                               str(self.directory)+'/'+str(self.project_name)+"/Post_Data/Processed")
        print("All post imageries have been reprojected :",self.img_crs)
        print("Reprojecting completed.")        
              
    def mosaic_imageries(self):
        print("Mosaicing in progress..") 
        #mosaic(self.pre_img_84_list,pre_image_list,
        mosaic(self.pre_img_ccrs_list,
               str(self.directory)+'/'+str(self.project_name)+"/Pre_Data/Processed")
        print("All pre imageries have been mosaiced.")
        #mosaic(self.pre_img_84_list,post_image_list,
        mosaic(self.post_img_ccrs_list,
               str(self.directory)+'/'+str(self.project_name)+"/Post_Data/Processed")
        print("All post imageries have been mosaiced.") 
        print("Mosaicing completed.")
               
    def calibrate_imageries(self): 
        print("Calibrating in progress..")
        # Pre image calibrating
        calibrate(str(self.directory)+'/'+str(self.project_name)+"/Pre_Data/Processed",
                      'Pre')
        print("Pre Mosaic has been calibrated.")
        # Post image calibrating
        calibrate(str(self.directory)+'/'+str(self.project_name)+"/Post_Data/Processed",
                      'Post')
        print("Post Mosaic has been calibrated.")
        
    def speckle_filtering(self,filter_size):
        print("Filtering in progress..")
        # Pre image filtering
        Lee_sigma(str(self.directory)+'/'+str(self.project_name)+"/Pre_Data/Processed"+'/'+'Pre_Mosaic.tif',
                  str(self.directory)+'/'+str(self.project_name)+"/Pre_Data/Processed"+'/'
                  +'Pre_Mosaic_Spec_'+str(filter_size)+'.tif',     
                  filter_size)        
        print("Pre image has been filtered.")
        # Post image filtering
        Lee_sigma(str(self.directory)+'/'+str(self.project_name)+"/Post_Data/Processed"+'/'+'Post_Mosaic.tif',
                  str(self.directory)+'/'+str(self.project_name)+"/Post_Data/Processed"+'/'
                  +'Post_Mosaic_Spec_'+str(filter_size)+'.tif',     
                  filter_size)        
        print("Post image has been filtered.")
                          
    def change_detection(self,filter_size):
        print("Image differencing in progress..")         
        change_gdal(str(self.directory)+'/'+str(self.project_name)+"/Pre_Data/Processed"+'/'
               +'Pre_Mosaic_Spec_'+str(filter_size)+'.tif',
               str(self.directory)+'/'+str(self.project_name)+"/Post_Data/Processed"+'/'
               +'Post_Mosaic_Spec_'+str(filter_size)+'.tif',
               str(self.directory)+'/'+str(self.project_name)+"/Results")        
        print("Change image has been produced.")            
           
    def change_thresholding(self,threshold_value):
        print("Thresholding in progress..") 
        print("Reprojecting in order to Final results to be in WGS84")
        # Adjust according to the resample function
        in_list =  [str(self.directory)+'/'+str(self.project_name)+"/Results"+'/Change.tif']
        wgs84_change_raster = resample(in_list,
                                        1,
                                        'EPSG:4326',
                                        str(self.directory)+'/'+str(self.project_name)+"/Results")
        threshold(wgs84_change_raster[0],
                  str(self.directory)+'/'+str(self.project_name)+"/Results"+'/'+'T_'+str(threshold_value)+'.tif',
                  threshold_value)     
        print("Threshold has been applied.")
        
    def majority_filtering(self,threshold_value,filter_size):
        print("Filtering in progress..")         
        majority(str(self.directory)+'/'+str(self.project_name)+"/Results"+'/'+'T_'+str(threshold_value)+'.tif',
                 str(self.directory)+'/'+str(self.project_name)+"/Results"+'/'+'M_'+str(filter_size)+'_'+'T_'+str(threshold_value)+'.tif',
                 str(self.directory)+'/'+str(self.project_name)+"/Results"+'/'+'M_'+str(filter_size)+'_'+'T_'+str(threshold_value)+'_01'+'.tif',
                 filter_size)        
        print("Change image has been filtered.") 
        
    def polygonize(self,threshold_value,filter_size):
        print("Polygonize in progress..")
        
        ras2poly(str(self.directory)+'/'+str(self.project_name)+"/Results"+'/'+'M_'+str(filter_size)+'_'+'T_'+str(threshold_value)+'_01'+'.tif',
                 str(self.directory)+'/'+str(self.project_name)+"/Results"+'/'+'Detected_flood_water_extent_'+
                 'M_'+str(filter_size)+'_'+'T_'+str(threshold_value)+'.shp')
        

class ALOS2_post():

    def __init__(self,directory,project_name):
        self.directory = directory
        self.project_name = project_name
        self.post_img_list = None
        self.post_img_ccrs_list = None
        self.img_crs = None
        
    def create_project_dir(self):
        folder_list = [str(self.project_name)+"/Post_Data",
                       str(self.project_name)+"/Post_Data/Processed",
                       str(self.project_name)+"/Results"]
        
        for item in folder_list:
            pathlib.Path(self.directory+'/'+item).mkdir(parents=True, exist_ok=True)           
     
    def unzip_imageries(self):
        self.post_img_list = unzip(str(self.directory)+'/'+str(self.project_name)+"/Post_Data",
                                     str(self.directory)+'/'+str(self.project_name)+"/Post_Data/Processed")        
        print("All post images have been unzipped.")

    def common_crs(self):
        ras_list = self.post_img_list
        self.img_crs = cordsys_check(ras_list) 

    def reproj_sample(self,scale):
        print("Reprojecting to the specified scale...")
        self.post_img_ccrs_list = resample(self.post_img_list,
                                               scale,
                                               self.img_crs,
                                               str(self.directory)+'/'+str(self.project_name)+"/Post_Data/Processed")
        print("All post imageries have been reprojected :",self.img_crs)
        print("Reprojecting completed.")      
                
    def mosaic_imageries(self):
        print("Mosaicing in progress..")
        mosaic(self.post_img_ccrs_list,
               str(self.directory)+'/'+str(self.project_name)+"/Post_Data/Processed")
        print("All post imageries have been mosaiced.") 
        print("Mosaicing completed.")
        
    def calibrate_imageries(self):
        print("Calibrating in progress..")
        # Post image calibrating
        calibrate(str(self.directory)+'/'+str(self.project_name)+"/Post_Data/Processed",
                      'Post')
        print("Post Mosaic has been calibrated.")
        
    def speckle_filtering(self,filter_size):
        print("Filtering in progress..")
        # Post image filtering

        Lee_sigma(str(self.directory)+'/'+str(self.project_name)+"/Post_Data/Processed"+'/'+'Post_Mosaic.tif',
                  str(self.directory)+'/'+str(self.project_name)+"/Post_Data/Processed"+'/'
                  +'Post_Mosaic_Spec_'+str(filter_size)+'.tif',     
                  filter_size)        
        print("Post image has been filtered.")
               
    def thresholding(self,filter_size,threshold_value):
        print("Thresholding in progress..") 
        print("Reprojecting in order to Final results to be in WGS84")
        # Adjust according to the resample function
        in_list =  [str(self.directory)+'/'+str(self.project_name)+"/Post_Data/Processed"+'/'
                  +'Post_Mosaic_Spec_'+str(filter_size)+'.tif']
        wgs84_post_raster = resample(in_list,
                                        1,
                                        'EPSG:4326',
                                        str(self.directory)+'/'+str(self.project_name)+"/Post_Data/Processed")
        
        threshold(wgs84_post_raster[0],
                  str(self.directory)+'/'+str(self.project_name)+"/Results"+'/'+'T_'+str(threshold_value)+'.tif',
                  threshold_value)     
        print("Threshold has been applied.") 
               
    def majority_filtering(self,threshold_value,filter_size):
        print("Filtering in progress..") 
        
        majority(str(self.directory)+'/'+str(self.project_name)+"/Results"+'/'+'T_'+str(threshold_value)+'.tif',
                 str(self.directory)+'/'+str(self.project_name)+"/Results"+'/'+'M_'+str(filter_size)+'_'+'T_'+str(threshold_value)+'.tif',
                 str(self.directory)+'/'+str(self.project_name)+"/Results"+'/'+'M_'+str(filter_size)+'_'+'T_'+str(threshold_value)+'_01'+'.tif',
                 filter_size)        
        print("Image has been filtered.")
                       
    def polygonize(self,threshold_value,filter_size):
        print("Polygonize in progress..")
        
        ras2poly(str(self.directory)+'/'+str(self.project_name)+"/Results"+'/'+'M_'+str(filter_size)+'_'+'T_'+str(threshold_value)+'_01'+'.tif',
                 str(self.directory)+'/'+str(self.project_name)+"/Results"+'/'+'Detected_water_extent_'+
                 'M_'+str(filter_size)+'_'+'T_'+str(threshold_value)+'.shp')
        
