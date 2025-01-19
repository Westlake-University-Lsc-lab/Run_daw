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
python configuration.py 50 1.8 5 CH2 True True
Usage: python configuration.py  fre=50 amp=1.8 delay=5 sync=CH2 comb=True C2_ON=True
```

#### Write DAW configure file

```
python write_config.py ext 40 120 20 test_run
USAGE: python write_config.py ext 40 480 file_name
USAGE: python write_config.py trig_style[self] rec_len[int] acq_time[int] threshold[int] file_name[str]
```

#### Run DAQ and pulse generator by auto

```
python run_data.py
USAGE: python run_data.py runType[saturation/time_const] run_tag[str]
USAGE: python run_data.py saturation new_nody7
```

This is just a simple example, the LED pulse generator and DAQ configure file can be modified according to your needs.

#### Close pusle generator

```
python close_pulse_gen.py
```

#### Check DAQ status

```
./check_daq_status.sh DAW_Demo
./check_daq_status.sh DAW_multiboard
./check_daq_status.sh run_data.py
```
