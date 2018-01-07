#! /usr/bin/env python
# -*- encoding: utf-8 -*-


import sys
reload(sys)
sys.setdefaultencoding('utf8')

import datetime
import time
import erppeek
import json
import base64

from datetime import date

from cfg_secret_configuration import odoo_configuration_user_prod as user_config

###############################################################################
# Odoo Connection
###############################################################################
def init_openerp(url, login, password, database):
    openerp = erppeek.Client(url)
    uid = openerp.login(login, password=password, database=database)
    user = openerp.ResUsers.browse(uid)
    tz = user.tz
    return openerp, uid, tz

openerp, uid, tz = init_openerp(
    user_config['url'],
    user_config['login'],
    user_config['password'],
    user_config['database'])


###############################################################################
# Configuration
###############################################################################

###############################################################################
# Script
###############################################################################

output_dir = "/var/www/html/sqq/data/membres"
#output_dir = "./"

# List members
try:
    out_members = []
    members = openerp.ResPartner.browse([('is_worker_member', '=', 'true')])
    for member in members:
        # Check if member has photo uploaded in Odoo
        if (len(member.image) < 100000):
            print member.name, "excluded because photo is to small"
            continue

        # Add member info to output list
        (name, surname) = member.name.split(',')
        out_members.append(
                {
                "num": member.barcode_base,
                "name": name,
                "surname": surname,
                "barcode": member.barcode,
                "sex": member.sex
                }
        )

        # Store member photo
        img_file = open("%s/data/photos/%s.png" % (output_dir, str(member.barcode_base)), 'w')
        img_file.write(base64.b64decode(member.image))
        img_file.close()

    # Create output json
    data_file = open("%s/data/membres.json" % (output_dir), 'w')
    json.dump(out_members, data_file, indent=4)
    data_file.close()

except Exception as e:
    print e
