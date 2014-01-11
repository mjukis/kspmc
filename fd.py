#! /usr/bin/python
# coding=UTF-8
#--------------------
# KSP Telemachus
# Mission Control
# By Erik N8MJK
#--------------------

import time
import datetime
import curses
import traceback
import locale
import sys
import os
import pwd
import urllib2
import json
import random

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

def xstr(s):
    if s is None:
        return ''
    return str(s)

def get_datetime():
    #let's make a pretty datetime
    global timeoutput
    global dateoutput
    t = datetime.datetime.now()
    currdatetime = t.timetuple()
    dateoutput = time.strftime("%Y-%m-%d",currdatetime)
    timeoutput = time.strftime("%d %b %Y %H:%M:%S",currdatetime)

def write_datetime(win):
    #separate function since this gets done A LOT
    get_datetime()

    win.move(0,59)
    win.clrtoeol()
    win.addstr(timeoutput, curses.A_REVERSE)
    win.refresh()

def init_window(win):
    win.erase()
    topstring = "FLIGHT DATA"
    bottomstring = "TELEMETRY - RADAR"
    bottomfillstring = (78- len(bottomstring)) * " "
    topfillstring  = (78 - len(topstring)) * " "
    win.addstr(0,0," " + topstring + topfillstring, curses.A_REVERSE)
    win.addstr(23,0,bottomfillstring + bottomstring + " ", curses.A_REVERSE)

def isNum(num):
    try:
        float(num)
        return True
    except ValueError:
        pass
    return False

def rSlop(num):
    if isNum(num):
        nnum = num * random.uniform(0.99,1.01)
        return nnum
    else:
        return num

def rAlt(num):
    if isNum(num):
        nnum = round(int(num),-2)
        return nnum
    else:
        return num

def checkTelemetry():
    check = random.uniform(1,100)
    if check > 95:
        return False
    else:
        return True

def getTelemetry(od):
    maxralt = 700000 #max radar altitude
    minralt = 500 #min radar altitude
    url = "http://108.196.82.116:8023/telemachus/datalink?throt=f.throttle&rcs=v.rcsValue&sas=v.sasValue&light=v.lightValue&pe=o.PeA&ap=o.ApA&ttap=o.timeTo$
    try:
        u = urllib2.urlopen(url)
        d = json.load(u)
    except:
        od["body"] = "ERR"
        od["altt"] = "?"
        return od
    d["asma"] = d["sma"] - 600000
    d["ralt"] = rAlt(rSlop(d["alt"]))
    d["rpe"] = rAlt(rSlop(d["pe"]))
    d["rap"] = rAlt(rSlop(d["ap"]))
    d["rlat"] = d["lat"]
    d["rlong"] = d["long"]
    d["lat"] = rSlop(d["lat"])
    d["long"] = rSlop(d["long"])
    d["altt"] = "?"
    d["rstatus"] = "NOMINAL"
    if isNum(d["vs"]):
        if d["vs"] < 0:
            d["altt"] = "-"
        else:
            d["altt"] = "+"
        if int(d["vs"]) == 0:
            d["altt"] = " "
    if d["body"] != "Kerbin":
        d["ralt"] = "N/A"
        d["rpe"] = "N/A"
        d["rap"] = "N/A"
        d["rlat"] = "N/A"
        d["rlong"] = "N/A"
        d["rstatus"] = "UNAVAIL"
    if d["alt"] > maxralt:
        d["ralt"] = "MAX"
        d["rpe"] = " "
        d["rap"] = " "
        d["rlat"] = " "
        d["rlong"] = " "
        d["rstatus"] = "UNAVAIL"
    if d["alt"] < minralt:
        d["ralt"] = "MIN"
        d["rpe"] = " "
        d["rap"] = " "
        d["rlat"] = " "
        d["rlong"] = " "
        d["rstatus"] = "UNAVAIL"
    if isNum(d["ralt"]):
        if d["ralt"] > 100000:
            if d["ralt"] > 1000000:
                  d["ralt"] = round(d["ralt"], -6)
            d["ralt"] = round(d["ralt"], -3)
        else:
            d["ralt"] = round(d["ralt"], -2)
#list
#       throttle        throt
#       rcs value       rcs
#       sas value       sas
#       lights value    light
#       PE              pe
#       AP              ap
#       time to PE      ttpe
#       time to AP      ttap
#       orbital period  operiod
#       SMA             sma
#       altitude        alt
#       HAT             hat
#       mission time    mt
#       sfc vel         sfcv
#       obt vel         ov
#       vertical speed  vs
#       lat             lat
#       long            long
#       body            body
#       oxygen          o2
#       co2             co2
#       water           h2o
#       watts           w
#       food            food
#       waste           waste
#       wastewater      wastewater
#       "       max     m"
#       pitch deg       pitch
#       roll deg        roll
#       hdg deg         hdg
#
#
    if checkTelemetry():
        return d
    else:
        od["body"] = "ERR!"
        od["altt"] = "?"
        return od

def pnum(num):
    if isNum(num):
        nnum = xstr("{:,}".format(int(num)))
    else:
        nnum = num
    return nnum

def pdeg(inum):
    if isNum(inum):
        num = xstr(abs(int(inum))).zfill(3)
        if inum < 0:
            nnum = "-%s" % num
        else:
            nnum = "+%s" % num
    else:
        nnum = inum
    return nnum

def ptime(num):
    if isNum(num):
        m, s = divmod(num, 60)
        h, m = divmod(m, 60)
        h = str(int(h)).zfill(2)
        m = str(int(m)).zfill(2)
        s = str(int(s)).zfill(2)
        nnum = "%s:%s:%s" % (h,m,s)
    else:
        nnum = num
    return nnum

def palt(num):
    kmlimit = 100000
    mmlimit = 999999000
    if isNum(num):
        if num < kmlimit:
            nnum = xstr("{:,}".format(int(num))) + "m"
        if num >= kmlimit:
            nnum = xstr("{:,}".format(int(num / 1000))) + "km"
        if num >= mmlimit:
            nnum = xstr("{:,}".format(int(num / 1000000))) + "Mm"
    else:
        nnum = num
    return nnum

def plat(inum):
    if isNum(inum):
        num = abs(inum)
        latmin = num - int(num)
        latdeg = num - latmin
        latmin = latmin * 60
        min = xstr(int(latmin)).zfill(2) + "'"
        deg = xstr(int(latdeg)).zfill(3) + " "
        if num < 0:
            nnum = deg + min + "S"
        else:
            nnum = deg + min + "N"
    else:
        nnum = inum
    return nnum

def plong(inum):
    if isNum(inum):
        if inum > 180:
            num = inum - 360
        else:
            num = inum
        longmin = abs(num - int(num))
        longdeg = abs(num - longmin)
        longmin = longmin * 60
        min = xstr(int(longmin)).zfill(2) + "'"
        deg = xstr(int(longdeg)).zfill(3) + " "
        if num < 0:
            nnum = deg + min + "W"
        else:
            nnum = deg + min + "E"
    else:
        nnum = inum
    return nnum

def init_tpos_window(win,y,x):
    twin = curses.newwin(11,18,y,x)
    twin.box()
    twin.bkgd(curses.color_pair(1));
    win.refresh()
    twin.addstr(0,1,"TPOS",curses.A_BOLD)
    twin.addstr(1,1,"  BODY ")
    twin.addstr(2,1,"  TALT ")
    twin.addstr(3,1,"  TLAT ")
    twin.addstr(4,1," TLONG ")
    twin.addstr(5,1,"  TPIT ")
    twin.addstr(6,1,"  TROL ")
    twin.addstr(7,1,"  THDG ")
    twin.addstr(8,1," TT AP ")
    twin.addstr(9,1," TT PE ")
    twin.refresh()
    return twin

def draw_tpos_window(win,data):
    win.addstr(1,8,"         ",curses.A_BOLD)
    win.addstr(2,8,"         ",curses.A_BOLD)
    win.addstr(3,8,"         ",curses.A_BOLD)
    win.addstr(4,8,"         ",curses.A_BOLD)
    win.addstr(5,8,"         ",curses.A_BOLD)
    win.addstr(6,8,"         ",curses.A_BOLD)
    win.addstr(7,8,"         ",curses.A_BOLD)
    win.addstr(8,8,"         ",curses.A_BOLD)
    win.addstr(1,8,pnum(data["body"]).upper(),curses.A_BOLD)
    win.addstr(2,7,pnum(data["altt"]))
    win.addstr(2,8,palt(data["alt"]),curses.A_BOLD)
    win.addstr(3,8,plat(data["lat"]),curses.A_BOLD)
    win.addstr(4,8,plong(data["long"]),curses.A_BOLD)
    win.addstr(5,8,pdeg(data["pitch"]),curses.A_BOLD)
    win.addstr(6,8,pdeg(data["roll"]),curses.A_BOLD)
    win.addstr(7,8,pdeg(data["hdg"]),curses.A_BOLD)
    win.addstr(8,8,ptime(data["ttap"]),curses.A_BOLD)
    win.addstr(9,8,ptime(data["ttpe"]),curses.A_BOLD)
    win.refresh()

def init_rpos_window(win,y,x):
    rwin = curses.newwin(6,18,y,x)
    rwin.box()
    rwin.bkgd(curses.color_pair(1));
    win.refresh()
    rwin.addstr(0,1,"RPOS",curses.A_BOLD)
    rwin.addstr(1,1,"STATUS ")
    rwin.addstr(2,1,"  RALT ")
    rwin.addstr(3,1,"  RLAT ")
    rwin.addstr(4,1," RLONG ")
    rwin.refresh()
    return rwin

def draw_rpos_window(win,data):
    win.addstr(1,8,"         ",curses.A_BOLD)
    win.addstr(2,8,"         ",curses.A_BOLD)
    win.addstr(3,8,"         ",curses.A_BOLD)
    win.addstr(4,8,"         ",curses.A_BOLD)
    win.addstr(1,8,pnum(data["rstatus"]).upper(),curses.A_BOLD)
    win.addstr(2,8,palt(data["ralt"]),curses.A_BOLD)
    win.addstr(3,8,plat(data["rlat"]),curses.A_BOLD)
    win.addstr(4,8,plong(data["rlong"]),curses.A_BOLD)
    win.refresh()

def mainloop(win):
    tposx = 0
    tposy = 4
    rposx = 18
    rposy = 4
    win.nodelay(1)
    init_window(win)
    twin = init_tpos_window(win,tposy,tposx)
    rwin = init_rpos_window(win,rposy,rposx)
    odata = getTelemetry("ERROR")
    while 1 is 1:
        data = getTelemetry(odata)
        odata = data
        write_datetime(win)
        draw_tpos_window(twin,data)
        draw_rpos_window(rwin,data)
        time.sleep(1)

def startup():
    #wrapper to avoid console errors on program bug
    #totally stolen btw
    try:
        # Initialize curses
        stdscr = curses.initscr()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        stdscr.bkgd(curses.color_pair(1));
        stdscr.bkgd(curses.color_pair(1));

        # Turn off echoing of keys, and enter cbreak mode,
        # where no buffering is performed on keyboard input
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(1)

        mainloop(stdscr)                # Enter the main loop

        # Set everything back to normal
        curses.echo()
        curses.nocbreak()
        stdscr.keypad(0)

        curses.endwin()                 # Terminate curses
    except:
        # In event of error, restore terminal to sane state.
        curses.echo()
        curses.nocbreak()
        stdscr.keypad(0)
        curses.endwin()
        traceback.print_exc()           # Print the exception

if __name__=='__main__':
    startup()



