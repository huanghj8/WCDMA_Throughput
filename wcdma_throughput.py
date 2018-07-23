import visa
import pyvisa


class WcdmaThroughput():
    def __init__(self):
        rm = visa.ResourceManager()
        print rm
        print rm.list_resources()
        # rm2 = pyvisa
        # print visa.get_instruments_list()
        my_instr = rm.open_resource('GPIB0::15::INSTR')

        channel = [10563, 10700, 10837,  # band1
                   4358, 4400, 4457,  # band5
                   2938, 3013, 3087]  # band8

    def handover(self, channel, band=1):
        self.my_instr.write("CALL:SETup:CHANnel:DOWNlink %s" % str(channel))
        self.my_instr.write("CALL:HAND:PCR")

    def init_logging(self):
        pass

    def save_result(self):
        pass

    def set_cable_loss(self):
        self.my_instr.write("SYST:CORR:STAT ON")

        # print my_instr
        # print my_instr.query("*IDN?")
        # my_instr.write("CALL:COUNt:DTMonitor")
        # my_instr.write("CALL:ORIG")
        # my_instr.write("SYST:CORR:STAT ON")
        # my_instr.write("CALL:END")
        # my_instr.write("SYSTEM:CORRECTION:FREQUENCY 800.0 MHZ,1800.0 MHZ")
        # my_instr.write("SYSTEM:CORRECTION:GAIN -0.50,-0.80")

    def get_throughput(self):
        print self.my_instr.query("CALL:HSDPa:MS:REPorted:ACK?")  # return blocks transmitted
        print self.my_instr.query("CALL:HSDPa:MS:REPorted:IBTHroughput?")  # return Throughput
        self.my_instr.write("SYST:MEAS:RES")  # Reset measurement

    def run_case(self):
        pass


if __name__ == "__main__":
    test_case = WcdmaThroughput()
    test_case.run_case()
