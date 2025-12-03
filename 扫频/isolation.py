import serial
import serial.tools.list_ports
import time
import os
from device import read_file
#606L没有
path_txt = "606_test"
suffix = '_1_' #后缀
#from device import read_file
cmd_serial_port = 'com8'                        # 连软件串口
log_serial_port = 'com9'                       # 打印log串口
freq_start_num = 900000                         # 起始频率（KHz）
freq_end_num = 930001                           # 终止频率（KHz）
freq_step_num = 5000                            # 频点间隔（KHz）
set_addr ="A004007300E9"#设置读写器地址为0x00
cmd_serial_command = [[0xa0, 0x03, 0x00, 0x70, 0xed],                       # 复位
                      [0xa0, 0x05, 0x00, 0xd2, 0x00, 0x01, 0x88],           # 扫隔离度(608ltx2)
                      [0xa0, 0x0a, 0x00, 0x78, 0x04, 0x00, 0x19, 0x01]]     # 设置频点
#path_tim = path_txt+"_"+time.strftime('%Y%m%d%H%M')
def make_file_return_path(freq):
    if not os.path.exists(path_txt):
        os.makedirs(path_txt)
        print(path_txt+"文件夹创建成功!")
    else:
        print(path_txt+"文件夹已存在!")
    return path_txt+('\\'+path_txt+suffix + str(freq) + 'khz''.txt')
class SerIsolation():
    def __init__(self, cmd_port, log_port):
        self.cmd_serial = serial.Serial()
        self.cmd_serial.port = cmd_port
        self.cmd_serial.baudrate = 115200
        self.cmd_serial.timeout = 1000
        self.log_serial = serial.Serial()
        self.log_serial.port = log_port
        self.log_serial.baudrate = 115200
        self.log_serial.timeout = 1000
    # 计算CRC
    def get_crc_sum(self, buf):
        buf_len = len(buf)
        crc_sum = 0
        for i in range(buf_len):
            crc_sum += buf[i]
        crc_sum = (~crc_sum) + 1
        crc_sum = crc_sum % 256
        return crc_sum

    def cmd_serial_send_data(self, send_buf: list):
        if self.cmd_serial.is_open:
            self.cmd_serial.write(send_buf)
        else:
            print("cmd串口断连1")

    def cmd_serial_send(self, send_head: list, send_data: list):
        send_buf = send_head + send_data
        send_buf += [self.get_crc_sum(send_buf)]
        if self.cmd_serial.is_open:
            self.cmd_serial.write(send_buf)
        else:
            print("cmd串口断连2")
    def log_serial_recv(self, freq):
        count = 0
        log_file = open(make_file_return_path(freq), 'w')
        if self.log_serial.closed:
            print('log串口出错')
            return False
        while count < 5:
            time.sleep(0.1)
            count += 1
            try:
                data_len = self.log_serial.in_waiting
                if data_len > 3:
                    data_buf = self.log_serial.read(data_len).decode('gbk').replace('\r', '')
                    #print(data_buf, file=log_file, end='')
                    log_file.write(data_buf)
                    count = 0
            except:
                print('log串口出错')
                return False
        log_file.close()
        return True
    def set_rfid_addr_0x00(self):
        print("set_rfid_addr_0x00")
        data = set_addr
        hex_data = bytes.fromhex(data)
        self.cmd_serial.write(hex_data)
        time.sleep(1)

    def send_config_cmd_and_receive_verify(self,send_config_cmd_function,send_config_cmd_back:str):
       self.cmd_serial.reset_input_buffer()#清理接收缓冲区
       send_config_cmd_function()
       rece_len = self.cmd_serial.in_waiting
       t1 = time.time()
       while (not self.cmd_serial.in_waiting):
           t2 = time.time()
           if (t2 - t1 > 5):
               print("Overtime_Error!")
               exit(1)
       time.sleep(0.1)
       if (self.cmd_serial.read(rece_len).hex().find(send_config_cmd_back) == -1):
           print("send config cmd error")
           exit(1)
       else:
           print("send config cmd ok!")
       time.sleep(1)

if __name__ == '__main__':
    print("begin test")
    freq_step_list = list(range(freq_start_num, freq_end_num, freq_step_num))
    print(freq_step_list)
    myser = SerIsolation(cmd_serial_port, log_serial_port)
    try:
        myser.cmd_serial.open()
    except:
        print("命令串口打开失败")
        exit(1)
    send_config_cmd_back = "a004007310d9"
    myser.send_config_cmd_and_receive_verify(myser.set_rfid_addr_0x00,send_config_cmd_back)#配置读写器地址为0x00
    for freq_num in freq_step_list:
        print('测试频率：' + str(freq_num) + 'KHz')
        data = [int(freq_num / 256 / 256), int(freq_num / 256 % 256), int(freq_num % 256)]
        print('板子复位')
        myser.cmd_serial_send_data(cmd_serial_command[0])                                       # 复位板子
        time.sleep(2)
        print('设置输出频率')
        myser.cmd_serial_send(cmd_serial_command[2], data)                                      # 设置输出频率
        time.sleep(1)
        try:
            print('打开log串口')
            myser.log_serial.open()
        except:
            print('打开log串口失败')
            break
        print('扫隔离度')
        myser.cmd_serial_send_data(cmd_serial_command[1])                                       # 扫隔离度
        try:
            print('log串口接收数据')
            myser.log_serial_recv(freq_num)
            myser.log_serial.close()
            time.sleep(1)
        except:
            print('打开log串口失败')
            break
        print('关闭log串口')
    read_file(path_txt)
    try:
        myser.log_serial.close()
    except:
        pass
    myser.cmd_serial.close()
