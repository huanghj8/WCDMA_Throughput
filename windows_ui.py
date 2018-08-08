#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C), TP-LINK Technologies Co., Ltd.
# Author: Huang Haijie
# Email : huanghaijie@tp-link.com.cn
# Create time: 2018/7/31 9:05
import wx
import my_logging


class AutoTestUI(wx.Frame):
    """
    AutoTest UI thread inherited form wx.Frame
    """

    def __init__(self, *args, **kw):
        """
        Call the parent's init
        """
        super(AutoTestUI, self).__init__(*args, **kw)
        self.my_logging = my_logging.MyLogging()
        self.logger = self.my_logging.get_logger()

        self.title_text = wx.StaticText(self, -1, label="WCDMA吞吐量测试")
        font = self.title_text.GetFont()
        font.PointSize += 5
        font = font.Bold()
        self.title_text.SetFont(font)

        self.output_text = wx.TextCtrl(self, -1, value="Output log...\n", style=wx.TE_READONLY | wx.TE_MULTILINE)

        self.band_text = wx.StaticText(self, -1, label="选择频段")
        self.cable_loss_text = wx.StaticText(self, -1, label="设置衰减")

        # text_control = wx.TextCtrl(self.input_panel, style=wx.TE_MULTILINE)
        self.begin_test_button = wx.Button(self, -1, label="开始测试")
        self.Bind(wx.EVT_BUTTON, self.on_begin_test, self.begin_test_button)

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

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.title_text)
        box.Add(self.band_text, wx.ALIGN_CENTER_HORIZONTAL)
        box.Add(self.list_box, wx.ALIGN_CENTER_VERTICAL)
        box.Add(self.cable_loss_text, wx.ALIGN_CENTER_VERTICAL)
        box.Add(self.begin_test_button, wx.ALIGN_CENTER_VERTICAL)
        box.Add(self.output_text, wx.GROW)

        self.SetSizer(box)
        self.SetAutoLayout(True)
        # box.Fit(self)

        self.make_menu_bar()
        self.CreateStatusBar()
        self.SetStatusText("Ready to work")

    def configure_input_panel(self):
        pass

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
        menu_bar.Append(rf_menu, "&射频")
        menu_bar.Append(base_band_menu, "&基带")
        menu_bar.Append(specific_menu, '&专项')
        menu_bar.Append(reliability_menu, '&可靠性')
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
        print test_bands
        self.logger.info("test_bands: %s" % str(test_bands))
        import wcdma_throughput
        test_case = wcdma_throughput.WcdmaThroughput(test_bands)
        try:
            test_case.case_all_downlink()
            test_case.case_all_uplink()
        except Exception, e:
            self.logger.error(str(Exception))
            self.logger.error(e)
            self.logger.error("请检查仪器及GPIB连接！")


if __name__ == '__main__':
    # 当该模块被运行（而不是被导入到其他模块）时，该部分会执行，运行相关框架，执行事件监听
    app = wx.App()
    frame = AutoTestUI(None, title="AutoTest Platform")
    frame.Show()
    app.MainLoop()
