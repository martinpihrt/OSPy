#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from threading import RLock

use_pigpio = False
try:
    import pigpio
    use_pigpio = True
except ImportError:
    use_pigpio = False
    print(traceback.format_exc())

if use_pigpio:
   import pigpio

i2c_lock = RLock()

try:
    pi = pigpio.pi('localhost', 8888) 
    #pi = pigpio.pi() ###Can't connect to pigpio at soft(8888)### 
                      ###Did you start the pigpio daemon?### 
                      ###E.g. sudo pigpiod Did you specify the correct Pi host/port in the environment variables PIGPIO_ADDR/PIGPIO_PORT?###
                      ###E.g. export PIGPIO_ADDR=soft, export PIGPIO_PORT=8888 Did you specify the correct Pi host/port in the pigpio.pi() function?###
                      ###E.g. pigpio.pi('soft', 8888)###
except Exception:
    use_pigpio = False
    print(traceback.format_exc())


SDA = 2
SCL = 3
BAUD = 300000 


def i2c_close():
    try:    
        with i2c_lock:
            if use_pigpio:
               print('Closing i2c bus')
               pi.bb_i2c_close(SDA)
        time.sleep(.5)
    except:
        pass
i2c_close()


def i2c_open():
    with i2c_lock:
        h = 0
        if use_pigpio:
           print('Opening i2c bus')
           h = pi.bb_i2c_open(SDA, SCL, BAUD)
    if h != 0:
        if use_pigpio:
           print('Cannot open i2c bus: ' + str(h))
i2c_open()


def i2c_reset(address, reg, val):
    if use_pigpio:
       print('Start resetting i2c address: ' + hex(address))
    with i2c_lock:
       i2c_write(address, reg, val)
       time.sleep(4)
       i2c_close()
       i2c_open()
    if use_pigpio:
       print('Finished resetting i2c address: ' + hex(address))


def i2c_read(address, reg):
    with i2c_lock:
      if use_pigpio:
         i2c_data = [4, address, 2, 7, 1, reg, 2, 6, 1, 3, 0]
#        print 'i2c_read data: ', i2c_data
         (count, data) = pi.bb_i2c_zip(SDA, i2c_data)
    if count < 0:  
#        print 'i2c_read failure count: ', count, ' addr: ', hex(address), ' reg: ', hex(reg)
        raise IOError, "i2c read failure"
#    print 'i2c_read count: ', count, ' data[0]: ', data[0], ' addr: ', hex(address), ' reg: ', hex(reg)
    return data[0]
    
    
def i2c_read_block_data(address, reg, byte_count):
    with i2c_lock:
       if use_pigpio:
         i2c_data = [4, address, 2, 7, 1, reg, 2, 6, byte_count, 3, 0]
#        print 'i2c_read_block data: ', i2c_data
         (count, data) = pi.bb_i2c_zip(SDA, i2c_data)
#    print 'i2c_read_block_data count: ', count, ' addr: ', hex(address), ' reg: ', hex(reg), ' byte_count: ', byte_count
    if count < 0:  
        raise IOError, "i2c read failure"
#    for i in range(count):
#        print 'i2c_read_block_data data[',i,']: ', data[i], hex(data[i])
    return data    


def i2c_write(address, reg, val, delay=.1):
    with i2c_lock:
      if use_pigpio:
         i2c_data = [4, address, 2, 7, 2, reg, val, 3, 0]
#        print 'i2c_write data: ', i2c_data
         (count, data) = pi.bb_i2c_zip(SDA, i2c_data)
         time.sleep(delay)
    if count < 0:  
#        print 'i2c_write failure count: ', count, ' addr: ', hex(address), ' reg: ', hex(reg), ' val: ', val
         raise IOError, "i2c write failure"
#    print 'i2c_write count: ', count, ' addr: ', hex(address), ' reg: ', hex(reg), ' val: ', val
    
    
def i2c_write_block_data(address, reg, wdata, delay=.1):
    """Write the list of bytes in data by writing them"""

    cmd = [4, address, 2, 7, 1+len(wdata), reg] # prepare for writing
    cmd += wdata
    cmd += [3, 0] # finish
    with i2c_lock:
       if use_pigpio:
#        print 'i2c_write_block_data cmd: ', cmd
         (count, data) = pi.bb_i2c_zip(SDA, cmd)
         time.sleep(delay)
    if count < 0:  
        raise IOError, "i2c write failure"
        

def sign_extend(value, bits):
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)
    
  
def i2c_structure_read(format, address, reg):
    byte_count = 0
    for c in format:
        if c == 'b' or c == 'B':
            byte_count += 1
        elif c == 'h' or c == 'H':
            byte_count += 2
        elif c == 'i' or c == 'I':
            byte_count += 4
        elif c == 'q' or c == 'Q':
            byte_count += 8
        elif c == ' ':
            continue
        else:
            raise ValueError("Unrecognized format")

    result = []
    try:
#        print 'attempt structure_read format: ' + format + ' address: ' + hex(address) + ' reg: ' + hex(reg) + ' byte_count: ' + str(byte_count)
        vs = i2c_read_block_data(address, reg, byte_count)
#        if byte_count == 14:
#            print ' len: ', byte_count, ' format: ', format
#            print 'structure bytes: ', ','.join([hex(i) for i in vs])
        for c in format:
            if c == 'b' or c == 'B':
                v = vs.pop(0)
                if c == 'b':
                    v = sign_extend(v, 8)
            elif c == 'h' or c == 'H':
                vss = [vs.pop(0) for i in range(2)]
                v = (vss[0]<<8) | vss[1]
                if c == 'h':
                    v = sign_extend(v, 16)
            elif c == 'i' or c == 'I':
                vss = [vs.pop(0) for i in range(4)]
                v = (vss[0]<<24) | (vss[1]<<16) | (vss[2]<<8) | vss[3]
                if c == 'i':
                    v = sign_extend(v, 32)
            elif c == 'q' or c == 'Q':
                vss = [vs.pop(0) for i in range(8)]
                v = (vss[0]<<56) | (vss[1]<<48) | (vss[2]<<40) | (vss[3]<<32) | \
                    (vss[4]<<24) | (vss[5]<<16) | (vss[6]<<8) | vss[7]
            result.append(v)
    except:
        pass
    return result
    

def i2c_structure_write(format, address, reg, data, delay=.1, byte_swap=False):
    # for now assume MSB written first
#    print 'sw size: ', len(data), binascii.hexlify(data), format, hex(address), hex(reg)
    w_data = []
    pos = 0
    for c in format:
        size = 0
        if c == 'b' or c == 'B':
            size = 1
        elif c == 'h' or c == 'H':
            size = 2
        elif c == 'i' or c == 'I':
            size = 4
        elif c == 'q' or c == 'Q':
            size = 8
        elif c == ' ':
            continue
        elif c == 'X': # skip a byte in data for alignment or whatever
            pos += 1
        else:
            raise ValueError("Unrecognized format")

        if (pos & ((1<<(size-1)) - 1)) != 0:
            print('i2c_structure_write_via_read requires aligned data.  Format: ' + format)
        for i in range(size):
            if byte_swap:
                w_data.append(data[pos+size-1-i])
            else:
                w_data.append(data[pos+i])
        pos += size

i2c_write_block_data(address, reg, w_data, delay)
