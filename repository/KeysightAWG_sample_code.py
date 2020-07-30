# Write introduction here

import keysightSD1 # Import Python SD1 library and AWG/Digitizer commands.
import base_experiment
from artiq.experiment import *
import numpy as np

class Keysight(base_experiment.base_experiment):

    def run(self):
        # Select settings and use specified variables
        product = 'M3202A'  # Product's model number
        chassis = 1 # Chassis number holding product
        slot = 3  # Slot number of product in chassis
        channel = 1  # Channel being used
        amplitude = 0.3  # (Unit: Vpp) Amplitude of AWG output signal (0.1 Vpp)
        frequency = 10e6  # (Unit: Hz ) Frequency of AWG output signal in MHz
        frequency2 = 1
        # waveshape = keysightSD1.SD_Waveshapes.AOU_AWG  # Specify AWG output
        # delay = 0  # (Unit: ns) Delay after trigger before generating output.
        # cycles = 0  # Number of cycles. Zero specifies infinite cycles.
        # # Otherwise, a new trigger is required to actuate each cycle
        # prescaler = 0  # Integer division reduces high freq signals to lower frequency
        # cycle_len = int(frequency1 - frequency2) + 1  # Define the length of one cycle of our wave

        success = 'AWG code ran successfully'
        error = 'Error loading AWG'

        try:
            awg = keysightSD1.SD_AOU()               # Creates SD_AOU object called awg

            # ERROR IS HERE:
            aouID = awg.openWithSlot(product, chassis, slot) # Connects awg object to module

            # Check aouID for errors and close connection if an error is found
            if aouID < 0:
                # If aouID is a negative number, an error occurred so print it out
                print("ERROR")
                # Print error code so it can be looked up in the Keysight SD1 error list.
                print("aouID:", aouID)
                # Since there was an error, close the connection with the AWG.
                awg.close()
                # Print out a message that the connection is closed.
                print("AOU connection closed")

            awg.channelAmplitude(channel, amplitude) # Sets output amplitude for awg
            waveshape = keysightSD1.SD_Waveshapes.AOU_SINUSOIDAL # Specify sine wave
            awg.channelWaveShape(channel, waveshape) # Sets output signal type for awg

            awg.waveformFlush() # Cleans the queue
            awg.AWGflush(channel) # Stops signal from output from channel 1

            # ----------
            # Select settings and use specified variables
            awg.channelFrequency(channel, frequency) # Sets output frequency for awg

            # ----------
            # Start playing the sine wave on the specified channel
            awg.AWGstart(channel)

            # Create an array that represents sum of two sine signals using "numpy"
            # array = np.zeros(100) # Create array of zeros
            #
            # for i in range(1, len(array)): #Create appropriate waveform in array
            #     # array[i] = np.sin(1000*i*2*np.pi*frequency1) + np.sin(1000*i*2*np.pi*frequency2)
            #     array[i] = np.sin(i)
            #
            # print(array)
            #
            # wave = keysightSD1.SD_Wave() # Create SD_Wave object and call it "wave"
            #
            # print(wave)
            # # (will place the array inside "wave")
            #
            # error = wave.newFromArrayDouble(keysightSD1.SD_WaveformTypes.WAVE_ANALOG, array.tolist()) # Place the array into the "wave" object
            # waveID = 0 # This number is arbitrary and used to identify the waveform
            #
            # awg.waveformLoad(wave, waveID) # Load the "wave" object and give it an ID
            # awg.AWGqueueWaveform(channel, waveID, keysightSD1.SD_TriggerModes.SWHVITRIG, delay, cycles, prescaler)      # Queue waveform to prepare it to be output
            #
            # delay(1)
            #
            # self.triggerAWG()   # Use artiq ttl0 to trigger the AWG

            print(success)

        except:
            print('Error: ',error)

        finally:
            awg.close()


    # def trigger(self):
    #     awg.AWGstart(channel)       # Start the AWG
    #     awg.AWGtrigger(channel)     # Trigger the AWG to begin
    #     awg.close()

    # @kernel
    # def triggerAWG(self):
    #     self.ttl0.pulse(100 * ns)


# ##########################################  SAMPLE CODE BELOW  ###########################################
#
# # ----------
# # Python - Sample Application to set up the AWG
# #          to output a sine wave out of channel 1, at 1 MHz, and at 0.1 Vpp.
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
# chassis = 1             # Chassis number holding product
# slot = 4                       # Slot number of product in chassis
# channel = 1        # Channel being used
# amplitude = 0.1     # (Unit: Vpp) Amplitude of AWG output signal (0.1 Vpp)
# frequency = 1e6     # (Unit: Hz ) Frequency of AWG output signal (1 MHz)
# waveshape = keysightSD1.SD_Waveshapes.AOU_SINUSOIDAL # Specify sine wave
#
# # ----------
# # Select settings and use specified variables
# awg = keysightSD1.SD_AOU()                 # Creates SD_AOU object called awg
# awg.openWithSlot(product, chassis, slot) # Connects awg object to module
# awg.channelAmplitude(channel, amplitude) # Sets output amplitude for awg
# awg.channelFrequency(channel, frequency) # Sets output frequency for awg
# awg.channelWaveShape(channel, waveshape) # Sets output signal type for awg
#
# # ----------
# # Start playing the sine wave on the specified channel
# awg.AWGstart(channel)
#
#
# # ----------
# # (Optional) Example: To vary the amplitude of the sine wave
# import time
#
# amps = [0.1, 0.2, 0.3, 0.4, 0.1]
# def varyAmplitude():
# for amplitude in amps:
# time.sleep(3) # Add delays before amplitude changes
# awg.channelAmplitude(channel, amplitude)
#
# # ----------
# # (Optional) Example: To vary the frequency of the sine wave
# freqs = [1e6, 2e6, 3e6, 4e6, 1e6]
# def varyFrequency():
# for frequency in freqs:
# time.sleep(3) # Add delays before frequency changes
# awg.channelFrequency(channel, frequency)
#
# varyAmplitude()
# varyFrequency()
#
# # ----------
# # Close the connection between the AWG object and the physical AWG hardware
# awg.close()
#
# # ----------
