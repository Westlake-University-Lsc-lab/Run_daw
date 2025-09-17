# Run_daw

Run DAQ and config pulse generator by auto.

#### to install the package, run the following command in terminal:

```
git clone https://github.com/Westlake-University-Lsc-lab/Run_daw.git
git checkout your_branch_name
```

#### Conigure LED pulse generator

type the following command in terminal as the example:

```
python configuration.py --freq 50 --amp 1.4 --delay 5 --sync CH1 --comb False --C2_ON False --LongS2 False
Usagee: python configuration.py --freq 50 --amp 1.4 --delay 5 --sync CH1 --Comb False --C2_ON False --LongS2 False
```
This script is just transmit the specific parameter to Pulse Generator, the syntax is in 'ConfigPulseGen.py'.
You can change and edit depen on your own requirement.  
Parameter descriptions:  
'freq'  --- trigger frequency for both Ch1 and Ch2  
'amp'   --- amplitude for Ch1, offset will be one half of 'amp'  
'delay' --- time delay from Ch1 to Ch2 by unit of 'us'  
'sync'  --- synchroniziton trigger source channel, Ch1 or Ch2   
'Comb'  --- Whether Combine the voltage from the 2 channel to output Ch1 ?  
'C2_ON' --- Open Ch2 output or not ?  
'LongS2'--- If true, Ch1 pulse width fixed to '2 us', if not Ch1 width fixed to '150 ns'  


#### Write DAW configure file

```
python write_config.py ext 40 120 20 test_run
USAGE: python write_config.py ext 40 480 file_name
USAGE: python write_config.py trig_style[self] rec_len[int] acq_time[int] threshold[int] file_name[str]
```
This script is to generator config file before run DAW_Demo. The input file is 'DAW_Config.txt' by auto,  
and output file is 'configure_new.txt'.  
Parameter explaination:  
'trig_style' --- str type, [ext, self],trigger mode, following with 'self' will run self-trigger mode,
	     	 while following with 'ext' will be external-trigger  
'rec_len'    --- int type, min record length of a raw waveform, suggest '5' for 'self' trigger,
	     	 and '20' for 'ext' trigger, unit by 4 samples  
'acq_time'   --- int type, data acquirsition time length, unit by second  
'threshold'  --- int type,self-trigger threshold, only efficient under 'self' trigger mode  
'file_name'  --- str type, rawdata file tag  


#### Run DAQ

```
DAW_Demo  configure_new.txt
```
This should be under 'daq' account and run daq.
And you should press 's' on your keyboard to start data recording, press
'q' to quit DAQ process, it will be stop after 'ACQ_TIME' seconds.


#### Run DAQ and pulse generator by auto

This is just tricky script to auto config LED and then run DAQ, should be customized,  
the below is just example script to do this
```
python run_data.py
USAGE: python run_data.py runType[saturation/time_const] run_tag[str]
USAGE: python run_data.py saturation new_nody7
```

This is just a simple example, the LED pulse generator and DAQ configure file
can be modified according to your needs.

#### Close pusle generator

```
python close_pulse_gen.py
```
Make sure the LED is closed after data taking.
This option will turn off the output of Ch1 and Ch2.

#### Check DAQ status
```
./check_daq_status.sh DAW_Demo
./check_daq_status.sh DAW_multiboard
./check_daq_status.sh run_data.py
```
