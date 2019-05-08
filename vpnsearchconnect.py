#!/usr/bin/python3
# -*- coding: utf-8 -*-

import csv
import codecs
import urllib.request
import json
import os.path
import sys
import base64
import subprocess
from subprocess import Popen

# script path
scriptpath = os.path.abspath(os.path.dirname(__file__)) + "/"

# args
args = sys.argv

# read cache
data = {}
exception_ip = []
if os.path.exists(scriptpath + "vsc.txt"):
	f = open(scriptpath + "vsc.txt", "r")
	data = json.load(f)
	f.close()
if os.path.exists(scriptpath + "exception.txt"):
	f = open(scriptpath + "exception.txt", "r")
	line = f.readline()
	for line in open(sys.srgv[2], 'r'):
		itemlist = line[:-1].split("\n")
		exception_ip.append([ item for item in itemlist ])
	f.close()
if os.path.exists(scriptpath + "api_key.txt"):
	f = open(scriptpath + "api_key.txt", "r")
	ipstack_key = f.read()
	f.close()
else:
	print("\n--------------------------------------------------------")
	print("Please enter ipstack API key .")
	ipstack_key = input('>>>  ')
	try:
		res2 = urllib.request.urlopen("http://api.ipstack.com/8.8.8.8?access_key=" + ipstack_key)
	except:
		print("\n--------------------------------------------------------")
		print("Please re-enter key.")
		print("\n--------------------------------------------------------")
		sys.exit(-1)
	f = open(scriptpath + "api_key.txt", "w")
	f.write(ipstack_key)
	f.close()

# read region
f = open(scriptpath + "region.txt", "r")
region = json.load(f)
f.close()

# read VPN list
'''
res1 = urllib.request.urlopen("http://www.vpngate.net/api/iphone/").read()
with open(scriptpath + "tukubavpn.csv", "wb") as f:
	f.write(res1)
with open(scriptpath + "tukubavpn.csv") as f:
	res2 = f.read()
cr = csv.reader(res2)
'''
res1 = urllib.request.urlopen("http://www.vpngate.net/api/iphone/")
cr = csv.reader(codecs.iterdecode(res1, 'utf-8'), delimiter=",", lineterminator="\r\n")

# search vpn server
print("\n--------------------------------------------------------")
print("Searching VPN server in the following region.")
print("--------------------------------------------------------")
for i,r in enumerate(args):
	if i != 0:
		print(region[int(r)-1])
print("--------------------------------------------------------")

for row in cr:
	if len(row) == 15 and row[6] == "JP":
		region_code = 0
		#list
		if row[1] in exception_ip:
			continue
		if row[1] in data:
			region_code = data[row[1]]
		else:
			# get region_code
			print("Searching the region of IP(" + row[1] + ").")
			res2 = urllib.request.urlopen("http://api.ipstack.com/" + row[1] + "?access_key=" + ipstack_key)
			iptoaddrs = json.loads(res2.read().decode('utf8'))
			print(iptoaddrs["region_code"])
			if iptoaddrs["region_code"] is None:
				region_code = 0
			if iptoaddrs["region_code"] != "" and iptoaddrs["region_code"] is not None:
				region_code = int(iptoaddrs["region_code"])
				data[row[1]] = region_code
				f = open(scriptpath + "vsc.txt", "w")
				json.dump(data, f)
				f.close()
			else:
				print("Cannot identify the region of IP(" + row[1] + ").")
		#if region_code != 0 or region_code != None or region_code != "":
		if region_code != 0:
			print("Region of " + row[0] + " (" + row[1] + ") => " + str(region_code) + ":" + region[region_code-1])
			# search region
			for i,arg in enumerate(args):
				if i != 0 and int(arg) == region_code:
					print("Connecting to " + row[0] + "... Please wait.")
					# Base64 decode
					ovpn = base64.b64decode(row[14])
					ovpn = ovpn.decode("UTF-8")
					# make .ovpn
					f = open(scriptpath + "vpnovpn.ovpn", "w")
					f.write(ovpn)
					f.close()
					# vpn connect
					com = "/usr/sbin/openvpn " + scriptpath + "vpnovpn.ovpn"
					proc = Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
					buf = []
					while True:
						line = proc.stdout.readline()
						line = line.decode("UTF-8")
						print(line)
						#buf =  buf + line
						if line.find("failed") > -1:
							print("Connection failed: " + row[0])
							#break
							cmd = scriptpath + "openvpnclient.sh stop"
							subprocess.call(cmd.split())
							continue
						elif line.find("Initialization Sequence Completed") > -1:
							print("Connection success: ")
							print("\t" + row[0] + " (" + row[1] + ") => " + str(region_code) + ":" + region[region_code-1])
							print("--------------------------------------------------------")
							sys.exit(0)
print("Cannot find a valid VPN server.")
print("--------------------------------------------------------")
sys.exit(-1)
