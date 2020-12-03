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

# from __future__ import print_function
import time,math
import sys
import os, signal
import paho.mqtt.client as mqtt
import subprocess 
import re
import json

from argparse import ArgumentParser, RawTextHelpFormatter

def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)
  sys.stderr.flush()

def flprint(*args, **kwargs):
  print(*args, **kwargs)
  sys.stdout.flush()

parser = ArgumentParser(description='print mqtt messages.\n\nDefaults in {curly braces}',formatter_class=RawTextHelpFormatter)
parser.add_argument("-o", "--brokerhost", dest="brokerhost", type=str, default='localhost',
                            help="subscribe to mqtt broker (addr: {localhost})", metavar="addr")
parser.add_argument("-t", "--topic", dest="topic", type=str, default='#',
                            help="subscribe to topic (#)", metavar="t")
parser.add_argument("-s", "--sensor", dest="sensor", action='store_true',
                            help="only send temperature to +/sensors/CPU topic")

parser.add_argument("-D", "--debug", dest="debug", action='store_true',
                            help="print debug messages")
args = parser.parse_args()

hostname = subprocess.check_output(['hostname']).decode('utf-8').strip()
topic = hostname + '/system/network'

brokerhost = args.brokerhost

DEBUG = args.debug

DEBUG and flprint('topic: ' + topic)

def exit_gracefully(a,b):
  flprint("exiting gracefully...")
  client.disconnect()
  exit(0)

def exit_hard():
  flprint("exiting hard...")
  client.disconnect()
  exit(1)

signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)

def on_connect(client, userdata, flags, rc):
  flprint("Connected with result code "+str(rc))

client = mqtt.Client(client_id="wireless-status", clean_session=True)
#client.connect("localhost",1883,60)
while True:
  try:
    client.connect(brokerhost,1883,60)
    break
  except Exception as e:
    print("mqtt: could not connect:", e)
    time.sleep(1)
client.on_connect = on_connect


# send on demand/change - only with retained.

"""
{ interfaces: {
  enblablupp: {
    status: up
    MAC
    IPv4: [ "1.1.1.1 / 8" ]
    IPv6
    SSID
    gw: 
"""

ifobjs = json.loads(subprocess.check_output(['ip','-j','address']).decode('utf-8'))
if len(ifobjs) == 0:
  eprint('no interfaces returned, exit')
  exit(1)
payload_json = { "interfaces": {} }
for iface in ifobjs:
  ifobj = { \
    "type": iface['link_type'], \
    "status": iface['operstate'], \
    "MAC": iface['address'] }
  for ip in iface['addr_info']:
    ifstr = ip['local'] + ' / ' + str(ip['prefixlen'])
    if ip['family'] == 'inet':  # IPv4
      key = 'IPv4'
    elif ip['family'] == 'inet6':
      key = 'IPv6'
    if not key in ifobj:
      ifobj[key] = []
    ifobj[key].append(ifstr)
  if ifobj['type'] == 'ether':
    try:
      iwinfo = subprocess.check_output(['iw','dev',iface['ifname'],'info'],stderr=subprocess.STDOUT).decode('utf-8')
      # print("i:",iwinfo)
      iwiarr = iwinfo.splitlines()
      for line in iwiarr:
        part = line.split()
        if part[0] == 'ssid':
          ifobj['SSID'] = part[1]
        elif part[0] == 'type':
          ifobj['wireless'] = part[1]
        elif part[0] == 'txpower':
          ifobj['txpower_dBm'] = part[1]
        elif part[0] == 'channel':
          ifobj['channel'] = part[1]
          ifobj['channel_width_MHz'] = part[5]
          ifobj['channel_MHz'] = part[2].lstrip('(')

    except subprocess.CalledProcessError:
      pass
      # print('not a wireless interface')
    # iwinfo = json.loads(

  payload_json['interfaces'][iface['ifname']] = ifobj

routes = json.loads(subprocess.check_output(['ip','-j','route']).decode('utf-8'))
for route in routes:
  if 'gateway' in route:
    payload_json['interfaces'][route['dev']]['gw'] = route['gateway']

      
# print(json.dumps(payload_json))
  
client.publish(topic, json.dumps(payload_json), retain=True)

