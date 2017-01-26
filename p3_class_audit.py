#!usr/bin/env python
# -*- coding: utf-8 -*-
# Title: p3_class_audit.py
# author: clasch
# class: Udacity SQL Project 3
# date: 1/26/2016


import re
import xml.etree.cElementTree as ET
from collections import defaultdict


class AuditFile(object):
    """Takes inpute file and parses through it, looking for method specified
    data consistencies and prints incongruencies."""

    def __init__(self, filename, street_list, post_list):
        self.filename = filename
        self.expected_street_types = street_list
        self.expected_postal_codes = post_list
        self.street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
    def audit_street_type(self, street_name):
        # purpose of this fuction is to detect and add to dict any irregular streets to print out
        """If street type (i.e. "rd") is not expected, returns tuple of
        (street_type, street_name), else 'None'. An example output would
        be "('rd', 'Happy rd')" """
        street_name = street_name.strip()
        m = self.street_type_re.search(street_name)
        if m:
            street_type = m.group()         # street_type is the last word in street_name
            if street_type not in expected_street_types:
                return street_type, street_name
            else:
                return street_type, None
        else:
            return "No Regex Match", street_name

    def unexpected_postal(self, post_code):
        """Returns post_code if it is not in city_zips, else 'None'"""
        if post_code[:5] not in expected_postal_codes:
            return post_code

    def process_file(self):
        # purpose of this function is to output a list to visually see and update mappings
        """Parses node and way child tags looking for specific tags with a
        certain key, such as 'addr:street' or 'addr:post', and then runs
        audit methods on it, returning set or defaultdict of unexpected values."""
        irreg_posts = set()
        irreg_streets = defaultdict(set)

        for _, elem in ET.iterparse(self.filename):
            if elem.tag == "node" or elem.tag == "way":

                for tag in elem.iter("tag"):
                    tag_key = tag.attrib["k"]
                    tag_val = tag.attrib["v"]

                    # Conditional following for each audit method
                    if tag_key == "addr:street":
                        street_type, irregular_street = self.audit_street_type(tag_val)
                        if irregular_street:
                            irreg_streets[street_type].add(irregular_street)

                    elif tag_key == "addr:postcode" or tag_key == "postal_code":
                        irregular_post = self.unexpected_postal(tag_val)
                        if irregular_post:
                            irreg_posts.add(irregular_post)

        return irreg_posts, irreg_streets

# class test case
# expected_street_types = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
#             "Trail", "Parkway", "Commons", "Way", "Circle", "East", "West", "North", "South",
#             "Southwest", "Alley", "Square"]
# expected_postal_codes = ["80521", "80522", "80523", "80524", "80525", "80526", "80527", "80528", "80553", "80547","80538","80535" ]
# f = "C:\Users\LonelyMerc\Documents\python\udacity\P3/osm_files/fort_collins.osm"
# foco_audit = AuditFile(f,expected_street_types,expected_postal_codes)
# posts, streets = foco_audit.process_file()
# for post in posts:
#     print post
# for street in streets:
#     print street
