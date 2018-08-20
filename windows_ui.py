#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C), TP-LINK Technologies Co., Ltd.
# Author: Huang Haijie
# Email : huanghaijie@tp-link.com.cn
# Create time: 2018/7/31 9:05
import wx
import wx.grid
import logging
import my_logging
import wcdma_throughput


class AutoTestUI(wx.Frame):
    """
    AutoTest UI thread inherited form wx.Frame
    """

    def __init__(self, *args, **kw):
        """
        Call the parent's init
        """
        super(AutoTestUI, self).__init__(*args, **kw)
        self.Center()
        self.my_logging = my_logging.MyLogging()
        self.logger = self.my_logging.get_logger()
        # self.panel = wx.Panel(self)

        self.title_text = wx.StaticText(self, - 1, label="WCDMA吞吐量测试", style=wx.ALIGN_CENTER)
        font = self.title_text.GetFont()
        font.PointSize += 5
        font = font.Bold()
        self.title_text.SetFont(font)

        self.band_text = wx.StaticText(self, -1, label="选择频段")
        self.bands = [
            [1, [10563, 10700, 10837]],  # band1
            [2, [9663, 9800, 9937]],  # band2
            [3, [1163, 1337, 1512]],  # band3
            [4, [1538, 1675, 1737]],  # band4
            [5, [4358, 4400, 4457]],  # band5
            [8, [2938, 3013, 3087]]  # band8
        ]
        self.test_list = ['band1', 'band2', 'band3', 'band4', 'band5', 'band8']
        self.list_box = wx.ListBox(self, -1, (140, 50), (80, 120), self.test_list, wx.LB_MULTIPLE)
        self.list_box.SetSelection(0)
        self.list_box.SetSelection(4)
        self.list_box.SetSelection(5)

        self.cable_loss_text = wx.StaticText(self, -1, label="设置衰减")
        # self.freq1 = wx.StaticText(self, -1, label="频点")
        # self.att1 = wx.StaticText(self, -1, label="衰减")
        # self.freq2 = wx.StaticText(self, -1, label="频点")
        # self.att2 = wx.StaticText(self, -1, label="衰减")
        #
        # self.freq_en_1 = wx.TextCtrl(self, -1, value="800.0")
        # self.att_en_1 = wx.TextCtrl(self, -1, value="-0.50")
        # self.freq_en_2 = wx.TextCtrl(self, -1, value="1800.0")
        # self.att_en_2 = wx.TextCtrl(self, -1, value="-0.80")

        self.cable_loss_grid = wx.grid.Grid(self, -1)
        self.cable_loss_grid.CreateGrid(2, 2)
        self.cable_loss_grid.SetCellValue(0, 0, '800.0')
        self.cable_loss_grid.SetCellValue(1, 0, '1800.0')
        self.cable_loss_grid.SetCellValue(0, 1, '-0.5')
        self.cable_loss_grid.SetCellValue(1, 1, '-0.8')
        self.cable_loss_grid.SetColLabelValue(0, '频率/MHz')
        self.cable_loss_grid.SetColLabelValue(1, '衰减/dB')
        self.cable_loss_grid.HideRowLabels()

        self.begin_test_button = wx.Button(self, -1, label="开始测试")
        self.Bind(wx.EVT_BUTTON, self.on_begin_test, self.begin_test_button)

        self.output_text = wx.TextCtrl(self, -1, value="Output log...\n", style=wx.TE_READONLY | wx.TE_MULTILINE)

        box = wx.BoxSizer(wx.VERTICAL)

        box.Add(self.title_text, 0, wx.ALIGN_CENTER)
        parameter_box = wx.BoxSizer(wx.HORIZONTAL)
        parameter_box.Add(self.band_text, flag=wx.ALL, border=2)
        parameter_box.Add(self.list_box, 1, flag=wx.ALL, border=2)
        parameter_box.Add(self.cable_loss_text, flag=wx.ALL, border=2)
        parameter_box.Add(self.cable_loss_grid, 1, flag=wx.ALL, border=2)
        box.Add(parameter_box, flag=wx.ALL, border=15)

        # para_box = wx.BoxSizer(wx.HORIZONTAL)

        # para_box.Add(self.cable_loss_text)
        # para_box.Add(self.cable_loss_grid)
        # loss_text_box = wx.BoxSizer(wx.VERTICAL)
        # loss_text_box.Add(self.freq1, 1, wx.EXPAND)
        # loss_text_box.Add(self.att1, 1, wx.EXPAND)
        # loss_text_box.Add(self.freq2, 1, wx.EXPAND)
        # loss_text_box.Add(self.att2, 1, wx.EXPAND)
        # para_box.Add(loss_text_box)

        # loss_en_box = wx.BoxSizer(wx.VERTICAL)
        # loss_en_box.Add(self.freq_en_1, 1)
        # loss_en_box.Add(self.att_en_1, 1)
        # loss_en_box.Add(self.freq_en_2, 1)
        # loss_en_box.Add(self.att_en_2, 1)
        # para_box.Add(loss_en_box)
        # box.Add(para_box)
        box.Add(self.begin_test_button, 0, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        box.Add(self.output_text, 1, wx.EXPAND)

        self.SetSizer(box)
        self.SetAutoLayout(True)
        # box.Fit(self)

        self.make_menu_bar()
        self.CreateStatusBar()
        self.SetStatusText("Ready to work")

    def write(self, str):
        self.output_text.AppendText(str)

    def make_menu_bar(self):
        """
        show the menu items. This method builds a set of menus and binds handlers to be called
        when the menu item is selected.
        :return: null
        """

        fileMenu = wx.Menu()
        # 可不加id 参数
        helloItem = fileMenu.Append(1, "&Hello...\tCtrl-H", "Help string shown in status bar")
        # 增加选项的分割线
        fileMenu.AppendSeparator()
        exitItem = fileMenu.Append(wx.ID_EXIT)
        helpMenu = wx.Menu()
        aboutItem = helpMenu.Append(wx.ID_ABOUT)

        rf_menu = wx.Menu()
        wifi_item = rf_menu.Append(1, "&Wi-Fi")
        bt_item = rf_menu.Append(2, "&BT")
        gps_item = rf_menu.Append(3, "&GPS")
        mobile_net_item = rf_menu.Append(4, "&2/3/4G")

        base_band_menu = wx.Menu()
        sensor_item = base_band_menu.Append(1, "&传感器")
        power_consumption_item = base_band_menu.Append(2, "&功耗")

        reliability_menu = wx.Menu()
        data_analysis_item = reliability_menu.Append(1, "&数据处理")

        specific_menu = wx.Menu()
        tp_item = specific_menu.Append(1, '&TP')
        lcd_item = specific_menu.Append(2, '&LCD')
        audio_item = specific_menu.Append(3, '&Audio')
        camera_item = specific_menu.Append(4, '&Camera')

        # Make the menu bar and add the two menus to it. The '&' defines
        # that the next letter is the "mnemonic" for the menu item. On the
        # platforms that support it those letters are underlined and can be
        # triggered from the keyboard.
        menu_bar = wx.MenuBar()
        menu_bar.Append(fileMenu, "&菜单")
        # menu_bar.Append(rf_menu, "&射频")
        # menu_bar.Append(base_band_menu, "&基带")
        # menu_bar.Append(specific_menu, '&专项')
        # menu_bar.Append(reliability_menu, '&可靠性')
        menu_bar.Append(helpMenu, "&帮助")

        self.SetMenuBar(menu_bar)

        # Finally, associate a handler function with the EVT_MENU event for
        # each of the menu items. That means that when that menu item is
        # activated then the associated handler function will be called.
        self.Bind(wx.EVT_MENU, self.OnHello, helloItem)
        self.Bind(wx.EVT_MENU, self.OnExit, exitItem)
        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)

    def OnExit(self, event):
        """
        Close the application
        :param event:
        :return: null
        """
        self.Close(True)

    def OnHello(self, event):
        """
        print message
        :param event:
        :return: null
        """
        wx.MessageBox("welcome to use!")

    def OnAbout(self, event):
        """
        show the About Dialog
        :param event:
        :return: null
        """
        wx.MessageBox("Contact: huanghaijie@tp-link.com.cn",
                      "AutoTest Platform Sample: Ver. 0.1",
                      wx.OK | wx.ICON_INFORMATION)

    def set_cable_loss(self):
        pass

    def on_begin_test(self, event):
        self.begin_test_button.SetLabel("测试中。。")
        self.title_text.SetLabel("测试中。。。")
        list_index = self.list_box.GetSelections()
        test_bands = []
        for index in list_index:
            test_bands.append(self.bands[index])
        self.logger.info("test_bands: %s" % str(test_bands))
        freq1 = self.cable_loss_grid.GetCellValue(0, 0)
        att1 = self.cable_loss_grid.GetCellValue(0, 1)
        freq2 = self.cable_loss_grid.GetCellValue(1, 0)
        att2 = self.cable_loss_grid.GetCellValue(1, 1)
        cable_loss = [(freq1, att1), (freq2, att2)]
        self.logger.info("cable loss: %s" % str(cable_loss))

        try:
            # test_case.case_all_downlink()
            # test_case.case_all_uplink()
            # 实例化线程并立即调用run()方法
            wcdma_throughput.WcdmaThroughput(test_bands, cable_loss)
            # test_case.run_all()
            event.GetEventObject().Disable()
        except Exception, e:
            # self.logger.error(str(Exception))
            self.logger.error(e)
            self.logger.error("请检查仪器及GPIB连接！")
            # self.my_logging.error("请检查仪器及GPIB连接")
            self.title_text.SetLabel("测试错误！")


if __name__ == '__main__':
    # 当该模块被运行（而不是被导入到其他模块）时，该部分会执行，运行相关框架，执行事件监听
    app = wx.App()
    frame = AutoTestUI(None, title="WCDMA Throughput", size=(600, 600))
    frame.Show()
    logging.basicConfig(stream=frame)
    app.MainLoop()
