
from typing import Union
from datetime import datetime

# envs = 'python'
# py_files_led = 'configuration.py'
# py_files_daw = 'write_config.py'


def generate_configure_list(env, py_file, led_configs=None, daw_configs=None):
    
    Conf_List = []
    if led_configs is not None:
        for led_config in led_configs:
            config_row = [
                str(env),
                str(py_file),
                str(led_config.get('trig_rate')),  # trigger rate as int
                str(led_config.get('voltage')),        # voltage as float
                str(led_config.get('delta_time')),     # delta time as int
                led_config.get('synch_ch', 'CH1'),  # default CH1 for Synchronize Channel
                str(led_config.get('combine_mode', 'False')),  # Convert to lower case string
                str(led_config.get('Ch2_option', 'False')),  # Convert to lower case string for consistency
                str(led_config.get('LongS2_option', 'False')),  # Convert to lower case string for consistency
            ]
            Conf_List.append(config_row)
                
    if daw_configs is not None:
        for daw_config in daw_configs:
            config_row = [
                str(env),
                str(py_file),
                daw_config.get('trig_mode','ext'),  # default to ext for trigger mode
                str(daw_config.get('rec_len')),  # record length as int
                str(daw_config.get('ACQ_TIME')),  # ACQ_TIME as int
                str(daw_config.get('trig_thr')),  # trigger threshold as int
                str(daw_config.get('output_file')),  # output file as str
            ]
            Conf_List.append(config_row)
    print(Conf_List)
    return Conf_List

def generate_led_configs(
        trig_rate: Union[int, None] = None,
        voltages: str='voltages',
        delta_time: Union[int, None] = None,
        synch_ch: str='CH1',
        combine_mode: str='True',
        Ch2_option: str='False',
        LongS2_option: str='False',
):
    """
    generator LED config list
        
    parameters:
    trig_rate (int): external trigger rate --> 1000 or 50 Hz, 1000 Hz for saturation test, 50 Hz for time constant test;
    voltages (str): should be vector or list of float type, it config the amplitude of CH1, amplitude of CH2 should be fixed to 1.36V;
    delta_time (int): time interval between Ch1 and Ch2, should be int type, unit is microsecond, Only valid on time_const run mode;
    synch_ch (str): selection the external trigger signal synchronizes channel, --> 'CH1' or 'CH2';
    combine_mode (str): --> 'True' or 'False', 'True' represents CH1 output under combine mode, means the voltage output from CH1 combined 
    the configuration both from CH1 and CH2;
    Ch2_option (str): ---> 'True' or 'False', 'True' represents CH2 'ON', and Configuration on CH2 will be executing whatever the Configuration it is on CH2;    
    """
    led_configs = []
    for voltage in voltages:
        config = {
            'trig_rate': trig_rate,
            'voltage':voltage,
            'delta_time':delta_time,
            'synch_ch': synch_ch,
            'combine_mode': combine_mode,
            'Ch2_option':Ch2_option,
            'LongS2_option':LongS2_option
        }
        led_configs.append(config)
    print(led_configs)
    return led_configs


def generate_daw_config(
        trig_mode: str='ext',
        rec_len: Union[int, None] = None,
        acq_time: Union[int, None] = None, 
        trig_thr: Union[int, None] = None,
        output_files: str='output_files'
):
    """
    generator daw config parameters

    parameters:
    trig_mode (str): trigger mode, str type, value can be --> 'ext' or 'self';
    rec_len (int): record length, must be int, 40 unit means 400 samples, 175 unit means 5 us length;
    acq_time (int): acqurisionn time length, must be int, if the value is 120, daq will run 2 minutes, 480 daq run 8 minutes;
    trig_thr (int): self trigger threshold, 20 adc unsually, the configuration executing only under 'self' trig_mode;
    output_file (str): output binary file name, the records the led config, and run condition infors ...etc.
    """
    daw_configs = []
    for output_file in output_files:
        daw_config = { 
            'trig_mode': trig_mode,
            'rec_len': rec_len,
            'ACQ_TIME': acq_time,
            'trig_thr': trig_thr,
            'output_file': output_file
        }
        daw_configs.append(daw_config)
    print(daw_configs)
    return daw_configs

def generate_saturation_output_filename(
        ch0_attenuation_factor: str='9DB',
        ch1_attenuation_factor: str='0DB', 
        voltages: float=1.36,
        trig: int=1000,
        run_tag: str='test',
        date: str='20150116',        
):
    if trig == 1000:
        trig_rate = '1kHz'
    elif trig == 50:
        trig_rate = '50Hz'
    elif trig == 10:
        trig_rate = '10Hz'
    else:
        trig_rate = 'unknown'
        
    voltage = str(voltages).replace('.','p')
    
    if date is None:
        now = datetime.now()
        date = now.strftime('%Y%m%d')
        
    """
    generate output filename
    
    Parameters:
    ch0_attenuation_fact (str): --> '20DB', '9DB'
    ch1_attenuation_fact (str): --> '9DB', '0DB'
    voltages (str): should be vector or list of float type, it config the amplitude of CH1, amplitude of CH2 should be fixed to 1.36V;
    trig (int):  --> 1000, or 50, 
    run_tage (str): --> some str to tag this run;
    date (int): --> date of the date taking,  [20250116] for example;
    """
    output_name = f'lv2414_{ch0_attenuation_factor}_lv2415_{ch1_attenuation_factor}_combine_{date}_{voltage}v_calibration_{trig_rate}_{run_tag}_run0'
    print(output_name)
    return output_name
        

def generate_time_constant_output_filename(
        ch0_attenuation_factor: str='20DB',
        ch1_attenuation_factor: str='9DB', 
        voltages: float=1.36,
        delta_time: int=100,
        trig: int=50,
        run_tag: str='test',
        date: str='20150116',        
):
    if trig == 1000:
        trig_rate = '1kHz'
    elif trig == 50:
        trig_rate = '50Hz'
        
    voltage = str(voltages).replace('.','p')
    
    if date is None:
        now = datetime.now()
        date = now.strftime('%Y%m%d')
    offset = str(voltages/2.).replace('.','p')
    Ch2_voltage = str(1.36).replace('.','p')
    offset_ch2 = str(1.36/2.).replace('.','p')
    """
    generate output filename
    
    Parameters:
    ch0_attenuation_fact (str): --> '20DB', '9DB'
    ch1_attenuation_fact (str): --> '9DB', '0DB'
    voltages (str): should be vector or list of float type, it config the amplitude of CH1, amplitude of CH2 should be fixed to 1.36V;
    delta_time (int): time interval between Ch1 and Ch2, should be int type, unit is microsecond, Only valid on time_const run mode;
    trig (int):  --> 1000, or 50, 
    run_tage (str): --> some str to tag this run;
    date (int): --> date of the date taking,  [20250116] for example;
    """
    output_name = f'lv2414_{ch0_attenuation_factor}_lv2415_{ch1_attenuation_factor}_combine_{date}_{voltage}v_{offset}v_{Ch2_voltage}v_{offset_ch2}v_{delta_time}us_{trig_rate}_{run_tag}_run0'
    print(output_name)
    return output_name


def generate_long_s2_output_filename(
        ch0_attenuation_factor: str='DB',
        ch1_attenuation_factor: str='DB', 
        voltages: float=1.40,
        trig: int=10,
        run_tag: str='long_s2',
        date: str='20150116',        
):
    if trig == 1000:
        trig_rate = '1kHz'
    elif trig == 50:
        trig_rate = '50Hz'
    elif trig == 10:
        trig_rate = '10Hz'
    else:
        trig_rate = 'unknown'
        
    voltage = str(voltages).replace('.','p')
    
    if date is None:
        now = datetime.now()
        date = now.strftime('%Y%m%d')
        
    """
    generate output filename
    
    Parameters:
    ch0_attenuation_fact (str): --> '20DB', '9DB'
    ch1_attenuation_fact (str): --> '9DB', '0DB'
    voltages (str): should be vector or list of float type, it config the amplitude of CH1, amplitude of CH2 should be fixed to 1.36V;
    trig (int):  --> 1000, or 50, 
    run_tage (str): --> some str to tag this run;
    date (int): --> date of the date taking,  [20250116] for example;
    """
    output_name = f'lv2414_{ch0_attenuation_factor}_lv2415_{ch1_attenuation_factor}_combine_{date}_{voltage}v_calibration_{trig_rate}_{run_tag}_run0'
    print(output_name)
    return output_name
        
        