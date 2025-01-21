import GenConfigList as gen
import RunDAQ as run
import sys
import time

def run_config(led_conf_list, daw_conf_list):
    len_sau = len(led_conf_list)
    len_daw = len(daw_conf_list)
    if len_sau != len_daw:
        print('configuration error')
        return
    for i in range(len_sau):
        run.run_daq(led_conf_list[i], daw_conf_list[i])
        time.sleep(10)


def main():
    
    if len(sys.argv) != 3:        
        print("USAGE: python run_data.py runType[saturation/time_const/LongS2] run_tag[str]")
        print("USAGE: python run_data.py saturation new_nody7")
        sys.exit(1)

    runType = sys.argv[1]
    run_tag = sys.argv[2]

    saturation_voltages = [ 1.36, 1.38, 1.40, 1.42, 1.44, 1.46, 1.48, 1.50, 1.52 , 1.54, 1.56, 1.58, 1.60, 1.62, 1.64, 1.66, 1.68, 1.70, 1.72, 1.74]
    time_const_voltages = [ 1.50, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5]
    delta_times = [2, 5, 10, 20, 50, 100, 200, 500, 1000, 10000]
    long_s2_voltages = [1.40]
    
    envs = 'python'
    py_files_led = 'configuration.py'
    py_files_daw = 'write_config.py'


    if runType == 'saturation':
        voltages = saturation_voltages
        trig_rate = 1000
        synch_ch = 'CH1'
        delta_t = 5
        combine_opt = 'True'
        Ch2_opt = 'False'

        trig_mode = 'ext'
        rec_len = 40
        acq_time = 120
        trig_thr = 20

        ch0_atten = '9DB'
        ch1_atten = '0DB'
        
        ### generate led configuration list
        led_configs = gen.generate_led_configs(trig_rate, voltages, delta_t, synch_ch, combine_opt, Ch2_opt)
        print('------------LED config params list-------------------')
        out_filenames=[]
        for voltage in voltages:
            out_filename = gen.generate_saturation_output_filename(ch0_atten, ch1_atten, voltage, trig_rate, run_tag=run_tag, date=None)
            out_filenames.append(out_filename)
        daw_configs = gen.generate_daw_config(trig_mode=trig_mode, rec_len=rec_len, acq_time=acq_time, trig_thr=trig_thr, output_files=out_filenames)
        print('------------Daw config params list--------------------')
        LED_Conf = gen.generate_configure_list(env=envs, py_file=py_files_led, led_configs=led_configs, daw_configs=None)
        print('------------LED Config list Done----------------------')
        DAW_Conf = gen.generate_configure_list(env=envs, py_file=py_files_daw, led_configs=None, daw_configs=daw_configs)
        print('------------Daw Config list Done----------------------')
        
        print('------------Run DAQ-----------------')
        # run_config(LED_Conf, DAW_Conf)

    elif runType == 'time_const':
        voltages = time_const_voltages
        trig_rate = 50
        delta_time = delta_times
        synch_ch = 'CH2'
        combine_opt = 'True'
        Ch2_opt = 'True'

        trig_mode = 'ext'
        rec_len = 40
        acq_time = 480
        trig_thr = 20

        ch0_atten = '20DB'
        ch1_atten = '9DB'
        
        for delta_t in delta_time:
            led_configs = gen.generate_led_configs(trig_rate, voltages, delta_t, synch_ch, combine_opt, Ch2_opt)
            # print('------------LED config params list-------------------')
            out_filenames=[]
            for voltage in voltages:
                out_filename = gen.generate_time_constant_output_filename(ch0_atten, ch1_atten, voltage, delta_t, trig_rate, run_tag=run_tag, date=None)
                out_filenames.append(out_filename)
                # print('------------Output filename----------------------')                
            daw_configs = gen.generate_daw_config(trig_mode=trig_mode, rec_len=rec_len, acq_time=acq_time, trig_thr=trig_thr, output_files=out_filenames)
            # print('------------Daw config params list--------------------')
            LED_Conf = gen.generate_configure_list(env=envs, py_file=py_files_led, led_configs=led_configs, daw_configs=None)
            print('------------LED Config list Done----------------------')
            DAW_Conf = gen.generate_configure_list(env=envs, py_file=py_files_daw, led_configs=None, daw_configs=daw_configs)
            print('------------Daw Config list Done----------------------')
            
            print('------------Run DAQ-----------------')
            # run_config(LED_Conf, DAW_Conf)

    elif runType == 'LongS2':
        voltages = long_s2_voltages
        trig_rate = 10
        delta_t = 5
        synch_ch = 'CH1'
        combine_opt = False
        Ch2_opt = False
        LongS2 = True
        
        led_configs = gen.generate_led_configs(trig_rate, voltages, delta_t, synch_ch, combine_opt, Ch2_opt, LongS2)
        print('------------LED config params list-------------------')
        
        ###---------------------------------------------------------------------------
        trig_mode = 'ext'
        rec_len = 5125
        acq_time = 600
        trig_thr = 20
        
        ch0_atten = '0DB'
        ch1_atten = '0DB'
        
        out_filenames=[]
        for voltage in voltages:
            out_filename = gen.generate_long_s2_output_filename(ch0_atten, ch1_atten, voltage, trig_rate, run_tag=run_tag, date=None)
            out_filenames.append(out_filename)
        daw_configs = gen.generate_daw_config(trig_mode=trig_mode, rec_len=rec_len, acq_time=acq_time, trig_thr=trig_thr, output_files=out_filenames)
        print('------------Daw config params list--------------------')
        LED_Conf = gen.generate_configure_list(env=envs, py_file=py_files_led, led_configs=led_configs, daw_configs=None)
        print('------------LED Config list Done----------------------')
        DAW_Conf = gen.generate_configure_list(env=envs, py_file=py_files_daw, led_configs=None, daw_configs=daw_configs)
        print('------------Daw Config list Done----------------------')
        
        print('------------Run DAQ-----------------')
        # run_config(LED_Conf, DAW_Conf)
        
    else:
        print('runType error')
        return


    '''
    len_sau = len(sauration_run_list)
    len_daw = len(DAW_config_list)
    if len_sau != len_daw:
        print('configuration error')
        return
    for i in range(len_sau):
        run.run_daq(sauration_run_list[i], DAW_config_list[i])
        time.sleep(10)
   '''


if __name__== "__main__":
    main()


