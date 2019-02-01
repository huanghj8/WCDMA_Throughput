# -*- coding: utf-8 -*-
# 用于测试WCDMA物理&IP层上下行吞吐量,8960 Application当前为Fast Switch Lab App
# 手机需关闭数据业务开关，否则无法进入Connected状态，而进入PDP ACTIVE状态
import re
import subprocess
import time
from threading import Thread
import os
import wx
import visa
import xlsxwriter
import PyChariot
import my_logging
import xml.etree.ElementTree as ElementTree


class WcdmaThroughput(Thread):
    """
    WCDMA物理层吞吐量测试线程
    """

    def __init__(self, windows, cable_loss):
        # def __init__(self, cable_loss):
        """
        初始化参数
        :param windows: 测试UI窗口
        :param test_bands:测试频段
        :param cable_loss: 线损
        :param chip_set: 芯片平台
        :param downlink_speed: DUT下行速率
        :param uplink_speed: DUT上行速率
        """
        super(WcdmaThroughput, self).__init__()
        self.debug_mode = 1
        self.windows = windows
        self.tree = ElementTree.parse('config.xml')
        self.root = self.tree.getroot()
        self.MAX_TIMES = 3
        self.DURATION = self.root.find('duration').text
        self.my_logging = my_logging.MyLogging()
        self.logger = self.my_logging.get_logger()
        self.local_time = time.strftime("%Y%m%d-%H%M%S")
        self.result_path = 'result'
        if not os.path.exists(self.result_path):
            os.makedirs(self.result_path)
        self.txt_result = 'result\\result_%s.txt' % str(self.local_time)
        self.bands_all = [
            [1, [10563, 10700, 10837]],  # band1
            [2, [9663, 9800, 9937]],  # band2
            [3, [1163, 1337, 1512]],  # band3
            [4, [1538, 1675, 1737]],  # band4
            [5, [4358, 4400, 4457]],  # band5
            [8, [2938, 3013, 3087]]  # band8
        ]
        rm = visa.ResourceManager()
        self.logger.info(rm)
        self.logger.info(rm.list_resources())

        try:
            self.instrument = rm.list_resources()[0]
            self.logger.info("选择设备列表第一个仪器，请确保只有一个GPIB设备连接")
            self.logger.info('Try to connect instrument, address: %s' % self.instrument)
            self.my_instr = rm.open_resource(self.instrument)
            query = self.my_instr.query("*IDN?")
            self.logger.info("Query result: %s" % str(query))
            if query == "":
                self.logger.error("无法连接至8960！")
            else:
                self.logger.info("连接成功！")
        except Exception, e:
            self.logger.error(str(Exception))
            self.logger.error(e)
            self.logger.error("无法识别GPIB设备！")

        # self.windows = windows
        self.bands_index = map(int, filter(None, re.split(r'[, ()]',
                                                          self.root.find('test_bands').text)))
        print "self.bands_index: ", self.bands_index
        self.bands = [self.bands_all[i] for i in self.bands_index]
        self.logger.info("Test bands: %s" % str(self.bands))
        # self.cable_loss = map(float, filter(None, re.split(r'[, ()]',
        #                                                        self.root.find('cable_loss').text)))
        self.cable_loss = cable_loss
        print self.cable_loss
        # self.cable_loss = self.root.find('cable_loss').text
        self.chip_set = self.root.find('chip_set').text
        self.downlink_speed = self.root.find('downlink_speed').text
        self.uplink_speed = self.root.find('uplink_speed').text
        self.e1 = '127.0.0.1'
        self.e2 = self.root.find('dut_ip').text
        if self.root.find('test_phy_flag').text == 'False':
            self.test_phy_flag = False
        else:
            self.test_phy_flag = True
        if self.root.find('test_ip_flag').text == 'False':
            self.test_ip_flag = False
        else:
            self.test_ip_flag = True

            # 线程实例化时立即启动
        self.start()

    def write(self, command):
        """
        向仪表发送执行指令
        :param command: SCPI语句
        :return: None
        """
        try:
            self.my_instr.write(command)
        except Exception, e:
            self.logger.error(e)
            self.logger.error("设备为空")

    def query(self, command):
        """
        向仪表发送执行指令，并获取返回值
        :param command: SCPI语句
        :return: 执行结果
        """
        return self.my_instr.query(command)

    def read(self):
        """
        获取仪表当前状态值
        :return: 当前状态
        """
        return self.my_instr.read()

    def handover(self, channel, band=1, channel_type="low/mid", test_type="phy"):
        """
        信道切换方法
        :param channel: 目标信道
        :param band: 目标频段
        :param channel_type: 信道类型，即低中高
        :return: None
        """
        if channel:
            self.logger.info("band: %s, channel: %s", str(band), str(channel))
            self.write("CALL:SETup:CHANnel:DOWNlink %s" % str(channel))
        if band == 5:
            self.write("CALL:SETup:CHANnel:BARBitrator BAND5")
        if channel_type == "high":
            self.write("CALL:SETup:SSCell:CHANnel:ADJacent LOWer")
        else:  # low/mid
            self.write("CALL:SETup:SSCell:CHANnel:ADJacent HIGHer")

        self.write("CALL:HAND:PCR")
        time.sleep(2)
        # 查询状态循环次数为50，避免程序卡住，并保留足够的手动连接时间
        i = 50
        while i > 0:
            if test_type == "phy":
                self.write("CALL:STAT?")
                status = str(self.read())
                self.logger.info("status:" + status)
                # Connected is returned when the test set and UE are connected on a call.
                if status == "CONN\n":
                    break
                else:
                    self.logger.info("wait for connect...")
                    time.sleep(2)
                    i -= 1
            elif test_type == "ip":
                # IP层上行handover会掉回Idle状态，需要加时延等待，否则太快读取会报错
                time.sleep(3)
                self.write("CALL:STATus:DATA?")
                time.sleep(2)
                status = str(self.read())
                self.logger.info("status:" + status)
                # PDP is returned when the test set and UE are PDP actived.
                if status == "PDP\n":
                    break
                else:
                    self.logger.info("wait for connect...")
                    time.sleep(2)
                    i -= 1

    def set_chipset_platform(self):
        """
        根据芯片平台设置RLC reestablish状态
        :return: None
        """
        if self.chip_set == 'MTK':
            self.write('CALL:CELL:RLC:REEStablish AUTO')
        elif self.chip_set == 'QUALCOMM':
            self.write('CALL:CELL:RLC:REEStablish OFF')

    def save_result(self, filename, band, channel, result, test_type=''):
        """
        保存数据为文本格式
        :param filename: 文本路径
        :param band: 频段
        :param channel: 信道
        :param result: 吞吐量
        :param test_type: 测试类型
        :return: None
        """
        self.logger.info('Save result...')
        result_file = open(filename, "a")
        result_file.writelines(str(test_type) + '\t')
        result_file.writelines(str(band) + '\t')
        result_file.writelines(str(channel) + '\t')
        # for i in result:
        #     result_file.write(str(float(i)) + '\t')
        result_file.write(str(float(result)) + '\t')
        result_file.write('\n')
        result_file.close()

    def process_result(self):
        """
        数据处理，输出Excel报告
        :return: None
        """
        filename = self.txt_result
        txt_result_file = open(filename)

        # 初始化表格
        workbook = xlsxwriter.Workbook('result//result_%s.xlsx' % str(self.local_time))
        worksheet = workbook.add_worksheet()
        bold = workbook.add_format({'bold': 1})
        lines = txt_result_file.readlines()

        # 写入表头
        worksheet.write(0, 0, 'Test mode', bold)
        worksheet.write(0, 1, 'Band', bold)
        worksheet.write(0, 2, 'Channel', bold)
        worksheet.write(0, 3, 'Throughput/Mbps', bold)

        # 写入数据
        row = 1
        for line in lines:
            result_list = line.split('\t')
            for col in range(len(result_list)):
                try:
                    # 第一列写入测试类型
                    if col == 0:
                        worksheet.write(row, col, str(result_list[col]))
                    # 换行符作为一行循环结束的标志
                    elif result_list[col] != '\n':
                        worksheet.write(row, col, float(result_list[col]))
                except Exception, e:
                    self.logger.error(e)
            row += 1

        # 保存文件
        txt_result_file.close()
        workbook.close()

    def set_gpib_debug(self, state):
        """
        设置GPIB调试模式
        :return:
        """
        if state:
            self.write("SYST:COMM:GPIB:DEB ON")
        else:
            self.write("SYST:COMM:GPIB:DEB OFF")
        self.logger.info("GPIB debug mode: %s" % bool(state))

    def set_cable_loss(self, fre1=800.0, fre2=1800.0, att1=-0.50, att2=-0.80):
        """
        设置衰减值
        :param fre1:频点1
        :param fre2: 频点2
        :param att1: 衰减值1
        :param att2: 衰减值2
        :return: None
        """
        if self.cable_loss:
            # fre1 = self.cable_loss[0][0]
            # att1 = self.cable_loss[0][1]
            # fre2 = self.cable_loss[1][0]
            # att2 = self.cable_loss[1][1]
            fre1 = self.cable_loss[0]
            att1 = self.cable_loss[1]
            fre2 = self.cable_loss[2]
            att2 = self.cable_loss[3]
        self.write("SYST:CORR:STAT ON")
        self.write("SYSTEM:CORRECTION:FREQUENCY %s MHZ,%s MHZ" % (str(fre1), str(fre2)))
        self.write("SYSTEM:CORRECTION:GAIN %s,%s" % (str(att1), str(att2)))

    def reset(self):
        """
        仪表重置命令
        :return: None
        """
        self.write("*RST")

    def clear_error_msg(self):
        """
        清除仪器面板的提示信息
        :return:
        """
        error_msg = self.query("SYSTem:ERRor? ")
        self.logger.info(str(error_msg))
        self.write("DISPlay:WINDow:ERRor:CLEar")

    def active_cell(self):
        """
        激活小区的命令
        :return: None
        """
        self.write("CALL:OPERating:MODE CALL")
        self.write("Turn on cell, please wait...")
        time.sleep(2)

    def off_cell(self):
        """
        关闭小区的命令
        :return:
        """
        self.reset()
        self.write("CALL:OPERating:MODE OFF")
        self.logger.info("Turn off cell, please wait...")
        time.sleep(5)

    def originate_call(self):
        """
        发起建立通话命令，并查询状态，直至连接状态为Connected
        :return: None
        """
        # 循环100次尝试，在这期间可以手动开关DUT飞行模式，以便更快注册上网络
        i = 100
        while i > 0:
            self.write("CALL:ORIGinate")
            # 等待5s再查询状态
            time.sleep(5)
            self.write("CALL:STAT?")
            status = str(self.read())
            self.logger.info("status:" + status)
            if status == "CONN\n":
                break
            else:
                self.logger.info("wait for connect... try time: %d" % (101 - i))
                self.logger.info("Try to turn on flight mode and turn off")
                time.sleep(2)
                i -= 1

    def pdp_active(self):
        """
        发起PDP连接
        :return: None
        """
        i = 100
        while i > 0:
            # self.write("CALL:ORIGinate")
            # 等待5s再查询状态
            # 等待自动连接PDP
            time.sleep(5)
            status = self.query("CALL:STATus:DATA?")
            # status = str(self.read())
            self.logger.info("status:" + status)
            if status == "PDP\n":
                break
            else:
                self.logger.info("wait for PDP active... try time: %d" % (101 - i))
                self.logger.info("Try to turn on flight mode and turn off")
                time.sleep(2)
                i -= 1

    def end_call(self):
        """
        结束连接
        :return:None
        """
        self.write("CALL:END")
        self.logger.info("End call...")
        time.sleep(3)

    def cell_power(self, power):
        """
        设置小区输出功率
        :param power: 功率值
        :return: None
        """
        try:
            self.write("CALL:POWer %s" % str(power))
        except Exception, e:
            self.logger.error(e)

    def set_dut_data_switch(self, mode):
        """
        设置手机数据业务开关的状态
        :param mode: 1为打开数据开关；0为关闭
        :return: None
        """
        if mode:
            os.system("adb shell svc data %s" % "enable")
        else:
            os.system("adb shell svc data %s" % "disable")
            time.sleep(3)

    def set_channel(self, channel):
        """
        关闭cell后设置信道
        :return: None
        """
        self.off_cell()
        self.write("CALL:CHANnel %s" %str(channel))
        self.logger.info("Set channel to %s" % str(channel))
        time.sleep(1)

    def set_init_connect_channel(self):
        """
        切换到DUT支持的初始连接信道
        :return:None
        """
        band = self.bands[0]
        channel = band[1][0]
        self.set_channel(channel)

    def set_downlink_environment(self):
        """
        配置下行吞吐量测试环境,手册未查找到配置E6.2.3.4表的指令，因此换用调用注册表方式。后续完善。
        :return: None
        """
        # preset
        self.logger.info("preset")
        self.reset()
        self.write("CALL:BCCHannel:UPDAtepage AUTO")
        self.write("CALL:ATTFlag ON")
        self.write("CALL:UPLink:TXPower:LEVel:MAXimum 24")
        # set Authentication code
        self.logger.info("set Authentication code")
        self.write("CALL:SECurity:AUTHenticate:KEY " +
                   "'000102030405060708090A0B0C0D0E0F'")
        # set RRC Reesablish to Auto for MTK, and Off for QUALCOMM
        if self.chip_set == "QUALCOMM":
            self.write("CALL:CELL:RLC:REEStablish OFF")
        else:
            self.write("CALL:CELL:RLC:REEStablish AUTO")
        # set attenuation
        self.logger.info("set attenuation")
        self.set_cable_loss()
        self.write("CALL:OPERating:MODE OFF")
        time.sleep(1)
        self.write("CALL:SERVice:RBTest:RAB HSDP12")
        # TODO find instruction to set E6.2.3.4
        self.write("")
        self.write("CALL:CCPChannel:SECondary:CONNected:CONFig:STATe OFF")
        time.sleep(1)
        # set test mode parameter
        self.logger.info("set test mode parameter")
        self.write("CALL:HSDPa:SERVice:RBTest:HSDSchannel:CONFig UDEFined")
        self.write(
            "CALL:HSDPa:SERVice:RBTest:UDEFined:HSDSchannel:MAC EHSPeed")  # enhanced high speed
        self.write("CALL:HSDPa:SERVice:RBTest:UDEFined:HARQ:PROCess:COUNt 6")
        self.write("CALL:HSDPa:SERVice:RBTest:UDEFined:MS:IREDundancy:BUFFer:ALLocation IMPLicit")
        self.write("CALL:HSDPa:SERVice:RBTest:UDEFined:DCHSdpa ON")
        self.write("CALL:HSDPa:SERVice:RBTest:DCHSdpa:DPCH:LOOPback ON")
        time.sleep(1)
        # set server cell parameter
        self.logger.info("set server cell parameter")
        self.write("CALL:HSDPa:SERVice:RBTest:UDEFined:QAM64:STATe ON")
        self.write("CALL:HSDPa:SERVice:RBTest:UDEFined:HSPDschannel:COUNt 15")
        self.write("CALL:HSDPa:SERVice:RBTest:UDEFined:TBSize:INDex 62")
        self.write("CALL:HSDPa:SERVice:RBTest:UDEFined:MODulation[:TYPE] QAM64")
        self.write("CALL:HSDPa:SERVice:RBTest:UDEFined:ITTI[:INTerval] 1")
        time.sleep(1)
        # set sencondary cell parameter
        self.logger.info("set secondary cell parameter")
        self.write("CALL:HSDPa:SSCell:RBTest:UDEFined:QAM64:STATe ON")
        self.write("CALL:HSDPa:SSCell:RBTest:UDEFined:HSPDschannel:COUNt 15")
        self.write("CALL:HSDPa:SSCell:RBTest:UDEFined:TBSize:INDex 62")
        self.write("CALL:HSDPa:SSCell:RBTest:UDEFined:MODulation QAM64")
        self.write("CALL:HSDPa:SSCell:RBTest:UDEFined:ITTI 1")
        # set power
        self.logger.info("set power")
        self.write("CALL:SSCell:POWer -60 DBM")
        self.write("CALL:CELL:POWer -60 DBM")
        # set downlink channel level
        self.logger.info("set downlink channel level")
        self.write("CALL:CONNected:CPIChannel:HSDPa -8")
        self.write("CALL:CONNected:CPIChannel:PRIMary:HSDPa -20")  # -20 is the lowest
        self.write("CALL:CONNected:PICHannel:STATe:HSDPa OFF")  # use state instrution to set OFF
        self.write("CALL:CONNected:DPCHannel:HSDPa -30")
        self.write("CALL:CONNected:HSPDschannel -1")
        self.write("CALL:CONNected:HSSCchannel[1] -20")
        self.write("CALL:CONNected:HSSCchannel2 -20")
        self.write("CALL:CONNected:HSSCchannel3 -15")  # -15 means off
        self.write("CALL:CONNected:HSSCchannel4 -15")  # -15 means off

        self.write("CALL:SSCell:CONNected:CPIChannel:LEVel:HSDPa -8")
        self.write("CALL:SSCell:CONNected:CCPChannel:PRIMary:LEVel:HSDPa -20")  # -20 is the lowest
        self.write(
            "CALL:SSCell:CONNected:PICHannel:STATe:HSDPa OFF")  # use state instrution to set OFF
        self.write("CALL:SSCell:CONNected:HSPDschannel:LEVel:HSDPa -1")
        self.write("CALL:SSCell:CONNected:HSSCchannel1:LEVel:HSDPa -20")
        self.write("CALL:SSCell:CONNected:HSSCchannel2:LEVel:HSDPa -20")
        time.sleep(1)

        # origin call
        i = 20
        while i > 0:
            self.write("CALL:ORIGinate")
            self.logger.info("wait for connect...")
            time.sleep(5)
            self.write("CALL:STAT?")
            status = str(self.read())
            self.logger.info("status:" + status)
            if status == "CONN\n":
                break
            else:
                time.sleep(1)
                i -= 1

    def set_uplink_environment(self):
        """
        配置上行吞吐量环境，目前使用注册表配置，后续根据需求再更新
        :return: None
        """
        self.reset()
        self.set_cable_loss()

    def recall_phy_dl_register(self):
        """
        调用仪器PHY42M注册表的方式配置，后续改为逐一配置指令
        :return: None
        """
        self.reset()
        # self.off_cell()
        self.write("SYSTem:REGister:RECall 6")
        self.set_cable_loss()
        self.set_chipset_platform()
        self.set_phy_downlink_speed()
        self.set_init_connect_channel()
        self.active_cell()
        self.originate_call()

    def recall_ip_dl_register(self):
        """
        调用仪器IP42M注册表的方式配置，后续改为逐一配置指令
        :return: None
        """
        self.reset()
        self.off_cell()
        self.write("SYSTem:REGister:RECall 5")
        self.set_cable_loss()
        self.set_chipset_platform()
        self.set_ip_downlink_speed()
        self.set_init_connect_channel()
        self.active_cell()
        self.pdp_active()

    def recall_phy_ul_register(self):
        """
        调用仪器PHY11M注册表的方式配置，后续改为逐一配置指令
        :return:None
        """
        self.reset()
        # self.off_cell()
        self.write("SYSTem:REGister:RECall 10")
        self.set_cable_loss()
        self.set_chipset_platform()
        self.set_phy_uplink_speed()
        self.set_init_connect_channel()
        self.active_cell()
        self.originate_call()

    def recall_ip_ul_register(self):
        """
        调用仪器IP11M注册表的方式配置，后续改为逐一配置指令
        :return:None
        """
        self.reset()
        self.off_cell()
        self.write("SYSTem:REGister:RECall 4")
        self.set_cable_loss()
        self.set_chipset_platform()
        self.set_ip_uplink_speed()
        self.set_init_connect_channel()
        self.active_cell()
        self.pdp_active()

    def set_phy_downlink_speed(self):
        """
         设置下行速率，支持DC则为42M，不支持则为21M
        :return: None
        """
        if self.downlink_speed == '42M':
            self.write("CALL:HSDPa:SERVice:RBTest:UDEFined:DCHSdpa ON")
            self.write("CALL:HSDPa:SERVice:RBTest:DCHSdpa:DPCH:LOOPback ON")
        elif self.downlink_speed == '21M':
            self.write("CALL:HSDPa:SERVice:RBTest:UDEFined:DCHSdpa OFF")
            self.write("CALL:HSDPa:SERVice:RBTest:DCHSdpa:DPCH:LOOPback OFF")

    def set_ip_downlink_speed(self):
        """
         设置下行速率，支持DC则为42M，不支持则为21M
        :return: None
        """
        if self.downlink_speed == '42M':
            self.write("CALL:HSDPa:SERVice:PSData:DCHSDPA ON")
            # self.write("CALL:HSDPa:SERVice:RBTest:DCHSdpa:DPCH:LOOPback ON")
        elif self.downlink_speed == '21M':
            self.write("CALL:HSDPa:SERVice:PSData:DCHSDPA OFF")
            # self.write("CALL:HSDPa:SERVice:RBTest:DCHSdpa:DPCH:LOOPback OFF")

    def set_phy_uplink_speed(self):
        """
        设置上行速率，支持16QAM为11.4M，不支持则为5.7M
        :return: None
        """
        if self.uplink_speed == '11.4M':
            self.write("CALL:HSUPa:EDCHannel:QAM16 ON")
        elif self.uplink_speed == '5.7M':
            self.write("CALL:HSUPa:EDCHannel:QAM16 OFF")

    def set_ip_uplink_speed(self):
        """
        设置上行速率，支持16QAM为11.4M，不支持则为5.7M
        :return: None
        """
        if self.uplink_speed == '11.4M':
            self.write("CALL:HSUPa:EDCHannel:QAM16 ON")
        elif self.uplink_speed == '5.7M':
            self.write("CALL:HSUPa:EDCHannel:QAM16 OFF")

    def get_phy_downlink_result(self):
        """
        获取物理下行传输块、吞吐量结果
        :return: 物理下行吞吐量
        """
        self.write("SYST:MEAS:RES")  # Reset measurement
        self.logger.info("Testing, wait for 5s...")
        time.sleep(5)
        transmit = self.query("CALL:HSDPa:MS:REPorted:BLOCks?")  # return blocks transmitted
        throughput = self.query("CALL:HSDPa:MS:REPorted:IBTHroughput?")  # return throughput
        # 转为Mbps为单位
        throughput = float(throughput) / float(1000)
        # ber = self.query("CALL:HSDPa:MS:REPorted:HBLerror:RATio?")  # return BER
        self.logger.info("transmit: " + str(transmit))
        self.logger.info("throughput: " + str(throughput))
        # self.logger.info("BER: " + str(ber)) # 暂时不获取BER，保持与上行结果一致。后续再看需求
        return throughput

    def get_phy_uplink_result(self):
        """
        获取物理上行传输块、吞吐量结果
        :return: 物理上行吞吐量
        """
        self.write("SYST:MEAS:RES")
        self.logger.info("Testing, wait for 10s...")
        time.sleep(10)
        transmit = self.query("CALL:STATus:EHIChannel:ACK?")
        throughput = self.query("CALL:STATus:EDCHannel:IBTHroughput?")
        # 转为Mbps为单位
        throughput = float(throughput) / float(1000)
        self.logger.info("transmit: " + str(transmit))
        self.logger.info("throughput: " + str(throughput))
        return throughput

    def get_ip_result(self, e1, e2, mode="downlink", channel=0, pair_num=10):
        """
        获取IP层吞吐量,使用chariot测试，传入PC和DUT的IP地址，PC为127.0.0.1
        :return: IP层吞吐量
        """
        a = PyChariot.chariot.Chariot()
        a.add_pair(
            e1_addr=str(e1), e2_addr=str(e2), script_name='Throughput.scr',
            protocol=a.PROTOCOL_TCP, pair_number=pair_num
        )

        a.set_run_option(duration=int(self.DURATION))
        self.logger.info("Running chariot, please wait %s seconds...", str(self.DURATION))
        try:
            a.run()
            a.save_test()
            a.set_filename('result/%s_channel_%s.tst' % (str(mode), str(channel)))
            (throughput, times) = a.get_group_throughput()
            self.SET_TIMES = 0
        except Exception, e:
            self.logger.error(e)
            self.logger.info('Wait for 35s to release TCP resource...')
            subprocess.Popen('ipconfig/flushdns', shell=True)
            time.sleep(35)
            self.SET_TIMES += 1
            if self.SET_TIMES < self.MAX_TIMES:
                throughput = self.get_ip_result(e1, e2, pair_num=1)
            else:
                throughput = 0
                self.SET_TIMES = 0
        try:
            a.clear_test()
        except Exception, e:
            self.logger.error(e)
            self.logger.error('Clear Chariot test fail!')
        self.logger.info("The result is: %s" % str(throughput))
        return throughput

    def case_all_phy_downlink(self):
        """
        遍历所有信道的phy下行测试，记录于结果文本
        :return: None
        """
        self.logger.info("#############  Begin Phy Downlink Test  #############")
        self.logger.info("Turn off DUT'S data switch...")
        self.set_dut_data_switch(0)
        self.recall_phy_dl_register()
        self.clear_error_msg()
        filename = self.txt_result
        for band in self.bands:
            for i in range(len(band[1])):
                channel = band[1][i]
                if i / 2 == 1:
                    channel_type = "high"
                else:
                    channel_type = "low/mid"
                self.handover(channel, band[0], channel_type)
                result = self.get_phy_downlink_result()
                self.save_result(filename, band[0], channel, result, test_type='Phy downlink')
        self.end_call()
        self.logger.info("############# Finish Phy Downlink Test ###########")

    def case_all_ip_downlink(self):
        """
        遍历所有信道的IP层上行测试，记录于结果文本
        :return: None
        """
        self.logger.info("#############  Begin IP Downlink Test   #############")
        self.logger.info("Turn on DUT'S data switch...")
        self.set_dut_data_switch(1)
        self.recall_ip_dl_register()
        self.clear_error_msg()
        filename = self.txt_result
        for band in self.bands:
            for i in range(len(band[1])):
                channel = band[1][i]
                if i / 2 == 1:
                    channel_type = "high"
                else:
                    channel_type = "low/mid"
                self.handover(channel, band[0], channel_type, test_type="ip")
                result = self.get_ip_result(self.e1, self.e2, mode="downlink", channel=channel)
                self.save_result(filename, band[0], channel, result, test_type='IP downlink')
        self.end_call()
        self.logger.info("############# Finish IP Downlink Test ###########")

    def case_all_phy_uplink(self):
        """
        遍历所有信道的phy上行测试，记录于结果文本
        :return: None
        """
        self.logger.info("#############  Begin Phy Uplink Test  #############")
        self.logger.info("Turn off DUT'S data switch...")
        self.set_dut_data_switch(0)
        self.recall_phy_ul_register()
        filename = self.txt_result
        for band in self.bands:
            for i in range(len(band[1])):
                channel = band[1][i]
                if i / 2 == 1:
                    channel_type = "high"
                else:
                    channel_type = "low/mid"
                self.handover(channel, band[0], channel_type)
                self.clear_error_msg()
                result = self.get_phy_uplink_result()
                self.save_result(filename, band[0], channel, result, test_type='Phy uplink')
        self.end_call()
        self.logger.info("############# Finish Phy Uplink Test #############")

    def case_all_ip_uplink(self):
        """
        遍历所有信道的ip上行测试，记录于结果文本
        :return: None
        """
        self.logger.info("#############  Begin IP Uplink Test #############")
        self.logger.info("Turn on DUT'S data switch...")
        self.set_dut_data_switch(1)
        self.recall_ip_ul_register()
        filename = self.txt_result
        for band in self.bands:
            for i in range(len(band[1])):
                channel = band[1][i]
                if i / 2 == 1:
                    channel_type = "high"
                else:
                    channel_type = "low/mid"
                self.handover(channel, band[0], channel_type, test_type="ip")
                self.clear_error_msg()
                result = self.get_ip_result(self.e2, self.e1, mode="uplink", channel=channel)
                self.save_result(filename, band[0], channel, result, test_type='IP uplink')
        self.end_call()
        self.logger.info("#############  Finish IP Uplink Test  #############")

    def phy_downlink_pat(self):
        """
        物理层拉锯测试
        :return:
        """

    def ip_downlink_pat(self):
        """
        ip层拉锯测试
        :return:
        """

    def run(self):
        """
        线程的run方法，实例化后立即运行
        :return: None
        """
        if self.debug_mode:
            self.set_gpib_debug(1)
        if self.test_phy_flag:
            self.case_all_phy_downlink()
            self.case_all_phy_uplink()
        if self.test_phy_flag and self.test_ip_flag:
            self.logger.info("wait for 60s for drop net...")
            time.sleep(60)
        if self.test_ip_flag:
            self.case_all_ip_downlink()
            self.case_all_ip_uplink()
        if self.test_phy_flag or self.test_ip_flag:
            self.process_result()
        self.reset()
        self.off_cell()
        self.logger.info("Test finish!")
        wx.CallAfter(self.windows.on_call_back_message, "Thread message to windows\n")

#
# if __name__ == "__main__":
#     # 当该模块被运行（而不是被导入到其他模块）时，该部分会执行，主要用于调试
#
#     # 调试用的配置参数
#     test_bands = [
#         [1, [10563, 10700, 10837]],  # band1
#         [5, [4358, 4400, 4457]],  # band5
#         [8, [2938, 3013, 3087]]  # band8
#     ]
#     cable_loss = [0, 0, 0, 0]
#     chip_set = 'MTK'
#     down_sp = '42M'
#     up_sp = '11.4M'
#     import windows_ui
#
#     test_ui = windows_ui.TestUI()
#     test_case = WcdmaThroughput(test_ui,cable_loss)
