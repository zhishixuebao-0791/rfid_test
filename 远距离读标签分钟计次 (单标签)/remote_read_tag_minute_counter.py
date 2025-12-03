import time
import serial
import serial.tools.list_ports
import binascii
import threading
import os
from collections import deque
from draw_statistical_graphs import Draw_Histogram
from Var_And_SD import Var_And_SD
#参数设置
path_txt = "60X"                               #创建文件夹
serial_port = 'com3'                          #串口号
run_ring = 5                                   #运行几轮
each_run_time = 5                              #每轮运行多久单位s
each_ring_tim_interval = 5                     #每轮之间的时间间隔单位s
#指令
set_addr ="A004007300E9"#设置读写器地址为0x00
realtime_inventory = "A004008901D2"#盘存指令
stop_inventory = "A003008CD1"#停止盘存

rf_link_table = {   
                    # 'FM0_200KHz_6_25'      :"D122",
                    # 'FM0_40KHz_25'         :"D91A",
                    'Miller_4_200KHz_25'   :"D61D",
                    'Miller_4_250KHz_25'   :"D71C"
                    # 'GB_FM0_64KHz_6_25'    :"DA19",
                    # 'GB_FM0_128KHz_6_25'   :"DB18",
                    # 'GB_FM0_64KHz_12_5'    :"DC17",
                    # 'GB_Miller_128KHz_12_5':"DD16" 
                }            
#环形缓冲区
class CircularBuffer:
    def __init__(self, size):
        self.buffer = deque(maxlen=size)

    def is_empty(self):
        return len(self.buffer) == 0
    
    def is_full(self):
        return len(self.buffer) == self.buffer.maxlen
    
    def enqueue(self, item):
        if self.is_full():
            self.buffer.popleft()
        self.buffer.append(item)

    def dequeue(self):
        if self.is_empty():
            raise Exception("Circular buffer is empty")
        return self.buffer.popleft()
class ucm60x_ucm_pro_t:
    def __init__(self):
        self.head = ""
        self.len  = ""
        self.addr = ""
        self.cmd  = ""
        self.data = []
        self.crc  = ""

def make_file_return_path(path_txt,fname):
    if not os.path.exists(path_txt):
        os.makedirs(path_txt)
        print(path_txt+"文件夹创建成功!")
    else:
        print(path_txt+"文件夹已存在!")
    return path_txt+('\\remote_read_counter_' + fname + '.txt')

def set_rfid_addr():
    print("set_rfid_addr_0x00")
    data = set_addr
    hex_data = bytes.fromhex(data)
    return hex_data

def send_reader_real_time_inventory():#盘存
    print("real time inventory")
    data = realtime_inventory
    hex_data = bytes.fromhex(data)
    return hex_data

def send_reader_stop_inventory():#停止盘存
    print("stop inventory")
    data = stop_inventory
    hex_data = bytes.fromhex(data)
    return hex_data

def send_set_rf_link(mode):#设置射频链路的通迅速率
    print("set rf_link")
    data = "A0040069"+mode
    hex_data = bytes.fromhex(data)
    return hex_data

def send_read_tag(mode):
    print('read tag')
    hex_data = bytes.fromhex(mode)
    print(hex_data)
    return hex_data

class SerThread():
    def __init__(self, portx):
        # 初始化串口
        self.my_serial = serial.Serial()
        self.my_serial.port = portx
        self.my_serial.baudrate = 115200
        self.my_serial.timeout = 1
        #buffer
        self.tag_package = ucm60x_ucm_pro_t()#tag包
        self.ring_temp_buff = []
        self.data_index = 0
        #ucm60X_decode_rfid_packet
        self.ucm60x_tag_epc_list_str = []
        self.ucm60x_tag_epc_num = 0
        #线程 ucm60X_recv_rfid_packet
        self.waitEnd = None   # 设置线程事件变量X
        self.alive = False    # 设置条件变量
        self.errorcode = 0
        self.rf_link = ""     #设置链路模式
        self.switch_index = "PACKAGE_HEAD"

    def start(self):
        # 打开串口并创建blog文件
        # self.my_serial.open()   # 打开串口
        if self.my_serial.is_open:#当前串口是否已经打开
            self.waitEnd = threading.Event()  # 将线程事件赋值给变量
            self.alive = True # 改变条件变量值
            self.thread_read = threading.Thread(target=self.ucm60X_recv_rfid_packet)  # 创建一个读取串口数据的线程
            self.thread_read.daemon = True  # 调用线程同时结束的函数
            #
            #send_config_cmd_back_3 = "a004008910c3"
            self.realtime_inventory()   # 发送盘存指令
            #self.send_config_cmd_and_receive_verify(self.realtime_inventory,send_config_cmd_back_3)
            self.thread_read.start()    # 启动线程
            return True     #成功就返回True
        else:
            return False    #失败就返回False
        
    def ucm60X_get_ucm_crc(self):
        uSum = 0
        for i in range(len(self.ring_temp_buff)):
            uSum += self.ring_temp_buff[i]
        uSum = (~uSum) + 1
        uSum = uSum & 0xff
        return uSum
    
    def ucm60X_decode_rfid_packet(self):
        if (int(self.tag_package.len,16) > 12):
            if (int(self.tag_package.cmd,16) == 0x89):
                epc_len = (int(self.tag_package.data[1],16)//8)*2
                epc_str = ""
                for i in range(epc_len):
                    if( i == (epc_len-1)):
                        epc_str += str(self.tag_package.data[i+3])
                    else:
                        epc_str += (str(self.tag_package.data[i+3])+" ")
                print('\033[32m'+"EPC: "+epc_str+'\033[0m')
                self.ucm60x_tag_epc_list_str.append(epc_str)
                self.ucm60x_tag_epc_num += 1
                del epc_str

    def switch(self,Receive_Buffer,index):
        flag_number = 0
        match self.switch_index:
            case "PACKAGE_HEAD":
                if(Receive_Buffer[index]== 0XA0):
                    self.tag_package.head = '{:02X}'.format(Receive_Buffer[index])
                    self.ring_temp_buff.clear()
                    self.ring_temp_buff.append(Receive_Buffer[index])
                    self.switch_index = "PACKAGE_LEN"
                    #print("1_"+self.switch_index)
            case "PACKAGE_LEN":
                    self.tag_package.len = '{:02X}'.format(Receive_Buffer[index])
                    self.ring_temp_buff.append(Receive_Buffer[index])
                    self.switch_index = "PACKAGE_ADDR"
                    #print("2_"+self.switch_index)
            case "PACKAGE_ADDR":
                    self.tag_package.addr = '{:02X}'.format(Receive_Buffer[index])
                    self.ring_temp_buff.append(Receive_Buffer[index])
                    self.switch_index = "PACKAGE_CMD"
            case "PACKAGE_CMD":
                    self.tag_package.cmd = '{:02X}'.format(Receive_Buffer[index])
                    self.ring_temp_buff.append(Receive_Buffer[index])
                    if (int(self.tag_package.len,16) > 4):
                        flag_number = 1
                        self.switch_index = "PACKAGE_DATA"
                        self.tag_package.data.clear()
                    else:
                        self.switch_index = "PACKAGE_HEAD"
                    #print("3_"+self.switch_index)    
            case "PACKAGE_DATA":
                    self.tag_package.data.append('{:02X}'.format(Receive_Buffer[index]))
                    self.ring_temp_buff.append(Receive_Buffer[index])
                    if(self.data_index >= (int(self.tag_package.len,16)-4)):
                        self.switch_index = "PACKAGE_CRC"
                    self.data_index += 1
                    #print("4_"+self.switch_index)    
            case "PACKAGE_CRC":
                    self.tag_package.crc = '{:02X}'.format(Receive_Buffer[index])
                    if (int(self.tag_package.crc,16) == self.ucm60X_get_ucm_crc()):
                        #正确数据
                        # print("rfid upload packet:",self.tag_package.head.upper(),self.tag_package.len.upper(),self.tag_package.addr.upper(),self.tag_package.cmd.upper(),sep=" ",end=" ")
                        # for i in range(int(self.tag_package.len,16) -3):
                        #     print(str(self.tag_package.data[i]).upper(),end=" ")
                        # print(self.tag_package.crc.upper())
                        self.ucm60X_decode_rfid_packet()
                    else:
                        #错误数据
                        print("\033[31m","rfid crc error!")
                        print("rfid error data:",self.tag_package.head.upper(),self.tag_package.len.upper(),self.tag_package.addr.upper(),self.tag_package.cmd.upper(),sep=" ",end=" ")
                        for i in range(int(self.tag_package.len,16) -3):
                            print(str(self.tag_package.data[i]).upper(),end=" ")
                        print(self.tag_package.crc.upper(),"\033[0m")
                    self.switch_index = "PACKAGE_HEAD"
                    self.data_index = 0
                    #print("5_"+self.switch_index)    
            case _:
                self.switch_index = "PACKAGE_HEAD"
                self.data_index = 0
                #print("5_"+self.switch_index)
        return flag_number
    def ucm60X_recv_rfid_packet(self):
        flag_num = 0
        begintime = time.time()#获取时间戳
        while self.alive:   # 当条件变量为True时执行
            finishtime = time.time()#获取时间戳
            running_time = finishtime - begintime
            if(running_time >= each_run_time):
                print('running_time = ', running_time)
                self.errorcode = 0
                if flag_num > 0:
                       print('flag_num = ', flag_num)
                else:
                    print("no epc!")
                    self.errorcode = 1
                break
            try:
                buf_len = self.my_serial.in_waiting    # 将接收缓存区数据字节数保存在变量uf_len中
                if buf_len > 0:
                    Receive_Buffer = self.my_serial.read(buf_len)#读buf_len个字符
                    #print(Receive_Buffer.hex().upper())
                    index = 0
                    while index < len(Receive_Buffer):
                        flag_num += self.switch(Receive_Buffer,index)
                        index += 1
            except Exception as ex:
                print(ex)
        self.waitEnd.set()    # 暂停子线程
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

    def set_rfid_addr_0x00(self):#设置读写器地址
       self.my_serial.write(set_rfid_addr())
       time.sleep(1)

    def realtime_inventory(self):#标签盘存
        self.my_serial.write(send_reader_real_time_inventory())

    def stop_invnetory(self):#停止盘存
        self.my_serial.write(send_reader_stop_inventory())
        time.sleep(5)
    
    def set_rf_link(self):#设置链路模式
        self.my_serial.write(send_set_rf_link(self.rf_link))
        time.sleep(3)
    
    def send_config_cmd_and_receive_verify(self,send_config_cmd_function,send_config_cmd_back:str):
       self.my_serial.reset_input_buffer()#清理接收缓冲区
       send_config_cmd_function()
       t1 = time.time()
       while (not self.my_serial.in_waiting):
           t2 = time.time()
           if (t2 - t1 > 5):
               print("Overtime_Error!")
               exit(1)
       time.sleep(0.2)
       if (self.my_serial.read(self.my_serial.in_waiting).hex().find(send_config_cmd_back) == -1):
           print("send config cmd error")
           exit(1)
       else:
           print("send config cmd ok!")
       time.sleep(1)

if __name__ == '__main__':
    com = ''
    inputsdirpath = os.path.join(os.curdir, 'Inputs')#组合os.curdir和Inputs返回一个路径字符串
    haveinputsdir = os.path.exists(inputsdirpath)#判断inputsdirpath路径是否存在
    if haveinputsdir:
        inputspath = os.path.join(inputsdirpath + '\\com_input.txt')
        if os.path.exists(inputspath):
            com = open(inputspath, 'r').read().strip()
        else:
            com = serial_port
    else:
        com = serial_port
    print('use:' + com)
    ser = SerThread(com)
   
    try:
        ser.my_serial.open()  # 打开串口
        send_config_cmd_back_1 = "a004007310d9"
        ser.send_config_cmd_and_receive_verify(ser.set_rfid_addr_0x00,send_config_cmd_back_1)#配置读写器地址为0x00
        for key, value in rf_link_table.items():
            read_rate_file = open(make_file_return_path(path_txt,key), 'w')#打开文件
            read_rate_file.write(key+"\n")
            print("rf_link = ", key)
            ser.rf_link = value
            send_config_cmd_back_2 = "a004006910e3"
            ser.send_config_cmd_and_receive_verify(ser.set_rf_link,send_config_cmd_back_2)#设置链路模式
            #盘存
            for num in range(run_ring):
                print("-"*23+"Start!"+"-"*23)
                print("round: ",(num+1))
                if(not ser.start()):#子线程解析计数#解析
                    exit(1)
                ser.waiting()#阻塞主线程等待子线程结束
                #send_config_cmd_back_4 = "a004008c10c0"
                ser.stop_invnetory()  # 发停止盘存指令
                #ser.send_config_cmd_and_receive_verify(ser.stop_invnetory,send_config_cmd_back_4)
                print("ucm60x_tag_epc_num = ",ser.ucm60x_tag_epc_num)
                print("-"*23+"Stop!"+"-"*23)
                if ser.errorcode == 1:
                    print('End error.')
                    exit(1)
                print("sleep: "+str(each_ring_tim_interval)+"s")
                time.sleep(each_ring_tim_interval)
                PSC_Number = [str(num+1)+" "+str(ser.ucm60x_tag_epc_num)+"\n"]
                read_rate_file.writelines(PSC_Number)#往txt文件写数据
                ser.ucm60x_tag_epc_list_str.clear()#清空列表
                ser.ucm60x_tag_epc_num = 0
            read_rate_file.close()
        Draw_Histogram(path_txt)#画图
        time.sleep(5)
        Var_And_SD(path_txt)#计算平均数和标准差
    except Exception as ex:
        print(ex)
    
    if ser.alive:
        ser.stop()
   
    if ser.errorcode == 0:
        print('End OK.')
        exit(0)
    del ser