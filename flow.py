    #!/usr/bin/python
#flowsensor.py
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
    
    with open('objs.pkl') as f:  # Python 3: open(..., 'rb')
        bot_token, bot_chatID = pickle.load(f)
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message

    response = requests.get(send_text)

    return response.json()


FLOW_SENSOR = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(FLOW_SENSOR, GPIO.IN, pull_up_down = GPIO.PUD_UP)

global count
count = 0
global cicliazero
global lastlog
global lastday
global positivi
with open('ciclipositivi.txt', 'r') as f:
    ciclipositivi = f.read()
with open('cicliazero.txt', 'r') as f:
    cicliazero = f.read()
with open('lastlog.txt', 'r') as f:
    lastlog = f.read()
with open('lastday.txt', 'r') as f:
    lastday = f.read()
# dd/mm/YY H:M:S
now = datetime.now()

#reading water sensor
def countPulse(channel):
   global count
   global cicliazero
   global ciclipositivi
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
        strhflow = str("Flow: %.3f L/hr" % (hflow))
        # dd/mm/YY H:M:S - time format
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        today = now.strftime("%d/%m/%Y")
        print today
        print lastday
        #if today == lastday:
            #print "Yep. Today is today"
        if hflow > 1:
            appendme = str(dt_string + " - " + strmflow + " - " + strhflow)
            appendmetg = str(dt_string + "\n" + strmflow + "\n" + strhflow)
            totg = telegram_bot_sendtext(appendmetg)
            with suppress_stdout():
                print(totg)
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            with open('lastflow.txt','w') as f:
                f.write(str(dt_string))
        #with open('out.txt', 'r') as original: data = original.read()
        #with open('out.txt', 'w') as modified: modified.write(appendme + "\n" + data)
        
        print "FLOW IS:" + str(flow)
        #if there is no flow then...
        if flow < 0.01: #ciclinegativi
            cicliazero = int(cicliazero)+1
            with open('cicliazero.txt','w') as f:
                f.write(str(cicliazero))
            ciclipositivi = 0
            with open('ciclipositivi.txt','w') as f:
                f.write(str(ciclipositivi))
                print "cicliazero =" + str(cicliazero)
                if cicliazero == 5:
                    appendmetg = str(dt_string + "\n" + "FINE FORNITURA" + "\n" + strmflow + "\n" + strhflow)
                    totg = telegram_bot_sendtext(appendmetg)
                    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
                    dt_string2 = now.strftime("%d/%m/%Y")
                    with open('lastlog.txt','w') as f:
                        f.write(str(dt_string))
                    with open('lastday.txt','w') as f:
                        f.write(str(dt_string2))
        #if there is flow then...
        elif flow > 0.01:
            if ciclipositivi == 0:
                #inizio fornitura
                appendmetg = str(dt_string + "\n" + "INIZIO FORNITURA" + "\n" + strmflow + "\n" + strhflow)
                totg = telegram_bot_sendtext(appendmetg)
            cicliazero = 0
            with open('cicliazero.txt','w') as f:
                f.write(str(cicliazero))
            ciclipositivi = int(ciclipositivi) + 1
            with open('ciclipositivi.txt','w') as f:
                f.write(str(ciclipositivi))
            print "cicliazero =" + str(cicliazero)
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            dt_string2 = now.strftime("%d/%m/%Y")
            with open('lastlog.txt','w') as f:
                f.write(str(dt_string))
            with open('lastday.txt','w') as f:
                f.write(str(dt_string2))
        
        count = 0
        time.sleep(5)
    except KeyboardInterrupt:
        print '\ncaught keyboard interrupt!, bye'
        GPIO.cleanup()
        sys.exit()
