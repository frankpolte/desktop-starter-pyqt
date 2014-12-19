#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  This file is part of Webkit App Bar.
#
#  Copyright 2011-2013 xDaks <http://xdaks.deviantart.com/>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

import sys, os, urllib, string, stat
from PyQt4 import QtCore, QtGui, QtWebKit
from PyQt4.QtCore import Qt, QUrl
from PyQt4.QtGui import QApplication, QPalette
from subprocess import Popen

# -------------------------------------------------------------------- #
# globals
# -------------------------------------------------------------------- #
appName = 'webkitAppBar'
updateTriggerFile = '/var/lock/appbar.refresh'
appPath = os.path.dirname(os.path.realpath( __file__ ))
appWorkDir = ''
#appWorkDir = 'DANews'
#appWorkDir = 'weather'
#appWorkDir = 'logout'
#appWorkDir = 'searchbar'
#appWorkDir = 'mail'
#appWorkDir = 'autohide'
#appWorkDir = 'appbar'
#appWorkDir = 'empty'
appFile = os.path.join(appWorkDir, 'index.html')
defaultSite = os.path.join(appPath, appFile)

class Browser:
    # ---------------------------------------------------------------- #
    # events - BEGIN
    # ---------------------------------------------------------------- #

    def _readLastNewsSeen(self):
        lastNewsSeen = "0"
        try:
            with open(os.path.expanduser('~') + '/.news', 'r') as f:
                lastNewsSeen = f.readline()
                f.close()
        except:
            lastNewsSeen = "0";
        self.lastNewsSeen = int(lastNewsSeen)
        return lastNewsSeen

    def _saveLastNewsSeen(self, date):
        with open(os.path.expanduser('~') + '/.news', 'w+') as f:
            f.write("%d\n"% (date))
            f.close()

    # event -  onLinkCliked
    def _on_navigation(self, url):
        url = str(url.toString().toUtf8())
        if self.on_command(url):
            return True
        else:
            #self.web_view.load(QUrl(url))
            return False

    # event -  onCompletePageLoading
    def _on_pageLoaded(self, ok):
        try:
            self.pageConfig = self.getConfig()
            l, t, w, h = self.getBarDimension()
            print(l, t, w, h)

            #test
            #self.web_view.setGeometry(0, 0, w, h)
            #self.web_view.setFixedSize(w, h);
            #self.web_view.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

            self.window.setGeometry(l, t, w, h)
            self.web_view.page().mainFrame().evaluateJavaScript("lastNewsSeen = %d;" % (int(self._readLastNewsSeen())))
        except:
            raise

        self.getDefaultApps()
        self.initPlugins()
        self.window.show()

    # event - timer onTimeout
    def _on_autoRefresh(self):
        # monitor updates
        if not os.path.isfile(updateTriggerFile):
            self.web_view.reload()
            open(updateTriggerFile, 'a').close()
            os.chmod(updateTriggerFile, 0666)
        if self.resolution != QtGui.QDesktopWidget().screenGeometry():
            self.web_view.reload()
            self.resolution = QtGui.QDesktopWidget().screenGeometry()
        # save date of last seen news
        lastNewsSeen = self.getVar(self.web_view, 'lastNewsSeen')
        if (lastNewsSeen > self.lastNewsSeen):
            self.lastNewsSeen = lastNewsSeen
            self._saveLastNewsSeen(int(lastNewsSeen))


    # ---------------------------------------------------------------- #
    # events - END
    # ---------------------------------------------------------------- #

    def setAutoRefresh(self, interval):
        if self.timer == None:
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self._on_autoRefresh)
            self.timer.start(interval * 1000)

    def initPlugins(self):
        import plugins
        plugins.init(self)
        return
        try:
            import plugins
            try:
                plugins.init(self)
            except:
                print('plugins init error')
        except:
            pass

    def getConfig(self):
        # convert - Qt types to  Python types
        result = {}
        cfg = self.getVar(self.web_view, 'config')
        if cfg is not None:
            for key in cfg:
                Val = cfg[key]
                if type(Val) == QtCore.QString:
                    Val = str(Val)
                result[str(key)] = Val
        return result

    def getDefaultApps(self):
        self.defaultBrowser = ''
        if 'defaultBrowser' in self.pageConfig:
            self.defaultBrowser = self.pageConfig['defaultBrowser']
        self.defaultFileManager = ''
        if 'defaultFileManager' in self.pageConfig:
            self.defaultFileManager = self.pageConfig['defaultFileManager']

    def normalizeCmd(self, cmd):
        cmd = cmd.replace('cmd::', '')
        cmd = urllib.unquote_plus(cmd)
        cmd = os.path.expandvars(cmd)
        if 'defaultBrowser' in cmd:
            cmd = cmd.replace('defaultBrowser', self.defaultBrowser)
        if 'defaultFileManager' in cmd:
            cmd = cmd.replace('defaultFileManager', self.defaultFileManager)

        return cmd

    def on_command(self, cmd):
        if cmd.startswith('cmd::'):
            cmd = self.normalizeCmd(cmd)
            print(cmd)

            if (cmd == 'exit'):
                sys.exit()
            elif (cmd == 'refresh'):
                self.web_view.reload()
            else:
                Popen(cmd, shell=True)

            return True
        else:
            return False

    def getVar(self, web_view, varName):
        try:
            return web_view.page().mainFrame().evaluateJavaScript(varName).toPyObject()
        except:
            pass

    def getBarDimension(self):
        top = self.pageConfig.get('Top', 0)
        left = self.pageConfig.get('Left', 0)
        width = self.pageConfig.get('Width', 0)
        height = self.pageConfig.get('Height', 0)
        return int(left), int(top), int(width), int(height)

    def getDesktop(self):
        try:
            curDesktop = os.environ['XDG_CURRENT_DESKTOP']
        except:
            curDesktop = ''

        try:
            wmName = os.environ['DESKTOP_SESSION']
        except:
            wmName = ''

        return curDesktop.lower() if curDesktop != '' else wmName.lower()

    def __init__(self):
        self.app = QtGui.QApplication(sys.argv)

        print(defaultSite)
        self.default_site = defaultSite
        self.appWorkDir = appWorkDir

        self.window = QtGui.QMainWindow()
        self.timer = None
        self.lastNewsSeen = 0
        # ------------------------------------------------------------ #
        desktop = self.getDesktop()
        print(desktop)

        # windowAttribute for openbox/pekwm WM
        if desktop in ['openbox', 'pekwm']:
            self.window.setAttribute(Qt.WA_X11NetWmWindowTypeDesktop)
        # windowAttribute for any other DE like xfce, gnome, unity ...
        else:
            self.window.setAttribute(Qt.WA_X11NetWmWindowTypeDock)
            self.window.setWindowFlags(Qt.WindowStaysOnBottomHint)

        self.window.setAttribute(Qt.WA_TranslucentBackground)
        # ------------------------------------------------------------ #

        self.web_view = QtWebKit.QWebView()
        self.web_view.setAttribute(Qt.WA_AcceptTouchEvents, False)

        # trasparent webview
        palette = self.web_view.palette()
        palette.setBrush(QPalette.Base, Qt.transparent)
        self.web_view.page().setPalette(palette)
        self.web_view.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateAllLinks)
        self.web_view.loadFinished.connect(self._on_pageLoaded)
        self.web_view.linkClicked.connect(self._on_navigation)

        self.window.setCentralWidget(self.web_view)
        self.web_view.load(QUrl(self.default_site))

        self.qr = self.window.frameGeometry()
        self.cp = QtGui.QDesktopWidget().availableGeometry().center()
        self.qr.moveCenter(self.cp)
        #self.window.setCentralWidget(self.web_view)

        # get resolution
        self.resolution = QtGui.QDesktopWidget().screenGeometry()


    def main(self):
        sys.exit(self.app.exec_())

def readCmdLine():
    if len(sys.argv) > 1:
        try:
            DirName = sys.argv[1]

            FileName = ''
            fName = os.path.join(appPath, DirName, appFile)
            if os.path.isfile(fName):
                FileName = fName

            #print(FileName)
            if FileName <> '':
                global defaultSite
                defaultSite = FileName

            if DirName != None:
                global appWorkDir
                appWorkDir = DirName

        except:
            print('read html source file error')
    else:
        print('no source file...')

readCmdLine()
browser = Browser()
browser.setAutoRefresh(1)
browser.main()