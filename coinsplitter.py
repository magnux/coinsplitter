# -*- coding: utf-8 -*-
from decimal import *
from bitcoinrpc.authproxy import AuthServiceProxy
import ConfigParser
import pprint
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

# getting current account state
access = AuthServiceProxy("{!s}://{!s}:{!s}@{!s}:{!s}".format(protocol, rpcuser, rpcpass, host, port))
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
        value['amount'] = float((value['shares']*pps).quantize(Decimal('.00000000'), rounding=ROUND_DOWN))

    print datetime.now()

    print "tx info:"
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(stakeholders)

    # creating transaction dict
    txdict = {}
    for key, value in stakeholders.items():
        txdict[value['address']] = value['amount']

    print "tx number:"
    print access.sendmany(account, txdict)

    print "-" * 40

#else:

    #sys.stderr.write("{!s}\nnot enough coins\n{!s}\n".format(datetime.now(), "-"*40))