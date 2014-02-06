# -*- coding: utf-8 -*-
from decimal import *
from bitcoinrpc.authproxy import AuthServiceProxy
import ConfigParser
import pprint
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from subprocess import call
import sys
import psutil

# reading the config
config = ConfigParser.RawConfigParser()
config.read('coinsplitter.cfg')

protocol = config.get('config', 'protocol')
host = config.get('config', 'host')
port = config.get('config', 'port')
rpcuser = config.get('config', 'rpcuser')
rpcpass = config.get('config', 'rpcpass')
mintx = Decimal(config.get('config', 'mintx'))
txfee = Decimal(config.get('config', 'txfee'))
account = config.get('config', 'account')

stakeholders = eval(config.get('config', 'stakeholders'))

email = config.getboolean('config', 'email')

binary = config.get('config', 'binary')
path = config.get('config', 'path')

try:
    # getting current account state
    access = AuthServiceProxy("{!s}://{!s}:{!s}@{!s}:{!s}"
                    .format(protocol, rpcuser, rpcpass, host, port))
    currentbalance = Decimal(access.getbalance(account))

    if currentbalance > (mintx + txfee):

        # setting tx fee
        access.settxfee(float(txfee))

        # summing the total shares
        totalshares = Decimal(0)
        for key, value in stakeholders.items():
            totalshares += value['shares']

        # calculating the pay per share
        pps = (currentbalance - txfee) / totalshares

        # calculating amounts to send
        for key, value in stakeholders.items():
            value['amount'] = float((value['shares'] * pps)
                            .quantize(Decimal('.00000000'), rounding=ROUND_DOWN))

        # creating transaction dict
        txdict = {}
        for key, value in stakeholders.items():
            txdict[value['address']] = value['amount']

        txnum = access.sendmany(account, txdict)

        pp = pprint.PrettyPrinter(indent=4)
        message = ("{!s}\ntx info:\ntx total: {!s}\ntx fee: {!s}\ntx stakeholders:\n{!s}\ntxnum:\n{!s}"
            .format(datetime.now(), (currentbalance - txfee), txfee, pp.pformat(stakeholders), txnum))

        print message
        print "-" * 40

        if email:

            # formatting email
            msg = MIMEText(message)

            msg['Subject'] = 'coinsplitter transaction information'
            From = 'coinsplitter'
            msg['From'] = From
            To = ''
            for key, value in stakeholders.items():
                To += value['email'] + ","
            To = To[0:-1]
            msg['To'] = To

            # sending email
            s = smtplib.SMTP('localhost')
            rcpts = [r.strip() for r in To.split(',') if r]
            s.sendmail(From, rcpts, msg.as_string())
            s.quit()

    else:
        sys.stderr.write("{!s} : Not enough coins\n"
                         .format(datetime.now()))

except:

    procs = [p for p in psutil.get_process_list() if p.name==binary]

    if len(procs) < 1:
        sys.stderr.write("{!s} : Daemon not running, attemping to restart: {!s}\n"
                         .format(datetime.now(), binary))
        call([path + binary, "-daemon"])
    else:
        pp = pprint.PrettyPrinter(indent=4)
        sys.stderr.write("{!s} : Something weird happened:\n{!s}\n"
                         .format(datetime.now(), pp.pformat(sys.exc_info())))