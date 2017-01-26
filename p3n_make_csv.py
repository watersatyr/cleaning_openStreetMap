#!usr/bin/env python
# -*- coding: utf-8 -*-
# Title: p3n_make_csv.py
# Description: Building a CSV From XML Doc Using Dictionaries
# author: sle7in
# class: Udacity SQL Project 3
# date: 1/24/2016

import csv
import codecs
import re
import xml.etree.cElementTree as ET
import sqlite3
import cerberus


OSM_PATH = "C:\Users\LonelyMerc\Documents\python\udacity\P3/fc_sample.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

# LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


# In[8]:

# Note: The schema is stored in a .py file in order to take advantage of the
# int() and float() type coercion functions. Otherwise it could easily stored as
# as JSON or another serialized format.


schema = {
    'node': {
        'type': 'dict',
        'schema': {
            'id': {'required': True, 'type': 'integer', 'coerce': int},
            'lat': {'required': True, 'type': 'float', 'coerce': float},
            'lon': {'required': True, 'type': 'float', 'coerce': float},
            'user': {'required': True, 'type': 'string'},
            'uid': {'required': True, 'type': 'integer', 'coerce': int},
            'version': {'required': True, 'type': 'string'},
            'changeset': {'required': True, 'type': 'integer', 'coerce': int},
            'timestamp': {'required': True, 'type': 'string'}
        }
    },
    'node_tags': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'id': {'required': True, 'type': 'integer', 'coerce': int},
                'key': {'required': True, 'type': 'string'},
                'value': {'required': True, 'type': 'string'},
                'type': {'required': True, 'type': 'string'}
            }
        }
    },
    'way': {
        'type': 'dict',
        'schema': {
            'id': {'required': True, 'type': 'integer', 'coerce': int},
            'user': {'required': True, 'type': 'string'},
            'uid': {'required': True, 'type': 'integer', 'coerce': int},
            'version': {'required': True, 'type': 'string'},
            'changeset': {'required': True, 'type': 'integer', 'coerce': int},
            'timestamp': {'required': True, 'type': 'string'}
        }
    },
    'way_nodes': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'id': {'required': True, 'type': 'integer', 'coerce': int},
                'node_id': {'required': True, 'type': 'integer', 'coerce': int},
                'position': {'required': True, 'type': 'integer', 'coerce': int}
            }
        }
    },
    'way_tags': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'id': {'required': True, 'type': 'integer', 'coerce': int},
                'key': {'required': True, 'type': 'string'},
                'value': {'required': True, 'type': 'string'},
                'type': {'required': True, 'type': 'string'}
            }
        }
    }
}


SCHEMA = schema


# ================================================== #
#          shape_element Helper Functions            #
# ================================================== #

def attrib_parser(element, fields):
    """Generate an attribute dictionary from an element"""
    attr_dict = {}

    # Fill attr_dict from element attributes but only attributes designated by field
    for attr in element.attrib:                         # takes elements specified in field
        if attr in fields:
            attr_dict[attr] = element.attrib[attr]      # and adds them to dict(attr_dict)

    return attr_dict

def tag_parser(element, default):
    """Adds an attribute dictionary for each child element to a list"""
    tags = []
    # append dicts to 'tags' list
    all_tags = element.findall('tag')
    for tag in all_tags:
        key = tag.attrib['k']
        tag_dict = {'id'    : element.attrib['id'],
                    'value' : tag.attrib['v'] }                 # instantiate with 'id' and 'value'

        if ':' in key:                                      # divide 'k' around ':' if it exists
            first = re.compile(r"^[a-zA-Z_]+")                  # matches first letter or underscore sequence
            second = re.compile(r":+?.+")                       # matches first ':' and all after it
            tag_dict['type'] = first.search(key).group()        # assigns 'type' to 'k' before first ':'
            tag_dict['key'] = second.search(key).group()[1:]    # assigns 'key' to 'k' after first ':'


        else:
            tag_dict['type']  = default                         # if no ':', assign type to default
            tag_dict['key']   = key                             # if no ':', assign 'key' to 'k'

        tags.append(tag_dict)

    return tags

expected_street_types = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons", "Way", "Circle", "East", "West", "North", "South",
            "Southwest", "Alley", "Square"]
mapping = {"st":"Street",
           "St":"Street",
           "St.":"Street",
           "Aventue":"Avenue",
           "Rd":"Road",
           "Dr":"Drive",
           "Ct":"Court"
           }
foco_manual_updates = { "S Summit View #11"  : "S Summit View Drive",
                        "Old Town Square #238"   : "Old Town Square",
                        "S Timberline"   : "S Timberline Road",
                        "West Oak"   : "West Oak Street",
                        "Seventh-Day Adventist Church"   : "E Pitkin Street" }
expected_postal_codes = ["80521", "80522", "80523", "80524", "80525", "80526",
                         "80527", "80528", "80553", "80547", "80538", "80535" ]
### ADD CleavValue Instantiation here ####

def shape_element(element, node_fields=NODE_FIELDS, way_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node and way XML elements to Python dict for
    CSV insertion"""

    if element.tag == 'node':

        node_attribs = attrib_parser(element, node_fields)
        tags = tag_parser(element, default_tag_type)

        return {'node': node_attribs, 'node_tags': tags}

    elif element.tag == 'way':

        way_attribs = attrib_parser(element, way_fields)
        tags = tag_parser(element, default_tag_type)

        # way_nodes defined
        way_nodes = []
        all_nd = element.findall('nd')
        for i, nd in enumerate(all_nd):
            nd_attrib = { 'node_id'  : nd.attrib['ref'],
                          'id'       : element.attrib['id'],
                          'position' : i }

            way_nodes.append(nd_attrib)

        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)

        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=False)
