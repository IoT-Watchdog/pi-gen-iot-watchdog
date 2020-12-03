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

# hints from https://www.raspberrypi.org/forums/viewtopic.php?p=600515#p600515

import time,math
import sys
import os, signal
import paho.mqtt.client as mqtt
import subprocess 
import json

import sdnotify

from argparse import ArgumentParser, RawTextHelpFormatter

def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)
  sys.stderr.flush()

parser = ArgumentParser(description='send iostats output as ut mqtt messages.\n\nDefaults in {curly braces}',formatter_class=RawTextHelpFormatter)
parser.add_argument("-o", "--brokerhost", dest="brokerhost", type=str, default='localhost',
                            help="subscribe to mqtt broker (addr: {localhost})", metavar="addr")
parser.add_argument("-i", "--interval", dest="interval", type=float, default=3,
                              help="measurement interval in s (float, default 3)", metavar="x")

parser.add_argument("-D", "--debug", dest="debug", action='store_true',
                            help="print debug messages")
args = parser.parse_args()

MEAS_INTERVAL = args.interval

n = sdnotify.SystemdNotifier()

hostname = os.uname()[1]
topic = hostname + '/system/io'
print('topic: ' + topic)

brokerhost = args.brokerhost

DEBUG = args.debug

def exit_gracefully(a,b):
  print("exiting gracefully...")
  client.disconnect()
  exit(0)

def exit_hard():
  print("exiting hard...")
  exit(1)

signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)

def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc))

client = mqtt.Client(client_id="iostats", clean_session=True)
client.connect(brokerhost,1883,60)
client.on_connect = on_connect

def mqttReconnect():
  print('attempting reconnect')
  success = False
  while not success:
    try:
      client.reconnect()
      success = True
      print('reconnect successful')
    except ConnectionRefusedError as e:
      eprint('ConnectionRefusedError', e, '\nnext attempt in 3s')
      time.sleep(3)

MQTT_ERR_SUCCESS = mqtt.MQTT_ERR_SUCCESS
def mqttPub(topic, payload_json):
  DEBUG and print(payload_json)
  ret = client.publish(topic, json.dumps(payload_json, separators=(',', ':'), sort_keys=True), retain=True)
  if ret[0] == MQTT_ERR_SUCCESS:
    n.notify("WATCHDOG=1")
  elif ret[0] == mqtt.MQTT_ERR_NO_CONN:
    eprint('no mqtt connnection')
    mqttReconnect()
  else:
    eprint('mqtt publishing not successful,', ret)

while 1:
  run_started_at = time.time()
  
  iostats = json.loads(subprocess.check_output(['iostat', '-y', '-d', '-o', 'JSON', '-x']).decode('utf-8'))
  if not 'sysstat' in iostats or not 'hosts' in iostats['sysstat'] or not len(iostats['sysstat']['hosts']) or not 'statistics' in iostats['sysstat']['hosts'][0] or not len(iostats['sysstat']['hosts'][0]['statistics']) or not 'disk' in iostats['sysstat']['hosts'][0]['statistics'][0] or not len(iostats['sysstat']['hosts'][0]['statistics'][0]['disk']):
    eprint('json output structure unknown')
    exit_hard()

  for diskstats in iostats['sysstat']['hosts'][0]['statistics'][0]['disk']:
    DEBUG and print(diskstats)
    payload = { 
        "tags": { "device": diskstats['disk_device'] },
        "values": {
          "readops_ps": diskstats['r/s'],
          "writeops_ps": diskstats['w/s'],
          "readKB_ps": diskstats['rkB/s'] if 'rkB/s' in diskstats else diskstats['rMB/s'] * 1000,
          "writtenKB_ps": diskstats['wkB/s'] if 'wkB/s' in diskstats else diskstats['wMB/s'] * 1000,
          "reads_queued_ps": diskstats["rrqm/s"],
          "writes_queued_ps": diskstats["wrqm/s"],
          "avg_read_time_ms": diskstats["r_await"],
          "avg_write_time_ms": diskstats["w_await"],
          "avg_rreqsize_KB": diskstats["rareq-sz"],
          "avg_wreqsize_KB": diskstats["wareq-sz"],
          "avg_queue_size": diskstats['aqu-sz']
          },
        "UTS": round(time.time(),3)
      }
    
    mqttPub(topic, payload)

  run_finished_at = time.time()
  run_duration = run_finished_at - run_started_at

  DEBUG and print("duration of run: {:10.4f}s.".format(run_duration))

  to_wait = MEAS_INTERVAL - run_duration
  if to_wait > 0:
    DEBUG and print("wait for "+str(to_wait)+"s")
    time.sleep(to_wait - 0.002)
  else:
    DEBUG and print("no wait, {0:4f}ms over".format(- to_wait*1000))

