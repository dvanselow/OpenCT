'''
r232 serial monitoring of an Oasis 170 liquid cooler
Reads and outputs current pump temperature
Resets pump during pump fault
Pump does not need
'''

import serial
import time
import sys
import binascii
import datetime
def bitstring_to_bytes(s):
    v = int(s, 2)
    b = bytearray()
    while v:
        b.append(v & 0xff)
        v >>= 8
    return bytes(b[::-1])

z1baudrate = 9600
z1port = 'COM2'  # set the correct port before run it
byte_size=8
stop_bits=1
z1serial = serial.Serial(port=z1port, baudrate=z1baudrate,bytesize=byte_size,stopbits=stop_bits)
z1serial.timeout = 2  # set read timeout
read_fault_table=[b'\xC8']
reset_cooler=[b'\xFF']
read_temp=[b'\xC9']
set_temp=[b'\xE1',b'\xA5',b'\x00']
# 
if z1serial.is_open:
    print('\n\n\n\n\n\n\n\n\n\n')
    print(z1port+" is open: "+str(z1serial.is_open))

    while True:
        z1serial.write(read_fault_table[0])
        time.sleep(.5)
        size = z1serial.inWaiting()
        if size:
            data = z1serial.read(size)
            hex_string=binascii.hexlify(data).encode('utf8')
            print("temp hex       : "+hex_string[0:5])
            print("fault table hex: "+hex_string[6:10])
            if hex_string[0:2]=='c9':
                sys.stdout.write("Temperature at "+str(datetime.datetime.now().time()).split(".")[0] +" - "+str(float(int(hex_string[2:4],16))/10)+u'\N{DEGREE SIGN}'+"C                "+"\r")
                sys.stdout.flush()
                
            if hex_string[6:10]!='c800':
                if hex_string[8:10]=='02': #This should actually be 20, but IRL it's triggering as 02 for some reason.***
                    print("pump fault  at "+str(datetime.datetime.now().time()).split(".")[0] +"!! Resetting")
                    print(str(datetime.datetime.now().time()).split(".")[0])
                    z1serial.write(reset_cooler[0])
                    time.sleep(10)
                if hex_string[8:10]=='20': #***So we're going to throw both of them in there ('20' and '02')
                    print("pump fault  at "+str(datetime.datetime.now().time()).split(".")[0] +"!! Resetting")
                    print(str(datetime.datetime.now().time()).split(".")[0])
                    z1serial.write(reset_cooler[0])
                    time.sleep(10)
                elif hex_string=="04":
                    print('Temp outside of normal operating range')
                    print('You probably just turned on or reset the pump')
                    print(hex_string)
                    print(hex_string[2:len(hex_string)])

            z1serial.write(read_temp[0])
            time.sleep(.1)
        else:
            sys.stdout.write('                        no data at '+str(datetime.datetime.now().time()).split(".")[0]+'\r')
            sys.stdout.flush()
        time.sleep(2)
else:
    print ('z1serial not open')