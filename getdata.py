#! /usr/bin/python
# coding=UTF-8
#--------------------
# KSP Telemachus
# Mission Control
# By Erik N8MJK
#--------------------

import time
import traceback
import locale
import urllib2
import json
import random
import pika
import logging
import random
import marshal

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
od = {"alt":0,"pitch":" ","yaw":" ","roll":" ","pstat":3}

pw = 0
lc = 0

def fetchData():
    global od
    global pw
    global lc
#    ip = "192.168.1.40:8023"
    ip = "108.196.82.116:8023"
#    ip = "mjuk.net:8023"
#    url = "http://" + str(ip) + "/telemachus/datalink?long=v.long"
    url = "http://" + str(ip) + "/telemachus/datalink?throt=f.throttle&rcs=v.rcsValue&sas=v.sasValue&light=v.lightValue&pe=o.PeA&ap=o.ApA&ttap=o.timeToAp&ttpe=o.timeToPe&operiod=o.period&sma=o.sma&alt=v.altitude&hat=v.heightFromTerrain&mt=v.missionTime&sfcs=v.surfaceSpeed&sfcv=v.surfaceVelocity&sfcvx=v.surfaceVelocityx&sfcvy=v.surfaceVelocityy&sfcvz=v.surfaceVelocityz&ov=v.orbitalVelocity&vs=v.verticalSpeed&lat=v.lat&long=v.long&body=v.body&o2=r.resource[Oxygen]&co2=r.resource[CarbonDioxide]&h2o=r.resource[Water]&w=r.resource[ElectricCharge]&food=r.resource[Food]&waste=r.resource[Waste]&wastewater=r.resource[WasteWater]&mo2=r.resourceMax[Oxygen]&mco2=r.resourceMax[CarbonDioxide]&mh2o=r.resourceMax[Water]&mw=r.resourceMax[ElectricCharge]&mfood=r.resourceMax[Food]&mwaste=r.resourceMax[Waste]&mwastewater=r.resourceMax[WasteWater]&pitch=n.pitch&roll=n.roll&hdg=n.heading&pstat=p.paused&inc=o.inclination&ecc=o.eccentricity&aoe=o.argumentOfPeriapsis&lan=o.lan&ut=t.universalTime&lf=r.resource[LiquidFuel]&oxidizer=r.resource[Oxidizer]&mono=r.resource[MonoPropellant]&mlf=r.resourceMax[LiquidFuel]&moxidizer=r.resourceMax[Oxidizer]&mmono=r.resourceMax[MonoPropellant]"
    try:
        u = urllib2.urlopen(url)
        d = json.load(u)
        od = d
        if d["w"] >= pw:
            lc = d["mt"]
        d["lc"] = lc
        d["wr"] = d["w"] - pw
        pw = d["w"]
        print "Got! :)"
    except:
        print "Didn't got :("
        d = od
    bytes = marshal.dumps(d)
    return bytes

def sendData(d):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
    channel = connection.channel()
    channel.queue_declare(queue="ksp_data")
    channel.basic_publish(exchange="logs", routing_key="ksp_data", body=d)
    print "Sent! :)"

def mainloop():
    while 1 is 1:
        data = fetchData()
        sendData(data)
        time.sleep(0.25)

mainloop()



