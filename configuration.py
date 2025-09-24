import ConfigPulseGen as config
import argparse
import sys

# argvs = sys.argv

def main():
    try:
        parser = argparse.ArgumentParser(description='configure pusle generator')
        parser.add_argument('--freq', type=int, help='trigger rate, 50Hz, 1kHz, 10Hz')
        parser.add_argument('--amp', type=float, help='S1 pulse amplitude, 1.36V')
        parser.add_argument('--width', type=int, help='pulse width, unit of ns, 20ns for SPE')
        parser.add_argument('--sync', type=str, help='Synchronize trigger Channel, CH1')
        parser.add_argument('--comb', type=str, help='CH1 Combine Mode option, True')
        parser.add_argument('--C2_ON', type=str, help='CH2 Open on Option, False')
        #parser.add_argument('--LongS2', type=str, help='Long2S2 200us Configure Option, False')
        args = parser.parse_args()  

        if len(vars(args)) != 6:
            raise Exception("Invalid number of arguments.")
            return 0
        freq = args.freq
        amp = args.amp
        width = args.width
        sync = args.sync
        comb = args.comb
        C2_ON = args.C2_ON
        #LongS2 = args.LongS2
        
        print("Frequency:", freq)
        print("Amplitude:", amp)
        print("Width:", width)
        print("Sync:", sync)
        print("CH1 Combine Mode:", comb)
        print("CH2 Open on:", C2_ON)
        #print("Long2S2 200us Configure:", LongS2)
        print("Arguments parsed successfully.")
        
        
        ip = "192.168.4.9"
        port = 5024

        #ip = "10.11.50.78"
        #port = 5025
        
        #config.configure_waveform_generator(ip, port, freq, amp, width, sync, comb=comb,C2_ON=C2_ON)
        #config.configure_waveform_generator(ip, port, freq, amp, width, sync, comb=comb,C2_ON=C2_ON,LongS2=LongS2)

        if comb == "True" and C2_ON == "True":
            config.configure_waveform_generator(ip, port, freq, amp, width, sync, True, True)
        elif comb == "False" and C2_ON == "False":
            config.configure_waveform_generator(ip, port, freq, amp, width, sync, False, False)
        elif comb == "True" and C2_ON == "False":
            config.configure_waveform_generator(ip, port, freq, amp, width, sync, True, False)
        elif comb == "False" and C2_ON == "True":
            config.configure_waveform_generator(ip, port, freq, amp, width, sync, False, True)

        config.pulse_generator_configure(ip, port)
        print("Pulse generator configured successfully.")
        
        sys.exit(0)

    except Exception as e:
        print("An error occurred while parsing arguments:", str(e))
        print("Usagee: python configuration.py --freq 50 --amp 1.4 --width 5 --sync CH1 --comb False --C2_ON False")        
        sys.exit(0)
        


if __name__ == "__main__":
    main()

    
