#!/usr/bin/python
import RPi.GPIO as GPIO
import time, sys
import requests
from datetime import datetime
from datetime import date
import sys
import io
from contextlib import contextmanager
import sys, os
from datetime import datetime as dt
import pickle

@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout

def telegram_bot_sendtext(bot_message):
    with open('vars.pkl') as f:  # Python 3: open(..., 'rb')
        bot_token, bot_chatID, lastday, lastlog, posloops,negloops = pickle.load(f)
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
    response = requests.get(send_text)
    return response.json()

FLOW_SENSOR = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(FLOW_SENSOR, GPIO.IN, pull_up_down = GPIO.PUD_UP)

global count
global negloops
global lastlog
global lastday
global positivi
global bot_token
global bot_chatID
count = 0
with open('vars.pkl') as f:  # Python 3: open(..., 'rb')
        bot_token, bot_chatID, lastday, lastlog, posloops,negloops = pickle.load(f)

# dd/mm/YY H:M:S
now = datetime.now()

#reading water sensor
def countPulse(channel):
   global count
   global negloops
   global posloops
   global lastlog
   if start_counter == 1:
      count = count+1   
      flow = count / (60 * 7.5)
      #print(flow)

GPIO.add_event_detect(FLOW_SENSOR, GPIO.FALLING, callback=countPulse)

while True:
    try:
        start_counter = 1
        time.sleep(1)
        start_counter = 0
        flow = (count * 60 * 2.25 / 1000)
        hflow = flow * 60
        print "Flow: %.3f L/min" % (flow)
        print "Hflow: %.3f L/hr" % (hflow)
        strmflow = str("Flow: %.3f L/min" % (flow))
        strhflow = str("HFlow: %.3f L/hr" % (hflow))
        # dd/mm/YY H:M:S - time format
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        today = now.strftime("%d/%m/%Y")
        print today
        
        if flow < 0.01: #ciclinegativi
            negloops = int(negloops)+1
            posloops = 0
            print "negloops = " + str(negloops)
            if negloops == 5:
                #telegram packet
                payloadtg = str(dt_string + "\n" + "FLOW STOP" + "\n" + strmflow + "\n" + strhflow)
                totg = telegram_bot_sendtext(payloadtg)

        #if there is flow then...
        elif flow > 0.01:
            if posloops == 0:
                #water day start
                payloadtg = str(dt_string + "\n" + "FLOW START" + "\n" + strmflow + "\n" + strhflow)
                totg = telegram_bot_sendtext(payloadtg)
            negloops = 0
            posloops = int(posloops) + 1
            print "negloops = " + str(negloops)
            print "posloops = " + str(posloops)
            lastlog = str(now.strftime("%d/%m/%Y %H:%M:%S"))
            lastday = str(now.strftime("%d/%m/%Y"))
            lastflow = str(lastlog)
            #telegram packet
            payloadtg = str(lastlog + "\n" + strmflow + "\n" + strhflow)
            totg = telegram_bot_sendtext(payloadtg)
            with suppress_stdout():
                print(totg)
            

            
        #saving data
        with open('vars.pkl', 'w') as f:  # P3: open(..., 'wb')
            pickle.dump([bot_token, bot_chatID,lastday,lastlog,posloops,negloops], f)
            
        #reset tp counters
        count = 0
        time.sleep(5)
    except KeyboardInterrupt:
        print '\ncaught keyboard interrupt!, bye'
        GPIO.cleanup()
        sys.exit()
