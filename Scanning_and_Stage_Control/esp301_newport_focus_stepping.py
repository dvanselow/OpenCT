#you should home this program using the standard PI homing program on buffer 8
#look at page 262 of ACS programing C book for Input (airlock) checking
# import SimpleITK as sitk  #used for image saving and manipulation #this is dumb
import dxchange as dx
import numpy as np
# import MMCorePy
import time
from datetime import datetime
import os
import sys
from acspy import acsc
from acspy.control import Controller
# from GrablinkSnapshot import *
# from GrablinkSnapshot import *
import ctypes
import MultiCam as MC
#Change these variables


load_camera10k=True
dont_dark=True #Our darks are super good. Taped the green LED and we're fine now.

proj_dir=os.path.dirname(sys.argv[0])
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


##########
#Initiate control of ESP301 (Focusing stage)
import clr
# Add reference to assembly and import names from namespace
clr.setPreload(True)
clr.AddReference(r'C:/Program Files (x86)/Newport/MotionControl/ESP301/Bin/Newport.ESP301.CommandInterface.dll')

from CommandInterfaceESP301 import *
import System
#=====================================================================
# Instrument Initialization
# The key should have double slashes since
# (one of them is escape character)
num_focal_steps=5 #This is doubled, forward and reverse
step_increment=.1 #how big is your focal hop
dummy_string="string dummy"
float_dummy=.01
stage_axis=1
instrument="COM3"
BAUDRATE = 921600
# create an ESP301 instance
ESP301Device = ESP301()
# Open communication
ret = ESP301Device.OpenInstrument(instrument, BAUDRATE);
#TP Reads current position
result, initial_position, errString = ESP301Device.TP(stage_axis,float_dummy,dummy_string)
if result == 0 :
    print ('position=>', initial_position)
else:
    print ('Error=>',errString)

focal_step_mtx=[initial_position]



for focal_step in range(num_focal_steps):
    focal_step_mtx.append(round(initial_position-step_increment*(focal_step+1)),4)
for focal_step in range(num_focal_steps):
    focal_step_mtx.append(round(initial_position+step_increment*(focal_step+1)),4)
print(focal_step_mtx)
focal_step_mtx.sort()
print(focal_step_mtx)
# moving_value=-.2
# move_to_position=0
#PR moves relative to current position by middle value
# result, errString = ESP301Device.PR(stage_axis,moving_value,dummy_string)

#PA_Set moves to absolute position
# result, errString = ESP301Device.PA_Set(stage_axis,move_to_position,dummy_string)

#MD Returns a 0 on the second value if the stage is moving. if you have trouble with blurry images, try adding a if [desired pos] == [target position <- DP]
while not ESP301Device.MD(stage_axis,float_dummy,dummy_string)[1]:
    time.sleep(.05)

#TP Reads current position
result, initial_position, errString = ESP301Device.TP(stage_axis,float_dummy,dummy_string)
if result == 0 :
    print ('position=>', initial_position)
else:
    print ('Error=>',errString)


# while ESP301Device.PR(stage_axis,float_dummy,dummy_string):
    # time.sleep(.1)







exposure_inpt=7000 #(in ms) #THIS DOES NOT OVERRIDE SETTINGS IN VIEWWORKS APPLET FOR NOW. SET EXPOSURE OVER THERE.
binning_value="1x1"
num_gain_per_scan=2
num_exposures_per_projection=num_gain_per_scan
focus="-.2"
sample_name="Spencers_AAA345_30kv_30w_s20_0db_z115_focus_stepping"

# if load_camera10k:
dimm_1=10000
dimm_2=7096
gain_fill=np.zeros([len(focal_step_mtx),dimm_2/int(binning_value[0]),dimm_1/int(binning_value[0])])
projection_fill=np.zeros([len(focal_step_mtx),dimm_2/int(binning_value[0]),dimm_1/int(binning_value[0])])


dark = dx.read_tiff("C:/Users/ChengLab/Desktop/PyMicroTest_Outputs/Projection_test/10k_DARKSETS/dark_%d" %exposure_inpt)

#Don't really change this
load_stages=1
load_camera=0
scan_gain=1
where_i_was = 118.5
do_scan = 1
# wait_ms=.0001
wait_ms=.0005

#Directory Business
base_dir="C:/Users/ChengLab/Desktop/PyMicroTest_Outputs/"
timestr = time.strftime("%Y%m%d-%H%M%S")
output_dir=base_dir+"\\"+"Projection_test"+"\\10k_"+timestr+"_"+str(num_exposures_per_projection*exposure_inpt)+"ms"+"_"+sample_name+"\\"
# output_dir=base_dir+"\\"+"Projection_test"+"\\"
if not os.path.exists(output_dir): os.makedirs(output_dir)
startTime = datetime.now()


if gain_z_out_of_beam < 110:
    print("MAKE SURE THIS IS ACTUALLY WHAT YOU WANT")
    exit()
#Functions
def change_focus(move_to_position):
    # move_to_position=focal_step_mtx[index]
    #PA_Set moves to absolute position
    result, errString = ESP301Device.PA_Set(stage_axis,move_to_position,dummy_string)
    #MD Returns a 0 on the second value if the stage is moving. if you have trouble with blurry images, try adding a if [desired pos] == [target position <- DP]
    while not ESP301Device.MD(stage_axis,float_dummy,dummy_string)[1]:
        time.sleep(.05)



def move_stage(set_degree):
    acsc.toPoint(hcomm, None,1,set_degree)
    
def gainscan(idx,position_to_move_to):
    gain_32bit_filler=np.zeros([dimm_2/int(binning_value[0]),dimm_1/int(binning_value[0])])
    change_focus(position_to_move_to)
    
    
    for gainnum in range(num_gain_per_scan):
        print("Gain projection %d out of %d" %(gainnum+1,num_gain_per_scan))
        if load_camera10k:
            # print("Projection %d out of %d" %(gainnum+1,num_exposures_per_projection))
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

        else:
            mmc.snapImage()
            image_npy = mmc.getImage()
        gain_32bit_filler = gain_32bit_filler + image_npy

    return gain_32bit_filler
    
def take_photo(deg,idx,position_to_move_to):
    #test image
    proj_32bit_filler=np.zeros([dimm_2/int(binning_value[0]),dimm_1/int(binning_value[0])])
    # print(projection_fill)
    change_focus(position_to_move_to)
    for projnum in range(num_exposures_per_projection):
        print("Projection %d out of %d" %(projnum+1,num_exposures_per_projection))
        if load_camera10k:
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
        else:
            mmc.snapImage()
            image_npy = mmc.getImage()
        proj_32bit_filler = proj_32bit_filler+image_npy
    return proj_32bit_filler


##################
####stage calls###
##################
if load_stages:
    #initiate connection
    hcomm = acsc.openCommEthernetTCP(address="10.0.0.100", port=701)
    if scan_gain:
        acsc.enable(hcomm, 0)   #z
        # acsc.toPoint(hcomm, None,0,110) #YIFU CHECK THIS
        acsc.setVelocity(hcomm, 0, 5) #velocity in mm/sec
        r_pos_0=acsc.getRPosition(hcomm,0)
        f_pos_0=acsc.getFPosition(hcomm,0)
    
    acsc.enable(hcomm, 1)   #theta
    acsc.setVelocity(hcomm, 1, 5) #velocity in degrees/sec
    r_pos_1=acsc.getRPosition(hcomm,1)
    f_pos_1=acsc.getFPosition(hcomm,1)
    # acsc.toPoint(hcomm, None,1,0)
    print("z-stage F pos: %f \n z-stage R pos: %f" %(f_pos_0,r_pos_0))
    print("theta-stage F pos: %f \n theta-stage R pos: %f" %(f_pos_1,r_pos_1))
    where_i_was = r_pos_0        
        
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
    mmc.setExposure(exposure_inpt)
    mmc.setProperty(device_id,"Binning",binning_value)
    print(mmc.getProperty(device_id,"Binning"))
    os.chdir(prev_dir)

##################
###camera calls###
##################
#load in 10k devices
if load_camera10k:
    camefile_path="C:\\Users\\ChengLab\\Desktop\\MP71Camera\\VP-71MC-M5_P200SC_4tap(H)_12bit_RG (VST Y12).cam"



#Actually do the imaging
if do_scan:
    while(not acsc.getMotorState(hcomm,1)['in position']): #check for stop event using other API call?
        time.sleep(.1)
    for focal_idx,focal_position in enumerate(focal_step_mtx):
        projection_fill[focal_idx]=take_photo(1,1,focal_position)
        print("projecting at "+str(focal_position))
    where_i_was=acsc.getRPosition(hcomm,0)
    acsc.toPoint(hcomm, None,0,gain_z_out_of_beam)
    while(not acsc.getMotorState(hcomm,0)['in position']): #check for stop event using other API call?
        time.sleep(.1)
    
    if scan_gain:
        for focal_idx,focal_position in enumerate(focal_step_mtx):
            gain_fill[focal_idx]=gainscan(1,focal_position)
            print("projecting at "+str(focal_position))
    acsc.toPoint(hcomm, None,0,where_i_was)
    while(not acsc.getMotorState(hcomm,0)['in position']): #check for stop event using other API call?
        time.sleep(.1)

if load_stages:
    while(not acsc.getMotorState(hcomm,1)['in position']): #check for stop event using other API call?
        time.sleep(.1)
    acsc.closeComm(hcomm)   
print(datetime.now()-startTime)
idx=1







for proj_idx,projection in enumerate(projection_fill):
    gain_corrected_image=np.divide(projection,gain_fill[proj_idx],dtype=np.float32)
    dx.write_tiff(gain_corrected_image, output_dir+"\\GC_Image_Focus_"+str(focal_step_mtx[proj_idx])+"_f"+str(proj_idx)+".tiff",dtype=np.float32)

#PA_Set moves to absolute position
result, errString = ESP301Device.PA_Set(stage_axis,initial_position,dummy_string)

#MD Returns a 0 on the second value if the stage is moving. if you have trouble with blurry images, try adding a if [desired pos] == [target position <- DP]
while not ESP301Device.MD(stage_axis,float_dummy,dummy_string)[1]:
    time.sleep(.05)

#TP Reads current position
result, initial_position, errString = ESP301Device.TP(stage_axis,float_dummy,dummy_string)
if result == 0 :
    print ('position=>', initial_position)
else:
    print ('Error=>',errString)


print("ALL DONE!!")
