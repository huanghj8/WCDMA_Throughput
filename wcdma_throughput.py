# coding=utf-8
# -*- coding: utf-8 -*-
# 用于测试WCDMA物理层上下行吞吐量
# 手机需关闭数据业务开关，否则无法进入Connected状态，而进入PDP ACTIVE状态

import time
import visa
import my_logging


class WcdmaThroughput(object):
    def __init__(self):
        self.my_logging = my_logging.MyLogging()
        self.logger = self.my_logging.get_logger()
        self.local_time = time.strftime("%Y%m%d-%H%M%S")

        rm = visa.ResourceManager()
        self.logger.info(rm)
        self.logger.info(rm.list_resources())

        self.my_instr = rm.open_resource('GPIB0::15::INSTR')
        self.logger.info(str(self.my_instr.query("*IDN?")))

        self.bands = [
            [1, [10563, 10700, 10837]],  # band1
            # [2, [9663, 9800, 9937]],  # band2
            # [4, [1538, 1675, 1737]],  # band4
            [5, [4358, 4400, 4457]],  # band5
            [8, [2938, 3013, 3087]]  # band8
        ]
        self.chip_set = "MTK"

    def write(self, command):
        self.my_instr.write(command)

    def query(self, command):
        return self.my_instr.query(command)

    def read(self):
        return self.my_instr.read()

    def handover(self, channel, band=1, channel_type="low/mid"):
        if channel:
            self.logger.info("band: %s, channel: %s", str(band), str(channel))
            self.write("CALL:SETup:CHANnel:DOWNlink %s" % str(channel))
            # self.write("CALL:SETup:CHANnel:DOWNlink %s" % str(channel))
        # print self.read()
        if band == 5:
            self.write("CALL:SETup:CHANnel:BARBitrator BAND5")
        if channel_type == "high":
            # CALL:SETup[:PCRconfig]:SSCell:CHANnel:ADJacent HIGHer
            self.write("CALL:SETup:SSCell:CHANnel:ADJacent LOWer")
        else:  # low/mid
            self.write("CALL:SETup:SSCell:CHANnel:ADJacent HIGHer")

        self.write("CALL:HAND:PCR")
        time.sleep(2)
        i = 3
        while i > 0:
            self.write("CALL:STAT?")
            status = str(self.read())
            self.logger.info("status:" + status)
            if status == "CONN\n":
                break
            else:
                self.logger.info("wait for connect...")
                time.sleep(1)
                i -= 1

    def init_logging(self):
        pass

    def create_file(self):
        pass

    def save_result(self, filename, band, channel, result):
        self.logger.info('begin to save...')
        result_file = open(filename, "a")
        result_file.writelines(str(self.local_time) + '\n')
        result_file.writelines(str(band) + '\t')
        result_file.writelines(str(channel) + '\t')
        result_file.writelines(str(result) + '\n')
        result_file.close()

    def set_cable_loss(self):
        self.write("SYST:CORR:STAT ON")
        self.write("SYSTEM:CORRECTION:FREQUENCY 800.0 MHZ,1800.0 MHZ")
        self.write("SYSTEM:CORRECTION:GAIN -0.50,-0.80")

    def set_downlink_environment(self):
        """
        配置下行吞吐量测试环境
        :return: null
        """
        # preset
        self.logger.info("preset")
        self.write("*RST")
        self.write("CALL:BCCHannel:UPDAtepage AUTO")
        self.write("CALL:ATTFlag ON")
        self.write("CALL:UPLink:TXPower:LEVel:MAXimum 24")
        # set Authentication code
        self.logger.info("set Authentication code")
        self.write("CALL:SECurity:AUTHenticate:KEY " +
                   "'000102030405060708090A0B0C0D0E0F'")
        # set RRC Reesablish to Auto for MTK, and Off for QC
        if self.chip_set == "QC":
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
        i = 3
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

    def recall_dl_register(self):
        self.write("SYSTem:REGister:RECall 6")

    def recall_ul_register(self):
        self.write("SYSTem:REGister:RECall 4")

    def set_uplink_environment(self):
        self.set_cable_loss()

    def get_downlink_result(self):
        self.write("SYST:MEAS:RES")  # Reset measurement
        time.sleep(5)
        transmit = self.query("CALL:HSDPa:MS:REPorted:BLOCks?")  # return blocks transmitted
        throughput = self.query("CALL:HSDPa:MS:REPorted:IBTHroughput?")  # return throughput
        ber = self.query("CALL:HSDPa:MS:REPorted:HBLerror:RATio?")  # return BER
        self.logger.info("transmit: " + str(transmit))
        self.logger.info("throughput: " + str(throughput))
        self.logger.info("BER: " + str(ber))
        return [transmit, throughput, ber]

    def get_uplink_result(self):
        self.write("SYST:MEAS:RES")
        time.sleep(5)
        transmit = self.query("CALL:STATus:EHIChannel:ACK?")
        throughput = self.query("CALL:STATus:EDCHannel:IBTHroughput?")
        self.logger.info("transmit: " + str(transmit))
        self.logger.info("throughput: " + str(throughput))
        return [transmit, throughput]

    def case_all_downlink(self):
        filename = 'result\\result_%s.txt' % str(self.local_time)
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

    def case_all_uplink(self):
        filename = 'result\\result_%s.txt' % str(self.local_time)
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

    def test_handover(self):
        self.write("CALL:SETup:CHANnel:DOWNlink 10700")
        self.write("CALL:HAND:PCR")

    def test_instrution(self):
        self.write("CALL:CONNected:PICHannel:STATe:HSDPa OFF ")  # use state instrution to set OFF


if __name__ == "__main__":
    test_case = WcdmaThroughput()
    # test_case.case_all_uplink()
    # test_case.case_all_downlink()
    test_case.recall_dl_register()
