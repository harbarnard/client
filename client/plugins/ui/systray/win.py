#!/usr/bin/env python
# encoding: utf-8
"""Copyright (C) 2013 COLDWELL AG

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import os

from functools import partial
from gevent import threadpool

import win32gui, win32con
import glob
from PIL import IcnsImagePlugin, BmpImagePlugin # preload for py2exe
from PIL import Image

from .... import settings, event, login, localize
from ....contrib.systrayicon import SysTrayIcon

from .common import open_browser, relogin, quit

_X = localize.X

def menu_color():
    return win32gui.GetSysColor(win32con.COLOR_MENU)
    
def create_icon(name, inputpath, width, height, bgcolor):
    path = os.path.join(settings.menuiconfolder, "{}_{}_{}_{}.bmp".format(name, width, height, bgcolor))
    if os.path.exists(path):
        return path
    source = Image.open(inputpath)
    source.thumbnail((width, height), Image.ANTIALIAS)
    r, g, b, alpha = source.split()
    new = Image.new(source.mode, source.size, bgcolor)
    new.paste(source, mask=alpha)
    new.convert("RGB").save(path, "BMP")
    return path
    
def bmp_factory(name, path=None):
    if path is None:
        path = os.path.join(settings.menuiconfolder, '{}.icns'.format(name))
        if not os.path.exists(path):
            raise RuntimeError("Loading of icon for action '{}' failed".format(name))
    return partial(create_icon, name, path)

def init():
    icons = glob.glob(os.path.join(settings.menuiconfolder, "*.icns"))
    for i in icons:
        name = os.path.basename(i)
        name = name[:name.rfind(".")]
    
    @login.config.register('username')
    def update_username():
        #options[0] = (login.config.username or _X("Open"), bmp_factory('open'), lambda _: event.call_from_thread(open_browser))
        options[0] = (_X("Open"), bmp_factory('open'), lambda _: event.call_from_thread(open_browser))

    thread = threadpool.ThreadPool(1)
    options = [
        None,
        (_X("Logout"), bmp_factory('logout'), lambda _: event.call_from_thread(relogin, _)),
        (_X("Quit"), bmp_factory('quit'), 'QUIT')
    ]

    update_username()
    
    icon = settings.mainicon
    if not icon:
        return

    thread.spawn(SysTrayIcon, icon, "Download.am Client", options, lambda _: event.call_from_thread(quit), 0, "download.am")