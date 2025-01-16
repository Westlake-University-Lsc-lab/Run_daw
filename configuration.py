import sys

import ConfigPulseGen as config

argvs = sys.argv

if len(argvs) != 7:
    print(
        "Usage: python configuration.py  fre=50 amp=1.8 delay=5 sync=CH2 comb=True C2_ON=True"
    )
    sys.exit()

fre = int(sys.argv[1])
amp = float(sys.argv[2])
delay = int(sys.argv[3])
sync = str(sys.argv[4])
comb = sys.argv[5]
C2_ON = sys.argv[6]
ip = "10.11.50.78"
port = 5025

if comb == "True" and C2_ON == "True":
    config.configure_waveform_generator(ip, port, fre, amp, delay, sync, True, True)
elif comb == "False" and C2_ON == "False":
    config.configure_waveform_generator(ip, port, fre, amp, delay, sync, False, False)
elif comb == "True" and C2_ON == "False":
    config.configure_waveform_generator(ip, port, fre, amp, delay, sync, True, False)
elif comb == "False" and C2_ON == "True":
    config.configure_waveform_generator(ip, port, fre, amp, delay, sync, False, True)

config.pulse_generator_configure(ip, port)

sys.exit(0)
