#!/usr/bin/python
#
#
# this is the honeypot stuff
#
#
#
import thread
import socket
import sys
import re
import subprocess
import time
import SocketServer
import os
import random
import datetime
# import artillery modules
from src.core import *
from src.smtp import *

# port ranges to spawn pulled from config
ports = check_config("PORTS=")
# check to see what IP we need to bind to
bind_interface = check_config("BIND_INTERFACE=")
send_email = check_config("ALERT_USER_EMAIL=")

# main socket server listener for responses
class SocketListener((SocketServer.BaseRequestHandler)):

    def handle(self):
        #print self.server.server_name, self.server.server_port
        pass
    def setup(self):

        # hehe send random length garbage to the attacker
        length = random.randint(5, 30000)

        # fake_string = random number between 5 and 30,000 then os.urandom the command back
        fake_string = os.urandom(int(length))

        try:
            self.request.send(fake_string)
            ipcheck = is_valid_ipv4(self.client_address[0])

            if ipcheck != False:
                check_whitelist = whitelist(self.client_address[0])
                if check_whitelist == 0:
                    now = str(datetime.datetime.today())
                    log_message = "%s [!] Artillery has detected an attack from IP address: %s for a connection on a honeypot port: %s" % (now,self.client_address[0],self.server.server_address[1])

                    write_log(log_message)

                    email_alerts = check_config("EMAIL_ALERTS=").lower()

                    if email_alerts == "on":
                        email_frequency = check_config("EMAIL_TIMER=").lower()

                        if email_frequency.isdigit():
                            prep_email(log_message)
                        else:
                            mail(send_email, log_message)

                    if check_config("HONEYPOT_BAN=").lower() == "on":
                        ban(self.client_address[0])

                    self.request.close()


        except Exception, e:
            write_log("[!] Error detected. Printing: " + str(e))
            pass

# here we define a basic server
def listen_server(port,bind_interface):
            # specify port
    try:
        port = int(port)
        if bind_interface == "":
            server = SocketServer.ThreadingTCPServer(('', port), SocketListener)
        else:
            server = SocketServer.ThreadingTCPServer(('%s' % bind_interface, port), SocketListener)
        server.serve_forever()

    # if theres already something listening on this port
    except Exception: pass

# check to see which ports we are using and ban if ports are touched
def main(ports,bind_interface):

        # pull the banlist path
    if os.path.isfile("check_banlist_path"):
        banlist_path = check_banlist_path()
        fileopen = file(banlist_path, "r")
        for line in fileopen:
        # remove any bogus characters
            line = line.rstrip()
            # ban actual IP addresses
            honeypot_ban = check_config("HONEYPOT_BAN=")
            if honeypot_ban.lower() == "yes":
                whitelist = check_config("WHITELIST_IP=")
                match = re.search(line, whitelist)
                if not match:
                        # ban the ipaddress
                    ban(line)
    # split into tuple
    ports = ports.split(",")
    for port in ports:
        thread.start_new_thread(listen_server, (port,bind_interface,))

# launch the application
honeypot_enabled = check_config("HONEYPOT=")
#if honeypot_enabled.lower() == "yes":
main(ports,bind_interface)
