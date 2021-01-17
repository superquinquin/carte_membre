#! /usr/bin/env python3
# -*- encoding: utf-8 -*-


import sys
import os
import argparse
import logging
import datetime
import erppeek
import json
import base64

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

def add_member_to_list(member, member_list):
    (name, surname) = member.name.split(',', 1)
    member_list.append(
            {
            "num": member.barcode_base,
            "name": name,
            "surname": surname,
            "barcode": member.barcode,
            "sex": member.sex,
            "email": member.email
            }
    )

def save_json(file_name, data):
    data_file = open(file_name, 'w')
    json.dump(data, data_file, indent=4)
    data_file.close()
    logging.debug("Data saved to json file %s", file_name)

def main():
    # configure arguments parser
    parser = argparse.ArgumentParser(
            description='Export des membres dont la carte doit être imprimée')
    parser.add_argument('-v', '--verbose', action='store_true',
            help='activate debug mode')
    parser.add_argument('-a', '--all', action='store_true',
            help='export all members instead of only those to print')
    parser.add_argument('-n', '--no-photo-files', action='store_true',
            help='do not export photo files')
    parser.add_argument('-m', '--mark-as-printed', action='store_true',
            help="mark members as printed (warning this can't be undone)")
    args = parser.parse_args()

    # configure logger
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    today = datetime.date.today().isoformat()
    output_dir=today
    nb_member = 0
    members_with_photo = []

    import os, sys
    if not os.path.isdir("%s" % (output_dir)):
 	    os.makedirs("%s" % (output_dir))

    from shutil import copyfile
    copyfile("carte_membre_associe.html", "%s/carte_membre_associe.html" %(output_dir))
    copyfile("JsBarcode.all.min.js", "%s/JsBarcode.all.min.js" %(output_dir))
    copyfile("mains.css", "%s/mains.css" %(output_dir))
    copyfile("verso_associe.jpg", "%s/verso_associe.jpg" %(output_dir))
    copyfile("Neou-Bold.ttf", "%s/Neou-Bold.ttf" %(output_dir))
    copyfile("Raleway-ExtraBold.ttf", "%s/Raleway-ExtraBold.ttf" %(output_dir))
    copyfile("Raleway-Light.ttf", "%s/Raleway-Light.ttf" %(output_dir))
    copyfile("Raleway-Medium.ttf", "%s/Raleway-Medium.ttf" %(output_dir))


    try:
        # List members
        browse_filter = [('is_associated_people', '=', 'true')]
        if not args.all:
            browse_filter.append(('badge_to_print', '=', 'true'))
        for member in openerp.ResPartner.browse(browse_filter):
            if ',' not in member.name:
                logging.info("ERROR for [%s] (no comma)", member.name)
                continue
            # Check if member has photo uploaded in Odoo
#            if ( isinstance(member.image, str) ):
            if ( isinstance(member.image, str) and ( len(member.image) > 24000 or str(member.barcode_base) == "1141")):

                ##print "-%s;%s" % (len(member.image) , str(member.barcode_base) )
                logging.debug("Found member with photo: %s", member.name)
                print("%4d;%s;%s;%s" % (member.barcode_base,member.sex,member.name ,member.email))
                nb_member = nb_member+1
                add_member_to_list(member, members_with_photo)
                if not args.no_photo_files:
                    # Store member photo
                    img_file_name = "%s/%s.jpg" % (output_dir,
                            str(member.barcode_base))
                    if not os.path.isfile(img_file_name): 
                        img_file = open(img_file_name, 'wb')
                        img_file.write(base64.b64decode(member.image))
                        img_file.close()
                        logging.info("Member photo saved to file %s",
        	                    img_file_name)
            else:
                logging.debug("Found member without photo: %s", member.name)
             
            logging.info("Data extracted for [%s]", member.name)
            
            # Mark member as printed if asked to
            if args.mark_as_printed:
                    member.badge_print_date = today
                    member.badge_to_print = False
                    logging.debug("Member [%s] marked as printed to %s",
                            member.name, today)

        # Create output json
        save_json("%s/membres_associe.json" % (output_dir),
                members_with_photo)
        print("Total: %d members exported from Odoo" % (nb_member))


    except Exception as e:
        logging.exception(e)

if __name__ == "__main__":
    main()
