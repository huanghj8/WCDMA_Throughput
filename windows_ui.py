#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C), TP-LINK Technologies Co., Ltd.
# Author: Huang Haijie
# Email : huanghaijie@tp-link.com.cn
# Create time: 2018/7/31 9:05
import wx
import wx.grid
import logging
import os

import my_logging
import wcdma_throughput


class TestUI(wx.Frame):
    """
    测试UI类
    """

    def __init__(self, *args, **kw):
        """
        初始化并调用父类init方法
        :param args: None
        :param kw: None
        """
        super(TestUI, self).__init__(*args, **kw)
        self.Center()
        self.my_logging = my_logging.MyLogging()
        self.logger = self.my_logging.get_logger()
        # 标题
        self.title_text = wx.StaticText(self, - 1, label="WCDMA吞吐量测试", style=wx.ALIGN_CENTER)
        font = self.title_text.GetFont()
        font.PointSize += 5
        font = font.Bold()
        self.title_text.SetFont(font)
        # 测试频段
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
        # 默认选中A版支持频段
        self.list_box.SetSelection(0)
        self.list_box.SetSelection(4)
        self.list_box.SetSelection(5)
        # 衰减设置
        self.cable_loss_text = wx.StaticText(self, -1, label="设置衰减")

        self.cable_loss_grid = wx.grid.Grid(self, -1)
        self.cable_loss_grid.CreateGrid(2, 2)
        self.cable_loss_grid.SetCellValue(0, 0, '800.0')
        self.cable_loss_grid.SetCellValue(1, 0, '1800.0')
        self.cable_loss_grid.SetCellValue(0, 1, '-0.5')
        self.cable_loss_grid.SetCellValue(1, 1, '-0.8')
        self.cable_loss_grid.SetColLabelValue(0, '频率/MHz')
        self.cable_loss_grid.SetColLabelValue(1, '衰减/dB')
        self.cable_loss_grid.HideRowLabels()
        # 芯片
        self.chip_list = ['MTK', 'QUALCOMM']
        self.chip_box = wx.RadioBox(self, -1, '芯片平台', pos=(0, 0),
                                    choices=self.chip_list, style=wx.RA_SPECIFY_COLS)
        self.chip_box.Bind(wx.EVT_RADIOBOX, self.on_select_chip)

        self.downlink_speed = ['42M', '21M']
        self.dl_sp_box = wx.RadioBox(self, -1, '下行速率', pos=(0, 0),
                                     choices=self.downlink_speed, style=wx.RA_SPECIFY_COLS)
        self.dl_sp_box.Bind(wx.EVT_RADIOBOX, self.on_select_down_speed)

        self.uplink_speed = ['11.4M', '5.7M']
        self.ul_sp_box = wx.RadioBox(self, -1, '上行速率', pos=(0, 0),
                                     choices=self.uplink_speed, style=wx.RA_SPECIFY_COLS)
        self.ul_sp_box.Bind(wx.EVT_RADIOBOX, self.on_select_up_speed)

        self.begin_test_button = wx.Button(self, -1, label="开始测试")
        self.Bind(wx.EVT_BUTTON, self.on_begin_test, self.begin_test_button)

        self.output_text = wx.TextCtrl(self, -1, value="Output log...\n", style=wx.TE_READONLY | wx.TE_MULTILINE)

        box = wx.BoxSizer(wx.VERTICAL)

        box.Add(self.title_text, 0, wx.ALIGN_CENTER)
        # 参数框
        parameter_box = wx.BoxSizer(wx.HORIZONTAL)
        parameter_box.Add(self.band_text, flag=wx.ALL, border=2)
        parameter_box.Add(self.list_box, 1, flag=wx.ALL, border=2)
        parameter_box.Add(self.cable_loss_text, flag=wx.ALL, border=2)
        parameter_box.Add(self.cable_loss_grid, 1, flag=wx.ALL, border=2)
        # 速率框
        speed_box = wx.BoxSizer(wx.VERTICAL)
        speed_box.Add(self.chip_box)
        speed_box.Add(self.dl_sp_box)
        speed_box.Add(self.ul_sp_box)

        parameter_box.Add(speed_box, 1, flag=wx.ALL, border=2)

        box.Add(parameter_box, flag=wx.ALL, border=15)
        # 开始按钮
        box.Add(self.begin_test_button, 0, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        # 输出日志框
        box.Add(self.output_text, 1, wx.EXPAND)

        self.SetSizer(box)
        self.SetAutoLayout(True)

        self.make_menu_bar()
        self.CreateStatusBar()
        self.SetStatusText("Ready to work")

    def write(self, string):
        """
        通过重定向Stream到frame的output_text后，输出handler会调用该write方法，在该UI类中没有显式调用
        :param string: 输出日志参数
        :return: None
        """
        self.output_text.AppendText(string)

    def make_menu_bar(self):
        """
        生成菜单栏
        :return: None
        """
        file_menu = wx.Menu()
        # 可不加id 参数
        file_item = file_menu.Append(1, "&File...\tCtrl-H", "Open result File")
        # 增加选项的分割线
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT)
        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT)

        menu_bar = wx.MenuBar()
        menu_bar.Append(file_menu, "&菜单")
        menu_bar.Append(help_menu, "&帮助")

        self.SetMenuBar(menu_bar)

        # 通过EVT_MENU事件触发Handler方法，调用相关方法.
        self.Bind(wx.EVT_MENU, self.on_file, file_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)

    def on_exit(self, event):
        """
        关闭应用
        :param event:点击事件
        :return: None
        """
        self.Close(True)

    def on_file(self, event):
        """
        打开结果目录
        :param event:点击事件
        :return: None
        """
        path = os.getcwd()
        os.system('start explorer %s\\result' % path)

    def on_about(self, event):
        """
        打开‘关于’对话框
        :param event:点击事件
        :return: None
        """
        wx.MessageBox("Contact: huanghaijie@tp-link.com.cn",
                      "AutoTest Platform Sample: Ver. 0.1",
                      wx.OK | wx.ICON_INFORMATION)

    def on_select_chip(self, event):
        """
        选中芯片后的事件
        :param event: 点击事件
        :return: None
        """
        self.logger.info("The chipset is: %s" % self.chip_box.GetStringSelection())

    def on_select_down_speed(self, event):
        """
        选中速率后的事件
        :param event: 点击事件
        :return: None
        """
        self.logger.info('Downlink speed is: %s' % self.dl_sp_box.GetStringSelection())

    def on_select_up_speed(self, event):
        """
        选中速率后的事件
        :param event: 点击事件
        :return: None
        """
        self.logger.info('Uplink speed is: %s' % self.ul_sp_box.GetStringSelection())

    def on_begin_test(self, event):
        """
        开始测试后的处理逻辑，将测试频段、衰减值、传输速率、芯片平台等参数传入实例化类，同时更新UI
        :param event: 按钮点击事件
        :return: None
        """
        self.begin_test_button.SetLabel("测试中。。")
        self.title_text.SetLabel("测试中。。。")
        list_index = self.list_box.GetSelections()
        # 更新测试频段
        test_bands = []
        for index in list_index:
            test_bands.append(self.bands[index])
        self.logger.info("test_bands: %s" % str(test_bands))
        # 更新衰减档,频率值保留一位小数，衰减值保留两位，否则8960无法识别会报错
        freq1 = '%.1f' % float(self.cable_loss_grid.GetCellValue(0, 0))
        att1 = '%.2f' % float(self.cable_loss_grid.GetCellValue(0, 1))
        freq2 = '%.1f' % float(self.cable_loss_grid.GetCellValue(1, 0))
        att2 = '%.2f' % float(self.cable_loss_grid.GetCellValue(1, 1))
        cable_loss = [(freq1, att1), (freq2, att2)]
        self.logger.info("cable loss: %s" % str(cable_loss))
        # 更新芯片平台
        chip_set = self.chip_box.GetStringSelection()
        self.logger.info("The chipset is: %s" % chip_set)
        # 更新速率
        downlink_speed = self.dl_sp_box.GetStringSelection()
        self.logger.info("Downlink Speed is: %s" % downlink_speed)
        uplink_speed = self.ul_sp_box.GetStringSelection()
        self.logger.info("Uplink Speed is: %s" % uplink_speed)

        try:
            # 实例化线程并立即调用run()方法
            wcdma_throughput.WcdmaThroughput(test_bands, cable_loss, chip_set, downlink_speed, uplink_speed)
            event.GetEventObject().Disable()
        except Exception, e:
            self.logger.error(e)
            self.logger.error("请检查仪器及GPIB连接！")
            self.title_text.SetLabel("测试错误！")


if __name__ == '__main__':
    # 当该模块被运行（而不是被导入到其他模块）时，该部分会执行，运行UI框架
    app = wx.App()
    frame = TestUI(None, title="WCDMA Throughput", size=(620, 600))
    frame.Show()
    logging.basicConfig(stream=frame)
    app.MainLoop()
