#! /usr/bin/python
# coding=UTF-8
#----------------------
# KSP Telemachus
# Mission Control
# Flight Overview v0.90
# By Erik N8MJK
#----------------------

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
from kspmc import *

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

def init_window(win):
    win.erase()
    topstring = "FLIGHT OVERVIEW v0.90"
    bottomstring = "ORBITAL POSITION, RADAR AND BASIC FUEL TELEMETRY"
    bottomfillstring = (78- len(bottomstring)) * " "
    topfillstring  = (78 - len(topstring)) * " "
    win.addstr(0,0," " + topstring + topfillstring, curses.A_REVERSE)
    win.addstr(23,0,bottomfillstring + bottomstring + " ", curses.A_REVERSE)

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

def init_sys_window(win,y,x):
    syswin = curses.newwin(2,21,y,x)
    syswin.box()
    syswin.bkgd(curses.color_pair(1));
    win.refresh()
    syswin.addstr(0,1,"SYSTEMS",curses.A_BOLD)
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
    if data["pstat"] == 0:
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
    pstat = data["pstat"]
    body = pnum(data["body"])
    altt = fuck(pstat,pnum(data["altt"]))
    alt = fuck(pstat,palt(data["alt"]))
    lat = fuck(pstat,plat(data["lat"]))
    long = fuck(pstat,plong(data["long"]))
    ttap = fuck(pstat,ptime(data["ttap"]))
    ttpe = fuck(pstat,ptime(data["ttpe"]))
    pitch = fuck(pstat,pdeg(data["pitch"]))
    roll = fuck(pstat,pdeg(data["roll"]))
    hdg = fuck(pstat,pdeg(data["hdg"]))
    win.addstr(1,8,"         ",curses.A_BOLD)
    win.addstr(2,8,"         ",curses.A_BOLD)
    win.addstr(3,8,"         ",curses.A_BOLD)
    win.addstr(4,8,"         ",curses.A_BOLD)
    win.addstr(5,8,"         ",curses.A_BOLD)
    win.addstr(6,8,"         ",curses.A_BOLD)
    win.addstr(7,8,"         ",curses.A_BOLD)
    win.addstr(8,8,"         ",curses.A_BOLD)
    win.addstr(9,8,"         ",curses.A_BOLD)
    win.addstr(1,8,body.upper(),curses.A_BOLD)
    win.addstr(2,7,altt)
    win.addstr(2,8,alt,curses.A_BOLD)
    win.addstr(3,8,lat,curses.A_BOLD)
    win.addstr(4,8,long,curses.A_BOLD)
    win.addstr(5,8,ttap,curses.A_BOLD)
    win.addstr(6,8,ttpe,curses.A_BOLD)
    win.addstr(7,8,pitch,curses.A_BOLD)
    win.addstr(8,8,roll,curses.A_BOLD)
    win.addstr(9,8,hdg,curses.A_BOLD)
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
    pstat = data["pstat"]
    sma = fuck(pstat,palt(data["sma"]))
    ap = fuck(pstat,palt(data["ap"]))
    pe = fuck(pstat,palt(data["pe"]))
    inc = fuck(pstat,pdeg(data["inc"]))
    lan = fuck(pstat,plong(data["lan"]))
    operiod = fuck(pstat,ptime(data["operiod"]))
    ov = fuck(pstat,pvel(data["ov"]))
    win.addstr(1,8,"         ",curses.A_BOLD)
    win.addstr(2,8,"         ",curses.A_BOLD)
    win.addstr(3,8,"         ",curses.A_BOLD)
    win.addstr(4,8,"         ",curses.A_BOLD)
    win.addstr(5,8,"         ",curses.A_BOLD)
    win.addstr(6,8,"         ",curses.A_BOLD)
    win.addstr(7,8,"         ",curses.A_BOLD)
    win.addstr(1,8,sma,curses.A_BOLD)
    win.addstr(2,8,ap,curses.A_BOLD)
    win.addstr(3,8,pe,curses.A_BOLD)
    win.addstr(4,8,inc,curses.A_BOLD)
    win.addstr(5,8,lan,curses.A_BOLD)
    win.addstr(6,8,operiod,curses.A_BOLD)
    win.addstr(7,8,ov,curses.A_BOLD)
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
    pstat = data["pstat"]
    grstatus = fuck(pstat,xstr(data["grstatus"]))
    hat = fuck(pstat,palt(data["hat"]))
    asl = fuck(pstat,palt(data["asl"]))
    altt = fuck(pstat,xstr(data["altt"]))
    vs = fuck(pstat,pvel(data["vs"]))
    hs = fuck(pstat,pvel(data["hs"]))
    sfcv = fuck(pstat,pvel(data["sfcv"]))
    sfcvx = fuck(pstat,pvel(data["sfcvx"]))
    sfcvy = fuck(pstat,pvel(data["sfcvy"]))
    sfcvz = fuck(pstat,pvel(data["sfcvz"]))
    if isNum(vs) == False:
        altt = " "
    win.addstr(1,8,"         ",curses.A_BOLD)
    win.addstr(2,8,"         ",curses.A_BOLD)
    win.addstr(3,8,"         ",curses.A_BOLD)
    win.addstr(4,8,"         ",curses.A_BOLD)
    win.addstr(5,8,"         ",curses.A_BOLD)
    win.addstr(6,8,"         ",curses.A_BOLD)
    win.addstr(7,8,"         ",curses.A_BOLD)
    win.addstr(8,8,"         ",curses.A_BOLD)
    win.addstr(9,8,"         ",curses.A_BOLD)
    win.addstr(1,8,grstatus,curses.A_BOLD)
    win.addstr(2,8,hat,curses.A_BOLD)
    win.addstr(3,8,asl,curses.A_BOLD)
    win.addstr(4,7,altt,curses.A_BOLD)
    win.addstr(4,8,vs,curses.A_BOLD)
    win.addstr(5,8,hs,curses.A_BOLD)
    win.addstr(6,8,sfcv,curses.A_BOLD)
    win.addstr(7,8,sfcvx,curses.A_BOLD)
    win.addstr(8,8,sfcvy,curses.A_BOLD)
    win.addstr(9,8,sfcvz,curses.A_BOLD)
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
    if data["pstat"] == 0:
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

def processData(indata):
    if indata["pstat"] == 0:
        outdata = indata
    if indata["pstat"] == 1:
        #paused, do stuff?
        outdata = indata
#        outdata["alt"] = "ERR!"
    if indata["pstat"] == 1:
        #out of power
        outdata = indata
        numerr = random.uniform(0.75,1.25)
        outdata["alt"] = indata["alt"] * numerr
        numerr = random.uniform(0.9,1.1)
        outdata["pitch"] = indata["pitch"] * numerr
        numerr = random.uniform(0.9,1.1)
        outdata["roll"] = indata["roll"] * numerr
        numerr = random.uniform(0.9,1.1)
        outdata["hdg"] = indata["hdg"] * numerr
        outdata["tstatus"] = 0
        outdata["lf"] = indata["lf"] * numerr
        outdata["tstatus"] = 0
        outdata["oxidizer"] = indata["oxidizer"] * numerr
        outdata["tstatus"] = 0
    if indata["pstat"] == 3:
        #no antenna
        outdata = indata
#               else:
#                   ns = list(indata[key])
#                   for (n,value) in ns.items():
#                       error = random.uniform(0.9,1.1)
#                       nc = chr(ord(value) * error)
    return outdata

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
    datex = 31
    datey = 1
    udatex = 42
    udatey = 1
    sysx = 55
    sysy = 1
    sfcx =58
    sfcy = 12
    fuelx = 1
    fuely = 14
    oxix = 1
    oxiy = 17
    monox = 1
    monoy = 20
    alarmx = 39
    alarmy = 12
    wrx = 46
    wry = 12
    wtx = 39
    wty = 15
    wgx = 46
    wgy = 15
    throtx = 53
    throty = 12

    win.nodelay(1)
    init_window(win)

    timewin = init_time_window(win,timeposy,timeposx,"MISSION TIME")
    utimewin = init_time_window(win,utimeposy,utimeposx,"UNIVRSL TIME")
    datewin = init_date_window(win,datey,datex,"M DATE")
    udatewin = init_date_window(win,udatey,udatex,"U DATE")
    syswin = init_sys_window(win,sysy,sysx)
    twin = init_tpos_window(win,tposy,tposx)
    rwin = init_rpos_window(win,rposy,rposx)
    rowin = init_rorb_window(win,roposy,roposx)
    owin = init_orbit_window(win,oposy,oposx)
    sfcwin = init_sfc_window(win,sfcy,sfcx)
    lfuelwin = init_hbar_window(win,fuely,fuelx,"T.LIQUID FUEL")
    oxiwin = init_hbar_window(win,oxiy,oxix,"T.OXIDIZER")
    monowin = init_hbar_window(win,monoy,monox,"T.MONOPROPELLANT")
    wrwin = init_wr_window(win,wry,wrx)
    wtwin = init_wt_window(win,wty,wtx)
    wgwin = init_wg_window(win,wgy,wgx)
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
        draw_date_window(datewin,tele["mt"])
        draw_date_window(udatewin,tele["ut"])
        draw_sys_window(syswin,tele)
        draw_tpos_window(twin,tele)
        draw_rpos_window(rwin,radar)
        draw_rorb_window(rowin,radar)
        draw_orbit_window(owin,tele)
        draw_sfc_window(sfcwin,tele)
        draw_hbar_window(lfuelwin,tele,"lf","mlf")
        draw_hbar_window(oxiwin,tele,"oxidizer","moxidizer")
        draw_hbar_window(monowin,tele,"mono","mmono")
        draw_wr_window(wrwin,tele)
        draw_wt_window(wtwin,tele)
        draw_wg_window(wgwin,tele)
        draw_alarm_window(alarmwin,tele)
        draw_throt_window(throtwin,tele)
        write_datetime(win)

    channel.basic_consume(callback, queue="ksp_data", no_ack=True)
    channel.start_consuming()

if __name__=='__main__':
    start_module(mainloop)
