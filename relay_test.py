#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

__author__ = 'Martin Pihrt'

# If you need to test the hardware board (to see if all relays are switching—e.g., in case of a hardware problem with the relays).
# Stop the service (sudo service ospy stop) and run the relay_test.py script in the OSPy folder.
# All relays on the board will switch on and off at 1.5-second intervals.

# www.pihrt.com ver: 1.0

# --- GPIO pins ---
DATA = 27   # SER
CLOCK = 4   # SRCLK
LATCH = 22  # RCLK
OE = 17     # OE (active LOW)
EXTRA_PIN = 15  # master relay physical pin 10 (RXI)
MR_PIN = None   # MR is connect to VCC -> None

# --- Setup ---
GPIO.setmode(GPIO.BCM)
GPIO.setup(DATA, GPIO.OUT, initial=0)
GPIO.setup(CLOCK, GPIO.OUT, initial=0)
GPIO.setup(LATCH, GPIO.OUT, initial=0)
GPIO.setup(OE, GPIO.OUT, initial=1)
GPIO.setup(EXTRA_PIN, GPIO.OUT, initial=0)

if MR_PIN is not None:
    GPIO.setup(MR_PIN, GPIO.OUT, initial=1)

TICK = 0.00002  # 20 µs delay

def pulse(pin):
    GPIO.output(pin, 1)
    time.sleep(TICK)
    GPIO.output(pin, 0)
    time.sleep(TICK)

def shift_out(byte, msb_first=True):
    if msb_first:
        bits = [(byte >> bit) & 1 for bit in range(7, -1, -1)]
    else:
        bits = [(byte >> bit) & 1 for bit in range(0, 8)]
    for b in bits:
        GPIO.output(DATA, b)
        time.sleep(TICK)
        GPIO.output(CLOCK, 1)
        time.sleep(TICK)
        GPIO.output(CLOCK, 0)
        time.sleep(TICK)

def latch_out():
    GPIO.output(LATCH, 1)
    time.sleep(TICK)
    GPIO.output(LATCH, 0)
    time.sleep(TICK)

try:
    GPIO.output(OE, 0)
    if MR_PIN is not None:
        GPIO.output(MR_PIN, 1)

    print("Starting test: 0xFF / 0x00 every 1.5s. Ctrl-C for exit.")
    while True:
        # turn ON all relay
        shift_out(0xFF, msb_first=True)
        latch_out()
        GPIO.output(EXTRA_PIN, 1)
        time.sleep(1.5)

        # turn OFF all relay
        shift_out(0x00, msb_first=True)
        latch_out()
        GPIO.output(EXTRA_PIN, 0)
        time.sleep(1.5)

except KeyboardInterrupt:
    print("Exit...")

finally:
    GPIO.output(OE, 1)
    GPIO.output(EXTRA_PIN, 0)
    GPIO.cleanup()