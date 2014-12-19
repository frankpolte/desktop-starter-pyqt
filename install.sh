#!/bin/sh

export INSTALLPATH=/opt/desktop-starter

mkdir -pv $INSTALLPATH
cp -v desktop-starter.sh plugins.py  plugins.pyc  qBrowser.py  qBrowser.pyc  README $INSTALLPATH
