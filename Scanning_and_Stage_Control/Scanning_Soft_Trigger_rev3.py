#you should home this program using the standard PI homing program on buffer 8
#look at page 262 of ACS programing C book for Input (airlock) checking
# import SimpleITK as sitk  #used for image saving and manipulation #this is dumb
import numpy as np
# import MMCorePy
import time
from datetime import datetime
import os
import sys
from acspy import acsc
from acspy.control import Controller
import dxchange as dx
import ctypes
import MultiCam as MC


proj_dir=os.path.dirname(sys.argv[0])


#Camera initialize channel
# camFile="C:\\Users\\ChengLab\\Desktop\\MP71Camera\\VP-71MC-M5_P200SC_4tap(H)_12bit_RG (VST Y12).cam"
camFile=proj_dir+"\\VP-71MC-M5_P200SC_4tap(H)_12bit_RG (VST Y12).cam" 

channel = MC.Create('CHANNEL')
driverIndex=0
connector="M"
MC.SetParamInt(channel, 'DriverIndex', driverIndex)
MC.SetParamStr(channel, 'Connector', connector)
MC.SetParamStr(channel, 'CamFile', camFile)
MC.SetParamInt(channel, 'SeqLength_Fr', 1) #Edit this


MC.SetParamStr(channel, MC.SignalEnable + MC.SIG_SURFACE_PROCESSING, 'ON')
MC.SetParamStr(channel, MC.SignalEnable + MC.SIG_ACQUISITION_FAILURE, 'ON')
MC.SetParamStr(channel, MC.SignalEnable + MC.SIG_END_CHANNEL_ACTIVITY, 'ON')

planeIndex=0
MC.SetParamStr(channel, 'ChannelState', 'READY')

#45kv30w_-.4f
#Change these variables
binning_value="1x1"
exposure_inpt=4000 #(in ms)
total_degrees=360*4
total_projections=1500
degrees_array=np.linspace(0,total_degrees,total_projections,endpoint=True)
drift_check_count=1 #number of times you want to seek back to 0 degrees and take a projection to check drift throughout scan.
# print(degrees_array)

drift_track_angle_array=degrees_array[0::int(degrees_array.shape[0]/drift_check_count)]
print(drift_track_angle_array)
print(degrees_array)




gain_z_out_of_beam=160  ######## YO YIFU MAKE THIS CORRECT************
gain_num= 0        #gainscan this many times during scan (will distribute evenly over degrees)
num_gain_per_scan=0

num_exposures_per_projection=1
# num_exposures_per_projection=5

# projection_fill=np.zeros([num_exposures_per_projection,2048/int(binning_value[0]),2048/int(binning_value[0])])
###THIS WILL INCLUDE FIRST SCAN AND LAST SCAN

#Generate the gainscan index list
gainarray=np.around(np.linspace(0,total_projections-1,gain_num,endpoint=True)).astype(int)
print("GainScans at following Degrees:")
print(degrees_array[gainarray])



#Really change this
load_stages=1
load_camera=0
load_camera10k=True
scan_gain=0
# where_i_was = 105.1
do_scan = 1
# wait_ms=.0001
wait_ms=.0001
#MAYBE USE the controller property: moving to figure out of it's moving
if load_camera10k:
    camefile_path="C:\\Users\\ChengLab\\Desktop\\MP71Camera\\VP-71MC-M5_P200SC_4tap(H)_12bit_RG (VST Y12).cam"
#Directory Business
# base_dir="C:/Users/ChengLab/Desktop/PyMicroTest_Outputs/"
base_dir="D:/10k_Detector/Scans/"
timestr = time.strftime("%Y%m%d-%H%M%S")
# output_dir=base_dir+"\\"+timestr+"\\"
# output_dir=base_dir+"\\"+"Projection_set_"+"\\"+timestr+"_"+str(num_exposures_per_projection*exposure_inpt)+"ms\\"
output_dir=base_dir+"\\"+timestr+"_Projection_set_"+str(total_projections)+"projections_"+str(exposure_inpt)+"ms_"+str(num_exposures_per_projection)+"avg\\"
if not os.path.exists(output_dir): os.makedirs(output_dir)
startTime = datetime.now()
if scan_gain:
    if not os.path.exists(output_dir+"\\gain\\"): os.makedirs(output_dir+"\\gain\\")
file_output= open(output_dir+"\\"+timestr+".txt","w+")
file_output.write("Projection\tz\tfTheta\trTheta\tTime\tdTime\tExposure(ms)\n")

if load_camera10k:
    dimm_1=10000
    dimm_2=7096
    # gain_fill=np.zeros([num_gain_per_scan,dimm_2/int(binning_value[0]),dimm_1/int(binning_value[0])])
    projection_fill=np.zeros([num_exposures_per_projection,dimm_2/int(binning_value[0]),dimm_1/int(binning_value[0])])

#Functions
def move_stage(set_degree):
    acsc.toPoint(hcomm, None,1,set_degree)
    
def gainscan(idx):
    gainnum = 1
    #where_i_was=acsc.getRPosition(hcomm,0)
    acsc.toPoint(hcomm, None,0,gain_z_out_of_beam)
    # while(abs(acsc.getFVelocity(hcomm, 0))>wait_ms):
        # 1+1
    while(not acsc.getMotorState(hcomm,0)['in position']): #check for stop event using other API call?
        time.sleep(.1)    
    while(gainnum<num_gain_per_scan):
        mmc.snapImage()
        image_npy = mmc.getImage()
        image_itk = sitk.GetImageFromArray(image_npy)
        sitk.WriteImage(image_itk, output_dir+"\\gain\\gain_"+str(idx)+"_"+str(gainnum)+".tiff") #Change this to Gainscan_"+str(idx)+".tiff" if you would rather sort by time and not filename
        dt = datetime.now()
        micro=dt.microsecond
        time_temp=time.strftime("%Y%m%d-%H%M%S")+":"+str(micro)
        file_output.write("gain_%d\t%f\t%f\t%f\t%s\t%s\t%d\n" % (idx,0,acsc.getRPosition(hcomm,1),acsc.getFPosition(hcomm,1),time_temp,(datetime.now() - startTime),exposure_inpt))
        gainnum = gainnum+1
    acsc.toPoint(hcomm, None,0,where_i_was)
    # while(abs(acsc.getFVelocity(hcomm, 0))>wait_ms):
        # 1+1
    while(not acsc.getMotorState(hcomm,0)['in position']): #check for stop event using other API call?
        time.sleep(.1)
    
def take_photo(deg,idx):
    #test image
    if scan_gain:
        if idx in gainarray:
            gainscan(idx)
            
    q = time.time()
    for projnum in range(num_exposures_per_projection):
        print("Projection average %d out of %d" %(projnum+1,num_exposures_per_projection))
        if load_camera10k:
            print("Projection %d out of %d" %(projnum+1,num_exposures_per_projection))
            # image_npy,channel_temp=GrabOneImage(channel)
            s2= datetime.now()
            MC.SetParamStr(channel, 'ChannelState', 'ACTIVE')
            gotEndOfChannelActivity = False
            gotAcquisitionFailure = False

            while not gotEndOfChannelActivity:
                signalInfo = MC.WaitSignal(channel, MC.SIG_ANY, 15000) #Attempt to make this call shorter (1.5 second overhead as written....)
                # signalInfo = MC.WaitSignal(channel, MC.SIG_ANY, 1000)
                if signalInfo.Signal == MC.SIG_END_CHANNEL_ACTIVITY:
                    gotEndOfChannelActivity = True
                elif signalInfo.Signal == MC.SIG_ACQUISITION_FAILURE:
                    gotAcquisitionFailure = True
                elif signalInfo.Signal == MC.SIG_SURFACE_PROCESSING:
                    MC.SetParamStr(signalInfo.SignalInfo, 'SurfaceState', 'FREE')
                else:
                    raise MC.MultiCamError('Unexpected signal: %d' % signalInfo.Signal)
                # MC.SetParamStr(channel, "ForceTrig", "TRIG");
            if gotAcquisitionFailure:
                raise MC.MultiCamError('Acquisition failure!')

            surface = MC.GetParamInst(channel, 'Cluster:0')
            width = MC.GetParamInt(surface, 'SurfaceSizeX')
            height = MC.GetParamInt(surface, 'SurfaceSizeY')
            # image = ConvertSurfaceIntoImage(surface)
            surfaceAddress = MC.GetParamPtr(surface, 'SurfaceAddr:%d' % planeIndex)
            surfaceSize = MC.GetParamInt(surface, 'SurfaceSize:%d' % planeIndex)
            imageBuffer = ctypes.string_at(surfaceAddress, surfaceSize)
            MC.SetParamStr(channel, 'ChannelState', 'READY')
            data = np.fromstring(imageBuffer, np.uint16)
            image_npy=np.reshape(data,(height,width))
            # image = ConvertBufferIntoImage(width, height, imageBuffer)
            # print(image.shape)
            # print(image[0].shape)
            # channel_temp=channel
            print(str(datetime.now()-s2)+" single proj")

        else:
            mmc.snapImage()
            image_npy = mmc.getImage()
        projection_fill[projnum] = image_npy
    proj=np.mean(projection_fill,axis=0)
    # image_itk = sitk.GetImageFromArray(proj)
    #sitk.WriteImage(image_itk, output_dir+"/Projection_"+str(idx)+".tiff")
    if idx==0:
        dx.write_tiff(proj, output_dir+"//Drift_Projections_at_0deg/Correction_Projection_from_"+str(int(deg))+"_deg"+".tiff",dtype=np.uint16)
    dx.write_tiff(proj, output_dir+"//Raw_Projections/Projection_"+str(idx)+".tiff",dtype=np.uint16)
    #Projection\tZ\tTheta\trTheta\tTime\tdTime\tExposure(ms)\r\n
    dt = datetime.now()
    micro=dt.microsecond
    time_temp=time.strftime("%Y%m%d-%H%M%S")+":"+str(micro)
    file_output.write("%d\t%f\t%f\t%f\t%s\t%s\t%d\n" % (idx,0,acsc.getRPosition(hcomm,1),acsc.getFPosition(hcomm,1),time_temp,(datetime.now() - startTime),exposure_inpt))
    print("Projection "+str(idx+1)+" out of "+str(total_projections)+ " Acquired")   

def take_drift_correction_photo(deg):
    move_stage(0)
    moving=True
    # while(abs(acsc.getFVelocity(hcomm, 1))>wait_ms): #check for stop event using other API call?
        # 1+1
    while(not acsc.getMotorState(hcomm,1)['in position']): #check for stop event using other API call?
        time.sleep(.1)
    for projnum in range(num_exposures_per_projection):
        print("Projection average %d out of %d" %(projnum+1,num_exposures_per_projection))
        if load_camera10k:
            print("Projection %d out of %d" %(projnum+1,num_exposures_per_projection))
            # image_npy,channel_temp=GrabOneImage(channel)
            s2= datetime.now()
            MC.SetParamStr(channel, 'ChannelState', 'ACTIVE')
            gotEndOfChannelActivity = False
            gotAcquisitionFailure = False

            while not gotEndOfChannelActivity:
                signalInfo = MC.WaitSignal(channel, MC.SIG_ANY, 15000) #Attempt to make this call shorter (1.5 second overhead as written....)
                # signalInfo = MC.WaitSignal(channel, MC.SIG_ANY, 1000)
                if signalInfo.Signal == MC.SIG_END_CHANNEL_ACTIVITY:
                    gotEndOfChannelActivity = True
                elif signalInfo.Signal == MC.SIG_ACQUISITION_FAILURE:
                    gotAcquisitionFailure = True
                elif signalInfo.Signal == MC.SIG_SURFACE_PROCESSING:
                    MC.SetParamStr(signalInfo.SignalInfo, 'SurfaceState', 'FREE')
                else:
                    raise MC.MultiCamError('Unexpected signal: %d' % signalInfo.Signal)
                # MC.SetParamStr(channel, "ForceTrig", "TRIG");
            if gotAcquisitionFailure:
                raise MC.MultiCamError('Acquisition failure!')

            surface = MC.GetParamInst(channel, 'Cluster:0')
            width = MC.GetParamInt(surface, 'SurfaceSizeX')
            height = MC.GetParamInt(surface, 'SurfaceSizeY')
            # image = ConvertSurfaceIntoImage(surface)
            surfaceAddress = MC.GetParamPtr(surface, 'SurfaceAddr:%d' % planeIndex)
            surfaceSize = MC.GetParamInt(surface, 'SurfaceSize:%d' % planeIndex)
            imageBuffer = ctypes.string_at(surfaceAddress, surfaceSize)
            MC.SetParamStr(channel, 'ChannelState', 'READY')
            data = np.fromstring(imageBuffer, np.uint16)
            image_npy=np.reshape(data,(height,width))
            # image = ConvertBufferIntoImage(width, height, imageBuffer)
            # print(image.shape)
            # print(image[0].shape)
            # channel_temp=channel
            print(str(datetime.now()-s2)+" single proj")
        else:
            mmc.snapImage()
            image_npy = mmc.getImage()
        projection_fill[projnum] = image_npy
    proj=np.mean(projection_fill,axis=0)
    # image_itk = sitk.GetImageFromArray(proj)
    #sitk.WriteImage(image_itk, output_dir+"/Projection_"+str(idx)+".tiff")
    dx.write_tiff(proj, output_dir+"//Drift_Projections_at_0deg/Correction_Projection_from_"+str(int(np.where(degrees_array==deg)[0][0]))+".tiff",dtype=np.uint16)
    move_stage(deg)
    # while(abs(acsc.getFVelocity(hcomm, 1))>wait_ms): #check for stop event using other API call?
        # 1+1
    while(not acsc.getMotorState(hcomm,1)['in position']): #check for stop event using other API call?
        time.sleep(.1)
##################
###camera calls###
##################
#load in devices
if load_camera:
    mmc = MMCorePy.CMMCore()  # Instance micromanager core
    print(mmc.getVersionInfo())
    prev_dir=os.getcwd()
    os.chdir("C:\Program Files\Micro-Manager-1.4")
    mmc.loadSystemConfiguration("C:\Program Files\Micro-Manager-1.4\zyla42.cfg")
    #print devices
    # print("\nCurrent Device(s):")  
    # print(mmc.getCameraDevice())
    device_id=mmc.getCameraDevice() #THIS IS NOT CALLING THE CORRECT THING!!! FIGURE OUT HOW TO GET REAL STATUS!
    #exposure=60
    print(device_id)
    mmc.setExposure(exposure_inpt)
    mmc.setProperty(device_id,"Binning",binning_value)
    print(mmc.getProperty(device_id,"Binning"))
    os.chdir(prev_dir)

##################
####stage calls###
##################
if load_stages:
    #initiate connection
    hcomm = acsc.openCommEthernetTCP(address="10.0.0.100", port=701)
    #z
    if scan_gain:
        acsc.enable(hcomm, 0)   
        acsc.toPoint(hcomm, None,0,110) #YIFU CHECK THIS
        acsc.setVelocity(hcomm, 0, 5) #velocity in mm/sec
    #theta
    acsc.enable(hcomm, 1)   
    acsc.setVelocity(hcomm, 1, 10) #velocity in degrees/sec
    acsc.setJerk(hcomm, 1, 500) #jerk, normal is 9000
    acsc.setDeceleration(hcomm, 1, 450) #jerk, normal is 9000
    acsc.setAcceleration(hcomm, 1, 450) #Acceleration, normal is 9000
    acsc.toPoint(hcomm, None,1,0)


#Actually do the imaging
if do_scan:
    for idx in range(degrees_array.shape[0]):
        q = time.time()
        set_degree=degrees_array[idx]
        move_stage(degrees_array[idx])
        # print("time it takes to moves")
        # print(time.time()-q)
        moving=True
        # while(abs(acsc.getFVelocity(hcomm, 1))>wait_ms): #check for stop event using other API call?
            # 1+1
        while(not acsc.getMotorState(hcomm,1)['in position']): #check for stop event using other API call?
            time.sleep(.1)
            
        take_photo(set_degree,idx)
        # if degrees_array[idx] in drift_track_angle_array and idx>0:
        if degrees_array[idx] in drift_track_angle_array and idx>0:
            take_drift_correction_photo(set_degree)
        # print("between moves")
        # print(time.time()-q)



if load_stages:
    take_drift_correction_photo(total_degrees)
    move_stage(0)
    while(not acsc.getMotorState(hcomm,1)['in position']): #check for stop event using other API call?
        time.sleep(.1)
    acsc.closeComm(hcomm)   
print(datetime.now()-startTime)