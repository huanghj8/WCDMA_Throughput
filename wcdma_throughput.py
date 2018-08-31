# -*- coding: utf-8 -*-
# 用于测试WCDMA物理层上下行吞吐量,8960 Application当前为Fast Switch Lab App
# 手机需关闭数据业务开关，否则无法进入Connected状态，而进入PDP ACTIVE状态

import time
from threading import Thread
import os
import wx
import visa
import xlsxwriter

import my_logging
import windows_ui


class WcdmaThroughput(Thread):
    """
    WCDMA物理层吞吐量测试线程
    """

    def __init__(self, windows, test_bands, cable_loss, chip_set, downlink_speed, uplink_speed):
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
        self.my_logging = my_logging.MyLogging()
        self.logger = self.my_logging.get_logger()
        self.local_time = time.strftime("%Y%m%d-%H%M%S")
        self.result_path = 'result'
        if not os.path.exists(self.result_path):
            os.makedirs(self.result_path)
        self.txt_result = 'result\\result_%s.txt' % str(self.local_time)
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

        self.windows = windows
        self.bands = test_bands
        self.cable_loss = cable_loss
        self.chip_set = chip_set
        self.downlink_speed = downlink_speed
        self.uplink_speed = uplink_speed

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

    def handover(self, channel, band=1, channel_type="low/mid"):
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
        # 查询状态循环次数为5，避免程序卡住，并保留足够的手动连接时间
        i = 5
        while i > 0:
            self.write("CALL:STAT?")
            status = str(self.read())
            self.logger.info("status:" + status)
            if status == "CONN\n":  # Connected is returned when the test set and UE are connected on a call.
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

    def save_result(self, filename, band, channel, result):
        """
        保存数据为文本格式
        :param filename: 文本路径
        :param band: 频段
        :param channel: 信道
        :param result: 吞吐量即传输块结果
        :return: None
        """
        self.logger.info('Save result...')
        result_file = open(filename, "a")
        result_file.writelines(str(band) + '\t')
        result_file.writelines(str(channel) + '\t')
        for i in result:
            result_file.write(str(float(i)) + '\t')
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
        worksheet.write(0, 0, 'Band', bold)
        worksheet.write(0, 1, 'Channel', bold)
        worksheet.write(0, 2, 'Transmit block', bold)
        worksheet.write(0, 3, 'Throughput/Kbps', bold)

        # 写入数据
        row = 1
        for line in lines:
            result_list = line.split('\t')
            for col in range(len(result_list)):
                try:
                    # 换行符作为一行循环结束的标志
                    if result_list[col] != '\n':
                        worksheet.write(row, col, float(result_list[col]))
                except Exception, e:
                    self.logger.error(e)
            row += 1

        # 保存文件
        txt_result_file.close()
        workbook.close()

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
            fre1 = self.cable_loss[0][0]
            att1 = self.cable_loss[0][1]
            fre2 = self.cable_loss[1][0]
            att2 = self.cable_loss[1][1]
        self.write("SYST:CORR:STAT ON")
        self.write("SYSTEM:CORRECTION:FREQUENCY %s MHZ,%s MHZ" % (str(fre1), str(fre2)))
        self.write("SYSTEM:CORRECTION:GAIN %s,%s" % (str(att1), str(att2)))

    def reset(self):
        """
        仪表重置命令
        :return: None
        """
        self.write("*RST")

    def active_cell(self):
        """
        激活小区的命令
        :return: None
        """
        self.write("CALL:OPERating:MODE CALL")
        time.sleep(1)

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
        self.write("CALL:HSDPa:SERVice:RBTest:UDEFined:HSDSchannel:MAC EHSPeed")  # enhanced high speed
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
        self.write("CALL:SSCell:CONNected:PICHannel:STATe:HSDPa OFF")  # use state instrution to set OFF
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

    def recall_dl_register(self):
        """
        调用仪器PHY42M注册表的方式配置，后续改为逐一配置指令
        :return: None
        """
        self.reset()
        self.write("SYSTem:REGister:RECall 6")
        self.set_cable_loss()
        self.set_chipset_platform()
        self.set_downlink_speed()
        self.active_cell()
        self.originate_call()

    def recall_ul_register(self):
        """
        调用仪器PHY11M注册表的方式配置，后续改为逐一配置指令
        :return:
        """
        self.reset()
        self.write("SYSTem:REGister:RECall 10")
        self.set_cable_loss()
        self.set_chipset_platform()
        self.set_uplink_speed()
        self.active_cell()
        self.originate_call()

    def set_downlink_speed(self):
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

    def set_uplink_speed(self):
        """
        设置上行速率，支持16QAM为11.4M，不支持则为5.7M
        :return: None
        """
        if self.uplink_speed == '11.4M':
            self.write("CALL:HSUPa:EDCHannel:QAM16 ON")
        elif self.uplink_speed == '5.7M':
            self.write("CALL:HSUPa:EDCHannel:QAM16 OFF")

    def get_downlink_result(self):
        """
        获取下行传输块、吞吐量结果
        :return: 包含传输块、吞吐量的列表
        """
        self.write("SYST:MEAS:RES")  # Reset measurement
        time.sleep(5)
        transmit = self.query("CALL:HSDPa:MS:REPorted:BLOCks?")  # return blocks transmitted
        throughput = self.query("CALL:HSDPa:MS:REPorted:IBTHroughput?")  # return throughput
        # ber = self.query("CALL:HSDPa:MS:REPorted:HBLerror:RATio?")  # return BER
        self.logger.info("transmit: " + str(transmit))
        self.logger.info("throughput: " + str(throughput))
        # self.logger.info("BER: " + str(ber)) # 暂时不获取BER，保持与上行结果一致。后续再看需求
        return [transmit, throughput]

    def get_uplink_result(self):
        """
        获取下行传输块、吞吐量结果
        :return: 包含传输块、吞吐量的列表
        """
        self.write("SYST:MEAS:RES")
        time.sleep(10)
        transmit = self.query("CALL:STATus:EHIChannel:ACK?")
        throughput = self.query("CALL:STATus:EDCHannel:IBTHroughput?")
        self.logger.info("transmit: " + str(transmit))
        self.logger.info("throughput: " + str(throughput))
        return [transmit, throughput]

    def case_all_downlink(self):
        """
        遍历所有信道的下行测试，记录于结果文本
        :return: None
        """
        self.logger.info("#############  Begin to Test Downlink  #############")
        self.recall_dl_register()
        filename = self.txt_result
        for band in self.bands:
            for i in range(len(band[1])):
                channel = band[1][i]
                if i / 2 == 1:
                    channel_type = "high"
                else:
                    channel_type = "low/mid"
                self.handover(channel, band[0], channel_type)
                result = self.get_downlink_result()
                self.save_result(filename, band[0], channel, result)
        self.logger.info("############# DownLink Test Completed! ###########")

    def case_all_uplink(self):
        """
        遍历所有信道的上行测试，记录于结果文本
        :return: None
        """
        self.logger.info("#############  Begin to Test Uplink  #############")
        self.recall_ul_register()
        filename = self.txt_result
        for band in self.bands:
            for i in range(len(band[1])):
                channel = band[1][i]
                if i / 2 == 1:
                    channel_type = "high"
                else:
                    channel_type = "low/mid"
                self.handover(channel, band[0], channel_type)
                result = self.get_uplink_result()
                self.save_result(filename, band[0], channel, result)

        self.logger.info("############# UpLink Test Completed! #############")

    def run(self):
        """
        线程的run方法，实例化后立即运行
        :return: None
        """
        self.case_all_downlink()
        self.case_all_uplink()
        self.process_result()
        self.logger.info("Test finish!")
        wx.CallAfter(self.windows.on_call_back_message, "Thread message to windows")


if __name__ == "__main__":
    # 当该模块被运行（而不是被导入到其他模块）时，该部分会执行，主要用于调试

    # 调试用的配置参数
    test_bands = [
        [1, [10563, 10700, 10837]],  # band1
        [5, [4358, 4400, 4457]],  # band5
        [8, [2938, 3013, 3087]]  # band8
    ]
    cable_loss = [(0, 0), (0, 0)]
    chip_set = 'MTK'
    down_sp = '42M'
    up_sp = '11.4M'
    test_ui = windows_ui.TestUI()
    test_case = WcdmaThroughput(test_ui, test_bands, cable_loss, chip_set, down_sp, up_sp)
