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
    topstring = "EECOM"
    bottomstring = "TELEMETRY"
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
            if indata < 3:
                outdata = random.uniform(-5,5)
            else:
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

def pfloat(num):
    if isNum(num):
        nnum = xstr("{:,}".format(round(num,2)))
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

def init_ctime_window(win,y,x):
    ctimewin = curses.newwin(2,14,y,x)
    ctimewin.box()
    ctimewin.bkgd(curses.color_pair(1));
    win.refresh()        
    ctimewin.addstr(0,1,"LAST CHARGE",curses.A_BOLD)
    ctimewin.refresh()
    return ctimewin

def draw_ctime_window(win,data):
    win.addstr(1,1,"           ",curses.A_BOLD)
    win.addstr(1,1,pltime(data["lc"]),curses.A_BOLD)
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
    win.addstr(1,1,"RCS|SAS|LGT|TEL")
    if data["rcs"] == "True":
        win.addstr(1,1,"RCS",curses.A_REVERSE)
    if data["sas"] == "True":
        win.addstr(1,5,"SAS",curses.A_REVERSE)
    if data["light"] == "True":
        win.addstr(1,9,"LGT",curses.A_REVERSE)
    if data["pstat"] == 0:
        win.addstr(1,13,"TEL",curses.A_REVERSE)
    else:
        win.addstr(1,1,"???|???|???")
    win.refresh()

def init_batt_window(win,y,x):
    bwin = curses.newwin(5,18,y,x)
    bwin.box()
    bwin.bkgd(curses.color_pair(1));
    win.refresh()
    bwin.addstr(0,1,"T.BATT",curses.A_BOLD)
    bwin.addstr(1,1,"  MAIN ")
    bwin.addstr(2,1,"    CM ")
    bwin.addstr(3,1,"  RATE ")
    bwin.refresh()
    return bwin

def draw_batt_window(win,data):
    if data["wr"] < 0.1:
        wr = " 0.00"
    if data["wr"] >= 0.1:
        wr = "+" + str(pfloat(data["wr"]))
    if data["wr"] < 0:
        wr = pfloat(data["wr"])
        if wr == "-0.0":
            wr = "-0.00"
    cmw = 0
    battw = 0
    maxw = data["mw"]
    totw = data["w"]
    cmm = 50
    battm = maxw - cmm
    diff = maxw - totw
    if maxw > 50:
            if totw <= cmm:
                cmw = totw
            else:
                battw = battm - diff
                cmw = cmm

    win.addstr(1,8,"         ",curses.A_BOLD)
    win.addstr(2,8,"         ",curses.A_BOLD)
    win.addstr(3,8,"         ",curses.A_BOLD)
    win.addstr(1,8,pfloat(battw),curses.A_BOLD)
    win.addstr(2,8,pfloat(cmw),curses.A_BOLD)
    win.addstr(3,8,wr,curses.A_BOLD)
    win.refresh()

def init_stor_window(win,y,x):
    storwin = curses.newwin(13,18,y,x)
    storwin.box()
    storwin.bkgd(curses.color_pair(1));
    win.refresh()
    storwin.addstr(0,1,"T.CONTAINERS",curses.A_BOLD)
    storwin.addstr(1,1,"    LF ")
    storwin.addstr(2,1,"   OXI ")
    storwin.addstr(3,1," MONOP ")
    storwin.addstr(4,1,"------ ---------")
    storwin.addstr(5,1,"OXYGEN ")
    storwin.addstr(6,1,"   H2O ")
    storwin.addstr(7,1,"  FOOD ")
    storwin.addstr(8,1,"------ ---------")
    storwin.addstr(9,1,"   CO2 ")
    storwin.addstr(10,1," WASTE ")
    storwin.addstr(11,1," W.H2O ")
    storwin.refresh()
    return storwin

def draw_stor_window(win,data):
    pstat = data["pstat"]
    lf = fuck(pstat,pfloat(data["lf"]))
    oxidizer = fuck(pstat,pfloat(data["oxidizer"]))
    mono = fuck(pstat,pfloat(data["mono"]))
    o2 = fuck(pstat,pfloat(data["o2"]))
    h2o = fuck(pstat,pfloat(data["h2o"]))
    food = fuck(pstat,pfloat(data["food"]))
    co2 = fuck(pstat,pfloat(data["co2"]))
    waste = fuck(pstat,pfloat(data["waste"]))
    wastewater = fuck(pstat,pfloat(data["wastewater"]))
    win.addstr(1,8,"         ",curses.A_BOLD)
    win.addstr(2,8,"         ",curses.A_BOLD)
    win.addstr(3,8,"         ",curses.A_BOLD)
    win.addstr(5,8,"         ",curses.A_BOLD)
    win.addstr(6,8,"         ",curses.A_BOLD)
    win.addstr(7,8,"         ",curses.A_BOLD)
    win.addstr(9,8,"         ",curses.A_BOLD)
    win.addstr(10,8,"         ",curses.A_BOLD)
    win.addstr(11,8,"         ",curses.A_BOLD)
    win.addstr(1,8,lf,curses.A_BOLD)
    win.addstr(2,8,oxidizer,curses.A_BOLD)
    win.addstr(3,8,mono,curses.A_BOLD)
    win.addstr(5,8,o2,curses.A_BOLD)
    win.addstr(6,8,h2o,curses.A_BOLD)
    win.addstr(7,8,food,curses.A_BOLD)
    win.addstr(9,8,co2,curses.A_BOLD)
    win.addstr(10,8,waste,curses.A_BOLD)
    win.addstr(11,8,wastewater,curses.A_BOLD)
    win.refresh()

def init_weight_window(win,y,x):
    wwin = curses.newwin(15,18,y,x)
    wwin.box()
    wwin.bkgd(curses.color_pair(1));
    win.refresh()
    wwin.addstr(0,1,"T.STORAGE(KG)",curses.A_BOLD)
    wwin.addstr(1,1," TOTAL ")
    wwin.addstr(2,1,"------ ---------")
    wwin.addstr(3,1,"    LF ")
    wwin.addstr(4,1,"   OXI ")
    wwin.addstr(5,1," MONOP ")
    wwin.addstr(6,1,"------ ---------")
    wwin.addstr(7,1,"OXYGEN ")
    wwin.addstr(8,1,"   H2O ")
    wwin.addstr(9,1,"  FOOD ")
    wwin.addstr(10,1,"------ ---------")
    wwin.addstr(11,1,"   CO2 ")
    wwin.addstr(12,1," WASTE ")
    wwin.addstr(13,1," W.H2O ")
    wwin.refresh()
    return wwin

def draw_weight_window(win,data):
    pstat = data["pstat"]
    wlf = fucknum(pstat,data["lf"] * 5)
    woxi = fucknum(pstat,data["oxidizer"] * 5)
    wmono = fucknum(pstat,data["mono"] * 4)
    wo2 = fucknum(pstat,data["o2"] * 0.04290144)
    wh2o = fucknum(pstat,data["h2o"] * 1.7977746)
    wfood = fucknum(pstat,data["food"] * 0.3166535)
    wco2 = fucknum(pstat,data["co2"] * 0.00561805)
    wwaste = fucknum(pstat,data["waste"] * 0.00561805)
    wwh2o = fucknum(pstat,data["wastewater"] * 1.9765307)
    wtot = wlf + woxi + wmono + wo2 + wh2o + wfood + wco2 + wwaste + wwh2o
    win.addstr(1,8,"         ",curses.A_BOLD)
    win.addstr(2,8,"         ",curses.A_BOLD)
    win.addstr(3,8,"         ",curses.A_BOLD)
    win.addstr(5,8,"         ",curses.A_BOLD)
    win.addstr(6,8,"         ",curses.A_BOLD)
    win.addstr(7,8,"         ",curses.A_BOLD)
    win.addstr(9,8,"         ",curses.A_BOLD)
    win.addstr(10,8,"         ",curses.A_BOLD)
    win.addstr(11,8,"         ",curses.A_BOLD)
    win.addstr(13,8,"         ",curses.A_BOLD)
    win.addstr(1,8,str(wtot),curses.A_BOLD)
    win.addstr(3,8,pfloat(wlf),curses.A_BOLD)
    win.addstr(4,8,pfloat(woxi),curses.A_BOLD)
    win.addstr(5,8,pfloat(wmono),curses.A_BOLD)
    win.addstr(7,8,pfloat(wo2),curses.A_BOLD)
    win.addstr(8,8,pfloat(wh2o),curses.A_BOLD)
    win.addstr(9,8,pfloat(wfood),curses.A_BOLD)
    win.addstr(11,8,pfloat(wco2),curses.A_BOLD)
    win.addstr(12,8,pfloat(wwaste),curses.A_BOLD)
    win.addstr(13,8,pfloat(wwh2o),curses.A_BOLD)
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
    pstat = data["pstat"]
    lf = fucknum(pstat,data["lf"])
    win.addstr(1,1,"                    ",curses.A_BOLD)
    fuelbar = phbar(lf,data["mlf"])
    fuelperc = lf / data["mlf"]
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
    pstat = data["pstat"]
    oxidizer = fucknum(pstat,data["oxidizer"])
    oxibar = phbar(oxidizer,data["moxidizer"])
    oxiperc = oxidizer / data["moxidizer"]
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
    pstat = data["pstat"]
    mono = fucknum(pstat,data["mono"])
    monobar = phbar(mono,data["mmono"])
    monoperc = mono / data["mmono"]
    win.move(1,1)
    printhbar(win,monobar,monoperc)
    win.refresh()

def init_elec_window(win,y,x):
    elecwin = curses.newwin(3,37,y,x)
    elecwin.box()
    elecwin.bkgd(curses.color_pair(1));
    win.refresh()
    elecwin.addstr(0,1,"T.ELEC",curses.A_BOLD)
    elecwin.refresh()
    return elecwin

def draw_elec_window(win,data):
    win.addstr(1,1,"                   ",curses.A_BOLD)
    pstat = data["pstat"]
    w = fucknum(pstat,data["w"])
    elecbar = phbar(w,data["mw"])
    elecperc = w / data["mw"]
    win.move(1,1)
    printhbar(win,elecbar,elecperc)
    win.refresh()

def init_o2_window(win,y,x):
    o2win = curses.newwin(3,37,y,x)
    o2win.box()
    o2win.bkgd(curses.color_pair(1));
    win.refresh()
    o2win.addstr(0,1,"T.O2",curses.A_BOLD)
    o2win.refresh()
    return o2win

def draw_o2_window(win,data):
    win.addstr(1,1,"                   ",curses.A_BOLD)
    pstat = data["pstat"]
    o2 = fucknum(pstat,data["o2"])
    o2bar = phbar(o2,data["mo2"])
    o2perc = o2 / data["mo2"]
    win.move(1,1)
    printhbar(win,o2bar,o2perc)
    win.refresh()

def init_h2o_window(win,y,x):
    h2owin = curses.newwin(3,37,y,x)
    h2owin.box()
    h2owin.bkgd(curses.color_pair(1));
    win.refresh()
    h2owin.addstr(0,1,"T.H2O",curses.A_BOLD)
    h2owin.refresh()
    return h2owin

def draw_h2o_window(win,data):
    win.addstr(1,1,"                   ",curses.A_BOLD)
    pstat = data["pstat"]
    h2o = fucknum(pstat,data["h2o"])
    h2obar = phbar(h2o,data["mh2o"])
    h2operc = h2o / data["mh2o"]
    win.move(1,1)
    printhbar(win,h2obar,h2operc)
    win.refresh()

def mainloop(win):
    timeposx = 1
    timeposy = 1
    utimeposx = 16
    utimeposy = 1
    ctimeposx = 1
    ctimeposy = 3
    battx = 39
    batty = 5
    storx = 39
    story = 10
    wx = 58
    wy = 8
    sysx = 31
    sysy = 1
    fuelx = 1
    fuely = 5
    oxix = 1
    oxiy = 8
    monox = 1
    monoy = 11
    elecx = 1
    elecy = 14
    o2x = 1
    o2y = 17
    h2ox = 1
    h2oy = 20

    win.nodelay(1)
    init_window(win)

    timewin = init_time_window(win,timeposy,timeposx)
    utimewin = init_utime_window(win,utimeposy,utimeposx)
    ctimewin = init_ctime_window(win,ctimeposy,ctimeposx)
    syswin = init_sys_window(win,sysy,sysx)
    battwin = init_batt_window(win,batty,battx)
    storwin = init_stor_window(win,story,storx)
    wwin = init_weight_window(win,wy,wx)
    lfuelwin = init_lfuel_window(win,fuely,fuelx)
    oxiwin = init_oxi_window(win,oxiy,oxix)
    monowin = init_mono_window(win,monoy,monox)
    elecwin = init_elec_window(win,elecy,elecx)
    o2win = init_o2_window(win,o2y,o2x)
    h2owin = init_h2o_window(win,h2oy,h2ox)

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange='logs',type='fanout')
    channel.queue_bind(exchange='logs',queue='ksp_data')

    def callback(ch, method, properties, body):
        indata = marshal.loads(body)
        data = dict(indata)
        write_datetime(win)
        tele = getTelemetry(data)
        write_datetime(win)
        draw_time_window(timewin,tele)
        draw_utime_window(utimewin,tele)
        draw_ctime_window(ctimewin,tele)
        draw_sys_window(syswin,tele)
        draw_batt_window(battwin,tele)
        draw_stor_window(storwin,tele)
        draw_weight_window(wwin,tele)
        draw_lfuel_window(lfuelwin,tele)
        draw_oxi_window(oxiwin,tele)
        draw_mono_window(monowin,tele)
        draw_elec_window(elecwin,tele)
        draw_o2_window(o2win,tele)
        draw_h2o_window(h2owin,tele)
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



