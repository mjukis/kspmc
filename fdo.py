#! /usr/bin/python
# coding=UTF-8
#--------------------
# KSP Telemachus
# Mission Control
# Flight Dynamics v0.6
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
import math

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

def xstr(s):
    if s is None:
        return ''
    return str(s)

def pfloat(num):
    if isNum(num):
        nnum = xstr("{:,}".format(round(num,2)))
    else:
        nnum = num
    return nnum

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
    topstring = "FLIGHT DYNAMICS v0.6"
    bottomstring = "ORBITAL PARAMETERS AND DESIRED CHANGES"
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
    if d["ttt1"] > 0:
        d["t1"] = d["mt"] + d["ttt1"]
    else:
        d["t1"] = d["ttt1"]
    if d["ttt2"] > 0:
        d["t2"] = d["mt"] + d["ttt2"]
    else:
        d["t2"] = d["ttt2"]
    d["apat"] = d["mt"] + d["ttap"]
    d["peat"] = d["mt"] + d["ttpe"]
    if isNum(d["pe"]) and d["pe"] < 0:
        d["pe"] = 0
    if d["pstat"] == 0:
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
    if isNum(d["lf"]) and isNum(d["oxidizer"]):
        d["fuel"] = d["lf"] + d["oxidizer"]
    if isNum(d["mlf"]) and isNum(d["moxidizer"]):
        d["mfuel"] = d["mlf"] + d["moxidizer"]
    if isNum(d["asl"]):
        if d["hat"] == -1 or d["hat"] > maxgralt or d["pstat"] != 0:
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
        return d

def fuck(status,instring):
    if status == 0 or status == 1:
        return instring
    if isNum(instring):
        workstring = str(instring)
    else:
        workstring = instring
    worklist = list(workstring)
    if status == 2:
        for i,char in enumerate(worklist):
            charlist = [char,char,char,char,char,char,char,char,char,char,char,char,char,char,char,char,char,char,'!','?','i','$','/','|','#']
            newchar = random.choice(charlist)
            worklist[i] = newchar
        outstring = "".join(worklist)
    if status == 3 or status == 4:
        for i,char in enumerate(worklist):
            newchar = " "
            worklist[i] = newchar
        outstring = "".join(worklist)    
    return outstring

def fucknum(status,indata):
    if status == 0 or status == 1:
        return indata
    if status == 2:
        if isNum(indata):
            errnum = random.uniform(0.75,1.25)
            outdata = indata * errnum
        else:
            return indata
    if status == 3 or status == 4:
        outdata = 0
    return outdata

def pnum(num):
    if isNum(num):
        nnum = xstr("{:,}".format(int(num)))
    else:
        nnum = num
    return nnum

def pvel(num):
    kmlimit = 10000
    if isNum(num):
        if num < kmlimit:
            nnum = xstr("{:,}".format(int(round(num,0)))) + "m/s"
        if num >= kmlimit:
            nnum = xstr("{:,}".format(round(num / 1000,1))) + "km/s"
    else:
        nnum = num
    return nnum

def phbar(num,mnum):
    if isNum(num) and isNum(mnum):
        pnum = int((num / mnum) * 100)
        onum = xstr(" " + "{:,}".format(round(num,1))) + " (" + xstr(pnum) + "%)"
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
        if num >= 7884000:
            m, s = divmod(num, 60)
            h, m = divmod(m, 60)
            d, h = divmod(h, 6)
            y, d = divmod(d, 365)
            y = xstr(int(y))
            d = xstr(int(d)).zfill(2)
            nnum = "%sy %sd" % (y,d)
        else:
            m, s = divmod(num, 60)
            h, m = divmod(m, 60)
            d, h = divmod(h, 6)
            d = xstr(int(d))
            h = xstr(int(h)).zfill(2)
            m = xstr(int(m)).zfill(2)
            s = xstr(int(s)).zfill(2)
            nnum = "%sd%s:%s:%s" % (d,h,m,s)
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

def pwgt(num):
    tonlimit = 10000
    if isNum(num):
        if num >= tonlimit:
            nnum = xstr("{:,}".format(round(num / 1000,3))) + "t"
        if num < tonlimit:
            nnum = xstr("{:,}".format(int(round(num,0)))) + "kg"
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

def init_time_window(win,y,x,title):
    timewin = curses.newwin(2,14,y,x)
    timewin.box()
    timewin.bkgd(curses.color_pair(1));
    win.refresh()
    timewin.addstr(0,1,title,curses.A_BOLD)
    timewin.refresh()
    return timewin

def draw_time_window(win,data):
    win.addstr(1,1,"           ",curses.A_BOLD)
    win.addstr(1,1,pltime(data),curses.A_BOLD)
    win.refresh()

def init_input_window(win,y,x,title):
    iwin = curses.newwin(2,9,y,x)
    iwin.box()
    iwin.bkgd(curses.color_pair(1));
    win.refresh()
    iwin.addstr(0,1,title,curses.A_BOLD)
    iwin.refresh()
    return iwin

def draw_input_window(win,data):
    win.addstr(1,1,"       ",curses.A_BOLD)
    win.addstr(1,1,str(data),curses.A_BOLD)
    win.refresh()

def init_sys_window(win,y,x):
    syswin = curses.newwin(2,17,y,x)
    syswin.box()
    syswin.bkgd(curses.color_pair(1));
    win.refresh()
    syswin.addstr(0,1,"SYSTEMS",curses.A_BOLD)
    syswin.refresh()
    return syswin

def draw_sys_window(win,data):
    win.addstr(1,1,"RCS|SAS|TEL|RAD")
    if data["rcs"] == "True":
        win.addstr(1,1,"RCS",curses.A_REVERSE)
    if data["sas"] == "True":
        win.addstr(1,5,"SAS",curses.A_REVERSE)
    if data["pstat"] == 0:
        win.addstr(1,9,"TEL",curses.A_REVERSE)
    else:
        win.addstr(1,1,"???|???")
    if isNum(data["ralt"]):
        win.addstr(1,13,"RAD",curses.A_REVERSE)
    else:
        if data["ralt"] == "MAX":
            win.addstr(1,13,"RMX")
        if data["ralt"] == "MIN":
            win.addstr(1,13,"RMN")
        if data["ralt"] == "N/A":
            win.addstr(1,13,"RNA")
    win.refresh()

def init_pos_window(win,y,x):
    twin = curses.newwin(10,18,y,x)
    twin.box()
    twin.bkgd(curses.color_pair(1));
    win.refresh()
    twin.addstr(0,1,"T/R.ORBIT",curses.A_BOLD)
    twin.addstr(1,1,"  BODY ")
    twin.addstr(2,1,"  .ALT ")
    twin.addstr(3,1,"  .LAT ")
    twin.addstr(4,1," .LONG ")
    twin.addstr(5,1,"   .AP ")
    twin.addstr(6,1," .TTAP ")
    twin.addstr(7,1,"   .PE ")
    twin.addstr(8,1," .TTPE ")
    twin.refresh()
    return twin

def draw_pos_window(win,data):
    pstat = data["pstat"]
    body = pnum(data["body"])
    try:
        if isNum(fuck(pstat,data["alt"])):
            alttype = "T"
            alt = fuck(pstat,palt(data["alt"]))
        else:
            alttype = "R"
            alt = palt(data["ralt"])
        if isNum(data["rlat"]):
            lattype = "R"
            lat = plat(data["rlat"])
        else:
            lattype = "T"
            lat = fuck(pstat,plat(data["lat"]))
        if isNum(data["rlong"]):
            longtype = "R"
            long = plong(data["rlong"])
        else:
            longtype = "T"
            long = fuck(pstat,plong(data["long"]))
        if isNum(fuck(pstat,data["ap"])):
            aptype = "T"
            ap = fuck(pstat,palt(data["ap"]))
        else:
            aptype = "R"
            ap = palt(data["rap"])
        if isNum(fuck(pstat,data["ttap"])):
            ttaptype = "T"
            ttap = fuck(pstat,ptime(data["ttap"]))
        else:
            ttaptype = "R"
            ttap = ptime(data["rttap"])
        if isNum(fuck(pstat,data["pe"])):
            petype = "T"
            pe = fuck(pstat,palt(data["pe"]))
        else:
            petype = "R"
            pe = palt(data["rpe"])
        if isNum(fuck(pstat,data["ttpe"])):
            ttpetype = "T"
            ttpe = fuck(pstat,ptime(data["ttpe"]))
        else:
            ttpetype = "R"
            ttpe = ptime(data["rttpe"])
    except:
        pass
    win.addstr(1,8,"         ",curses.A_BOLD)
    win.addstr(2,8,"         ",curses.A_BOLD)
    win.addstr(3,8,"         ",curses.A_BOLD)
    win.addstr(4,8,"         ",curses.A_BOLD)
    win.addstr(5,8,"         ",curses.A_BOLD)
    win.addstr(6,8,"         ",curses.A_BOLD)
    win.addstr(7,8,"         ",curses.A_BOLD)
    win.addstr(8,8,"         ",curses.A_BOLD)
    win.addstr(1,8,body.upper(),curses.A_BOLD)
    win.addstr(2,2,alttype,curses.A_BOLD)
    win.addstr(3,2,lattype,curses.A_BOLD)
    win.addstr(4,1,longtype,curses.A_BOLD)
    win.addstr(5,3,aptype,curses.A_BOLD)
    win.addstr(6,1,ttaptype,curses.A_BOLD)
    win.addstr(7,3,petype,curses.A_BOLD)
    win.addstr(8,1,ttpetype,curses.A_BOLD)
    win.addstr(2,8,alt,curses.A_BOLD)
    win.addstr(3,8,lat,curses.A_BOLD)
    win.addstr(4,8,long,curses.A_BOLD)
    win.addstr(5,8,ap,curses.A_BOLD)
    win.addstr(6,8,ttap,curses.A_BOLD)
    win.addstr(7,8,pe,curses.A_BOLD)
    win.addstr(8,8,ttpe,curses.A_BOLD)
    win.refresh()

def init_dv_window(win,y,x):
    nwin = curses.newwin(10,18,y,x)
    nwin.box()
    nwin.bkgd(curses.color_pair(1));
    win.refresh()
    nwin.addstr(0,1,"DELTA V",curses.A_BOLD)
    nwin.addstr(1,1,"  T.MD ")
    nwin.addstr(2,1,"  T.MF ")
    nwin.addstr(3,1,"  T.MT ")
    nwin.addstr(4,1,"DV MAX ")
    nwin.addstr(5,1,"BT MAX ")
    nwin.addstr(6,1,"------ ---------")
    nwin.addstr(7,1,"I.RAD1 ")
    nwin.addstr(8,1,"I.RAD2 ")
    nwin.refresh()
    return nwin

def draw_dv_window(win,data):
    pstat = data["pstat"]
    wlf = fucknum(pstat,data["lf"] * 5)
    woxi = fucknum(pstat,data["oxidizer"] * 5)
    wfuel = fucknum(pstat,(wlf + woxi))
    wmono = fucknum(pstat,data["mono"] * 4)
    wo2 = fucknum(pstat,data["o2"] * 0.04290144)
    wh2o = fucknum(pstat,data["h2o"] * 1.7977746)
    wfood = fucknum(pstat,data["food"] * 0.3166535)
    wco2 = fucknum(pstat,data["co2"] * 0.00561805)
    wwaste = fucknum(pstat,data["waste"] * 0.00561805)
    wwh2o = fucknum(pstat,data["wastewater"] * 1.9765307)
    wcon = wmono + wo2 + wh2o + wfood + wco2 + wwaste + wwh2o
    wdry = 2325.93
    wsemidry = wdry + wcon
    wtot = wsemidry + wfuel
    availthrust = 50000
    isp = 390 * 9.82
    mdot = availthrust / isp
    dvmax = isp * math.log(wtot / wsemidry)
    btmax = wfuel / mdot
    win.addstr(1,8,"         ",curses.A_BOLD)
    win.addstr(2,8,"         ",curses.A_BOLD)
    win.addstr(3,8,"         ",curses.A_BOLD)
    win.addstr(4,8,"         ",curses.A_BOLD)
    win.addstr(5,8,"         ",curses.A_BOLD)
    win.addstr(7,8,"         ",curses.A_BOLD)
    win.addstr(8,8,"         ",curses.A_BOLD)
    win.addstr(1,8,pwgt(wsemidry),curses.A_BOLD)
    win.addstr(2,8,pwgt(wfuel),curses.A_BOLD)
    win.addstr(3,8,pwgt(wsemidry + wfuel),curses.A_BOLD)
    win.addstr(4,8,pvel(dvmax),curses.A_BOLD)
    win.addstr(5,8,ptime(btmax),curses.A_BOLD)
    win.addstr(7,8,fuck(pstat,palt(data["alt"])),curses.A_BOLD)
    win.addstr(8,8,palt(0),curses.A_BOLD)
    win.refresh()

def init_hbar_window(win,y,x,title):
    fuelwin = curses.newwin(3,37,y,x)
    fuelwin.box()
    fuelwin.bkgd(curses.color_pair(1));
    win.refresh()
    fuelwin.addstr(0,1,title,curses.A_BOLD)
    fuelwin.refresh()
    return fuelwin

def draw_hbar_window(win,data,key,mkey):
    win.addstr(1,1,"                    ",curses.A_BOLD)
    pstat = data["pstat"]
    fkey = fucknum(pstat,data[key])
    if isNum(mkey):
        fmkey = mkey
    else:
        fmkey = data[mkey]
    hbar = phbar(fkey,fmkey)
    hperc = fkey / fmkey
    win.move(1,1)
    printhbar(win,hbar,hperc)
    win.refresh()

def init_alarm_window(win,y,x):
    wgwin = curses.newwin(3,7,y,x)
    wgwin.box()
    wgwin.bkgd(curses.color_pair(1));
    win.refresh()
    wgwin.addstr(1,1,"     ",curses.A_BOLD)
    wgwin.refresh()
    return wgwin

def draw_alarm_window(win,data):
    lfp = data["lf"] / data["mlf"]
    oxip = data["oxidizer"] / data["moxidizer"]
    monop = data["mono"] / data["mmono"]
    o2p = data["o2"] / data["mo2"]
    h2op = data["h2o"] / data["mh2o"]
    foodp = data["food"] / data["mfood"]
    mp = data["w"] / data["mw"]
    if o2p > 0.1 and h2op > 0.1 and foodp > 0.1:
        lsstatus = 0
    else:
        lsstatus = 1
    if lfp > 0.1 and oxip > 0.1 and monop > 0.1 and lsstatus == 0 and mp > 0.1:
        state = 0
    else:
        state = 1
    printwarn(win,"ALARM",state)
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
    pstat = data["pstat"]
    throt = fucknum(pstat,data["throt"])
    printvbar(win,throt)
    win.refresh()

def mainloop(win):
    timeposx = 1
    timeposy = 1
    utimeposx = 16
    utimeposy = 1
    aptimeposx = 1
    aptimeposy = 3
    petimeposx = 1
    petimeposy = 5
    t1timeposx = 16
    t1timeposy = 3
    t2timeposx = 16
    t2timeposy = 5
    posx = 1
    posy = 7
    in1x = 49
    in1y = 1
    in2x = 58
    in2y = 1
    in3x = 67
    in3y = 1
    dvx = 20
    dvy = 7
    sysx = 31
    sysy = 1
    fuelx = 1
    fuely = 17
    monox = 1
    monoy = 20
    alarmx = 31
    alarmy = 4
    throtx = 71
    throty = 5
    hthrotx = 39
    hthroty = 20

    win.nodelay(1)
    init_window(win)

    timewin = init_time_window(win,timeposy,timeposx,"MISSION TIME")
    utimewin = init_time_window(win,utimeposy,utimeposx,"UNIVRSL TIME")
    aptimewin = init_time_window(win,aptimeposy,aptimeposx,"NEXT AP")
    petimewin = init_time_window(win,petimeposy,petimeposx,"NEXT PE")
    t1timewin = init_time_window(win,t1timeposy,t1timeposx,"TRANSITION 1")
    t2timewin = init_time_window(win,t2timeposy,t2timeposx,"TRANSITION 2")
    syswin = init_sys_window(win,sysy,sysx)
    in1win = init_input_window(win,in1y,in1x,"I.kN")
    in2win = init_input_window(win,in2y,in2x,"I.Isp")
    in3win = init_input_window(win,in3y,in3x,"I.RAD2")
    poswin = init_pos_window(win,posy,posx)
    dvwin = init_dv_window(win,dvy,dvx)
    fuelwin = init_hbar_window(win,fuely,fuelx,"T.BIPROPELLANT")
    monowin = init_hbar_window(win,monoy,monox,"T.MONOPROPELLANT")
    hthrotwin = init_hbar_window(win,hthroty,hthrotx,"T.THRUST")
    alarmwin = init_alarm_window(win,alarmy,alarmx)
    throtwin = init_throt_window(win,throty,throtx)

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange='logs',type='fanout')
    channel.queue_bind(exchange='logs',queue='ksp_data')

    def callback(ch, method, properties, body):
        indata = marshal.loads(body)
        data = dict(indata)
        write_datetime(win)
        radar = getRadar(data)
        tele = getTelemetry(data)
        write_datetime(win)
        draw_time_window(timewin,tele["mt"])
        draw_time_window(utimewin,tele["ut"])
        draw_time_window(aptimewin,tele["apat"])
        draw_time_window(petimewin,tele["peat"])
        draw_time_window(t1timewin,tele["t1"])
        draw_time_window(t2timewin,tele["t2"])
        draw_sys_window(syswin,tele)
        draw_input_window(in1win,"50")
        draw_input_window(in2win,"390")
        draw_input_window(in3win,"0")
        draw_pos_window(poswin,radar)
        draw_dv_window(dvwin,tele)
        draw_hbar_window(fuelwin,tele,"fuel","mfuel")
        draw_hbar_window(monowin,tele,"mono","mmono")
        draw_hbar_window(hthrotwin,tele,"throt",1)
        draw_alarm_window(alarmwin,tele)
        draw_throt_window(throtwin,tele)
        write_datetime(win)

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



