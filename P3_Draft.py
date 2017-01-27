
# coding: utf-8

# # P3: Fort Collins Map

# In[84]:

# import libraries
import re, csv, codecs
import sqlite3, cerberus
import xml.etree.cElementTree as ET
from collections import defaultdict
from p3_clean_class import CleanValue
from p3_validator_schema import schema as SCHEMA



# # Building CSV From XML Doc

OSM_PATH = "C:\Users\LonelyMerc\Documents\python\udacity\P3/fc_sample.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

fc_st_types = ["Street", "Avenue", "Boulevard", "Drive", "Court",
                         "Place", "Square", "Lane", "Road", "Trail", "Parkway", "Commons", "Way",
                         "Circle", "East", "West", "North", "South", "Southwest", "Alley", "Square"]
st_mapping = { "st" : "Street",
                   "St" : "Street",
                   "St." : "Street",
                   "Aventue" : "Avenue",
                   "Rd" : "Road",
                   "Dr" : "Drive",
                   "Ct" : "Court" }
fc_manual_st = { "S Summit View #11" : "S Summit View Drive",
                        "Old Town Square #238" : "Old Town Square",
                        "S Timberline" : "S Timberline Road",
                        "West Oak" : "West Oak Street",
                        "Seventh-Day Adventist Church" : "E Pitkin Street" }
fc_posts = ["80521", "80522", "80523", "80524", "80525", "80526",
                         "80527", "80528", "80553", "80547", "80538", "80535" ]

# instantiate CleanValue class for fort collins data
fc_cleaner = CleanValue(fc_st_types, st_mapping, fc_manual_st, fc_posts)


# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


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
        val = tag.attrib['v']
        tag_dict = {'id' : element.attrib['id']}           # instantiate with 'id'

        tag_dict['value'] = fc_cleaner.process(key, val)      # imported cleaning module

        if ':' in key:                                     # split key around ':' if it exists
            first = re.compile(r"^[a-zA-Z_]+")                  # matches first letter or underscore sequence
            second = re.compile(r":+?.+")                       # matches first ':' and all after it
            tag_dict['type'] = first.search(key).group()        # assigns 'type' to 'k' before first ':'
            tag_dict['key'] = second.search(key).group()[1:]    # assigns 'key' to 'k' after first ':'

        else:
            tag_dict['type']  = default                         # if no ':', assign type to default
            tag_dict['key']   = key                             # if no ':', assign 'key' to 'k'

        tags.append(tag_dict)

    return tags

def shape_element(element, node_fields=NODE_FIELDS, way_fields=WAY_FIELDS,
                  default_tag_type='regular'):
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


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file,          codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file,          codecs.open(WAYS_PATH, 'w') as ways_file,          codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file,          codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

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


FILEPATH = "C:\Users\LonelyMerc\Documents\python\udacity\P3"


MAP = "\\osm_files\\map"
FOCO = "\\osm_files\\fort_collins.osm"
MAP_SAMPLE = "\\sample.osm"
FOCO_SAMPLE = "\\fc_sample.osm"


# ================================================== #
#                  SQL Creation                      #
# ================================================== #
import csv, sqlite3

db_fpath = 'C:\\Users\\LonelyMerc\\Documents\\python\\udacity\\P3\\'
db_fname = 'foco_osm_test.db'
write_fpath = db_fpath
write_fname = 'sql_manager_test.txt'
read_fname = ''

conn = sqlite3.connect(db_fpath + db_fname)
c = conn.cursor()

# purges table from database             # just for testing reasons
for drop in ["DROP TABLE Nodes;","DROP TABLE Nodes_Tags;","DROP TABLE Ways;","DROP TABLE Ways_Tags;","DROP TABLE Ways_Nodes;"]:
    c.execute(drop)

# Create Database Tables for:
# Nodes
c.execute("""CREATE TABLE Nodes(
                id INTEGER PRIMARY KEY,
                lat REAL,
                lon REAL,
                user TEXT,
                uid INTEGER,
                version INTEGER,
                changeset INTEGER,
                timestamp TEXT);    """)
# Nodes_Tags
c.execute("""CREATE TABLE Nodes_Tags(
                id INTEGER,
                key TEXT,
                value TEXT,
                type TEXT,
                FOREIGN KEY(id) REFERENCES Nodes(id));    """)
# Ways
c.execute("""CREATE TABLE Ways(
                id INTEGER PRIMARY KEY,
                user TEXT,
                uid INTEGER,
                version INTEGER,
                changeset INTEGER,
                timestamp TEXT);    """)
# Way_Tags
c.execute("""CREATE TABLE Ways_Tags(
                id INTEGER,
                key TEXT,
                value TEXT,
                type TEXT,
                FOREIGN KEY(id) REFERENCES Ways(id));    """)
# Way_Nodes
c.execute("""CREATE TABLE Ways_Nodes(
                id INTEGER,
                node_id INTEGER,
                position INTEGER,
                FOREIGN KEY(id) REFERENCES Ways(id));    """)

print "Database creation successful!"
conn.commit()
conn.close()


# ================================================== #
#                Populate Database                   #
# ================================================== #

conn = sqlite3.connect(db_fpath + db_fname)
c = conn.cursor()

csv_db_pair = { "Nodes" : "C:\\Users\\LonelyMerc\\nodes.csv",
                "Nodes_Tags" : "C:\\Users\\LonelyMerc\\nodes_tags.csv",
                "Ways" : "C:\\Users\\LonelyMerc\\ways.csv",
                "Ways_Tags" : "C:\\Users\\LonelyMerc\\ways_tags.csv",
                "Ways_Nodes" : "C:\\Users\\LonelyMerc\\ways_nodes.csv" }

def populate_db_from_csv(table, csv_path):

    with open(csv_path, 'r') as csv_f:
        reader = csv.reader(csv_f)
        columns = next(reader)
        query = 'INSERT INTO {0}({1}) VALUES ({2});'
        query = query.format(table, ','.join(columns), ','.join('?' * len(columns)))
        for data in reader:
            c.execute(query, data)
        conn.commit()


for key in csv_db_pair:
    populate_db_from_csv(key, csv_db_pair[key])
    print "Success populating", key, "!"
conn.close()


conn = sqlite3.connect(db_fpath + db_fname)
c = conn.cursor()

## Printing output from each

for table in ["Nodes","Nodes_Tags","Ways","Ways_Tags","Ways_Nodes"]:
    c.execute("SELECT * FROM {0} LIMIT 1;".format(table))
    # print c.fetchall()

print c.execute("SELECT * FROM Nodes WHERE id in (SELECT id FROM Nodes_Tags WHERE value== 80525 LIMIT 5);").fetchall()


conn.close()
