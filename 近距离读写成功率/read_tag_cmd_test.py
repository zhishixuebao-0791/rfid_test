import time
import serial
import serial.tools.list_ports
import binascii
import threading
import os
path_txt = "60X"                                #创建文件夹
serial_port = 'com3'                            #send_cmd的串口号
#
each_bank_read_whell = 10                     #每个区域要读多少轮
each_timeout = 5                              #每轮的超时时间s
def make_file_return_path(path_txt:str):
    if not os.path.exists(path_txt):
        os.makedirs(path_txt)
        print(path_txt+"文件夹创建成功!")
    else:
        print(path_txt+"文件夹已存在!")
    return path_txt+('\\read_success_rate_' + time.strftime('%Y%m%d%H%M') + '.txt')

set_freq = "A006017801073B9E"
set_addr ="A004007300E9"#设置读写器地址为0x00
realtime_inventory = "A004008901D2"
stop_inventory = "A003018CD0"
 
rf_link_table = {   
                    'FM0_200KHz_6_25'      :"D122",
                    'FM0_40KHz_25'         :"D91A",
                    'Miller_4_200KHz_25'   :"D61D",
                    'Miller_4_250KHz_25'   :"D71C"
                    # 'GB_FM0_64KHz_6_25'    :"DA19",
                    # 'GB_FM0_128KHz_6_25'   :"DB18",
                    # 'GB_FM0_64KHz_12_5'    :"DC17",
                    # 'GB_Miller_128KHz_12_5':"DD16" 
                }
#每个区域每次读2byte的数据,读写其地址为0x00        
mem_bank_table = {
                    'READ_BANK_00':'A00E00810000000000000200000000CF',#密码区
                    'READ_BANK_01':'A00E00810100000002000200000000CC',#EPC区
                    'READ_BANK_10':'A00E00810200000000000200000000CD',#TID区
                    'READ_BANK_11':'A00E00810300000000000200000000CC' #USER区
                }

def set_freq_std_902_928():
    print("set std freq 902-928")
    data = set_freq
    hex_data = bytes.fromhex(data)
    return hex_data

def set_rfid_addr():
    print("set_rfid_addr_0x00")
    data = set_addr
    hex_data = bytes.fromhex(data)
    return hex_data

def send_reader_real_time_inventory():
    print("real time inventory")
    data = realtime_inventory
    hex_data = bytes.fromhex(data)
    return hex_data

def send_reader_stop_inventory():
    print("stop inventory")
    data = stop_inventory
    hex_data = bytes.fromhex(data)
    return hex_data

def send_set_rf_link(mode):
    print("set rf_link")
    data = "A0040069"+mode
    hex_data = bytes.fromhex(data)
    return hex_data

def send_read_tag(mode):
    print('read tag')
    hex_data = bytes.fromhex(mode)
    return hex_data


class SerThread():
    def __init__(self, portx):
        # 初始化串口
        self.my_serial = serial.Serial()
        self.my_serial.port = portx
        self.my_serial.baudrate = 115200
        self.my_serial.timeout = 1
        self.waitEnd = None   # 设置线程事件变量
        self.alive = False    # 设置条件变量
        self.errorcode = 0
        self.rf_link = ""
        self.mem_bank = ""
        self.read_success_num = 0

    def start(self):
        # 打开串口并创建blog文件
        # self.my_serial.open()   # 打开串口
        if self.my_serial.is_open:
            self.waitEnd = threading.Event()  # 将线程事件赋值给变量
            self.alive = True # 改变条件变量值
            self.thread_read = threading.Thread(target=self.Reader)  # 创建一个读取串口数据的线程
            self.thread_read.daemon = True  # 调用线程同时结束的函数
            self.thread_read.start()    # 启动读数据线程
            return True     # 如果串口打开了，就返回True
        else:
            return False    #如果串口未打开，就返回False


    def Reader(self):
        exit_flag = False
        begintime = time.time()#获取时间戳
        while self.alive:   # 当条件变量为True时执行
            finishtime = time.time()#获取时间戳
            running_time = finishtime - begintime
            if(running_time >= each_timeout):
                print('running_time = ', running_time)
                print("no epc")
                break
            try:
                t1 = time.time()
                while (not self.my_serial.in_waiting):
                    t2 = time.time()
                    if (t2 - t1 > 2):
                        print("Overtime_Error!")
                        exit_flag = True
                        break
                time.sleep(0.5)
                data_buf = self.my_serial.read(self.my_serial.in_waiting)#40
                print("Reception_Data:",data_buf.hex().upper())
                time.sleep(0.5)
                index = 0
                switch_index = "PACKAGE_HEAD"
                packet_len = 0
                while index < len(data_buf):
                    if switch_index == "PACKAGE_HEAD":
                        if data_buf[index] == 0xa0:                     # head
                            switch_index = "PACKAGE_LEN"
                    elif switch_index == "PACKAGE_LEN":                 # packet length
                        packet_len = data_buf[index]
                        switch_index = "PACKAGE_ADDR"
                    elif switch_index == "PACKAGE_ADDR":                 # address
                        switch_index = "PACKAGE_CMD"
                    elif switch_index == "PACKAGE_CMD":                 # cmd
                        if data_buf[index] == 0x81:
                            if packet_len > 4:
                                #print(data_buf.hex().upper())
                                self.read_success_num += 1
                                switch_index = "PACKAGE_HEAD"
                                exit_flag = True
                                break
                        switch_index = "PACKAGE_HEAD"
                    else:
                        switch_index = "PACKAGE_HEAD"
                    index += 1
                if exit_flag:
                    break
            except Exception as ex:
                print(ex)

        self.waitEnd.set()  # 改变线程事件状态为True，即唤醒后面的程序
        self.alive = False    # 改变条件量为False

    def waiting(self):
        # 等待event停止标志
        if not self.waitEnd is None:
            self.waitEnd.wait()     # 改变线程事件状态为False，使线程阻止后续程序执行

    # 关闭串口、保存文件
    def stop(self):
        self.alive = False
        if self.my_serial.is_open:
            self.my_serial.close()
    
    def realtime_inventory(self):
        self.my_serial.write(send_reader_real_time_inventory())

    def stop_invnetory(self):
        self.my_serial.write(send_reader_stop_inventory())
        time.sleep(5)

    def set_rfid_addr_0x00(self):
       self.my_serial.write(set_rfid_addr())
       time.sleep(1)

    def set_rf_link(self):
        self.my_serial.write(send_set_rf_link(self.rf_link))
        time.sleep(3)

    def read_tad(self):
        self.my_serial.write(send_read_tag(self.mem_bank))

    def send_config_cmd_and_receive_verify(self,send_config_cmd_function,send_config_cmd_back:str):
       self.my_serial.reset_input_buffer()#清理接收缓冲区
       send_config_cmd_function()
       t1 = time.time()
       while (not self.my_serial.in_waiting):
           t2 = time.time()
           if (t2 - t1 > 2):
               print("Overtime_Error!")
               exit(1)
       time.sleep(0.1)
       if (self.my_serial.read(self.my_serial.in_waiting).hex().find(send_config_cmd_back) == -1):
           print("send config cmd error")
           exit(1)
       else:
           print("send config cmd ok!")
       time.sleep(1)

if __name__ == '__main__':

    com = ''
    inputsdirpath = os.path.join(os.curdir, 'Inputs')
    haveinputsdir = os.path.exists(inputsdirpath)
    if haveinputsdir:
        inputspath = os.path.join(inputsdirpath + '\com_input.txt')
        if os.path.exists(inputspath):
            com = open(inputspath, 'r').read().strip()
        else:
            com = serial_port
    else:
        com = serial_port
        
    print('use:' + com)
    ser = SerThread(com)
    errorcode = 0
    try:
        ser.my_serial.open()  # 打开串口
        read_rate_file = open(make_file_return_path(path_txt), 'w')
        send_config_cmd_back_1 = "a004007310d9"
        ser.send_config_cmd_and_receive_verify(ser.set_rfid_addr_0x00,send_config_cmd_back_1)#配置读写器地址为0x00
        for key_link, value_link in rf_link_table.items():
            ser.my_serial.reset_input_buffer()
            print("rf_link = ", key_link)
            ser.rf_link = value_link
            send_config_cmd_back_2 = "a004006910e3"
            ser.send_config_cmd_and_receive_verify(ser.set_rf_link,send_config_cmd_back_2)#设置链路模式
            for key_bank, value_bank in mem_bank_table.items():
                print(key_bank)
                ser.read_success_num = 0
                for num in range(each_bank_read_whell):
                    print('round : ', num)
                    ser.mem_bank = value_bank
                    print("send_cmd:",ser.mem_bank)
                    ser.my_serial.reset_input_buffer()#清理接收缓冲区
                    ser.read_tad()#发读指令
                    if(not ser.start()):#子线程解析计数#解析
                        exit(1)
                    ser.waiting()
                success_rate = (ser.read_success_num / each_bank_read_whell)*100#成功率
                print('read rate = {}%'.format(success_rate))
                read_rate_file.writelines("[" + key_bank + "], " + "[" + key_link + "], " + "[read rate = " + str(success_rate) + "%] \n")
        read_rate_file.close()

    except Exception as ex:
        print(ex)
    if ser.alive:
        ser.stop()
    del ser
    # ex = input('输入任意退出')

    if errorcode == 0:
        print('End OK.')
        exit(0)
    elif errorcode == 1:
        print('End error.')
        exit(1)