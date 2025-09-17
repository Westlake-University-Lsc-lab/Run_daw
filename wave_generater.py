#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import struct
import sys
import time


class WaveGenerator:
    def __init__(self, remote_ip: str, port: int):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            print('Failed to creat socket.')
            sys.exit()
        try:
            self.sock.connect((remote_ip, port))
        except socket.error:
            print('Failed to connect to ip' + remote_ip)
        #return self.sock

    def __del__(self):
        self.close()

    def query(self, cmd: str, bufsize: int = 4096):
        cmd = cmd + "\n"
        try:
            self.sock.sendall(cmd.encode("latin1"))
            time.sleep(1)
        except socket.error:
            print('Send cmd faild')
            sys.exit()
        reply = self.sock.recv(bufsize)
        return reply

    def send(self, cmd: str, timewait: int = 1):
        cmd = cmd + "\n"
        self.sock.sendall(cmd.encode("latin1"))
        time.sleep(timewait)

    def value_to_str(self, value_data: list):
        data_bytes = bytearray()
        for point in value_data:
            # convert to short value(2 bytes) with little-endian format
            temp = struct.pack("<h", point)
            data_bytes.extend(temp)

        data_str = data_bytes.decode("latin1")
        return data_str

    def voltage_to_value(
        self, voltage_data: list, value_bound: tuple = (-32768, 32767)
    ):
        max_voltage = max(voltage_data)
        min_voltage = min(voltage_data)
        value_data = []
        for voltage in voltage_data:
            value_data.append(
                int(
                    (voltage - min_voltage)
                    * ((value_bound[1] - value_bound[0]) / (max_voltage - min_voltage))
                )
                + value_bound[0]
            )
        ampl = max_voltage - min_voltage
        ofst = (max_voltage + min_voltage) / 2
        return value_data, ampl, ofst

    def send_wave(
        self,
        channel: str,
        wvnm: str,
        voltage_data: list,
        timestep: float = 4e-9,
        phase: float = 0.0,
    ):
        freq = 1 / timestep
        value_data, ampl, ofst = self.voltage_to_value(voltage_data)
        data_str = self.value_to_str(value_data)
        self.send(
            f"{channel}:WVDT WVNM,{wvnm},FREQ,{freq},AMPL,{ampl},OFST,{ofst},PHASE,{phase},WAVEDATA,{data_str}"
        )

    def set_wave_name(self, channel: str, wvnm: str):
        self.send(f"{channel}:ARWV NAME,{wvnm}")

    def set_wave(
        self,
        channel: str,
        wvnm: str,
        voltage_data: list,
        timestep: float = 4e-9,
        phase: float = 0.0,
    ):
        self.send_wave(channel, wvnm, voltage_data, timestep, phase)
        self.set_wave_name(channel, wvnm)

    def set_channel_on(self, channel: str, state: bool):
        if state:
            self.send(f"{channel}:OUTP ON")
        else:
            self.send(f"{channel}:OUTP OFF")

    def det_channel_load(self, channel: str, load: str):
        self.send(f"{channel}::OUTP LOAD,{load}")

    def close(self):
        self.sock.close()


def main(remote_ip: str, port: int, cmd: str):
    device = WaveGenerator(remote_ip, port)
    if cmd[-1] == "?":
        reply = device.query(cmd)
        return reply.decode("latin1").rstrip()
    else:
        device.send(cmd)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("USAGE: python3 wave_generater.py remote_ip[str] port[int] command[str]")
        sys.exit(1)
    remote_ip = sys.argv[1]
    port = int(sys.argv[2])
    cmd = sys.argv[3]
    reply = main(remote_ip, port, cmd)
    if reply is not None:
        print(reply)
