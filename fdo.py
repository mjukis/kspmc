#! /usr/bin/python
# coding=UTF-8
#----------------------
# KSP Telemachus
# Mission Control
# Flight Dynamics v0.65
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
import math
from kspmc import *

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

def init_window(win):
    win.erase()
    topstring = "FLIGHT DYNAMICS v0.65"
    bottomstring = "ORBITAL PARAMETERS AND DESIRED CHANGES"
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

if __name__=='__main__':
    start_module(mainloop)
