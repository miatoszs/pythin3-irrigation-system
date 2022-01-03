#!/usr/bin/python3
import RPi.GPIO as GPIO
import time, datetime
import json
import os
import signal


CONFIG_FILE = 'config.json'

last_read_timestamp = 0

def signal_handler(sig, frame):
    '''
    signal kezeles
    '''
    global running
    print("Received CTRL-BREAK, stopping..." )
    running = False

def configtime_to_unix_timestamp(starttime):
    ''' 
    Unix timestampre atalakitja a bemeno parameterben megadott oo:pp:mm idot
    oly modon, hogy kiegesziti az aktualis datum napjaval
    '''
    t = datetime.datetime.now().strftime("%Y-%m-%d") + ' ' + starttime
    aaa = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S").timetuple()
    return(int(time.mktime(aaa)))

def on_off_state(t, start, stop):
    # Eldonti, hogy benne vagyunk-e az ontozesi program intervallumban
    if t >= start and t < stop:
        return(True)
    else:
        return(False)

def read_config():
    ''' 
    Beolvassa a CONFIG_FILE fileban talalhato json formatumu config filet, 
    extra funkcioja, hogy csak akkor olvassa be ha konfig file os mtime attributuma ujabb,
    mint a legutolso alkalommal volt
    '''
    global CONFIG_FILE, last_read_timestamp, config, program
    # itt ellenorizzuk a legutolso alkalommal elmentett mtime erteket a mostanival
    if last_read_timestamp == int(os.path.getmtime(CONFIG_FILE)):
        return(config, program)
    if last_read_timestamp == 0:
        print("Reading config")
    else:
        print("Rereading config")
    last_read_timestamp = int(os.path.getmtime(CONFIG_FILE))

    with open(CONFIG_FILE) as f:
        # config valtozo tartalmazza a json file tartalmat
        config = json.load(f)
    #print(config)
    for zona in config['zonelist']:
        GPIO.setup(zona['pin'], GPIO.OUT)
    set_zone_pins_to_default_state()
    program = create_program_from_config(config)
    return(config, program)

def create_program_from_config(config):
    '''
    program dict valtozoba kigyujtjuk a config program alapjan az elemeket, 
    mikozben a start kulcs ertekeket atalakitjuk unix timestampre, az atfedo startokat eltoljuk a korabbi program vegere
    '''

    # ideiglenes dict letesitese, sorszam kulcssal
    tmp = {}
    index = 0
    for zona in config['zonelist']:
        for zona_program in zona['program']:
            #  a programban tarolt oo:pp:mm atalakitasa unix timestampre sajat fugvennyel
            start_unixtime = configtime_to_unix_timestamp(zona_program['start'])
            tmp[index] = {}
            tmp[index]['start']  = start_unixtime
            tmp[index]['start_orig'] = zona_program['start']
            tmp[index]['stop'] = int(start_unixtime + zona_program['interval'] * config['interval_multiplier']* 60)
            tmp[index]['interval'] = zona_program['interval']
            tmp[index]['name'] = zona['name']
            tmp[index]['pin'] = zona['pin']
            index += 1
    last_stop = 0
    program = {}
    # tmp elemek start ertekek ellenorzese, atfedes eseten csusztatas az elozo program vegere
    for k,v in sorted(tmp.items(), key=lambda x: x[0]):
        program[k] = v.copy()
        program[k]['running'] = False
        program[k]['interval'] = v['interval'] * config['interval_multiplier']* 60
        if v['start'] <= last_stop:
            program[k]['start'] = last_stop
            program[k]['start_orig'] = datetime.datetime.fromtimestamp(last_stop).strftime("%H:%M:%S")
            program[k]['tampered'] = True
            program[k]['stop'] = int(last_stop + v['interval'] * config['interval_multiplier']* 60)
        last_stop = program[k]['stop']

    for k,v in program.items():
        print(k, v)
        pass
    return(program)


def set_zone_pins_to_default_state():
    for zone in config['zonelist']:
        print(zone['pin'], 'pin kikapcsolasa')
        GPIO.output(zone['pin'], GPIO.HIGH)

# A raspberry PI fizikai pin sorszam hivatkozast allitjuk be
GPIO.setmode(GPIO.BOARD)

# signal hander beallitasa 
signal.signal(signal.SIGINT, signal_handler)
running = True

# Itt kezdodik a program fo resze, ami vegtelen ciklusban fut
while running:
    config, program = read_config()
    if config['suspend'] == True:
        time.sleep(1)
        continue
    #aktualis futasi timestamp eltarolasa
    t = int(time.time())
    # a program idopontok szerinti rendezese es az elemek iteracioja
    for k in sorted(program):
        # debug
        #print(k, program[k])
        # itt szuletik meg a zona pin statusa az aktualis illetve a programban tarolt start es interval alapjan 
        status = on_off_state(t, program[k]['start'], program[k]['stop'])
        # comment kozos reszenek elokeszitese 
        comment = str(k) +  '. program, "' + program[k]['name'] + '" zona, pin:#'+str(program[k]['pin'])
        # a GPIO pineket csak akkor csesztetjuk, ha szukseges es az adott program fut, vagy epp er veget
        if status and not program[k]['running']:
            program[k]['running'] = True
            GPIO.output(program[k]['pin'], GPIO.LOW)
            print(comment, 'bekapcsol')
        elif not status and program[k]['running']:
            GPIO.output(program[k]['pin'], GPIO.HIGH)
            program[k]['running'] = False
            print(comment, 'kikapcsol')

        if status:
            print(comment, 'aktiv, lekapcsolas: ', program[k]['stop'] - t, 's mulva')
    time.sleep(1)

# Takaritas, alapallapotba allitas
set_zone_pins_to_default_state()
GPIO.cleanup()

