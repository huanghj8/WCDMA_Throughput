#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C), TP-LINK Technologies Co., Ltd.
# Author: Huang Haijie
# Email : huanghaijie@tp-link.com.cn
# Create time: 2018/8/9 17:50
import logging
import wx


class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title)
        self.textctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        wx.CallAfter(self.dologging)
        self.Show()

    def write(self, s):
        self.textctrl.AppendText(s)

    def dologging(self):
        print 'do logging...'
        logging.warning('This message should go to my wxTextCtrl...')
        wx.CallLater(3000, self.dologging)


app = wx.App(False)
frame = MyFrame(None, 'logging demo')
logging.basicConfig(stream=frame)
app.MainLoop()