import os
import datetime
import glob
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
import numpy as np
from whitebox.WBT.whitebox_tools import WhiteboxTools
from zipfile import ZipFile 
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio import Affine,merge
from pathlib import Path 

import paramiko
import re
import shutil

# White toolbox integration
wbt = WhiteboxTools()


# Main two classes for directory making and unzipping files
class ALOS2_pre_post():
    
    def __init__(self,directory,project_name):            
        self.directory = directory
        self.project_name = project_name
        self.local_pre_path = None
        self.local_post_path = None
        self.downlink_pre_path = None
        self.downlink_post_path = None
        

    
    ########################## Creating the project directories ###########################
    
    def create_project_dir(self,working_dir):
        folder_list = [str(self.project_name),str(self.project_name)+"/1_Pre_data",str(self.project_name)+"/1_Pre_data/HH_imgs",str(self.project_name)+"/1_Post_Data",str(self.project_name)+"/1_Post_Data/HH_imgs",str(self.project_name)+"/2_Results"]
        for item in folder_list:
            Path(working_dir+'/'+item).mkdir(parents=True, exist_ok=True)
    
    ######### List data paramiko sftp connection ###########
    def list_ALOS_data(self,activation_name,sftp_key):

        #Activation name eg- 20200603-India-Flood-Storm-00373
        #paramiko.util.log_to_file('D:/6_SA_2020_Plan/ost/logs/paramiko.log')
        host = ""
        port = ""
        # private key given to us has to be convert into rsa or pem format 
        #sftp_key = "D:/6_SA_2020_Plan/ost/keys/****"
        username = ""
        password = ""

        sftp_key = paramiko.RSAKey.from_private_key_file(sftp_key)
        transport = paramiko.Transport((host, port))
        transport.start_client(event=None, timeout=15)
        transport.get_remote_server_key()
        transport.auth_publickey(username, sftp_key, event=None)
        transport.auth_password(username, password, event=None)
        sftp = paramiko.SFTPClient.from_transport(transport)

        #Show data in the Optemis system
        remote_archive = '/Sentinel-Asia/Emergency_Response/'+str(activation_name)+'/ARCHIVE/jp_jaxa'
        remote_observe = '/Sentinel-Asia/Emergency_Response/'+str(activation_name)+'/OBSERVE/jp_jaxa'
        Jaxa_pre_list = sftp.listdir(remote_archive)
        Jaxa_post_list = sftp.listdir(remote_observe) 


        post_downlist = []
        pre_downlist = []
        post_down_link = []
        pre_down_link = []

        #for download purpose ALOS pre post
        local_path_pre = []
        local_path_post = []

        ######## Post Links ##################
        for x in Jaxa_post_list:
            y = re.search(".zip$", x)
            if y:
                post_downlist.append(str(x))
        print('Available post file to download')
        print(post_downlist)

        for x in post_downlist:
            dl = remote_observe + "/" + str(x)
            post_down_link.append(dl)

        ######## Pre Links ##################

        for x in Jaxa_pre_list:
            y = re.search(".zip$", x)
            if y:
                pre_downlist.append(str(x))
        print('Available pre file to download')
        print(pre_downlist)

        for x in pre_downlist:
            dl = remote_archive + "/" + str(x)
            pre_down_link.append(dl)

        ######## local path links #############
        #post
        for x in post_downlist:
            da2 = self.directory+"/"+str(self.project_name)+'/1_Post_Data' + "/" + str(x)
            local_path_post.append(da2)

        #pre
        for x in pre_downlist:
            da2 = self.directory+"/"+str(self.project_name)+'/1_Pre_Data' + "/" + str(x)
            local_path_pre.append(da2)
 
        self.local_pre_path = local_path_pre
        self.local_post_path = local_path_post
        self.downlink_pre_path = pre_down_link
        self.downlink_post_path = post_down_link
        
        sftp.close()
        transport.close()

        ######### Downlaod data #######
    def download_ALOS_data(self,pre,post,sftp_key):
        
        host = ""
        port = ""
        # private key given to us has to be convert into rsa or pem format 
        #sftp_key = "D:/6_SA_2020_Plan/ost/keys/****"
        username = ""
        password = ""

        sftp_key = paramiko.RSAKey.from_private_key_file(sftp_key)
        transport = paramiko.Transport((host, port))
        transport.start_client(event=None, timeout=15)
        transport.get_remote_server_key()
        transport.auth_publickey(username, sftp_key, event=None)
        transport.auth_password(username, password, event=None)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
                
        if pre == True:
            #pre data
            for i in range(len(self.downlink_pre_path)):
                sftp.get(str(self.downlink_pre_path[i]),str(self.local_pre_path[i]))

        print("Pre files have been downloaded")

        if post == True:

            for i in range(len(self.downlink_post_path)):
                sftp.get(str(self.downlink_post_path[i]),str(self.local_post_path[i]))

        print("Post files have been downloaded")
        self.local_pre_path = None
        self.local_post_path = None
        self.downlink_pre_path = None
        self.downlink_post_path = None
        sftp.close()
        transport.close()
            
    
        
    ########################## Unziping ##################################################
    
    
    def unzip_to_mosaic(self,pre_mosaic,post_mosaic):
        
        
        for file in glob.glob(self.directory+"/"+str(self.project_name)+'/1_Post_Data'+'/*.zip'):
            with ZipFile(file,'r') as outzip:                    
                with outzip.open(outzip.namelist()[0],'r') as inzip:
                    with ZipFile(inzip,'r') as inner: 
                        for img in inner.namelist():
                            if img.startswith('IMG-HH'):
                                inner.extract(img, self.directory+"/"+str(self.project_name)+'/1_Post_Data/HH_imgs')
        
        print("###########  ALOS_pre_post  ##########")
        print("All Post Files have been unzipped")
        
        for file in glob.glob(self.directory+"/"+str(self.project_name)+'/1_Pre_Data'+'/*.zip'):
            with ZipFile(file,'r') as outzip:                    
                with outzip.open(outzip.namelist()[0],'r') as inzip:
                    with ZipFile(inzip,'r') as inner: 
                        for img in inner.namelist():
                            if img.startswith('IMG-HH'):
                                inner.extract(img, self.directory+"/"+str(self.project_name)+'/1_Pre_Data/HH_imgs')
        
        print("###########  ALOS_pre_post  ##########")
        print("All Pre Files have been unzipped")
            
        if post_mosaic == True:           
            src_mosic_files = []

            for ext_img in glob.glob(self.directory+"/"+str(self.project_name)+'/1_Post_Data/HH_imgs'+"/*"):
                ext_ras = rasterio.open(ext_img)
                src_mosic_files.append(ext_ras)

            #print(src_mosic_files)

            #single mosaic array and transformartion info
            mosaic, out_trans = merge.merge(src_mosic_files)

            # Writing the mosaic
            mosaic_meta = ext_ras.meta.copy()

            # Update the metadata
            mosaic_meta.update({"driver": "GTiff",
                             "height": mosaic.shape[1],
                             "width": mosaic.shape[2],
                             "transform": out_trans,}
                           )
            with rasterio.open(self.directory+"/"+str(self.project_name)+'/1_Post_Data/HH_imgs'+"/"+"post_stage00.tif", "w", **mosaic_meta) as dest:
                dest.write(mosaic)
                print("###########  Raster Info  ##########")
                print(dest.meta)
            print("###########  ALOS_pre_post  ##########")
            print("Post Mosaic file has been created")
            
        
            
        else:
            with rasterio.open(glob.glob(self.directory+"/"+str(self.project_name)+'/1_Post_Data/HH_imgs' +"/*.tif")[0]) as src:
                meta = src.meta.copy()
                data = src.read(out_shape=(src.count, src.height, src.width))
                with rasterio.open(self.directory+"/"+str(self.project_name)+'/1_Post_Data/HH_imgs'+"/"+"post_stage00.tif", "w", **meta) as dest:
                    dest.write(data)
                    #print(list(x.values())[list(x.keys()).index('transform')) 
                    print("###########  Raster Info  ##########")
                    print(dest.meta)
            
            print("###########  ALOS_pre_post  ##########")
            print("Post single img file has been created")
            
        
        
        if pre_mosaic == True:           
            src_mosic_files = []

            for ext_img in glob.glob(self.directory+"/"+str(self.project_name)+'/1_Pre_Data/HH_imgs'+"/*"):
                ext_ras = rasterio.open(ext_img)
                src_mosic_files.append(ext_ras)

            #print(src_mosic_files)

            #single mosaic array and transformartion info
            mosaic, out_trans = merge.merge(src_mosic_files)

            # Writing the mosaic
            mosaic_meta = ext_ras.meta.copy()

            # Update the metadata
            mosaic_meta.update({"driver": "GTiff",
                             "height": mosaic.shape[1],
                             "width": mosaic.shape[2],
                             "transform": out_trans,}
                           )
            with rasterio.open(self.directory+"/"+str(self.project_name)+'/1_Pre_Data/HH_imgs'+"/"+"pre_stage00.tif", "w", **mosaic_meta) as dest:
                dest.write(mosaic)
                print("###########  Raster Info  ##########")
                print(dest.meta)
            print("###########  ALOS_pre_post  ##########")
            print("Pre Mosaic file has been created")
            
        
            
        else:
            with rasterio.open(glob.glob(self.directory+"/"+str(self.project_name)+'/1_Pre_Data/HH_imgs' +"/*.tif")[0]) as src:
                meta = src.meta.copy()
                data = src.read(out_shape=(src.count, src.height, src.width))
                with rasterio.open(self.directory+"/"+str(self.project_name)+'/1_Pre_Data/HH_imgs'+"/"+"pre_stage00.tif", "w", **meta) as dest:
                    dest.write(data)
                    #print(list(x.values())[list(x.keys()).index('transform')) 
                    print("###########  Raster Info  ##########")
                    print(dest.meta)
            
            print("###########  ALOS_pre_post  ##########")
            print("Pre single img file has been created")
            
        
        ############################ Resample #####################################################
        
    def resample(self,pre,post,pre_scale,post_scale):
        
        if pre == True:
            x = glob.glob(self.directory+"/"+str(self.project_name)+'/1_Pre_Data/HH_imgs'+'/pre*stage00.tif')[0]
                #Define the scale eg:- 2, 0.5

            with rasterio.open(x) as raster:

                t = raster.transform

                # rescale the metadata
                transform = Affine(t.a * pre_scale, t.b, t.c, t.d, t.e * pre_scale, t.f)
                height = int(raster.height / pre_scale)
                width = int(raster.width / pre_scale)

                profile = raster.profile
                profile.update(transform=transform, driver='GTiff', height=height, width=width, compress='lzw')

                data = raster.read(out_shape=(raster.count, height, width),resampling=Resampling.nearest)


                with rasterio.open(self.directory+"/"+str(self.project_name)+'/2_Results'+'/pre_stage01.tif', 'w', **profile) as dataset:

                    # Open as DatasetWriter
                    dataset.write(data)
                    print("###########  Raster Info  ##########")
                    print(dataset.meta)

                print("###########  Pre image resampled  ##########")
        else:
            
            original = self.directory+"/"+str(self.project_name)+'/1_Pre_Data/HH_imgs'+'/pre_stage00.tif'
            target = self.directory+"/"+str(self.project_name)+'/2_Results'+'/pre_stage01.tif'

            shutil.copyfile(original, target)
            print("Pre image skipped resample  ##########")
            
        if post == True:
            x = glob.glob(self.directory+"/"+str(self.project_name)+'/1_Post_Data/HH_imgs'+'/post*stage00.tif')[0]
                #Define the scale eg:- 2, 0.5

            with rasterio.open(x) as raster:

                t = raster.transform

                # rescale the metadata
                transform = Affine(t.a * post_scale, t.b, t.c, t.d, t.e * post_scale, t.f)
                height = int(raster.height / post_scale)
                width = int(raster.width / post_scale)

                profile = raster.profile
                profile.update(transform=transform, driver='GTiff', height=height, width=width, compress='lzw')

                data = raster.read(out_shape=(raster.count, height, width),resampling=Resampling.nearest)


                with rasterio.open(self.directory+"/"+str(self.project_name)+'/2_Results'+'/post_stage01.tif', 'w', **profile) as dataset:

                    # Open as DatasetWriter
                    dataset.write(data)
                    print("###########  Raster Info  ##########")
                    print(dataset.meta)

            print("###########  Post image resampled  ##########")
        else:
            original = self.directory+"/"+str(self.project_name)+'/1_Post_Data/HH_imgs'+'/post_stage00.tif'
            target = self.directory+"/"+str(self.project_name)+'/2_Results'+'/post_stage01.tif'

            shutil.copyfile(original, target)
            
            print("Post image skipped resample  ##########")
        
        ############################ Calibration #####################################################
        
    def img_calibration(self):
                    
        for x in glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/*_stage01.tif'):
            #Fetchin the post mosaic/nonmosaic + resample + projected file using GDAL    
            
            print(x)

            raster_post=gdal.Open(x)

            post_band = raster_post.GetRasterBand(1)

            gtpost =raster_post.GetGeoTransform()

            post_intersect = post_band.ReadAsArray()


            #ALOS 2 Calibration for post image

            post_intersect = np.where(post_intersect == 0,np.nan, post_intersect)
            calib_array = 20*np.log10(post_intersect)-83
            calib_post_intersect = np.where(calib_array < -30, -30, calib_array)
            

            #out put the calibrated file

            #self.geotransform=([intersection[0],gtpost[1],gtpost[2],intersection[1],gtpost[2], gtpost[5]]) 
            proj = raster_post.GetProjection()

            output_raster_1 = gdal.GetDriverByName('GTiff').Create((x.split(".", 1)[0])+'_calib.tif',raster_post.RasterXSize, raster_post.RasterYSize, 1 ,gdal.GDT_Float32)  # Open the file
            output_raster_1.SetGeoTransform(gtpost)  


            output_raster_1.SetProjection(proj)  
            output_raster_1.GetRasterBand(1).WriteArray(calib_post_intersect) 
            output_raster_1.FlushCache()

        print("###########  PRE Post images calibrated  ##########")
        
    #################################### Speckle Filter ########################################
    def speckle_filtering(self,filter_size):
        
        def my_callback(value):
            if not "%" in value:
                print(value)
        
        for x in glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/*_calib.tif'):
            
            #Speckle filtering
            wbt.lee_sigma_filter(x,str((x.split("_stage01_calib", 1)[0])+'_calib_spec.tif'), 
                                 filterx=filter_size, filtery=filter_size, 
                                 sigma=10.0, 
                                 m=5.0, 
                                 callback=my_callback)

        print("###########  Speckle Filtered  ##########")

        
        
    ###################################### Change(pre-post) created #################################################
        
    def change(self):
        
        
        pre_image  = os.path.normpath(glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/pre*spec.tif',recursive = True)[0])
        post_image = os.path.normpath(glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/post*spec.tif',recursive = True)[0])
        
        raster_pre=gdal.Open(pre_image)
        raster_post=gdal.Open(post_image)

        pre_band = raster_pre.GetRasterBand(1)
        post_band = raster_post.GetRasterBand(1)
        
        gtpost =raster_post.GetGeoTransform()
        gtpre =raster_pre.GetGeoTransform()

        #Pre and post top(x,y) bottom(x,y) co-ordinates
        post_bound  = [gtpost[0], gtpost[3], gtpost[0] + (gtpost[1] * raster_post.RasterXSize), gtpost[3] + (gtpost[5] * raster_post.RasterYSize)]
        pre_bound   = [gtpre[0] , gtpre[3] , gtpre[0]  + (gtpre[1]  * raster_pre.RasterXSize) , gtpre[3]  + (gtpre[5]  * raster_pre.RasterYSize)]
        
        #Finding the intersection boundry
        intersection = [max(post_bound[0], pre_bound[0]), min(post_bound[1], pre_bound[1]), min(post_bound[2], pre_bound[2]), max(post_bound[3], pre_bound[3])]

        post_bound_pix = [abs(round((gtpost[0]-intersection[0])/gtpost[1])),abs(round((gtpost[3]-intersection[1])/gtpost[5])),
                  abs(round((gtpost[0]-intersection[2])/gtpost[1])),abs(round((gtpost[3]-intersection[3])/gtpost[5]))]

        pre_bound_pix = [abs(round((gtpre[0]-intersection[0])/gtpre[1])),abs(round((gtpre[3]-intersection[1])/gtpre[5])),
                 abs(round((gtpre[0]-intersection[2])/gtpre[1])),abs(round((gtpre[3]-intersection[3])/gtpre[5]))]
        
        post_intersect = post_band.ReadAsArray(post_bound_pix[0],post_bound_pix[1],post_bound_pix[2] - post_bound_pix[0],
                                               post_bound_pix[3] - post_bound_pix[1],post_bound_pix[2] - post_bound_pix[0],
                                               post_bound_pix[3] - post_bound_pix[1],buf_type=gdal.GDT_Float32)

        pre_intersect = pre_band.ReadAsArray(pre_bound_pix[0],pre_bound_pix[1],pre_bound_pix[2] - pre_bound_pix[0],
                                             pre_bound_pix[3] - pre_bound_pix[1],pre_bound_pix[2] - pre_bound_pix[0], 
                                             pre_bound_pix[3] - pre_bound_pix[1],buf_type=gdal.GDT_Float32)

        nrows = pre_bound_pix[3] - pre_bound_pix[1]
        ncols = pre_bound_pix[2] - pre_bound_pix[0]
        
        #Getting the  change image using the numpy array operations
        #import numpy as np
        change_array = np.subtract(post_intersect,pre_intersect)
        
        
        geotransform=([intersection[0],gtpost[1],gtpost[2],intersection[1],gtpost[2], gtpost[5]]) 
        proj = raster_pre.GetProjection()
        
        output_raster = gdal.GetDriverByName('GTiff').Create(self.directory+"/"+str(self.project_name)+'/2_Results/'+'change.tif',ncols, nrows, 1 ,gdal.GDT_Float32)
        output_raster.SetGeoTransform(geotransform)  
        #srs = osr.SpatialReference()                
        #srs.ImportFromEPSG(4326)                                                                                                         
        output_raster.SetProjection(proj)  
        output_raster.GetRasterBand(1).WriteArray(change_array) 
        output_raster.FlushCache()
        
        print("###########  Change image is created  ##########")
        
        ###################### Reprojecting ###########################################################################        
            
    def reproject_wgs84(self):
        
        x = glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/change.tif')[0]
    
        # Input and Output file names including the path    
        dst_crs = 'EPSG:4326'

        with rasterio.open(x) as src:
            transform, width, height = calculate_default_transform(src.crs, dst_crs, src.width, src.height, *src.bounds)
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': dst_crs,
                'transform': transform,
                'width': width,
                'height': height
            })


            with rasterio.open((x.split(".", 1)[0])+'_wgs84.tif', 'w', **kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.nearest)
        print("###########  Change image reprojected  ##########")
    
        for x in glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/*spec.tif'):
                
            # Input and Output file names including the path    
            dst_crs = 'EPSG:4326'

            with rasterio.open(x) as src:
                transform, width, height = calculate_default_transform(src.crs, dst_crs, src.width, src.height, *src.bounds)
                kwargs = src.meta.copy()
                kwargs.update({
                    'crs': dst_crs,
                    'transform': transform,
                    'width': width,
                    'height': height
                })


                with rasterio.open((x.split(".", 1)[0])+'_wgs84.tif', 'w', **kwargs) as dst:
                    for i in range(1, src.count + 1):
                        reproject(
                            source=rasterio.band(src, i),
                            destination=rasterio.band(dst, i),
                            src_transform=src.transform,
                            src_crs=src.crs,
                            dst_transform=transform,
                            dst_crs=dst_crs,
                            resampling=Resampling.nearest)
        print("###########  Speckle images reprojected  ##########")
        
        

        
    ###################################### Thresholding ##############################################
        
    def thresholding(self,threshold_value):
        
        #Fetchin the post mosaic/nonmosaic + resample + projected file using GDAL    

        calib_spec=gdal.Open(os.path.normpath(glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/*change_wgs84.tif',recursive = True)[0]))

        post_band = calib_spec.GetRasterBand(1)

        gtpost =calib_spec.GetGeoTransform()

        post_calib_spec = post_band.ReadAsArray(buf_type=gdal.GDT_Float32)


        #ALOS 2 Calibration for post image

        post_calib_spec[post_calib_spec == 0] = 'nan'

        threshold = np.where(post_calib_spec < threshold_value,1,0)


        #out put the calibrated file

        #self.geotransform=([intersection[0],gtpost[1],gtpost[2],intersection[1],gtpost[2], gtpost[5]]) 
        proj = calib_spec.GetProjection()

        output_raster_1 = gdal.GetDriverByName('GTiff').Create(self.directory+"/"+str(self.project_name)+'/2_Results/'+'change_threshold_'+str(threshold_value)+'.tif',calib_spec.RasterXSize, calib_spec.RasterYSize, 1 ,gdal.GDT_Byte)  # Open the file
        output_raster_1.SetGeoTransform(gtpost)  


        output_raster_1.SetProjection(proj)  
        output_raster_1.GetRasterBand(1).WriteArray(threshold)
        #output_raster_1.GetRasterBand(1).SetNoDataValue(0)
        output_raster_1.FlushCache()

        print("###########  Threshold Applied  ##########")
        
    def maj_filtering(self,filter_size,threshold):   
        #Printing the running status
        def my_callback(value):             
            if not "%" in value:
                print(value)

        #Majority filter        
        wbt.majority_filter(os.path.normpath(glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/*threshold_'+str(threshold)+'.tif',recursive = True)[0]),
                    self.directory+"/"+str(self.project_name)+'/2_Results/'+'threshold_'+str(threshold)+'_maj_'+str(filter_size)+'.tif', 
                    filterx=filter_size, filtery=filter_size, callback=my_callback)
                
        
        # giving the no data values
        calib_spec_ndata=gdal.Open(os.path.normpath(glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/'+'*threshold_'+str(threshold)+'_maj_'+str(filter_size)+'.tif',recursive = True)[0]))

        post_band = calib_spec_ndata.GetRasterBand(1)

        gtpost =calib_spec_ndata.GetGeoTransform()

        post_calib_spec = post_band.ReadAsArray(buf_type=gdal.GDT_Byte)
        
        proj = calib_spec_ndata.GetProjection()
        
        output_raster_2 = gdal.GetDriverByName('GTiff').Create(self.directory+"/"+str(self.project_name)+'/2_Results/'+'threshold_'+str(threshold)+'final_maj_'+str(filter_size)+'.tif',calib_spec_ndata.RasterXSize, calib_spec_ndata.RasterYSize, 1 ,gdal.GDT_Byte)  # Open the file
        output_raster_2.SetGeoTransform(gtpost)  


        output_raster_2.SetProjection(proj)  
        output_raster_2.GetRasterBand(1).WriteArray(post_calib_spec)
        output_raster_2.GetRasterBand(1).SetNoDataValue(0)
        output_raster_2.FlushCache()
        
        
        #os.remove(os.path.normpath(glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/'+'*threshold_'+str(threshold)+'_maj_'+str(filter_size)+'.tif',recursive = True)[0]))
                
        
        print("###########  majotiry filtered  ##########")
        
        
    def ras2poly(self,threshold,filter_size):

        #Printing the running status
        def my_callback(value):             
            if not "%" in value:
                print(value)

        wbt.raster_to_vector_polygons(os.path.normpath(glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/'+'*threshold_'+str(threshold)+'final_maj_'+str(filter_size)+'.tif',recursive = True)[0]),
                                   self.directory+"/"+str(self.project_name)+'/2_Results/'+'Detected_Flood_Water.shp', 
                                    callback=my_callback)
        print("###########  Polygonized  ##########")
        
    def clean_result_folder(self):
        garbage = glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/*stage01*.tif',recursive = True)
        g2 = glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/*spec.tif',recursive = True)
        g3 = glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/*change.tif',recursive = True)[0]
        
        os.remove(g3)
        
        for item in g2:
            os.remove(item)
        
        
        for item in garbage:
            os.remove(item)
            
        print("###########  Floder Cleaned  ##########")

        
    
################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>################################################     
                        
class ALOS2_post():
    
    def __init__(self,directory,project_name):            
        self.directory = directory
        self.project_name = project_name        
        self.local_post_path = None        
        self.downlink_post_path = None
        
            
    ########################## Creating the project directories ###########################
    
    def create_project_dir(self,working_dir):
        folder_list = [str(self.project_name),str(self.project_name)+"/1_Post_Data",str(self.project_name)+"/1_Post_Data/HH_imgs",str(self.project_name)+"/2_Results"]
        for item in folder_list:
            Path(working_dir+'/'+item).mkdir(parents=True, exist_ok=True)
            
        ######### List data paramiko sftp connection ###########
    def list_ALOS_data(self,activation_name,sftp_key):

        #Activation name eg- 20200603-India-Flood-Storm-00373
        #paramiko.util.log_to_file('D:/6_SA_2020_Plan/ost/logs/paramiko.log')
        host = "****"
        port = ""
        # private key given to us has to be convert into rsa or pem format 
        #sftp_key = "D:/6_SA_2020_Plan/ost/keys/****"
        username = ""
        password = ""

        sftp_key = paramiko.RSAKey.from_private_key_file(sftp_key)
        transport = paramiko.Transport((host, port))
        transport.start_client(event=None, timeout=15)
        transport.get_remote_server_key()
        transport.auth_publickey(username, sftp_key, event=None)
        transport.auth_password(username, password, event=None)
        sftp = paramiko.SFTPClient.from_transport(transport)

        #show data
        #remote_archive = '/Sentinel-Asia/Emergency_Response/'+str(activation_name)+'/ARCHIVE/jp_jaxa'
        remote_observe = '/Sentinel-Asia/Emergency_Response/'+str(activation_name)+'/OBSERVE/jp_jaxa'
        #Jaxa_pre_list = sftp.listdir(remote_archive)
        Jaxa_post_list = sftp.listdir(remote_observe) 



        post_downlist = []

        post_down_link = []

        #for download purpose ALOS pre post
        
        local_path_post = []

        ######## Post Links ##################
        for x in Jaxa_post_list:
            y = re.search(".zip$", x)
            if y:
                post_downlist.append(str(x))
        print('Available post file to download')
        print(post_downlist)

        for x in post_downlist:
            dl = remote_observe + "/" + str(x)
            post_down_link.append(dl)

        ######## Pre Links ##################


        ######## local path links #############
        #post
        for x in post_downlist:
            da2 = self.directory+"/"+str(self.project_name)+'/1_Post_Data' + "/" + str(x)
            local_path_post.append(da2)


    
        self.local_post_path = local_path_post
 
        self.downlink_post_path = post_down_link
        
        sftp.close()
        transport.close()

        ######### Downlaod data #######
    def download_ALOS_data(self,post,sftp_key):
        
        host = ""
        port = ""
        # private key given to us has to be convert into rsa or pem format 
        #sftp_key = "D:/6_SA_2020_Plan/ost/keys/****"
        username = ""
        password = ""

        sftp_key = paramiko.RSAKey.from_private_key_file(sftp_key)
        transport = paramiko.Transport((host, port))
        transport.start_client(event=None, timeout=15)
        transport.get_remote_server_key()
        transport.auth_publickey(username, sftp_key, event=None)
        transport.auth_password(username, password, event=None)
        sftp = paramiko.SFTPClient.from_transport(transport)
        


        if post == True:

            for i in range(len(self.downlink_post_path)):
                sftp.get(str(self.downlink_post_path[i]),str(self.local_post_path[i]))
                
        else:
            sftp.close()
            transport.close()

        print("Post files have been downloaded")
        self.local_pre_path = None
        self.local_post_path = None
        self.downlink_pre_path = None
        self.downlink_post_path = None
        sftp.close()
        transport.close()
        

            
            
    
        
    
    ########################## unzip #####################################################3
    
    def unzip_to_mosaic(self,mosaic):
        
        
        for file in glob.glob(self.directory+"/"+str(self.project_name)+'/1_Post_Data'+'/*.zip'):
            with ZipFile(file,'r') as outzip:                    
                with outzip.open(outzip.namelist()[0],'r') as inzip:
                    with ZipFile(inzip,'r') as inner: 
                        for img in inner.namelist():
                            if img.startswith('IMG-HH'):
                                inner.extract(img, self.directory+"/"+str(self.project_name)+'/1_Post_Data/HH_imgs')
        
        print("###########  ALOS_post  ##########")
        print("All Files have been unzipped")
            
        if mosaic == True:           
            src_mosic_files = []

            for ext_img in glob.glob(self.directory+"/"+str(self.project_name)+'/1_Post_Data/HH_imgs'+"/*"):
                ext_ras = rasterio.open(ext_img)
                src_mosic_files.append(ext_ras)

            #print(src_mosic_files)

            #single mosaic array and transformartion info
            mosaic, out_trans = merge.merge(src_mosic_files)

            # Writing the mosaic
            mosaic_meta = ext_ras.meta.copy()

            # Update the metadata
            mosaic_meta.update({"driver": "GTiff",
                             "height": mosaic.shape[1],
                             "width": mosaic.shape[2],
                             "transform": out_trans,}
                           )
            with rasterio.open(self.directory+"/"+str(self.project_name)+'/2_Results'+"/"+"post_stage01.tif", "w", **mosaic_meta) as dest:
                dest.write(mosaic)
                print("###########  Raster Info  ##########")
                print(dest.meta)
            print("###########  ALOS_post  ##########")
            print("Post Mosaic file has been created")
            
        else:
            with rasterio.open(glob.glob(self.directory+"/"+str(self.project_name)+'/1_Post_Data/HH_imgs'+"/*.tif")[0]) as src:
                meta = src.meta.copy()
                data = src.read(out_shape=(src.count, src.height, src.width))
                with rasterio.open(self.directory+"/"+str(self.project_name)+'/2_Results'+"/"+"post_stage01.tif", "w", **meta) as dest:
                    dest.write(data)
                    #print(list(x.values())[list(x.keys()).index('transform')) 
                    print("###########  Raster Info  ##########")
                    print(dest.meta)
            
            print("###########  ALOS_post  ##########")
            print("Post single img file has been created")
            
            
    ########################## Reproject ###########################
            
    def reproject_wgs84(self):
        
        for x in glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/*tif'):
    
            # Input and Output file names including the path    
            dst_crs = 'EPSG:4326'

            with rasterio.open(x) as src:
                
                transform, width, height = calculate_default_transform(src.crs, dst_crs, src.width, src.height, *src.bounds)
                kwargs = src.meta.copy()
                kwargs.update({
                    'crs': dst_crs,
                    'transform': transform,
                    'width': width,
                    'height': height
                })


                with rasterio.open((x.split(".", 1)[0])+'_wgs84.tif', 'w', **kwargs) as dst:
                    for i in range(1, src.count + 1):
                        reproject(
                            source=rasterio.band(src, i),
                            destination=rasterio.band(dst, i),
                            src_transform=src.transform,
                            src_crs=src.crs,
                            dst_transform=transform,
                            dst_crs=dst_crs,
                            resampling=Resampling.nearest)
        print("###########  Post image reprojected  ##########")
        
    ########################## Resample ###########################
    
    def resample(self,scale):
        
        for x in glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/*_wgs84.tif'):
            
            #Define the scale eg:- 2, 0.5

            with rasterio.open(x) as raster:

                t = raster.transform

                # rescale the metadata
                transform = Affine(t.a * scale, t.b, t.c, t.d, t.e * scale, t.f)
                height = int(raster.height / scale)
                width = int(raster.width / scale)

                profile = raster.profile
                profile.update(transform=transform, driver='GTiff', height=height, width=width , compress='lzw')

                data = raster.read(out_shape=(raster.count, height, width),resampling=Resampling.nearest)


                with rasterio.open((x.split(".", 1)[0])+'_resample.tif', 'w', **profile) as dataset:

                    # Open as DatasetWriter
                    dataset.write(data)
                    print("###########  Raster Info  ##########")
                    print(dataset.meta)

        print("###########  Post image resampled  ##########")
        
    
    ########################## Calibration ###########################
                
    def img_calibration(self):
        
        for x in glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/*_resample.tif'):
            
            print(x)
            
            #Fetchin the post mosaic/nonmosaic + resample + projected file using GDAL    

            raster_post=gdal.Open(x)

            post_band = raster_post.GetRasterBand(1)

            gtpost =raster_post.GetGeoTransform()

            post_intersect = post_band.ReadAsArray()


            #ALOS 2 Calibration for post image

            post_intersect = np.where(post_intersect == 0, np.nan, post_intersect)
            calib_array = 20*np.log10(post_intersect)-83
            calib_post_intersect = np.where(calib_array < -30, -30, calib_array)
            
            #out put the calibrated file

            #self.geotransform=([intersection[0],gtpost[1],gtpost[2],intersection[1],gtpost[2], gtpost[5]]) 
            proj = raster_post.GetProjection()

            output_raster_1 = gdal.GetDriverByName('GTiff').Create((x.split(".", 1)[0])+'_calib.tif',raster_post.RasterXSize, raster_post.RasterYSize, 1 ,gdal.GDT_Float32)  # Open the file
            output_raster_1.SetGeoTransform(gtpost)  


            output_raster_1.SetProjection(proj)  
            output_raster_1.GetRasterBand(1).WriteArray(calib_post_intersect) 
            output_raster_1.FlushCache()

        print("###########  Post image calibrated  ##########")
        
    ###################### Speckle filtering ##########################################################
        
    def speckle_filtering(self,filter_size):
        
        def my_callback(value):
            if not "%" in value:
                print(value)
        
        for x in glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/*_calib.tif'):
            
            #Speckle filtering
            wbt.lee_sigma_filter(x,str((x.split("_stage01_wgs84_resample_calib", 1)[0])+'_calib_spec.tif'), 
                                 filterx=filter_size, filtery=filter_size, 
                                 sigma=10.0, 
                                 m=5.0, 
                                 callback=my_callback)

        print("###########  Speckle Filtered  ##########")
        
    ###################### Thresholding ##########################################################
        
    def thresholding(self,threshold_value):
        #Fetchin the post mosaic/nonmosaic + resample + projected file using GDAL    

        calib_spec=gdal.Open(os.path.normpath(glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/*spec.tif',recursive = True)[0]))

        post_band = calib_spec.GetRasterBand(1)

        gtpost =calib_spec.GetGeoTransform()

        post_calib_spec = post_band.ReadAsArray(buf_type=gdal.GDT_Float32)


        #ALOS 2 Calibration for post image

        #post_calib_spec[post_calib_spec == 0] = 'nan'

        threshold = np.where(post_calib_spec < threshold_value,1,0)


        #out put the calibrated file

        #self.geotransform=([intersection[0],gtpost[1],gtpost[2],intersection[1],gtpost[2], gtpost[5]]) 
        proj = calib_spec.GetProjection()

        output_raster_1 = gdal.GetDriverByName('GTiff').Create(self.directory+"/"+str(self.project_name)+'/2_Results/'+'threshold_'+str(threshold_value)+'.tif',calib_spec.RasterXSize, calib_spec.RasterYSize, 1 ,gdal.GDT_Byte)  # Open the file
        output_raster_1.SetGeoTransform(gtpost)  


        output_raster_1.SetProjection(proj)  
        output_raster_1.GetRasterBand(1).WriteArray(threshold)
        #output_raster_1.GetRasterBand(1).SetNoDataValue(0)
        output_raster_1.FlushCache()

        print("###########  Threshold Applied  ##########") 
        
        
    def maj_filtering(self,filter_size,threshold):   
        #Printing the running status
        def my_callback(value):             
            if not "%" in value:
                print(value)

        #Majority filter        
        wbt.majority_filter(os.path.normpath(glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/*threshold_'+str(threshold)+'.tif',recursive = True)[0]),
                    self.directory+"/"+str(self.project_name)+'/2_Results/'+'threshold_'+str(threshold)+'_maj_'+str(filter_size)+'.tif', 
                    filterx=filter_size, filtery=filter_size, callback=my_callback)
        
        calib_spec_ndata=gdal.Open(os.path.normpath(glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/'+'*threshold_'+str(threshold)+'_maj_'+str(filter_size)+'.tif',recursive = True)[0]))

        post_band = calib_spec_ndata.GetRasterBand(1)

        gtpost =calib_spec_ndata.GetGeoTransform()

        post_calib_spec = post_band.ReadAsArray(buf_type=gdal.GDT_Byte)
        
        proj = calib_spec_ndata.GetProjection()
        
        output_raster_2 = gdal.GetDriverByName('GTiff').Create(self.directory+"/"+str(self.project_name)+'/2_Results/'+'threshold_'+str(threshold)+'final_maj_'+str(filter_size)+'.tif',calib_spec_ndata.RasterXSize, calib_spec_ndata.RasterYSize, 1 ,gdal.GDT_Byte)  # Open the file
        output_raster_2.SetGeoTransform(gtpost)  


        output_raster_2.SetProjection(proj)  
        output_raster_2.GetRasterBand(1).WriteArray(post_calib_spec)
        output_raster_2.GetRasterBand(1).SetNoDataValue(0)
        output_raster_2.FlushCache()
        
        
        #os.remove(os.path.normpath(glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/'+'*threshold_'+str(threshold)+'_maj_'+str(filter_size)+'.tif',recursive = True)[0]))
        
        
        
        print("###########  majotiry filtered  ##########")
        
        
    def ras2poly(self,threshold,filter_size):

        #Printing the running status
        def my_callback(value):             
            if not "%" in value:
                print(value)

        wbt.raster_to_vector_polygons(os.path.normpath(glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/'+'*threshold_'+str(threshold)+'final_maj_'+str(filter_size)+'.tif',recursive = True)[0]),
                                   self.directory+"/"+str(self.project_name)+'/2_Results/'+'Detected_Water.shp', 
                                    callback=my_callback)
        print("###########  Polygonized  ##########")
        
    def clean_result_folder(self):
        garbage1 = glob.glob(self.directory+"/"+str(self.project_name)+'/2_Results'+'/*stage01*.tif',recursive = True)

        
        for item in garbage1:
            os.remove(item)
            
        print("###########  Floder Cleaned  ##########")
        

        

