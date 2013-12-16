# -*- coding: utf-8 -*-
from decimal import *
from bitcoinrpc.authproxy import AuthServiceProxy
import ConfigParser
import pprint
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
#import sys

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

    print datetime.now()

    print "tx info:"
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(stakeholders)

    # creating transaction dict
    txdict = {}
    for key, value in stakeholders.items():
        txdict[value['address']] = value['amount']

    print "tx number:"
    txnum = access.sendmany(account, txdict)
    print txnum

    print "-" * 40

    if email:

        # formatting email
        msg = MIMEText("{!s}\ntxinfo\n{!s}\ntxnum:\n{!s}"
                    .format(datetime.now(), pp.pformat(stakeholders), txnum))

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
        s.sendmail(From, To, msg.as_string())
        s.quit()

#else:

    #sys.stderr.write("{!s}\nnot enough coins\n{!s}\n".format(datetime.now(), "-" * 40))