#!/usr/bin/env python
# coding: utf-8


import os
from zipfile import ZipFile
import gdal
import glob
import numpy as np
import pathlib
import rasterio
from rasterio.warp import calculate_default_transform,reproject, Resampling
from rasterio.merge import merge
from rasterio import Affine
from rasterio.enums import Resampling
#from rasterio.windows import Window
from shapely.geometry import Point, LineString, Polygon,box
from whitebox.WBT.whitebox_tools import WhiteboxTools
wbt = WhiteboxTools()


def unzip(in_path,out_path):
    while True:
        polarization = input("Polarization(HH/HV):")
        if polarization not in ('HH','HV'):
            print("Not an appropriate choice.")
        else:
            break

    #Unzip files according to polarization
    img_list = np.array([])
    for currentFile in pathlib.Path(in_path).glob("*.zip"):
        with ZipFile(currentFile, 'r') as zipObj:
            listOfFileNames = zipObj.namelist()
            for fileName in listOfFileNames:
                if polarization == "HH":
                    if fileName.startswith('IMG-HH-ALOS2') and fileName.endswith('.tif'):
                        filePath = out_path+'/'+fileName
                        print(filePath)
                        img_list = np.append(img_list,filePath)                      
                        zipObj.extract(fileName,out_path)
                else:
                    if fileName.startswith('IMG-HV-ALOS2') and fileName.endswith('.tif'):
                        filePath = out_path+'/'+fileName
                        print(filePath)
                        img_list = np.append(img_list,filePath)         
                        zipObj.extract(fileName,out_path)                                      
    return img_list

def resample(raster_path_list,upscale_factor,dst_crs,outpath):
    #dst_crs = 'EPSG:4326'/'EPSG:3857'
    img_path_list = np.array([])
    
    for n in range(len(raster_path_list)):

        with rasterio.open(raster_path_list[n]) as src:
            transform, width, height = calculate_default_transform(
                src.crs, dst_crs, src.width* upscale_factor, src.height* upscale_factor, *src.bounds)
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': dst_crs,
                'transform': transform,
                'width': width,
                'height': height
            })

            with rasterio.open((outpath+'/'+raster_path_list[n].split('/')[-1].split('.tif')[0]+'-CCRS.tif'), 'w', **kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.bilinear)
            
            img_path_list = np.append(img_path_list,str(outpath+'/'+raster_path_list[n].split('/')[-1].split('.tif')[0]+'-CCRS.tif'))
                                   
    src.close()
    dst.close()
    # Remove unzipped files and carry out with CCRS images
    for item in raster_path_list:
        os.remove(item)
    return img_path_list

def mosaic(in_list,out_path): 
    RasList = []
    for x in range(len(in_list)):
        raster = rasterio.open(in_list[x])
        RasList.append(raster)
    #Mosaicing
    mos_img, out_trans = merge(RasList)
        
    #Metadata gathering from a one image(last image)
    rasterLast = rasterio.open(in_list[len(in_list)-1])
    metaData = rasterLast.meta.copy()

    #Update the metadata
    mosaic_meta = metaData

    #writing the new mosaic raster
    mosaic_meta.update({"driver": "GTiff",
                        "height": mos_img.shape[1],
                        "width": mos_img.shape[2],
                        "transform": out_trans,
                        "compress": 'lzw' })

    with rasterio.open(out_path+'/Mosaic.tif', "w", **mosaic_meta) as dest:
        dest.write(mos_img)
        dest.close()
              
def calibrate(product_path,raster_prefix):
    with rasterio.open(product_path+'/'+'Mosaic.tif') as dataset:
        band1 = dataset.read(1)
        band1 = np.where(band1 == 0, np.nan, band1)
        band1_calib = 20*np.log10(band1)-83
        band1_calib = np.float32(band1_calib)

        metaCalib = dataset.meta.copy()

        #writing the new mosaic raster
        metaCalib.update({"driver": "GTiff",
                        "height": dataset.shape[0],
                        "width": dataset.shape[1],                    
                        'dtype':'float32',    
                        "compress": 'lzw' })
            
    with rasterio.open(product_path+'/'+raster_prefix+'_Mosaic.tif', "w", **metaCalib) as dest:

        dest.write(band1_calib,1)
        dest.close()            
    dataset.close()
    os.remove(product_path+'/'+'Mosaic.tif')
       
def Lee_sigma(in_path,out_path,filter_size): 
    def my_callback(value):
        if not "%" in value:
            print(value)
    #Speckle filtering
    wbt.lee_sigma_filter(in_path,out_path, 
                         filterx=filter_size, 
                         filtery=filter_size, 
                         sigma=10.0, 
                         m=5.0, 
                         callback=my_callback)
    
def threshold(in_path,product_path,threshold_value):    
    np.warnings.filterwarnings('ignore')
    with rasterio.open(in_path) as dataset:        
        band1 = dataset.read(1)
        threshold = np.where(band1 < threshold_value,1,0)
        metaCalib = dataset.meta.copy()
        #writing the new mosaic raster
        metaCalib.update({"driver": "GTiff",
                        "height": dataset.shape[0],
                        "width": dataset.shape[1],                    
                        'dtype':'int32',    
                        "compress": 'lzw' })
            
    with rasterio.open(product_path, "w", **metaCalib) as dest:

        dest.write(threshold,1)
        dest.close()            
    dataset.close()
    
def majority(in_path,product_path,final_path,filter_size):   
    # Running status
    def my_callback(value):             
        if not "%" in value:
            print(value)
    #Majority filter        
    wbt.majority_filter(in_path,
                        product_path,
                        filterx=filter_size,
                        filtery=filter_size,
                        callback=my_callback)
    
    with rasterio.open(product_path) as dataset:
        band1 = dataset.read(1)
        selection = np.where(band1 == 1,1,0)
        metaCalib = dataset.meta.copy()
        #writing the new mosaic raster
        metaCalib.update({"driver": "GTiff",
                "height": dataset.shape[0],
                "width": dataset.shape[1],                    
                'dtype': 'int32',    
                "compress": 'lzw' })
        
        with rasterio.open(final_path, "w", **metaCalib) as dest:
            dest.write(selection,1)
            dest.close()            
        dataset.close()
    os.remove(product_path)
                    
def ras2poly(in_path,product_path):    
    #Printing the running status
    def my_callback(value):             
        if not "%" in value:
            print(value)

    wbt.raster_to_vector_polygons(in_path,
                                  product_path,
                                  callback=my_callback)
                  
def change_gdal(img01,img02,out_path):
    pre_image  = img01
    post_image = img02

    raster_pre=gdal.Open(pre_image)
    raster_post=gdal.Open(post_image)

    pre_band = raster_pre.GetRasterBand(1)
    post_band = raster_post.GetRasterBand(1)

    gtpost =raster_post.GetGeoTransform()
    gtpre =raster_pre.GetGeoTransform()

    #Pre and post top(x,y) bottom(x,y) co-ordinates
    post_bound  = [gtpost[0], gtpost[3], 
                   gtpost[0] + (gtpost[1] * raster_post.RasterXSize), gtpost[3] + (gtpost[5] * raster_post.RasterYSize)]
    pre_bound   = [gtpre[0] , gtpre[3] , 
                   gtpre[0]  + (gtpre[1]  * raster_pre.RasterXSize) , gtpre[3]  + (gtpre[5]  * raster_pre.RasterYSize)]

    #Finding the intersection boundry
    intersection = [max(post_bound[0], pre_bound[0]), 
                    min(post_bound[1], pre_bound[1]), 
                    min(post_bound[2], pre_bound[2]),
                    max(post_bound[3], pre_bound[3])]

    post_bound_pix = [abs(round((gtpost[0]-intersection[0])/gtpost[1])),
                      abs(round((gtpost[3]-intersection[1])/gtpost[5])),
                      abs(round((gtpost[0]-intersection[2])/gtpost[1])),
                      abs(round((gtpost[3]-intersection[3])/gtpost[5]))]

    pre_bound_pix = [abs(round((gtpre[0]-intersection[0])/gtpre[1])),
                     abs(round((gtpre[3]-intersection[1])/gtpre[5])),
                     abs(round((gtpre[0]-intersection[2])/gtpre[1])),
                     abs(round((gtpre[3]-intersection[3])/gtpre[5]))]

    post_intersect = post_band.ReadAsArray(post_bound_pix[0],post_bound_pix[1],post_bound_pix[2] - post_bound_pix[0],
                                           post_bound_pix[3] - post_bound_pix[1],post_bound_pix[2] - post_bound_pix[0],
                                           post_bound_pix[3] - post_bound_pix[1],buf_type=gdal.GDT_Float32)

    pre_intersect = pre_band.ReadAsArray(pre_bound_pix[0],pre_bound_pix[1],pre_bound_pix[2] - pre_bound_pix[0],
                                         pre_bound_pix[3] - pre_bound_pix[1],pre_bound_pix[2] - pre_bound_pix[0], 
                                         pre_bound_pix[3] - pre_bound_pix[1],buf_type=gdal.GDT_Float32)

    nrows = pre_bound_pix[3] - pre_bound_pix[1]
    ncols = pre_bound_pix[2] - pre_bound_pix[0]

    #Getting the  change image using the numpy array operations
    change_array = np.subtract(post_intersect,pre_intersect)


    geotransform=([intersection[0],gtpost[1],gtpost[2],intersection[1],gtpost[2], gtpost[5]]) 
    proj = raster_pre.GetProjection()

    output_raster = gdal.GetDriverByName('GTiff').Create(out_path+'/'+'Change.tif',ncols, nrows, 1 ,gdal.GDT_Float32)
    output_raster.SetGeoTransform(geotransform)                                                                                                        
    output_raster.SetProjection(proj) 
    output_raster.GetRasterBand(1).SetNoDataValue(-99)
    output_raster.GetRasterBand(1).WriteArray(change_array) 
    output_raster.FlushCache()
    print("Change image has been created using the intersection region")        
        
def cordsys_check(raster_list):       
    crs_list = []
    for x in raster_list:
        with rasterio.open(x) as src:
            crs_list.append(src.crs)            
            src.close()
            
    if len(set(crs_list))==1:
        print("All images in same co-sys")
        def_crs = crs_list[0]
    else:
        print("Reproject needed for same co-sys")
        def_crs = crs_list[0]
    return def_crs
        
