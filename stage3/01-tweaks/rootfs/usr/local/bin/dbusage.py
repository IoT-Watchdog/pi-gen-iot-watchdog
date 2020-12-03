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

import sdnotify
n = sdnotify.SystemdNotifier()
n.notify("WATCHDOG=1")

import time
starttime = time.time()
print('started at', starttime)
import json
import sys
import os, signal
import subprocess

from argparse import ArgumentParser, RawTextHelpFormatter
import textwrap

import pprint

from copy import deepcopy

print('after imports', time.time() - starttime)
n.notify("WATCHDOG=1")

def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)
  sys.stderr.flush()

# config order (later overwrites newer)
# 1. default cfg
# 2. config file
# 3. cmdline args
# 4. runtime cfg via MQTT $host/sensors/$name/config

name = "DB" # Uppercase
cfg = {
  "interval": 60,
  "mqtt_influx": True,
  "mqtt_json": True,
  "brokerhost": "localhost",
  "configfile": "/etc/lcars/" + name.lower() + ".yml"
}
required_params = ['brokerhost']

parser = ArgumentParser(description=name + ' driver.\n\nDefaults in {curly braces}', formatter_class=RawTextHelpFormatter)
parser.add_argument("-i", "--interval", type=float, default=cfg['interval'],
                            help="measurement interval in s (float, default "+str(cfg['interval'])+")", metavar="x")
parser.add_argument("-D", "--debug", action='store_true', #cmdline arg only, not in config
                            help="print debug messages")

# if using MQTT
parser.add_argument("-o", "--brokerhost", type=str, default=cfg['brokerhost'],
                            help="use mqtt broker (addr: {"+cfg['brokerhost']+"})", metavar="addr")
parser.add_argument("-x", "--no-mqtt-influx", dest="mqtt_influx", action='store_false',
                            help="disable MQTT format influx")
parser.add_argument("-j", "--no-mqtt-json", dest="mqtt_json", action='store_false',
                            help="disable MQTT format json")

# if using configfiles
parser.add_argument("-c", "--configfile", type=str, default=cfg['configfile'],
                            help="load configfile ("+cfg['configfile']+")", metavar="nn")

args = parser.parse_args()
print('after args', time.time() - starttime)
n.notify("WATCHDOG=1")
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
for key in fcfg:
  if key in argdict and argdict[key] != fcfg[key]:
    value = argdict[key]
    fcfg[key] = value
    print('cmdline param', key, 'used with', value)

cfg = fcfg
for param in required_params:
  if not param in cfg or not cfg[param]:
    eprint('param', param, 'missing from config, exit')
    exit(1)

print("config used:", cfg)
print('after cfg', time.time() - starttime)
n.notify("WATCHDOG=1")

SENSOR_NAME = name.lower()

hostname = os.uname()[1]

brokerhost = cfg['brokerhost']

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

def onDisconnect(client, userdata, rc):
  if rc != 0:
    print("mqtt: Unexpected disconnection.")
    mqttReconnect()

if cfg['mqtt_json'] or cfg['mqtt_influx']:
  import paho.mqtt.client as mqtt
  client = mqtt.Client(client_id="dbsize", clean_session=True) # client id only useful if subscribing, but nice in logs # clean_session if you don't want to collect messages if daemon stops
  client.on_connect = onConnect
  client.on_disconnect = onDisconnect
  mqttConnect()
  client.loop_start()

  topic_influx = 'influx'
  topic_json = hostname + '/sensors/' + SENSOR_NAME.upper() + '/size'

  if cfg['mqtt_json']:
    jsontags = {
        "type": "influx",
        "interval_s": int(cfg['interval'])
        }
    print("enabled mqtt json output")
  if cfg['mqtt_influx']:
    influxstart = 'size,type=influx,sensor=' + name + ',interval_s='+str(cfg['interval'])+' '
    print("enabled mqtt influx output")
  n.notify("WATCHDOG=1")
  print('after mqtt', time.time() - starttime)

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

def exit_gracefully(a=False,b=False):
  print("exit gracefully...")
  if cfg['mqtt_json'] or cfg['mqtt_influx']:
    client.disconnect()
  exit(0)

def exit_hard():
  print("exiting hard...")
  exit(1)

signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)

first_run = True

MEAS_INTERVAL = cfg['interval']

location = "/var/lib/influxdb"

n.notify("READY=1") #optional after initializing
n.notify("WATCHDOG=1")
error_count = 0
print('starting loop', time.time() - starttime)
while True:
  if error_count > 3:
    eprint("too many errors, exit")
    exit_hard()

  run_started_at = time.time()

  try:
    du = subprocess.check_output(['du', '-b', '-s', location]).decode('utf-8')
    value = int(du.split()[0])
    error_count = 0
  except Exception as e:
    print("reading out sensor values failed:", e)
    error_count += 1
    continue

  ts = time.time()

#  if(cfg['mqtt_influx']):
#    payload = influxstart + 'UVA_raw={0},UVB_raw={1},visible_raw={2},ir_raw={3},UVA_={4},UVB_={5},exposure_s={6}'.format(float(ch_uva),float(ch_uvb),float(ch_vcomp),float(ch_ircomp),uva,uvb,exposure_s) + ' ' + format(ts*1000000000,'.0f')
#    mqttPub(topic_influx, payload, retain=False)

  if(cfg['mqtt_json']):
    payload = {
        "tags": jsontags,
        "values": {
          location: value
          },
        "UTS": round(ts,3)
        }

    mqttJsonPub(topic_json, payload)

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
