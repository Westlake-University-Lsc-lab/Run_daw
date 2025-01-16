from wave_generater import WaveGenerator

# pulse_generator = 'USB0::0xF4EC::0x1101::SDG6XFCD7R0976::INSTR'
# pulse_generator = 'TCPIP0::192.168.4.9::INSTR'
# ip = "10.11.50.78"
# port = 5025


def configure_waveform_generator(
    ip: str,
    port: int,
    fre: int = 50,
    amp: float = 1.8,
    delay: int = 5,
    sync: str = "CH2",
    comb=True,
    C2_ON=True,
):
    afg = WaveGenerator(ip, port)
    if sync == "CH1":
        SYNC_CH = sync
        afg.send("C1:SYNC ON, TYPE,{}".format(SYNC_CH))

    elif sync == "CH2":
        SYNC_CH = sync
        afg.send("C2:SYNC ON, TYPE,{}".format(SYNC_CH))

    if C2_ON is True:
        amp_2 = 1.36
        ch2_on = "ON"
    elif C2_ON is False:
        amp_2 = 0
        ch2_on = "OFF"

    if comb is True:
        afg.send("C1:CoMBiNe ON")  # CH1组合输出配置为ON
    elif comb is False:
        afg.send("C1:CoMBiNe OFF")  # CH1组合输出配置为ON

    # 配置输出通道的命令
    commands = [
        "C1:OUTP ON",
        "C1:OUTP LOAD,50",
        "C1:OUTP PLRT,NOR",
        "C1:BSWV WVTP,PULSE",
        r"C2:OUTP {}".format(ch2_on),
        "C2:OUTP LOAD,50",
        "C2:OUTP PLRT,NOR",
        "C2:BSWV WVTP,PULSE",
        r"C1:BSWV FRQ,{}".format(fre),  # 频率配置为50 Hz
        r"C2:BSWV FRQ,{}".format(fre),  # 频率配置为50 Hz
        r"C2:BSWV AMP, {}".format(amp_2),  # 幅度配置为1.36 V
        r"C2:BSWV OFST, {}".format(amp_2 / 2),  # 偏移量配置为780 mV
        r"C1:BSWV AMP,{}".format(amp),  # 幅度配置为1.8V
        r"C1:BSWV OFST,{}".format(amp / 2.0),  # 偏移量配置为900 mV (即0.9 V)
        "C1:BSWV WIDTH,150.E-9",  # S1脉冲宽度固定为150纳秒 (ns)
        "C2:BSWV WIDTH,1000.E-9",  # S2脉冲宽度固定为1us
        "C1:BSWV RISE, 1.E-9",  # 上升时间固定为1纳秒 (ns)
        "C2:BSWV RISE, 1.E-9",  # 上升时间固定为1纳秒 (ns)
        "C1:BSWV FALL, 1.E-9",  # 下降时间固定为1纳秒 (ns)
        "C2:BSWV FALL, 1.E-9",  # 下降时间固定为1纳秒 (ns)
        "C1:BSWV DLY, 0",  # CH1没有延迟, 单位为微秒 (us)
        r"C2:BSWV DLY, {}.E-6".format(delay),  # CH2延迟时间配置, 单位为微秒 (us)
    ]

    # 执行配置命令
    for command in commands:
        afg.send(command)
    print("Finished configuring.")
    # 关闭资源（如果需要）
    afg.close()  # 如果不再需要保持连接可以注释掉或删除这行代码
    # return afg


def pulse_generator_configure(ip: str, port: int):
    afg = WaveGenerator(ip, port)
    config_info = [
        "*IDN?",
        "C1:SYNC?",
        "C2:SYNC?",
        "C1:CoMBiNe?",
        "C2:CoMBiNe?",
        "C1:OUTP?",
        "C2:OUTP?",
        "C1:BSWV?",
        "C2:BSWV?",
    ]
    for info in config_info:
        # print('----------\n')
        print(afg.query(info))
        # print(afg.query())
    afg.close()


def close_pulse_generator(ip: str, port: int):
    afg = WaveGenerator(ip, port)
    commands = [
        "C1:OUTP OFF",
        "C2:OUTP OFF",
        ]
    for command in commands:
        afg.send(command)

    print("Pulse Generator output CH1,CH2 are closed!")
    afg.close()
