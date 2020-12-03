#!/usr/bin/env python3
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

# from __future__ import print_function
import time
import sys
import os, signal
import paho.mqtt.client as mqtt
from subprocess import call

from argparse import ArgumentParser, RawTextHelpFormatter

parser = ArgumentParser(description='print mqtt messages.\n\nDefaults in {curly braces}',formatter_class=RawTextHelpFormatter)
parser.add_argument("-o", "--brokerhost", type=str, default='localhost',
                            help="subscribe to mqtt broker (addr: {localhost})", metavar="addr")
parser.add_argument("-t", "--topic", type=str, default='#',
                            help="subscribe to topic (#)", metavar="t")
parser.add_argument("-r", "--retain", action='store_true',
                            help="display only retained messages" )

args = parser.parse_args()

def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)
  sys.stderr.flush()

listen_host = args.brokerhost

DEBUG = False
DEBUG = True

def exit_gracefully(a,b):
  print("exiting gracefully...")
  client.on_disconnect = None
  client.disconnect()
  exit(0)

def exit_hard():
  print("exiting hard...")
  exit(1)

signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)

client = mqtt.Client(client_id='mqtt-receive-script', clean_session=True)
client.connect(listen_host,1883,60)

def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc)+" to " + listen_host)
  client.subscribe(args.topic)

def mqttReconnect():
  print('attempting reconnect')
  while True:
    try:
      client.reconnect()
      print('reconnect successful')
      break
    except ConnectionRefusedError as e:
      eprint('ConnectionRefusedError', e, '\nnext attempt in 3s')
      time.sleep(3)

def onDisconnect(client, userdata, rc):
  if rc != 0:
    print("Unexpected disconnection.")
    mqttReconnect()

def on_message(client, userdata, msg):
  #  if not msg.retain:
 #   exit_gracefully()
  retained_status = "RET" if msg.retain else ""
  print( msg.qos, retained_status, msg.topic, msg.payload.decode())

client.on_connect = on_connect
client.on_disconnect = onDisconnect
client.on_message = on_message

client.loop_forever()

