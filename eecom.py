#! /usr/bin/python
# coding=UTF-8
#--------------------
# KSP Telemachus
# Mission Control
# EECOM v0.96
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
from kspmc import *

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

def init_window(win):
    win.erase()
    topstring = "EECOM v0.96"
    bottomstring = "ELECTRICAL, ENVIRONMENTAL AND COMSUMABLES TELEMETRY"
    bottomfillstring = (78- len(bottomstring)) * " "
    topfillstring  = (78 - len(topstring)) * " "
    win.addstr(0,0," " + topstring + topfillstring, curses.A_REVERSE)
    win.addstr(23,0,bottomfillstring + bottomstring + " ", curses.A_REVERSE)

def printbwarn(win,warn,state):
    if state == 0:
        win.addstr(1,7,"    ")
        win.addstr(2,7,"    ")
        win.addstr(3,1,warn,curses.A_BOLD)
        win.addstr(4,7,"    ")
        win.addstr(5,7,"    ")
    else:
        win.addstr(1,7,"    ",curses.A_BLINK + curses.A_REVERSE)
        win.addstr(2,7,"    ",curses.A_BLINK + curses.A_REVERSE)
        win.addstr(3,1,warn,curses.A_BLINK + curses.A_REVERSE)
        win.addstr(4,7,"    ",curses.A_BLINK + curses.A_REVERSE)
        win.addstr(5,7,"    ",curses.A_BLINK + curses.A_REVERSE)

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

def init_malarm_window(win,y,x):
    alarmwin = curses.newwin(7,18,y,x)
    alarmwin.box()
    alarmwin.bkgd(curses.color_pair(1));
    win.refresh()
    alarmwin.addstr(3,1,"            ",curses.A_BOLD)
    alarmwin.refresh()
    return alarmwin

def draw_malarm_window(win,data):
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
    printbwarn(win,"  MASTER ALARM  ",state)
    win.refresh()

def init_wls_window(win,y,x):
    wlswin = curses.newwin(3,7,y,x)
    wlswin.box()
    wlswin.bkgd(curses.color_pair(1));
    win.refresh()
    wlswin.addstr(1,1,"     ",curses.A_BOLD)
    wlswin.refresh()
    return wlswin

def draw_wls_window(win,data):
    o2p = data["o2"] / data["mo2"]
    h2op = data["h2o"] / data["mh2o"]
    foodp = data["food"] / data["mfood"]
    if o2p > 0.1 and h2op > 0.1 and foodp > 0.1:
        state = 0
    else:
        state = 1
    printwarn(win,"LIF.S",state)
    win.refresh()

def init_wm_window(win,y,x):
    wmwin = curses.newwin(3,7,y,x)
    wmwin.box()
    wmwin.bkgd(curses.color_pair(1));
    win.refresh()
    wmwin.addstr(1,1,"     ",curses.A_BOLD)
    wmwin.refresh()
    return wmwin

def draw_wm_window(win,data):
    if data["mono"] / data["mmono"] > 0.1:
        state = 0
    else:
        state = 1
    printwarn(win," RCS ",state)
    win.refresh()

def init_wb_window(win,y,x):
    wbwin = curses.newwin(3,7,y,x)
    wbwin.box()
    wbwin.bkgd(curses.color_pair(1));
    win.refresh()
    wbwin.addstr(1,1,"     ",curses.A_BOLD)
    wbwin.refresh()
    return wbwin

def draw_wb_window(win,data):
    if data["w"] / data["mw"] > 0.1:
        state = 0
    else:
        state = 1
    printwarn(win," BAT ",state)
    win.refresh()

def init_wf_window(win,y,x):
    wfwin = curses.newwin(3,7,y,x)
    wfwin.box()
    wfwin.bkgd(curses.color_pair(1));
    win.refresh()
    wfwin.addstr(1,1,"     ",curses.A_BOLD)
    wfwin.refresh()
    return wfwin

def draw_wf_window(win,data):
    if data["lf"] / data["mlf"] > 0.1 and data["oxidizer"] / data["moxidizer"] > 0.1:
        state = 0
    else:
        state = 1
    printwarn(win,"LF/OX",state)
    win.refresh()

def init_batt_window(win,y,x):
    bwin = curses.newwin(5,18,y,x)
    bwin.box()
    bwin.bkgd(curses.color_pair(1));
    win.refresh()
    bwin.addstr(0,1,"T.BATTERIES",curses.A_BOLD)
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
    win.addstr(3,7,wr,curses.A_BOLD)
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
    win.addstr(3,8,"         ",curses.A_BOLD)
    win.addstr(4,8,"         ",curses.A_BOLD)
    win.addstr(5,8,"         ",curses.A_BOLD)
    win.addstr(7,8,"         ",curses.A_BOLD)
    win.addstr(8,8,"         ",curses.A_BOLD)
    win.addstr(9,8,"         ",curses.A_BOLD)
    win.addstr(11,8,"         ",curses.A_BOLD)
    win.addstr(12,8,"         ",curses.A_BOLD)
    win.addstr(13,8,"         ",curses.A_BOLD)
    win.addstr(1,8,pfloat(wtot),curses.A_BOLD)
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
    fuelwin.addstr(0,1,"T.BIPROPELLANT",curses.A_BOLD)
    fuelwin.refresh()
    return fuelwin

def draw_lfuel_window(win,data):
    pstat = data["pstat"]
    lf = fucknum(pstat,data["lf"])
    oxi = fucknum(pstat,data["oxidizer"])
    mlf = data["mlf"]
    moxi = data["moxidizer"]
    fuel = lf + oxi
    mfuel = mlf + moxi
    win.addstr(1,1,"                    ",curses.A_BOLD)
    fuelbar = phbar(fuel,mfuel)
    fuelperc = fuel / mfuel
    win.move(1,1)
    printhbar(win,fuelbar,fuelperc)
    win.refresh()

def mainloop(win):
    timeposx = 1
    timeposy = 1
    utimeposx = 16
    utimeposy = 1
    ctimeposx = 1
    ctimeposy = 3
    alarmx = 58
    alarmy = 1
    wlsx = 58
    wlsy = 1
    wmx = 58
    wmy = 5
    wbx = 69
    wby = 1
    wfx = 69
    wfy = 5
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
    monox = 1
    monoy = 8
    elecx = 1
    elecy = 11
    o2x = 1
    o2y = 14
    h2ox = 1
    h2oy = 17
    foodx = 1
    foody = 20

    win.nodelay(1)
    init_window(win)

    timewin = init_time_window(win,timeposy,timeposx,"MISSION TIME")
    utimewin = init_time_window(win,utimeposy,utimeposx,"UNIVRSL TIME")
    ctimewin = init_time_window(win,ctimeposy,ctimeposx,"LAST CHARGE")
    syswin = init_sys_window(win,sysy,sysx)
    alarmwin = init_malarm_window(win,alarmy,alarmx)
    wmwin = init_wm_window(win,wmy,wmx)
    wlswin = init_wls_window(win,wlsy,wlsx)
    wbwin = init_wb_window(win,wby,wbx)
    wfwin = init_wf_window(win,wfy,wfx)
    battwin = init_batt_window(win,batty,battx)
    storwin = init_stor_window(win,story,storx)
    wwin = init_weight_window(win,wy,wx)
    lfuelwin = init_lfuel_window(win,fuely,fuelx)
    monowin = init_hbar_window(win,monoy,monox,"T.MONOPROPELLANT")
    elecwin = init_hbar_window(win,elecy,elecx,"T.ELECTRIC CHARGE")
    o2win = init_hbar_window(win,o2y,o2x,"T.O2")
    h2owin = init_hbar_window(win,h2oy,h2ox,"T.H2O")
    foodwin = init_hbar_window(win,foody,foodx,"T.FOOD")

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
        draw_time_window(timewin,tele["mt"])
        draw_time_window(utimewin,tele["ut"])
        draw_time_window(ctimewin,tele["lc"])
        draw_sys_window(syswin,tele)
        draw_malarm_window(alarmwin,tele)
        draw_wls_window(wlswin,tele)
        draw_wm_window(wmwin,tele)
        draw_wb_window(wbwin,tele)
        draw_wf_window(wfwin,tele)
        draw_batt_window(battwin,tele)
        draw_stor_window(storwin,tele)
        draw_weight_window(wwin,tele)
        draw_hbar_window(lfuelwin,tele,"fuel","mfuel")
        draw_hbar_window(monowin,tele,"mono","mmono")
        draw_hbar_window(elecwin,tele,"w","mw")
        draw_hbar_window(o2win,tele,"o2","mo2")
        draw_hbar_window(h2owin,tele,"h2o","mh2o")
        draw_hbar_window(foodwin,tele,"food","mfood")
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



