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

def run_daw_demo(config_file="configure_new.txt"):
    # 启动 DAW_Demo 进程
    process = subprocess.Popen(
        ["DAW_Demo", config_file],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,  # 自动处理字符串
        bufsize=1
    )
    # 等待一小会儿，让程序跑到需要输入的地方
    time.sleep(2)

    # 自动输入 's'，并加上换行符模拟回车
    process.stdin.write("s\n")
    process.stdin.flush()
    # 如果你想持续查看输出，可以这样逐行读取
    try:
        for line in process.stdout:
            print(line, end="")  # 实时输出 DAW_Demo 的结果
    except KeyboardInterrupt:
        print("用户中断")
    # 等待进程结束
    process.wait()


def run_daq(config_pules_gen, write_config_file):
    conf_gen = run_command(config_pules_gen)
    print("Configuring pulse generator Done!")

    time.sleep(2)
    daw_config = run_command(write_config_file)
    print('DAW condiguration Done!')

    time.sleep(2)
    run_daq = run_daw_demo()
    # run_daq = ['DAQ_Demo' , './configure_new.txt']
    # run_daq = ['/home/daq/DAQ_DEMO/DAW_multiboard' , './configure_new.txt']
    run = run_command(run_daq)
    print('DAQ finished !')



def run_self_trig(write_config_file):
    daw_config = run_command(write_config_file)
    print('DAW configuration done')
        
    time.sleep(2)
    run_daq = run_daw_demo()
    # run_self_trig =['DAQ_Demo' , './configure_new.txt']
    # run_self_trig =['/home/daq/DAQ_DEMO/DAW_multiboard' , './configure_new.txt']
    print(run_self_trig)
    run = run_command(run_self_trig)
    time.sleep(2)
    print('DAQ finished')
