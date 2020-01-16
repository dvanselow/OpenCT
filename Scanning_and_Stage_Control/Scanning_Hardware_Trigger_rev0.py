'''
1) Start configurator.
2) Set exposure through configurator.
3) Select "External Sync", "Program," "External Port" and then active "High" or "Low" depending on what Berkeley Uses
also 3) Select "External Sync", "Pulse Width", "External Port" and then active "High" or "Low" depending on what Berkeley Uses
4) Activate acq
5) Don't forget to type in "python" before the script path.


Also, as long as everything is done, order doesn't actually matter.

REMEMBER, YOU CAN TEST THAT THE HW TRIGGER IS WORKING IN MULTICAM.

STILL USE MULTICAM TO FOCUS, AND OTHERWISE DO LIVE ALIGNMENT.

BUT YOU KNOW THAT ALREADY. Make sure SeqLength_Fr is -1 (In multicam. Not here.)


If the script errors on something stupid, it's probably the frame averaging logic, just fix it.
Otherwise it's probably the While loop not making sense. Also just fix it.
Other Otherwise, use R1.5 and treat the num_exposures_per_projection as # of projections and re-implement the frame averaging that we usually use.
'''


import dxchange as dx
import numpy as np
import time
from datetime import datetime
import os
import sys
# from acspy import acsc
# from acspy.control import Controller
#from GrablinkSnapshot import *  #not actually needed
import ctypes
import MultiCam as MC



proj_dir=os.path.dirname(sys.argv[0])



###############################################################################################
#Camera initialize channel
###############################################################################################
#This could be a cause for failure. Technically the RG version shouldn't work. It does. Don't tell anyone.
#Also make sure it's actually finding the file. It should be in the same folder as this script. Just hard link it if it's not.
###############################################################################################
#camFile="C:\\Users\\ChengLab\\Desktop\\MP71Camera\\VP-71MC-M5_P200SC_4tap(H)_12bit_RG (VST Y12).cam"
camFile=proj_dir+"\\VP-71MC-M5_P200SC_4tap(H)_12bit_RG (VST Y12).cam" 


channel = MC.Create('CHANNEL')
driverIndex=0
connector="M"
MC.SetParamInt(channel, 'DriverIndex', driverIndex)
MC.SetParamStr(channel, 'Connector', connector)
MC.SetParamStr(channel, 'CamFile', camFile)
MC.SetParamInt(channel, 'SeqLength_Fr', 1) #Don't set this to -1.

###############################################################################################
#Need these monitoring calls activated.
###############################################################################################
MC.SetParamStr(channel, MC.SignalEnable + MC.SIG_SURFACE_PROCESSING, 'ON')
MC.SetParamStr(channel, MC.SignalEnable + MC.SIG_ACQUISITION_FAILURE, 'ON')
MC.SetParamStr(channel, MC.SignalEnable + MC.SIG_END_CHANNEL_ACTIVITY, 'ON')

###############################################################################################
#The configurator takes care of all these commented out calls. Don't worry about them. I think.
###############################################################################################

# MC.SetParamInt(channel, "Expose_us", 4000000);
#Don't initiate trigger modes here, they're handled in the configurator.
# MC.SetParamStr(channel, "TrigMode", "IMMEDIATE");
# Choose the triggering mode for subsequent acquisitions
# MC.SetParamStr(channel, "NextTrigMode", "REPEAT");

# # #trigger
# # MC.SetParamStr(channel, "TrigMode", "IMMEDIATE");
# # # Choose the triggering mode for subsequent acquisitions
# # MC.SetParamStr(channel, "NextTrigMode", "REPEAT");
# # MC.SetParamInt(channel, 'SeqLength_Fr', MC.INDETERMINATE) #might need this for HW triggering?
# MC.SetParamStr(channel, "AcquisitionMode", "SNAPSHOT");
# # Choose the way the first acquisition is triggered
# MC.SetParamStr(channel, "TrigMode", "COMBINED");
# # Choose the triggering mode for subsequent acquisitions
# MC.SetParamStr(channel, "NextTrigMode", "COMBINED");
# #Configure triggering line
# #A rising edge on the triggering line generates a trigger.
# #See the TrigLine Parameter and the board documentation for more details.
# MC.SetParamStr(channel, "TrigLine", "NOM");
# MC.SetParamStr(channel, "TrigEdge", "GOHIGH");
# MC.SetParamStr(channel, "TrigFilter", "ON");

# #Parameter valid for all Grablink but Full, DualBase, Base
# # # MC.SetParam(channel, "TrigCtl", "ITTL");
# #Parameter valid only for Grablink Full, DualBase, Base
# MC.SetParamStr(channel, "TrigCtl", "ISO");

###############################################################################################
#Frame Averaging setup, Max knows what's up.  
###############################################################################################
#WARNING, THERE IS NO MECHANISM CODE SIDE THAT CAN HANDLE >1 FOR THIS VARIABLE. YOU WOULD HAVE TO MAKE SURE
#THAT THEIR HW TRIGGER CAN SEND MULTIPLE TRIGGERS PER ANGLE. HOPEFULLY 7S IS ENOUGH.
#OR USE A PULSE WIDTH TRIGGER AND TRIGGER WIDTH FOR HOWEVER LONG YOU WANT (ALLEDGEDLY)
num_exposures_per_projection=1 #Change this if you need more signal from exposures and 7s isn't enough.
###############################################################################################

dimm_1=10000    #don't change
dimm_2=7096     #don't change

###############################################################################################
#Change this to A:/Raw_Scans/"
###############################################################################################
# base_dir="C:/Users/ChengLab/Desktop/PyMicroTest_Outputs/"
# base_dir="Q:/Raw_Scans/"
base_dir="D:/Scratch_Space/function_generator/test/"

timestr = time.strftime("%Y%m%d-%H%M%S")
###############################################################################################
#Change this to whatever folder you want it in. They'll dump into a unique folder that starts with Berkeley_10k_ followed by a unique timestring and the number of exposures averaged. 
#Feel free to manually add expsure time at the end or whatever.
#Technically you can use this call to grab the exposure values assigned by the configurator:
#exposure = MC.GetParamInt(channel, "Expose_us")
#But you'll have to test it yourself. Otherwise, just keep track of it somewhere.
###############################################################################################
output_dir=base_dir+"\\Berkeley_10k_"+timestr+"_"+str(num_exposures_per_projection)+"_expAvg"+"\\"


#Last of the channel prep:
planeIndex=0
MC.SetParamStr(channel, 'ChannelState', 'READY') #Preps the channel for fast activation. READY STEADY MOM'S SPAGHETTI    



projection_fill=np.zeros([num_exposures_per_projection,dimm_2,dimm_1])
#Full scan timing
s1= datetime.now()


Scantron=True #don't change this
Proj_count=0 #don't change this
# for projnum in range(num_exposures_per_projection):
while Scantron:
    print("Projection %d" %(Proj_count))
    s2= datetime.now() #frame average timer
    #In case you need to frame average. But we can't control this our side, you'd have to get them to send more than one trigger per angle. So this is worthless.
    for avg_idx in range(0,num_exposures_per_projection):
        print("frame %d of %d" %(avg_idx, num_exposures_per_projection))
        s3= datetime.now()
        MC.SetParamStr(channel, 'ChannelState', 'ACTIVE')   #ACTIVE SET MOM'S SPAGHETT  
###############################################################################################
        #Where the literal magic happens
###############################################################################################
        gotEndOfChannelActivity = False
        gotAcquisitionFailure = False
        while not gotEndOfChannelActivity:
            signalInfo = MC.WaitSignal(channel, MC.SIG_ANY, 15000) #Attempt to make this call shorter (1.5 second overhead as written....)
            print(signalInfo.Signal)
            #signalInfo = MC.WaitSignal(channel, MC.SIG_ANY, 1000)
            print(signalInfo.Signal)
            if signalInfo.Signal == MC.SIG_END_CHANNEL_ACTIVITY:
                gotEndOfChannelActivity = True
            # elif signalInfo.Signal == MC.SIG_ACQUISITION_FAILURE: #This is commented out because failure is not an option.
                # gotAcquisitionFailure = True
            elif signalInfo.Signal == MC.SIG_SURFACE_PROCESSING:    #When the surface is done filling, it'll fall into a 'processing' state. We know the exposure is complete now. So get out of this loop // trigger the end of channel activity.
                MC.SetParamStr(signalInfo.SignalInfo, 'SurfaceState', 'FREE')   
            else:
                raise MC.MultiCamError('Unexpected signal: %d' % signalInfo.Signal)
        if gotAcquisitionFailure:
            raise MC.MultiCamError('Acquisition failure!')
            
###############################################################################################
        #Could actually make sense of the rest of this, but there should be no need to alter the below code
###############################################################################################
        surface = MC.GetParamInst(channel, 'Cluster:0')
        width = MC.GetParamInt(surface, 'SurfaceSizeX')
        height = MC.GetParamInt(surface, 'SurfaceSizeY')
        # image = ConvertSurfaceIntoImage(surface)
        surfaceAddress = MC.GetParamPtr(surface, 'SurfaceAddr:%d' % planeIndex)
        surfaceSize = MC.GetParamInt(surface, 'SurfaceSize:%d' % planeIndex)
        imageBuffer = ctypes.string_at(surfaceAddress, surfaceSize)
        MC.SetParamStr(channel, 'ChannelState', 'READY')    #READY STEADY MOM'S SPAGHETTI TAKE 2. 
        data = np.fromstring(imageBuffer, np.uint16)
        image=np.reshape(data,(height,width))   #it's a 1d string at this point, so have to turn it into a 2d matrix.
###############################################################################################
        #Could actually make sense of the rest of this, but there should be no need to alter the above code
###############################################################################################
        print(str(datetime.now()-s3)+" single proj")    #Feel free to comment this out if too verbose
        projection_fill[avg_idx] = image        #Filling the projection matrix. Max we never switched to 32bit addition into one 2d matrix, but whatever. You shouldn't have to grab more than 48 (~64GB RAM limit).
    print(str(datetime.now()-s3)+"frame avg")            #Feel free to comment this out
    proj=np.mean(projection_fill,axis=0)
    dx.write_tiff(proj, output_dir+"\\projection_"+str(Proj_count),dtype=np.uint16)
    Proj_count+=1
###############################################################################################
        #Uncomment out below if you are taking a single frame-average for testing purposes and don't believe it's working.
        #Because it wasn't until very recently.
###############################################################################################
    # for idx,image in enumerate(projection_fill):
        # dx.write_tiff(image, output_dir+"\\projection_singles_"+str(idx),dtype=np.uint16)
    
print(str(datetime.now()-s1)+" total scan")