import time
import visa
# import pyvisa
import my_logging


class WcdmaThroughput(object):
    def __init__(self):
        self.my_logging = my_logging.MyLogging()
        self.logger = self.my_logging.get_logger()
        self.local_time = time.strftime("%Y%m%d-%H%M%S")

        rm = visa.ResourceManager()
        self.logger.info(rm)
        self.logger.info(rm.list_resources())

        # rm2 = pyvisa
        # print visa.get_instruments_list()
        self.my_instr = rm.open_resource('GPIB0::15::INSTR')
        # print self.my_instr.query("*IDN?")

        self.bands = [
            [1, [10563, 10700, 10837]],  # band1
            [2, [9663, 9800, 9937]],  # band2
            # [4, [1538, 1675, 1737]],  # band4
            [5, [4358, 4400, 4457]],  # band5
            [8, [2938, 3013, 3087]]  # band8
        ]

    def write(self, command):
        self.my_instr.write(command)

    def query(self, command):
        return self.my_instr.query(command)

    def read(self):
        return self.my_instr.read()

    def handover(self, channel, band=1, channel_type="low/mid"):
        if channel:
            self.write("CALL:SETup:CHANnel:DOWNlink %s" % str(channel))
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
            self.logger.info( "status:"+ status)
            if status == "CONN\n":
                break
            else:
                print "wait for connect..."

                time.sleep(1)
                i -= 1
                # print self.read()

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

        # print my_instr
        # print my_instr.query("*IDN?")
        # my_instr.write("CALL:COUNt:DTMonitor")
        # my_instr.write("CALL:ORIG")
        # my_instr.write("SYST:CORR:STAT ON")
        # my_instr.write("CALL:END")
        # my_instr.write("SYSTEM:CORRECTION:FREQUENCY 800.0 MHZ,1800.0 MHZ")
        # my_instr.write("SYSTEM:CORRECTION:GAIN -0.50,-0.80")

    def get_downlink_result(self):
        self.write("SYST:MEAS:RES")  # Reset measurement
        time.sleep(5)
        transmit = self.query("CALL:HSDPa:MS:REPorted:BLOCks?")  # return blocks transmitted
        # while transmit < 1E4:
        #     print "transmit: ", transmit
        #     transmit = self.query("CALL:HSDPa:MS:REPorted:ACK?")  # return blocks transmitted
        throughput = self.query("CALL:HSDPa:MS:REPorted:IBTHroughput?")  # return throughput
        ber = self.query("CALL:HSDPa:MS:REPorted:HBLerror:RATio?")  # return BER
        self.logger.info("transmit: " + str(transmit))
        self.logger.info("throughput: " + str(throughput))
        self.logger.info("BER: " + str(ber))
        return [transmit, throughput, ber]

    def get_uplink_result(self):
        self.write("SYST:MEAS:RES")

    def run_case(self):
        filename = 'result\\result_%s.txt' % str(self.local_time)
        for band in self.bands:
            for i in range(len(band[1])):
                channel = band[1][i]
                if i / 2 == 1:
                    channel_type = "high"
                else:
                    channel_type = "low/mid"
                self.handover(channel, band[0], channel_type)
                throughput = self.get_downlink_result()
                self.save_result(filename, band[0], channel, throughput)


if __name__ == "__main__":
    test_case = WcdmaThroughput()
    test_case.run_case()
