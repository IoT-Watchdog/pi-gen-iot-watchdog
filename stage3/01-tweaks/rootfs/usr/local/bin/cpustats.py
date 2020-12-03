#!/usr/bin/python3
# coding=utf-8
#
# Copyright © 2018 UnravelTEC
# Michael Maier <michael.maier+github@unraveltec.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# If you want to relicense this code under another license, please contact info+github@unraveltec.com.

import time
import json
import sys
import re
import os, signal
from subprocess import call

from argparse import ArgumentParser, RawTextHelpFormatter
import textwrap

import pprint

from copy import deepcopy

import sdnotify

def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)
  sys.stderr.flush()

# config order (later overwrites newer)
# 1. default cfg
# 2. config file
# 3. cmdline args
# 4. runtime cfg via MQTT $host/sensors/$name/config

name = "cpustats" # Uppercase
cfg = {
  "interval": 3,
  "brokerhost": "localhost",
  "configfile": "/etc/lcars/" + name.lower() + ".yml"
}

parser = ArgumentParser(description=name + 'CPU driver.\n\nDefaults in {curly braces}', formatter_class=RawTextHelpFormatter)
parser.add_argument("-i", "--interval", type=float, default=cfg['interval'],
                            help="measurement interval in s (float, default "+str(cfg['interval'])+")", metavar="x")
parser.add_argument("-D", "--debug", action='store_true', #cmdline arg only, not in config
                            help="print debug messages")

# if using MQTT
parser.add_argument("-o", "--brokerhost", type=str, default=cfg['brokerhost'],
                            help="use mqtt broker (addr: {"+cfg['brokerhost']+"})", metavar="addr")

# if using configfiles
parser.add_argument("-c", "--configfile", type=str, default=cfg['configfile'],
                            help="load configfile ("+cfg['configfile']+")", metavar="nn")

args = parser.parse_args()
DEBUG = args.debug

fcfg = deepcopy(cfg) # final config used
if os.path.isfile(args.configfile) and os.access(args.configfile, os.R_OK):
  with open(args.configfile, 'r') as ymlfile:
    import yaml
    filecfg = yaml.load(ymlfile)
    print("opened configfile", args.configfile)
    for key in cfg:
      if key in filecfg:
        value = filecfg[key]
        fcfg[key] = value
        print("used file setting", key, value)
    for key in filecfg:
      if not key in cfg:
        value = filecfg[key]
        fcfg[key] = value
        print("loaded file setting", key, value)
else:
  print("no configfile found at", args.configfile)
DEBUG and print('config from default & file', fcfg)

argdict = vars(args)
for key in cfg:
  if key in argdict and argdict[key] != cfg[key]:
    value = argdict[key]
    fcfg[key] = value
    print('cmdline param', key, 'used with', value)

cfg = fcfg
required_params = ['brokerhost']
for param in required_params:
  if not param in cfg or not cfg[param]:
    eprint('param', param, 'missing from config, exit')
    exit(1)


print("config used:", cfg)

n = sdnotify.SystemdNotifier()

hostname = os.uname()[1]

brokerhost = cfg['brokerhost']
import paho.mqtt.client as mqtt

def mqttConnect():
  while True:
    try:
      print("mqtt: Connecting to", brokerhost)
      client.connect(brokerhost,1883,60)
      print('mqtt: connect successful')
      break
    except Exception as e:
      eprint('mqtt: Exception in client.connect to "' + brokerhost + '", E:', e)
      print('mqtt: next connect attempt in 3s... ', end='')
      time.sleep(3)
      print('retry.')

def mqttReconnect():
  print('mqtt: attempting reconnect')
  while True:
    try:
      client.reconnect()
      print('mqtt: reconnect successful')
      break
    except ConnectionRefusedError as e:
      eprint('mqtt: ConnectionRefusedError', e, '\nnext attempt in 3s')
      time.sleep(3)

def onConnect(client, userdata, flags, rc):
  try:
    if rc != 0:
      eprint('mqtt: failure on connect to broker "'+ brokerhost+ '", result code:', str(rc))
      if rc == 3:
        eprint('mqtt: broker "'+ brokerhost+ '" unavailable')
    else:
      print("mqtt: Connected to broker", brokerhost, "with result code", str(rc))
      return
  except Exception as e:
    eprint('mqtt: Exception in onConnect', e)
  mqttConnect()

MQTT_ERR_SUCCESS = mqtt.MQTT_ERR_SUCCESS
MQTT_ERR_NO_CONN = mqtt.MQTT_ERR_NO_CONN
def mqttPub(topic, payload, retain = True):
  try:
    (DEBUG or first_run) and print(topic, payload, "retain =", retain)
    ret = client.publish(topic, payload, retain=retain)
    if ret[0] == MQTT_ERR_SUCCESS:
      n.notify("WATCHDOG=1")
    elif ret[0] == MQTT_ERR_NO_CONN:
      eprint('no mqtt connnection')
      mqttReconnect()
    else:
      eprint('mqtt publishing not successful,', ret)
  except Exception as e:
    eprint('Exception in client.publish', e, topic, payload_json)

def mqttJsonPub(topic, payload_json, retain=True):
  mqttPub(topic, json.dumps(payload_json, separators=(',', ':'), sort_keys=True), retain)

client = mqtt.Client(client_id=name, clean_session=True) # client id only useful if subscribing, but nice in logs # clean_session if you don't want to collect messages if daemon stops
client.on_connect = onConnect
mqttConnect()
client.loop_start()

topic_cput = hostname + '/sensors/CPU/temperature'

serial = "?"
arch = "?"
with open("/proc/cpuinfo",'r') as lines:
  for line in lines:
    if line.startswith("Serial"):
      serial = line.split(":",1)[1].strip()
    if line.startswith("model"):
      arch = re.split("[ -]", line.split(":",1)[1].strip())[0]

model = "?"
with open("/proc/device-tree/model",'r') as lines:
  for line in lines:
    model = line.rstrip('\x00')


import json
jsontags = {
  "serial": serial,
  "arch": arch,
  "model": model,
  "interval_s": int(cfg['interval'])
  }
print(jsontags)

def exit_gracefully(a=False,b=False):
  print("exit gracefully...")
  client.disconnect()
  exit(0)

def exit_hard():
  print("exiting hard...")
  exit(1)

signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)

cpu_t_file = "/sys/class/thermal/thermal_zone0/temp"

first_run = True

MEAS_INTERVAL = cfg['interval']

n.notify("READY=1") #optional after initializing
while True:
  run_started_at = time.time()
  
  values = {}
  with open(cpu_t_file,'r') as temp_lines:
    for line in temp_lines:
      values["cpu_degC"] = float(line.strip()) / 1000
        
  payload = {
      "tags": jsontags,
      "values": values,
      "UTS": round(run_started_at, 3)
      }

  mqttJsonPub(topic_cput, payload)

  first_run = False

  run_finished_at = time.time()
  run_duration = run_finished_at - run_started_at

  DEBUG and print("duration of run: {:10.4f}s.".format(run_duration))

  to_wait = MEAS_INTERVAL - run_duration
  if to_wait > 0:
    DEBUG and print("wait for {0:4f}s".format(to_wait))
    time.sleep(to_wait - 0.002)
  else:
    DEBUG and print("no wait, {0:4f}ms over".format(- to_wait*1000))
