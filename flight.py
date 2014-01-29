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
import pika
import marshal

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
global olddata
olddata = {"alt":"0","pe":"0"}

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

def checkTelemetry(pstat):
    if pstat == 0:
        return True
    else:
        return False

def badtele(olddata):
    d = olddata
#        d["throt"] = " "	#Throttle
#        d["rcs"] = " "		#RCS status
#        d["sas"] = " "		#SAS status
#        d["light"] = " "	#Lights status
#        d["pe"] = " "		#PE
#        d["ap"] = " "		#AP
#        d["ttap"] = " "		#Time to AP
#        d["ttpe"] = " "		#Time to PE
#        d["operiod"] = " "	#Orbital period
#        d["sma"] = " "		#SMA
    d["alt"] = "ERR!"		#Altitude
#        d["hat"] = " "		#Height above terrain
#        d["mt"] = " "		#Mission time
#        d["ut"] = " "		#Universal time
#        d["sfcv"] = " "		#SFC velocity
#        d["ov"] = " "		#Orbital velocity
#        d["vs"] = " "		#Vertical speed
#        d["lat"] = " "		#Latitude
#        d["long"] = " "		#Longitude
#        d["body"] = " "		#Orbital body
#        d["o2"] = " "		#Oxygen
#        d["co2"] = " "		#Carbon dioxide
#        d["h2o"] = " "		#Water
#        d["w"] = " "		#Electric charge
#        d["food"] = " "		#Food
#        d["waste"] = " "	#Solid waste
#        d["wastewater"] = " "	#Liquid waste
#        d["mo2"] = " "		#Max oxygen
#        d["mco2"] = " "		#Max carbon dioxide
#        d["mh2o"] = " "		#Max water
#        d["mw"] = " "		#Max electric charge
#        d["mfood"] = " "	#Max food
#        d["mwaste"] = " "	#Max solid waste
#        d["mwastewater"] = " "	#Max liquid waste
    d["pitch"] = " "	#Pitch degrees
    d["roll"] = " "		#Roll degrees
    d["hdg"] = " "		#Heading degrees
#        d["pstat"] = "1"	#Telemetry status
#        d["inc"] = " "		#Inclination
#        d["ecc"] = " "		#Eccentricity
#        d["aope"] = " "		#Argument of PE
#        d["lan"] = " "		Longitude of AN
#        d["lf"] = " "		#Liquid Fuel
#        d["oxidizer"] = " "	#Oxidizer
#        d["mlf"] = " "		#Max liquid fuel
#        d["moxidizer"] = " "	#Max oxidizer
    d["tstatus"] = 0
    return d

def getRadar(d):
    maxralt = 7000000 #max radar altitude
    minralt = 500 #min radar altitude
    d["ralt"] = rAlt(rSlop(d["alt"]))
    d["rpe"] = rAlt(rSlop(d["pe"]))
    if isNum(d["rpe"]) and d["rpe"] < 0:
        d["rpe"] = 0
    d["rap"] = rAlt(rSlop(d["ap"]))
    if isNum(d["sma"]):
        d["smag"] = rAlt(rSlop(d["sma"]))
    else:
        d["smag"] = "ERR!"
    if d["smag"] < 0:
        d["smag"] = 0
    d["rlat"] = d["lat"]
    d["rlong"] = d["long"]
    d["rttap"] = d["ttap"]
    d["rttpe"] = d["ttpe"]
    d["rsfcs"] = d["sfcs"]
    if isNum(d["vs"]):
       d["rhs"] = d["sfcs"] - abs(d["vs"])
    else:
       d["rhs"] = " "
    d["rvs"] = d["vs"]
    d["rinc"] = d["inc"]
    d["rlan"] = d["lan"]
    d["roperiod"] = d["operiod"]
    d["rov"] = d["ov"]
    d["rstatus"] = "NOMINAL"
#    d["rstatus"] = d["tstatus"]
    if d["body"] != "Kerbin":
        d["ralt"] = "N/A"
        d["rpe"] = " "
        d["rap"] = " "
        d["rttpe"] = " "
        d["rttap"] = " "
        d["rlat"] = " "
        d["rlong"] = " "
        d["smag"] = "N/A"
        d["rinc"] = " "
        d["rlan"] = " "
        d["roperiod"] = " "
        d["rov"] = " "
        d["rhs"] = " "
        d["rvs"] = " "
        d["rsfcs"] = " "
        d["rstatus"] = "UNAVAIL"
    if d["alt"] > maxralt:
        d["ralt"] = "MAX"
        d["rpe"] = " "
        d["rap"] = " "
        d["rttpe"] = " "
        d["rttap"] = " "
        d["rlat"] = " "
        d["rlong"] = " "
        d["smag"] = "MAX"
        d["rinc"] = " "
        d["rlan"] = " "
        d["roperiod"] = " "
        d["rov"] = " "
        d["rhs"] = " "
        d["rvs"] = " "
        d["rsfcs"] = " "
        d["rstatus"] = "UNAVAIL"
    if d["alt"] < minralt:
        d["ralt"] = "MIN"
        d["rpe"] = " "
        d["rap"] = " "
        d["rttpe"] = " "
        d["rttap"] = " "
        d["rlat"] = " "
        d["rlong"] = " "
        d["smag"] = "MIN"
        d["rinc"] = " "
        d["rlan"] = " "
        d["roperiod"] = " "
        d["rov"] = " "
        d["rhs"] = " "
        d["rvs"] = " "
        d["rsfcs"] = " "
        d["rstatus"] = "UNAVAIL"    
    if isNum(d["ralt"]):
        if d["ralt"] > 100000:
            if d["ralt"] > 1000000:
                  d["ralt"] = round(d["ralt"], -6)
            d["ralt"] = round(d["ralt"], -3)
        else:
            d["ralt"] = round(d["ralt"], -2)
    return d

def getTelemetry(d):
    maxgralt = "15000" #max altitude for ground radar
    if isNum(d["pe"]) and d["pe"] < 0:
        d["pe"] = 0
    d["lat"] = rSlop(d["lat"])
    d["long"] = rSlop(d["long"])
    d["altt"] = "?"
    if isNum(d["vs"]):
        if d["vs"] < 0:
            d["altt"] = "-"
        else:
            d["altt"] = "+"
        if int(d["vs"]) == 0:
            d["altt"] = " "
        if isNum(d["vs"]):
            d["hs"] = d["sfcs"] - abs(d["vs"])
            d["vs"] = abs(d["vs"])
        else:
            d["hs"] = " "
    d["asl"] = d["alt"]
    if isNum(d["asl"]):
        if d["hat"] == -1 or d["hat"] > maxgralt:
            d["grstatus"] = "UNAVAIL"
            d["hat"] = "MAX"
            d["asl"] = " "
            d["vs"] = " "
            d["hs"] = " "
            d["sfcv"] = " "
            d["sfcvx"] = " "
            d["sfcvy"] = " "
            d["sfcvz"] = " "
        else:
            d["grstatus"] = "NOMINAL"
    if checkTelemetry(d["pstat"]):
        return d
    else:
        d = badtele(olddata)
#        d["alt"] = "ERR!"
#        d["altt"] = "?"
#        d["pitch"] = "0"
#        d["roll"] = "0"
#        d["hdg"] = "0"
        d["grstatus"] = "UNAVAIL"
        d["sma"] = "ERR!"
        return d

def pnum(num):
    if isNum(num):
        nnum = xstr("{:,}".format(int(num)))
    else:
        nnum = num
    return nnum

def pvel(num):
    if isNum(num):
        nnum = xstr("{:,}".format(int(num))) + "m/s"
    else:
        nnum = num
    return nnum

def phbar(num,mnum):
    if isNum(num) and isNum(mnum):
        pnum = int((num / mnum) * 100)
        onum = xstr(" " + "{:,}".format(int(num))) + " (" + xstr(pnum) + "%)"
    else:
        onum = num
    return onum

def printwarn(win,warn,state):
    if state == 0:
        win.addstr(1,1,warn,curses.A_BOLD)
    else:
        win.addstr(1,1,warn,curses.A_BLINK + curses.A_REVERSE)

def printhbar(win,instr,perc):
    i = 0
    barperc = int(35 * perc)
    barstring = instr.ljust(35)
    while i < 35:
        if i < barperc:
            win.addstr(barstring[i],curses.A_REVERSE)
        else:
            win.addstr(barstring[i])
        i = i + 1

def printvbar(win,perc):
    i = 0
    output = format(xstr(int(perc * 100)),">3s")
    barperc = int(9 * perc)
    while i < 9:
        if i < barperc:
            win.addstr(9-i,1,output,curses.A_REVERSE)
        else:
            win.addstr(9-i,1,output)
        i = i + 1
        output = "   "

def printvdef(win,perc):
    i = 0
    output = format(xstr(int(perc * 100)),">3s")
    barperc = int(9 * perc)
    while i < 9:
        if i < barperc:
            win.addstr(9-i,1,output,curses.A_REVERSE)
        else:
            win.addstr(9-i,1,output)
        i = i + 1
        output = "   "
   
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

def pltime(num):
    if isNum(num):
        m, s = divmod(num, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 6)
        d = xstr(int(d)).zfill(2)
        h = xstr(int(h)).zfill(2)
        m = xstr(int(m)).zfill(2)
        s = xstr(int(s)).zfill(2)
        nnum = "%sd %s:%s:%s" % (d,h,m,s)
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

def init_time_window(win,y,x):
    timewin = curses.newwin(2,14,y,x)
    timewin.box()
    timewin.bkgd(curses.color_pair(1));
    win.refresh()
    timewin.addstr(0,1,"MISSION TIME",curses.A_BOLD)
    timewin.refresh()
    return timewin

def draw_time_window(win,data):
    win.addstr(1,1,"           ",curses.A_BOLD)
    win.addstr(1,1,pltime(data["mt"]),curses.A_BOLD)
    win.refresh()

def init_utime_window(win,y,x):
    utimewin = curses.newwin(2,14,y,x)
    utimewin.box()
    utimewin.bkgd(curses.color_pair(1));
    win.refresh()        
    utimewin.addstr(0,1,"UNIVRSL TIME",curses.A_BOLD)
    utimewin.refresh()
    return utimewin

def draw_utime_window(win,data):
    win.addstr(1,1,"           ",curses.A_BOLD)
    win.addstr(1,1,pltime(data["ut"]),curses.A_BOLD)
    win.refresh()

def init_sys_window(win,y,x):
    syswin = curses.newwin(2,21,y,x)
    syswin.box()
    syswin.bkgd(curses.color_pair(1));
    win.refresh()
    syswin.addstr(0,1,"SYSYEMS",curses.A_BOLD)
    syswin.refresh()
    return syswin

def draw_sys_window(win,data):
    win.addstr(1,1,"RCS|SAS|LGT|TEL|RAD")
    if data["rcs"] == "True":
        win.addstr(1,1,"RCS",curses.A_REVERSE)
    if data["sas"] == "True":
        win.addstr(1,5,"SAS",curses.A_REVERSE)
    if data["light"] == "True":
        win.addstr(1,9,"LGT",curses.A_REVERSE)
    if isNum(data["alt"]):
        win.addstr(1,13,"TEL",curses.A_REVERSE)
    else:
        win.addstr(1,1,"???|???|???")
    if isNum(data["ralt"]):
        win.addstr(1,17,"RAD",curses.A_REVERSE)
    else:
        if data["ralt"] == "MAX":
            win.addstr(1,17,"RMX")
        if data["ralt"] == "MIN":
            win.addstr(1,17,"RMN")
        if data["ralt"] == "N/A":
            win.addstr(1,17,"RNA")
    win.refresh()

def init_tpos_window(win,y,x):
    twin = curses.newwin(11,18,y,x)
    twin.box()
    twin.bkgd(curses.color_pair(1));
    win.refresh()
    twin.addstr(0,1,"T.POS",curses.A_BOLD)
    twin.addstr(1,1,"  BODY ")
    twin.addstr(2,1," T.ALT ")
    twin.addstr(3,1," T.LAT ")
    twin.addstr(4,1,"T.LONG ")
    twin.addstr(5,1,"T.TTAP ")
    twin.addstr(6,1,"T.TTPE ")
    twin.addstr(7,1," T.PIT ")
    twin.addstr(8,1," T.ROL ")
    twin.addstr(9,1," T.HDG ")
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
    win.addstr(9,8,"         ",curses.A_BOLD)
    win.addstr(1,8,pnum(data["body"]).upper(),curses.A_BOLD)
    win.addstr(2,7,pnum(data["altt"]))
    win.addstr(2,8,palt(data["alt"]),curses.A_BOLD)
    win.addstr(3,8,plat(data["lat"]),curses.A_BOLD)
    win.addstr(4,8,plong(data["long"]),curses.A_BOLD)
    win.addstr(5,8,ptime(data["ttap"]),curses.A_BOLD)
    win.addstr(6,8,ptime(data["ttpe"]),curses.A_BOLD)
    win.addstr(7,8,pdeg(data["pitch"]),curses.A_BOLD)
    win.addstr(8,8,pdeg(data["roll"]),curses.A_BOLD)
    win.addstr(9,8,pdeg(data["hdg"]),curses.A_BOLD)
    win.refresh()

def init_rpos_window(win,y,x):
    rwin = curses.newwin(11,18,y,x)
    rwin.box()
    rwin.bkgd(curses.color_pair(1));
    win.refresh()
    rwin.addstr(0,1,"R.POS",curses.A_BOLD)
    rwin.addstr(1,1,"STATUS ")
    rwin.addstr(2,1," R.ALT ")
    rwin.addstr(3,1," R.LAT ")
    rwin.addstr(4,1,"R.LONG ")
    rwin.addstr(5,1,"R.TTAP ")
    rwin.addstr(6,1,"R.TTPE ")
    rwin.addstr(7,1,"  R.VS ")
    rwin.addstr(8,1,"  R.HS ")
    rwin.addstr(9,1,"R.SFCS ")
    rwin.refresh()
    return rwin

def draw_rpos_window(win,data):
    win.addstr(1,8,"         ",curses.A_BOLD)
    win.addstr(2,8,"         ",curses.A_BOLD)
    win.addstr(3,8,"         ",curses.A_BOLD)
    win.addstr(4,8,"         ",curses.A_BOLD)
    win.addstr(5,8,"         ",curses.A_BOLD)
    win.addstr(6,8,"         ",curses.A_BOLD)
    win.addstr(7,8,"         ",curses.A_BOLD)
    win.addstr(8,8,"         ",curses.A_BOLD)
    win.addstr(9,8,"         ",curses.A_BOLD)
    win.addstr(1,8,pnum(data["rstatus"]).upper(),curses.A_BOLD)
    win.addstr(2,8,palt(data["ralt"]),curses.A_BOLD)
    win.addstr(3,8,plat(data["rlat"]),curses.A_BOLD)
    win.addstr(4,8,plong(data["rlong"]),curses.A_BOLD)
    win.addstr(5,8,ptime(data["rttap"]),curses.A_BOLD)
    win.addstr(6,8,ptime(data["rttpe"]),curses.A_BOLD)
    win.addstr(7,8,pvel(data["rvs"]),curses.A_BOLD)
    win.addstr(8,8,pvel(data["rhs"]),curses.A_BOLD)
    win.addstr(9,8,pvel(data["rsfcs"]),curses.A_BOLD)
    win.refresh()

def init_orbit_window(win,y,x):
    owin = curses.newwin(9,18,y,x)
    owin.box()
    owin.bkgd(curses.color_pair(1));
    win.refresh()
    owin.addstr(0,1,"T.ORBIT",curses.A_BOLD)
    owin.addstr(1,1," T.SMA ")
    owin.addstr(2,1,"  T.AP ")
    owin.addstr(3,1,"  T.PE ")
    owin.addstr(4,1," T.INC ")
    owin.addstr(5,1," T.LAN ")
    owin.addstr(6,1,"T.OPRD ")
    owin.addstr(7,1,"T.OVEL ")
    owin.refresh()
    return owin

def draw_orbit_window(win,data):
    win.addstr(1,8,"         ",curses.A_BOLD)
    win.addstr(2,8,"         ",curses.A_BOLD)
    win.addstr(3,8,"         ",curses.A_BOLD)
    win.addstr(4,8,"         ",curses.A_BOLD)
    win.addstr(5,8,"         ",curses.A_BOLD)
    win.addstr(6,8,"         ",curses.A_BOLD)
    win.addstr(7,8,"         ",curses.A_BOLD)
    win.addstr(1,8,palt(data["sma"]),curses.A_BOLD)
    win.addstr(2,8,palt(data["ap"]),curses.A_BOLD)
    win.addstr(3,8,palt(data["pe"]),curses.A_BOLD)
    win.addstr(4,8,pdeg(data["inc"]),curses.A_BOLD)
    win.addstr(5,8,plong(data["lan"]),curses.A_BOLD)
    win.addstr(6,8,ptime(data["operiod"]),curses.A_BOLD)
    win.addstr(7,8,pvel(data["ov"]),curses.A_BOLD)
    win.refresh()

def init_rorb_window(win,y,x):
    rowin = curses.newwin(9,18,y,x)
    rowin.box()
    rowin.bkgd(curses.color_pair(1));
    win.refresh()
    rowin.addstr(0,1,"R.ORBIT",curses.A_BOLD)
    rowin.addstr(1,1," R.SMA ")
    rowin.addstr(2,1,"  R.AP ")
    rowin.addstr(3,1,"  R.PE ")
    rowin.addstr(4,1," R.INC ")
    rowin.addstr(5,1," R.LAN ")
    rowin.addstr(6,1,"R.OPRD ")
    rowin.addstr(7,1,"R.OVEL ")
    rowin.refresh()
    return rowin

def draw_rorb_window(win,data):
    win.addstr(1,8,"         ",curses.A_BOLD)
    win.addstr(2,8,"         ",curses.A_BOLD)
    win.addstr(3,8,"         ",curses.A_BOLD)
    win.addstr(4,8,"         ",curses.A_BOLD)
    win.addstr(5,8,"         ",curses.A_BOLD)
    win.addstr(6,8,"         ",curses.A_BOLD)
    win.addstr(7,8,"         ",curses.A_BOLD)
    win.addstr(1,8,palt(data["smag"]),curses.A_BOLD)
    win.addstr(2,8,palt(data["rap"]),curses.A_BOLD)
    win.addstr(3,8,palt(data["rpe"]),curses.A_BOLD)
    win.addstr(4,8,pdeg(data["rinc"]),curses.A_BOLD)
    win.addstr(5,8,plong(data["rlan"]),curses.A_BOLD)
    win.addstr(6,8,ptime(data["roperiod"]),curses.A_BOLD)
    win.addstr(7,8,pvel(data["rov"]),curses.A_BOLD)
    win.refresh()

def init_sfc_window(win,y,x):
    sfcwin = curses.newwin(11,18,y,x)
    sfcwin.box()
    sfcwin.bkgd(curses.color_pair(1));
    win.refresh()
    sfcwin.addstr(0,1,"T.GND RADAR",curses.A_BOLD)
    sfcwin.addstr(1,1,"STATUS ")
    sfcwin.addstr(2,1," T.HAT ")
    sfcwin.addstr(3,1," T.ASL ")
    sfcwin.addstr(4,1,"  T.VS ")
    sfcwin.addstr(5,1,"  T.HS ")
    sfcwin.addstr(6,1,"T.SFVT ")
    sfcwin.addstr(7,1,"T.SFVX ")
    sfcwin.addstr(8,1,"T.SFVY ")
    sfcwin.addstr(9,1,"T.SFVZ ")
    sfcwin.refresh()
    return sfcwin

def draw_sfc_window(win,data):
    win.addstr(1,8,"         ",curses.A_BOLD)
    win.addstr(2,8,"         ",curses.A_BOLD)
    win.addstr(3,8,"         ",curses.A_BOLD)
    win.addstr(4,8,"         ",curses.A_BOLD)
    win.addstr(5,8,"         ",curses.A_BOLD)
    win.addstr(6,8,"         ",curses.A_BOLD)
    win.addstr(7,8,"         ",curses.A_BOLD)
    win.addstr(8,8,"         ",curses.A_BOLD)
    win.addstr(9,8,"         ",curses.A_BOLD)
    win.addstr(1,8,xstr(data["grstatus"]),curses.A_BOLD)
    win.addstr(2,8,palt(data["hat"]),curses.A_BOLD)
    win.addstr(3,8,palt(data["asl"]),curses.A_BOLD)
    win.addstr(4,7,pvel(data["altt"]),curses.A_BOLD)
    win.addstr(4,8,pvel(data["vs"]),curses.A_BOLD)
    win.addstr(5,8,pvel(data["hs"]),curses.A_BOLD)
    win.addstr(6,8,pvel(data["sfcv"]),curses.A_BOLD)
    win.addstr(7,8,pvel(data["sfcvx"]),curses.A_BOLD)
    win.addstr(8,8,pvel(data["sfcvy"]),curses.A_BOLD)
    win.addstr(9,8,pvel(data["sfcvz"]),curses.A_BOLD)
    win.refresh()

def init_lfuel_window(win,y,x):
    fuelwin = curses.newwin(3,37,y,x)
    fuelwin.box()
    fuelwin.bkgd(curses.color_pair(1));
    win.refresh()
    fuelwin.addstr(0,1,"T.LIQUIDFUEL",curses.A_BOLD)
    fuelwin.refresh()
    return fuelwin

def draw_lfuel_window(win,data):
    win.addstr(1,1,"                    ",curses.A_BOLD)
    fuelbar = phbar(data["lf"],data["mlf"])
    fuelperc = data["lf"] / data["mlf"]
    win.move(1,1)
    printhbar(win,fuelbar,fuelperc)
    win.refresh()

def init_oxi_window(win,y,x):
    oxiwin = curses.newwin(3,37,y,x)
    oxiwin.box()
    oxiwin.bkgd(curses.color_pair(1));
    win.refresh()
    oxiwin.addstr(0,1,"T.OXIDIZER",curses.A_BOLD)
    oxiwin.refresh()
    return oxiwin

def draw_oxi_window(win,data):
    win.addstr(1,1,"                    ",curses.A_BOLD)
    oxibar = phbar(data["oxidizer"],data["moxidizer"])
    oxiperc = data["oxidizer"] / data["moxidizer"]
    win.move(1,1)
    printhbar(win,oxibar,oxiperc)    
    win.refresh()

def init_mono_window(win,y,x):
    monowin = curses.newwin(3,37,y,x)
    monowin.box()
    monowin.bkgd(curses.color_pair(1));
    win.refresh()
    monowin.addstr(0,1,"T.MONOPROP",curses.A_BOLD)
    monowin.refresh()
    return monowin

def draw_mono_window(win,data):
    win.addstr(1,1,"                   ",curses.A_BOLD)
    monobar = phbar(data["mono"],data["mmono"])
    monoperc = data["mono"] / data["mmono"]
    win.move(1,1)
    printhbar(win,monobar,monoperc)
    win.refresh()

def init_pitch_window(win,y,x):
    pitchwin = curses.newwin(11,4,y,x)
    pitchwin.box()
    pitchwin.bkgd(curses.color_pair(1));
    win.refresh()
    pitchwin.addstr(1,0,"P",curses.A_BOLD)
    pitchwin.addstr(2,0,"I",curses.A_BOLD)
    pitchwin.addstr(3,0,"T",curses.A_BOLD)
    pitchwin.refresh()
    return pitchwin

def draw_pitch_window(win,data):
    win.addstr(1,1," ",curses.A_BOLD)
    win.refresh()

def init_yaw_window(win,y,x):
    pitchwin = curses.newwin(11,4,y,x)
    pitchwin.box()
    pitchwin.bkgd(curses.color_pair(1));
    win.refresh()
    pitchwin.addstr(1,0,"Y",curses.A_BOLD)
    pitchwin.addstr(2,0,"A",curses.A_BOLD)
    pitchwin.addstr(3,0,"W",curses.A_BOLD)
    pitchwin.refresh()
    return pitchwin

def draw_yaw_window(win,data):
    win.addstr(1,1," ",curses.A_BOLD)
    win.refresh()

def init_roll_window(win,y,x):
    pitchwin = curses.newwin(11,4,y,x)
    pitchwin.box()
    pitchwin.bkgd(curses.color_pair(1));
    win.refresh()
    pitchwin.addstr(1,0,"R",curses.A_BOLD)
    pitchwin.addstr(2,0,"O",curses.A_BOLD)
    pitchwin.addstr(3,0,"L",curses.A_BOLD)
    pitchwin.refresh()
    return pitchwin

def draw_roll_window(win,data):
    win.addstr(1,1," ",curses.A_BOLD)
    win.refresh()

def init_wr_window(win,y,x):
    wrwin = curses.newwin(3,7,y,x)
    wrwin.box()
    wrwin.bkgd(curses.color_pair(1));
    win.refresh()
    wrwin.addstr(1,1,"     ",curses.A_BOLD)
    wrwin.refresh()
    return wrwin

def draw_wr_window(win,data):
    if data["rstatus"] == "NOMINAL":
        state = 0
    else:
        state = 1
    printwarn(win,"RADAR",state)
    win.refresh()

def init_wt_window(win,y,x):
    wtwin = curses.newwin(3,7,y,x)
    wtwin.box()
    wtwin.bkgd(curses.color_pair(1));
    win.refresh()
    wtwin.addstr(1,1,"     ",curses.A_BOLD)
    wtwin.refresh()
    return wtwin

def draw_wt_window(win,data):
    if isNum(data["alt"]):
        state = 0
    else:
        state = 1
    printwarn(win,"TELEM",state)
    win.refresh()

def init_wg_window(win,y,x):
    wgwin = curses.newwin(3,7,y,x)
    wgwin.box()
    wgwin.bkgd(curses.color_pair(1));
    win.refresh()
    wgwin.addstr(1,1,"     ",curses.A_BOLD)
    wgwin.refresh()
    return wgwin

def draw_wg_window(win,data):
    if data["grstatus"] == "NOMINAL":
        state = 0
    else:
        state = 1
    printwarn(win,"G RAD",state)
    win.refresh()

def init_throt_window(win,y,x):
    pitchwin = curses.newwin(11,5,y,x)
    pitchwin.box()
    pitchwin.bkgd(curses.color_pair(1));
    win.refresh()
    pitchwin.addstr(1,0,"T",curses.A_BOLD)
    pitchwin.addstr(2,0,"H",curses.A_BOLD)
    pitchwin.addstr(3,0,"R",curses.A_BOLD)
    pitchwin.addstr(4,0,"U",curses.A_BOLD)
    pitchwin.addstr(5,0,"S",curses.A_BOLD)
    pitchwin.addstr(6,0,"T",curses.A_BOLD)
    pitchwin.addstr(9,4,"%",curses.A_BOLD)
    pitchwin.refresh()
    return pitchwin

def draw_throt_window(win,data):
    win.move(1,1)
    printvbar(win,data["throt"])
    win.refresh()

def mainloop(win):
    timeposx = 1
    timeposy = 1
    utimeposx = 16
    utimeposy = 1
    tposx = 1
    tposy = 3
    rposx = 20
    roposy = 3
    roposx = 58
    rposy = 3
    oposx = 39
    oposy = 3
    sysx = 31
    sysy = 1
    sfcx =58
    sfcy = 12
    fuelx = 1
    fuely = 14
    oxix = 1
    oxiy = 17
    monox = 1
    monoy = 20
#    pitchx = 39
#    pitchy = 12
#    yawx = 44
#    yawy = 12
#    rollx = 49
#    rolly = 12
    wrx = 39
    wry = 12
    wtx = 46
    wty = 12
    wgx = 39
    wgy = 15
    throtx = 53
    throty = 12
    win.nodelay(1)
    init_window(win)
    timewin = init_time_window(win,timeposy,timeposx)
    utimewin = init_utime_window(win,utimeposy,utimeposx)
    syswin = init_sys_window(win,sysy,sysx)
    twin = init_tpos_window(win,tposy,tposx)
    rwin = init_rpos_window(win,rposy,rposx)
    rowin = init_rorb_window(win,roposy,roposx)
    owin = init_orbit_window(win,oposy,oposx)
    sfcwin = init_sfc_window(win,sfcy,sfcx)
    lfuelwin = init_lfuel_window(win,fuely,fuelx)
    oxiwin = init_oxi_window(win,oxiy,oxix)
    monowin = init_mono_window(win,monoy,monox)
#    pitchwin = init_pitch_window(win,pitchy,pitchx) not working
#    yawwin = init_yaw_window(win,yawy,yawx)
#    rollwin = init_roll_window(win,rolly,rollx)
    wrwin = init_wr_window(win,wry,wrx)
    wtwin = init_wt_window(win,wty,wtx)
    wgwin = init_wg_window(win,wgy,wgx)
    throtwin = init_throt_window(win,throty,throtx)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.exchange_declare(exchange='logs',type='fanout')
    channel.queue_bind(exchange='logs',queue='ksp_data')

    def callback(ch, method, properties, body):
        write_datetime(win)
        indata = marshal.loads(body)
        data = dict(indata)
#        data = fetchData()
        radar = getRadar(data)
        tele = getTelemetry(data)
        write_datetime(win)
        draw_time_window(timewin,tele)
        draw_utime_window(utimewin,tele)
        draw_sys_window(syswin,tele)
        draw_tpos_window(twin,tele)
        draw_rpos_window(rwin,radar)
        draw_rorb_window(rowin,radar)
        draw_orbit_window(owin,tele)
        draw_sfc_window(sfcwin,tele)
        draw_lfuel_window(lfuelwin,tele)
        draw_oxi_window(oxiwin,tele)
        draw_mono_window(monowin,tele)
#        draw_pitch_window(pitchwin,tele) not working
#        draw_yaw_window(yawwin,tele)
#        draw_roll_window(rollwin,tele)
        draw_wr_window(wrwin,tele)
        draw_wt_window(wtwin,tele)
        draw_wg_window(wgwin,tele)
        draw_throt_window(throtwin,tele)

    channel.basic_consume(callback, queue="ksp_data", no_ack=True)
    channel.start_consuming()

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



