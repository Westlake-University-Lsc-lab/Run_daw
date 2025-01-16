import time
import subprocess


def run_command(cmd):
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        if res.returncode !=0:
            print(f"System command execution exits unexpectedly: {res.returncode}")
            raise Exception(f"System command execution exits unexpectedly")
    except subprocess.CalledProcessError as e:
        print(f"subprocess error exit:{e}")
    except Exception as e:
        print(f"There is a error:{e}")

def run_daq(config_pules_gen, write_config_file):
    conf_gen = run_command(config_pules_gen)
    print("Configuring pulse generator Done!")

    time.sleep(2)
    daw_config = run_command(write_config_file)
    print('DAW condiguration Done!')

    time.sleep(2)
    run_daq = ['/home/daq/DAQ_DEMO/DAW_multiboard' , './configure_new.txt']
    run = run_command(run_daq)
    print('DAQ finished !')


def run_config(led_conf_list, daw_conf_list):
    len_sau = len(led_conf_list)
    len_daw = len(daw_conf_list)
    if len_sau != len_daw:
        print('configuration error')
        return
    for i in range(len_sau):
        run.run_daq(sauration_run_list[i], DAW_config_list[i])
        time.sleep(10)

