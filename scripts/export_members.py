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

#output_dir = "/var/www/html/sqq/data/membres"
output_dir = "/home/ben/git/sqq/carte_membre/html"
#output_dir = "./"

###############################################################################
# Script
###############################################################################

def add_member_to_list(member, member_list):
    (name, surname) = member.name.split(',', 1)
    member_list.append(
            {
            "num": member.barcode_base,
            "name": name,
            "surname": surname,
            "barcode": member.barcode,
            "barcode2":member.barcode[:-1],
            "sex": member.sex
            }
    )

# List members
try:
    nb_member = 0
    members_with_photo = []
    members_without_photo = []
    members = openerp.ResPartner.browse([('is_worker_member', '=', 'true')])
    for member in members:
        if ',' not in member.name:
            continue
        # Check if member has photo uploaded in Odoo
	# la photo du membre 69 fait 65391, on passe à 50000
        if (len(member.image) > 50000):
            # Add member info to output list
            add_member_to_list(member, members_with_photo)
            # Store member photo
            img_file = open("%s/data/photos/%s.jpg" % (output_dir, str(member.barcode_base)), 'w')
            img_file.write(base64.b64decode(member.image))
            img_file.close()
        else:
            add_member_to_list(member, members_without_photo)

        print "Data extracted for ", member.name
        nb_member = nb_member+1

    # Create output json
    data_file = open("%s/data/membres_photo.json" % (output_dir), 'w')
    json.dump(members_with_photo, data_file, indent=4)
    data_file.close()
    data_file = open("%s/data/membres_nophoto.json" % (output_dir), 'w')
    json.dump(members_without_photo, data_file, indent=4)
    data_file.close()
    print "Total: %d members exported from Odoo" % (nb_member)

except Exception as e:
    print e
