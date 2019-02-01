# -*- coding: utf-8 -*-
import time
import visa


class scpi_instr_debug():
    """
    调试SCPI指令的类
    """

    def __init__(self):
        rm = visa.ResourceManager()
        self.instrument = rm.list_resources()[0]
        self.my_instr = rm.open_resource(self.instrument)
        query = self.my_instr.query("*IDN?")
        print query

    def write(self, command):
        """
        向仪表发送执行指令
        :param command: SCPI语句
        :return: None
        """
        try:
            self.my_instr.write(command)
        except Exception, e:
            print e

    def query(self, command):
        """
        向仪表发送执行指令，并获取返回值
        :param command: SCPI语句
        :return: 执行结果
        """
        return self.my_instr.query(command)

    def debug_instr(self,para):
        """
        调试SCPI指令方法
        :return:None
        """
        # print self.write("SYST:COMM:GPIB:DEB ON")
        # self.write("CALL:POWer %s" % str(para))
        self.write("SYSTem:REGister:RECall 5")
        time.sleep(3)



if __name__ == "__main__":
    case = scpi_instr_debug()
    case.debug_instr(-75)
