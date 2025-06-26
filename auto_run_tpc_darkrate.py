import GenConfigList as gen
import RunDAQ as run
import sys
import time

def run_config(daw_conf):
    run.run_self_trig(daw_conf)
    time.sleep(2)


def main():
    
    if len(sys.argv) != 3:        
        print("USAGE: python auto_run_darkrate.py runType[DarkRate] run_tag[str]")
        print("USAGE: python auto_run_darkrate.py DarkRate tpc_2pmt_DR_800V_20250626")
        sys.exit(1)

    runType = sys.argv[1]
    run_tag = sys.argv[2]

    envs = 'python'
    py_files_daw = 'write_config.py'
    
    #run_list = ['0','1','2'] #,3,4,5,6,7,8,9,10,11,12,13,14,14,16,17,18,19,20]
    run_list = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,14,16,17,18,19,20,21,22,23,24]
    if runType == 'DarkRate':

        trig_mode = 'self'
        rec_len = 5
        acq_time = 300
        trig_thr = 20


        out_filenames =[]
        for runs in run_list:
            filename = run_tag+'run'+'_'+str(runs)
            #print(filename)
            out_filenames.append(filename)

        print('---')
        print(out_filenames)
        
        daw_configs = gen.generate_daw_config(trig_mode=trig_mode, rec_len=rec_len, acq_time=acq_time, trig_thr=trig_thr, output_files=out_filenames)
        print('------------Daw Config params list----------------------')
        
        DAW_Conf = gen.generate_configure_list(env=envs, py_file=py_files_daw, led_configs=None, daw_configs=daw_configs)
        print(len(DAW_Conf))
        print('------------Daw Config list Done----------------------')
        print('------------Run DAQ-----------------')
        i =0
        for  conf in DAW_Conf:
            run_config(conf)
            if i < 12:
                time.sleep(600)
            elif i >= 12:
                time.sleep(1800)
            i +=1
        print('------------Finished Run-----------------')
        
            
    else:
        print('runType error')
        return


if __name__== "__main__":
    main()


