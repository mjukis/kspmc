import random
import time
import datetime
import curses


#-------------------------------------------------------
# functions that modify data or make strings

def xstr(s):
    #versatile maker of strings from other variable types
    if s is None:
        return ''
    return str(s)

def pfloat(num):
    #makes a pretty string out of a float
    if isNum(num):
        nnum = xstr("{:,}".format(round(num,2)))
    else:
        nnum = num
    return nnum

def get_datetime():
    #makes a pretty local date and time
    global timeoutput
    global dateoutput
    t = datetime.datetime.now()
    currdatetime = t.timetuple()
    dateoutput = time.strftime("%Y-%m-%d",currdatetime)
    timeoutput = time.strftime("%d %b %Y %H:%M:%S",currdatetime)

def write_datetime(win):
    #writes pretty dates and times top right in the window
    get_datetime()

    win.move(0,59)
    win.clrtoeol()
    win.addstr(timeoutput, curses.A_REVERSE)
    win.refresh()

def isNum(num):
    #returns true if a variable is a number that can be used for calculations
    try:
        float(num)
        return True
    except ValueError:
        pass
    return False

def rSlop(num):
    #fumbles numbers (for inexact readings)
    if isNum(num):
        nnum = num * random.uniform(0.99,1.01)
        return nnum
    else:
        return num

def rAlt(num):
    #rounds numbers for less accuracy
    if isNum(num):
        nnum = round(int(num),-2)
        return nnum
    else:
        return num

def getTelemetry(d):
    #prepares main data list for use as telemetry and returns it
    maxgralt = "15000" #max altitude for ground radar
#    if d["ttt1"] > 0:
#        d["t1"] = d["mt"] + d["ttt1"]
#    else:
    d["t1"] = d["ttt1"]
#    if d["ttt2"] > 0:
#        d["t2"] = d["mt"] + d["ttt2"]
#    else:
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
    #destroys strings if there is an error present on the Telemachus antenna
    #status comes as 0 = fine, 1 = paused, 2 = out of power,
    #3 = antenna turned off and 4 = antenna doesn't exist
    if status == 0 or status == 1: #all is well, return the original value
        return instring
    if isNum(instring):
        workstring = str(instring)
    else:
        workstring = instring
    if status == 2: #no power to antenna
        worklist = list(workstring) #divide incoming data into a list of characters
        for i,char in enumerate(worklist): #randomly replace characters
            charlist = [char,char,char,char,char,char,char,char,char,char,char,char,char,char,char,'!','?','i','$','/','|','#']
            newchar = random.choice(charlist)
            worklist[i] = newchar
        outstring = "".join(worklist)
    if status == 3 or status == 4: #antenna is off or doesn't exist, return blanks
        worklist = list(workstring) #divide incoming data into a list of characters
        for i,char in enumerate(worklist):
            newchar = " "
            worklist[i] = newchar
        outstring = "".join(worklist)    
    return outstring

def fucknum(status,indata):
    #introduces errors to numbers if there is an error present on the Telemachus antenna,
    #see fuck()
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
    #makes a pretty stirng out of a number
    if isNum(num):
        nnum = xstr("{:,}".format(int(num)))
    else:
        nnum = num
    return nnum

def pvel(num):
    #makes a velocity into a readable string
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
    #makes a string that displays amount and percentage for horizontal bars
    if isNum(num) and isNum(mnum):
        pnum = int((num / mnum) * 100)
        onum = xstr(" " + "{:,}".format(round(num,1))) + " (" + xstr(pnum) + "%)"
    else:
        onum = num
    return onum

def printwarn(win,warn,state):
    #prints a warning indicator
    if state == 0:
        win.addstr(1,1,warn,curses.A_BOLD)
    else:
        win.addstr(1,1,warn,curses.A_BLINK + curses.A_REVERSE)

def printhbar(win,instr,perc):
    #prints a horizontal bar
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
    #prints a vertical bar
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
    #makes a sensible string out of an angle
    if isNum(inum):
        num = xstr(abs(int(inum))).zfill(3)
        if inum < 0:
            nnum = "-%s" % num
        else:
            nnum = "+%s" % num
    else:
        nnum = inum
    return nnum

def pdate(num):
    #makes a date string out of count of seconds
    if isNum(num):
        m, s = divmod(num, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        y, d = divmod(d, 365)
        d = str(int(d)).zfill(3)
        y = str(int(y)).zfill(2)
        nnum = "Y%s D%s" % (y,d)
    else:
        nnum = num
    return nnum

def ptime(num):
    #makes a time string out of a count of seconds
    if isNum(num):
        m, s = divmod(num, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        y, d = divmod(d, 365)
        ys = str(int(y)).zfill(2)
        ds = str(int(d)).zfill(3)
        hs = str(int(h)).zfill(2)
        ms = str(int(m)).zfill(2)
        ss = str(int(s)).zfill(2)
        nnum = "%s:%s:%s" % (hs,ms,ss)
        if d >= 365:
            nnum = "%sy %sd" % (ys,ds)
        if h >= 24:
            nnum = "%s/%s%s" % (ds,hs,ms) 
    else:
        nnum = num
    return nnum

def pltime(num):
    #makes a long time (day + time) string out of a count of seconds
    if isNum(num):
        m, s = divmod(num, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        y, d = divmod(d, 365)
        sy = xstr(int(y)).zfill(2)
        syl = xstr(int(y)).zfill(4)
        sd = xstr(int(d)).zfill(3)
        sh = xstr(int(h)).zfill(2)
        sm = xstr(int(m)).zfill(2)
        ss = xstr(int(s)).zfill(2)
        nnum = "%s/%s:%s:%s" % (sd,sh,sm,ss)
        if d >= 365:
            nnum = "%sy%s/%s:%s" % (sy,sd,sh,sm)
        if y >= 99:
            nnum = "%sy%s/%sh" % (syl,sd,sh)
    else:
        nnum = num
    return nnum

def palt(num):
    #makes a sensible string out of an altitude in meters
    kmlimit = 100000
    mmlimit = 1000000
    if isNum(num):
        if abs(num) < kmlimit:
            nnum = xstr("{:,}".format(int(num))) + "m"
        if abs(num) >= kmlimit:
            nnum = xstr("{:,}".format(round(num / 1000,1))) + "km"
        if abs(num) >= kmlimit * 10:
            nnum = xstr("{:,}".format(int(round(num / 1000,0)))) + "km"
        if abs(num) >= mmlimit:
            nnum = xstr("{:,}".format(round(num / 1000000,2))) + "Mm"
        if abs(num) >= mmlimit * 10000:
            nnum = xstr("{:,}".format(int(round(num / 1000000,0)))) + "Mm"
    else:
        nnum = num
    return nnum

def pwgt(num):
    #makes a sensible string out of a mass in kilograms
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
    #makes a sensible string out of a latitude
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
    #makes a sensible string out of a longitude
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

#---------------------------------------------------------
# functions that initialize or print windows

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

def init_date_window(win,y,x,title):
    datewin = curses.newwin(2,10,y,x)
    datewin.box()
    datewin.bkgd(curses.color_pair(1));
    win.refresh()
    datewin.addstr(0,1,title,curses.A_BOLD)
    datewin.refresh()
    return datewin

def draw_date_window(win,data):
    win.addstr(1,1,"        ",curses.A_BOLD)
    win.addstr(1,1,pdate(data),curses.A_BOLD)
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

def init_hbar_window(win,y,x,title):
    nwin = curses.newwin(3,37,y,x)
    nwin.box()
    nwin.bkgd(curses.color_pair(1));
    win.refresh()
    nwin.addstr(0,1,title,curses.A_BOLD)
    nwin.refresh()
    return nwin

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
