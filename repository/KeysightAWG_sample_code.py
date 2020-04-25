'''
Sample code for Keysight AWG, M3202A from user manual
See below for examples on generating a sine wave output, and a sawtooth wave output
'''
# ----------
# Python - Sample Application, Overall Work Flow and Sequence of Commands
# ----------
# Import required system components
import sys
# ----------
# Append the system path to include the
# location of Keysight SD1 Programming Libraries then import the library
sys.path.append('/usr/local/Keysight/SD1/')
import keysightSD1 as key # Import SD1 library and AWG/Digitizer commands.
#
# # ----------
# # Specify values for variables related to the AWG and Chassis
# AWG_PRODUCT = "M3202A" # Product's model number
# CHASSIS = 1 # Chassis number holding product
# AWG_SLOT = 4 # Slot number of product in chassis
#
# # ----------
# # Specify values for variables related to the AWG waveform
# waveform_number = 1 # Numerical label of AWG waveform
# cycles = 1 # Number of times to play a waveform from same channel
# start_delay = 0 # Delay the start of the waveform playback
# prescalar = 0 # How much to scale the outgoing waveform
#
# # ----------
# # Select settings and use specified variables
# awg = key.SD_AOU() # Create an AWG object
#
# # ----------
# # Open and connect to the specific AWG, using openWithSlot().
# # If any errors occur, they are negative numbers and saved into aouID.
# aouID = awg.openWithSlot(AWG_PRODUCT, CHASSIS, AWG_SLOT)
# # Check aouID for errors and close connection if an error is found
# if aouID < 0:
# # If aouID is a negative number, an error occurred so print it out
#     print("ERROR")
# # Print error code so it can be looked up in the Keysight SD1 error list.
# print("aouID:", aouID)
# # Since there was an error, close the connection with the AWG.
# awg.close()
# # Print out a message that the connection is closed.
# print()
# print("AOU connection closed")
#
# # If NO errors occur, flush/remove remaining old waveforms from AWG memory
# awg.waveformFlush()
#
# # ----------
# # Set all four channels (1 to 4) of the AWG output mode
# awg.channelWaveShape(1, key.SD_Waveshapes.AOU_AWG)
# awg.channelWaveShape(2, key.SD_Waveshapes.AOU_AWG)
# awg.channelWaveShape(3, key.SD_Waveshapes.AOU_AWG)
# awg.channelWaveShape(4, key.SD_Waveshapes.AOU_AWG)
#
# # ----------
# # Create a new wave object
# wave = key.SD_Wave()
#
# # ----------
# # Load a .csv file as the wave data
# wave.newFromFile("C:\\Users\Public\Documents\Keysight\SD1\Examples\Waveforms\Gaussian.csv")
#
# # ----------
# # Load the wave csv file into AWG memory,
# # assigning it the arbitrary number set earlier in this program.
# awg.waveformLoad(wave, waveform_number)
#
# # ----------
# # Queue everything that will be playing, with AWGqueueWaveform()
# # AWGqueueWaveform(CHANNEL, number assigned to wave you want,
# # trigger mode, delay before start (ns), number of times to play, prescaler)
# awg.AWGqueueWaveform(1, waveform_number, key.SD_TriggerModes.SWHVITRIG,
# start_delay, cycles, prescalar)
# awg.AWGqueueWaveform(2, waveform_number, key.SD_TriggerModes.SWHVITRIG,
# start_delay, cycles, prescalar)
# awg.AWGqueueWaveform(3, waveform_number, key.SD_TriggerModes.SWHVITRIG,
# start_delay, cycles, prescalar)
# awg.AWGqueueWaveform(4, waveform_number, key.SD_TriggerModes.SWHVITRIG,
# start_delay, cycles, prescalar)
#
# # ----------
# # Set the relative amplitudes for each channel.
# # CSV waveforms are normalized between -1 and 1 * amplitude.
# awg.channelAmplitude(1, 1.5)
# awg.channelAmplitude(2, 1.5)
# awg.channelAmplitude(3, 1.5)
# awg.channelAmplitude(4, 1.5)
#
# # ----------
# # Start each channel's waveform - If trigger mode was set to AUTO, they would
# # start playing automatically but, since SD_TriggerModes.SWHVITRIG was
# # selected, a software trigger is required to play each channel's waveform
# awg.AWGstart(1)
# awg.AWGstart(2)
# awg.AWGstart(3)
# awg.AWGstart(4)
# # ----------
# # Trigger waveforms with software triggers to play the loaded waveforms
# awg.AWGtrigger(1)
# awg.AWGtrigger(2)
# awg.AWGtrigger(3)
# awg.AWGtrigger(4)
#
# # ----------
# # Close the connection with the AWG hardware.
# awg.close()
# # ----------
# # © Keysight Technologies, 2018
#
#
# # ----------
# # Python - Sample Application to set up the AWG
# # to output a sine wave out of channel 1, at 1 MHz, and at 0.1 Vpp.
# # ----------
# # Import required system components
# import sys
#
# # ----------
# # Append the system path to include the
# # location of Keysight SD1 Programming Libraries then import the library
# sys.path.append('C:\Program Files (x86)\Keysight\SD1\Libraries\Python')
# import keysightSD1 # Import Python SD1 library and AWG/Digitizer commands.
#
# # ----------
# # Specify values for variables
# product = 'M3202A' # Product's model number
# chassis = 1 # Chassis number holding product
# slot = 4 # Slot number of product in chassis
# channel = 1 # Channel being used
# amplitude = 0.1 # (Unit: Vpp) Amplitude of AWG output signal (0.1 Vpp)
# frequency = 1e6 # (Unit: Hz ) Frequency of AWG output signal (1 MHz)
# waveshape = keysightSD1.SD_Waveshapes.AOU_SINUSOIDAL # Specify sine wave
#
# # ----------
# # Select settings and use specified variables
# awg = keysightSD1.SD_AOU() # Creates SD_AOU object called awg
# awg.openWithSlot(product, chassis, slot) # Connects awg object to module
# awg.channelAmplitude(channel, amplitude) # Sets output amplitude for awg
# awg.channelFrequency(channel, frequency) # Sets output frequency for awg
# awg.channelWaveShape(channel, waveshape) # Sets output signal type for awg
#
# # ----------
# # Start playing the sine wave on the specified channel
# awg.AWGstart(channel)
#
# # ----------
# # (Optional) Example: To vary the amplitude of the sine wave
# import time
# amps = [0.1, 0.2, 0.3, 0.4, 0.1]
# def varyAmplitude():
#     for amplitude in amps:
#         time.sleep(3) # Add delays before amplitude changes
#         awg.channelAmplitude(channel, amplitude)
# # ----------
# # (Optional) Example: To vary the frequency of the sine wave
# freqs = [1e6, 2e6, 3e6, 4e6, 1e6]
# def varyFrequency():
#     for frequency in freqs:
#         time.sleep(3) # Add delays before frequency changes
#         awg.channelFrequency(channel, frequency)
#
# varyAmplitude()
# varyFrequency()
# # ----------
# # Close the connection between the AWG object and the physical AWG hardware
# awg.close()
# # ----------
# # © Keysight Technologies, 2018
#
#
#
# # ----------
# # Python - Sample Application to set up the AWG
# # to output an array that was created with numpy.
# # ----------
# # Import required system components
# import sys
# # ----------
# # Append the system path to include the
# # location of Keysight SD1 Programming Libraries then import the library
# sys.path.append('C:\Program Files (x86)\Keysight\SD1\Libraries\Python')
# import keysightSD1 # Import Python SD1 library and AWG/Digitizer commands.
# import numpy # Import numpy which is used to make an array
# # ----------
# # Specify values for variables
# product = 'M3202A' # Product's model number
# chassis = 1 # Chassis number holding product
# slot = 4 # Slot number of product in chassis
# channel = 1 # Channel being used
# amplitude = 0.1 # (Unit: Vpp) Amplitude of AWG output signal (0.1 Vpp)
# waveshape = keysightSD1.SD_Waveshapes.AOU_AWG # Specify AWG output
# delay = 0 # (Unit: ns) Delay after trigger before generating output.
# cycles = 0 # Number of cycles. Zero specifies infinite cycles.
# # Otherwise, a new trigger is required to actuate each cycle
# prescaler = 0 # Integer division reduces high freq signals to lower frequency
# # ----------
# # Select settings and use specified variables
# awg = keysightSD1.SD_AOU() # Creates SD_AOU object called awg
# awg.openWithSlot(product, chassis, slot) # Connects awg object to module
# awg.channelAmplitude(channel, amplitude) # Sets output amplitude for awg
# awg.channelWaveShape(channel, waveshape) # Sets output signal type for awg
# awg.waveformFlush() # Cleans the queue
# awg.AWGflush(channel) # Stops signal from outputing out of channel 1
#
# # Create an array that represents a sawtooth signal using "numpy"
# array = numpy.zeros(1000) # Create array of zeros with 1000 elements
# array[0] = -0.5 # Initialize element 0 as -0.5
# for i in range(1, len(array)): # This for..loop will increment from -0.5
#     array[i] = array[i-1] + .001 # Increment by .001 every iteration
#
# wave = keysightSD1.SD_Wave() # Create SD_Wave object and call it "wave"
# # (will place the array inside "wave")
# error = wave.newFromArrayDouble(keysightSD1.SD_WaveformTypes.WAVE_ANALOG,
# array.tolist()) # Place the array into the "wave" object
# waveID = 0 # This number is arbitrary and used to identify the waveform
# awg.waveformLoad(wave, waveID) # Load the "wave" object and give it an ID
# awg.AWGqueueWaveform(channel, waveID, keysightSD1.SD_TriggerModes.SWHVITRIG, delay, cycles, prescaler) # Queue waveform to prepare it to be output
#
# # ----------
# awg.AWGstart(channel) # Start the AWG
# awg.AWGtrigger(channel) # Trigger the AWG to begin
# # ----------
# # Close the connection between the AWG object and the physical AWG hardware.
# awg.close()
# # ----------
# # © Keysight Technologies, 2018
# # All rights reserved.
# # You have a royalty-free right to use, modify, reproduce
# # and distribute this Sample Application (and/or any modified
# # version) in any way you find useful, provided that
# # you agree that Keysight Technologies has no warranty,
# # obligations or liability for any Sample Application Files.
# # Keysight Technologies provides programming examples
# # for illustration only. This sample program assumes that
# # you are familiar with the programming language being
# # demonstrated and the tools used to create and debug
# # procedures. Keysight Technologies support engineers can
# # help explain the functionality of Keysight Technologies
# # software components and associated commands, but they
# # will not modify these samples to provide added
# # functionality or construct procedures to meet your
# # specific needs.
# # ----------