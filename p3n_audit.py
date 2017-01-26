#!usr/bin/env python
# -*- coding: utf-8 -*-
# Title: p3n_audit.py
# author: sle7in
# class: Udacity SQL Project 3
# date: 1/19/2016

import re
import xml.etree.cElementTree as ET
from collections import defaultdict

FILEPATH = "C:\Users\LonelyMerc\Documents\python\udacity\P3"


MAP = "/osm_files/map"
FOCO = "/osm_files/fort_collins.osm"
MAP_SAMPLE = "/sample.osm"
FOCO_SAMPLE = "/fc_sample.osm"


# expected values
expected_street_types = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons", "Way", "Circle", "East", "West", "North", "South",
            "Southwest", "Alley", "Square"]
expected_lat, expected_lon = (40.474096, 40.639273), (-105.153307, -104.982127)
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)


def audit_street_type(irreg_street_types, street_name):
    # purpose of this fuction is to detect and add to dict any irregular streets to print out
    """Determines type of street from street_name and returns dictionary
    irreg_street_types with sets of streets for each street type."""

    type_match = street_type_re.search(street_name)
    if type_match:
        street_type = type_match.group()         # street_type is the last word in street_name
        if street_type not in expected_street_types:
            irreg_street_types[street_type].add(street_name)

    return irreg_street_types

def coord_in_city(coord, expected_lat, expected_lon):
    """Accepts coords as a tuple or list, (lat, long).
       Checks if the input coordinates are within the city boundaries"""

    south_bound, north_bound = expected_lat     # input in tuple from south to north
    west_bound, east_bound = expected_lon       # input in tuple from west to east
    in_lat, in_lon = coord

    if (in_lon >= west_bound) and (in_lon <= east_bound) and \
    (in_lat >= south_bound) and (in_lat <= north_bound):
        return True, (in_lat, in_lon)
    else:
        # prints the violating bound
        if (in_lat < south_bound) or (in_lat > north_bound):
            print "Latitude out of bounds:", in_lat
        if (in_lon < west_bound) or (in_lon > east_bound):
            print "Longitude out of bounds:", in_lon
        return (False, (in_lat, in_lon))

def audit_post_code(irreg_posts, post_code):
    """Returns True if input post_code is in city_zips, else False"""

    if post_code[:5] not in expected_postal_codes:
        irreg_posts.add(post_code)
    return irreg_posts

# obsolete
def process_file(filename):
    # purpose of this function is to output a list to visually see and update mappings
    """Parses node and way child tags for attrib['v'] of the key 'addr:street'
    and then runs audit_street_type on it. Returns defaultdict of audited
    streets."""
    irreg_posts = set()
    irreg_street_types = defaultdict(set)

    for _, elem in ET.iterparse(filename):
        if elem.tag == "node" or elem.tag == "way":
        # if elem.tag == "node" and elem.attrib['id'] in post_codes:
            # print elem.tag, elem.attrib
            for child in elem.iter("tag"):
                child_attr_key = child.attrib["k"]
                change = clean_value(child)
                if change:
                    print change
                # if child_attr_key == "addr:street":
                #     audit_street_type(irreg_street_types, child.attrib["v"])
                # if child_attr_key == "addr:postcode" or child_attr_key == "postal_code":
                #     audit_post_code(irreg_posts, child.attrib["v"])

    return irreg_posts, irreg_street_types




def further_investigation(filename):
    type_counter = {"node":0, "way":0}
    for _, elem in ET.iterparse(filename):
        if elem.tag == "node" or elem.tag == "way":
        # if elem.tag == "node" and elem.attrib['id'] in post_codes:
            # print elem.tag, elem.attrib
            children = elem.findall("tag")

            for child in children:
                if child.attrib["k"] == "addr:street":
                    if street_type_re.search(child.attrib["v"].strip()).group() in mapping or child.attrib["v"] in foco_manual_updates:
                        print elem.tag, child.tag
                    type_counter[elem.tag]+=1
                elif "post" in child.attrib["k"]:
                    if child.attrib["v"][:5] not in expected_postal_codes:
                        print elem.tag, child.tag, child.attrib["v"]
    print type_counter
further_investigation(FILEPATH + FOCO)
# results = process_file(FILEPATH + FOCO)
# for val in results:
#     print val
#     print val,":", st_types[val]
