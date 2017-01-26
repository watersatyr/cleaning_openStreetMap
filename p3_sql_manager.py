#!usr/bin/env python
# -*- coding: utf-8 -*-
# Title: p3_sql_manager.py
# author: sle7in
# class: Udacity SQL Project 3
# date: 12/31/2016

import csv, sqlite3, np

db_fpath = 'C:\\Users\\LonelyMerc\\Documents\\python\\udacity\\P3\\'
db_fname = 'foco_osm.db'
write_fpath = db_fpath
write_fname = 'sql_manager_test.txt'
read_fname = ''

##################################
##### Valification Functions #####
def in_city(coords):
    """Accepts coords as a tuple or list, (lat, long).
       Checks if the input coordinates are within the city boundaries"""

    south_bound, north_bound = 40.474096, 40.639273
    west_bound, east_bound = -105.153307, -104.982127
    in_lat, in_lon = coords

    if (in_lon >= west_bound) and (in_lon <= east_bound) and \
    (in_lat >= south_bound) and (in_lat <= north_bound):
        return True, (in_lat, in_lon)
    else:
        # prints the violating bound
        if (in_lat < south_bound) or (in_lat > north_bound):
            print "Latitude out of bounds:", in_lat
        if (in_lon < west_bound) or (in_lon > east_bound):
            print "Longitude out of bounds:", in_lon
        return False, (in_lat, in_lon)

def zip_in_city(zip_code):
    """Returns True if input zip_code is in city_zips, else False"""

    city_zips = [80521, 80522, 80523, 80524, 80525, 80526, 80527, 80528, 80553]

    return zip_code in city_zips







# with open(write_fname, 'w') as of:                                           # opens output file to write to
#     of.write("This is line 1 of the 'p3_sql_manager.py' output file.\n")
# def connect_db(db_fpath, db_fname):
#     """connect to database"""
conn = sqlite3.connect(db_fpath + db_fname)
c = conn.cursor()

# def creat_table():
# purges table from database
c.execute("DROP TABLE Nodes")

# creates Nodes table with desired columns
c.execute("""
    CREATE TABLE Nodes
        (
        id INTEGER PRIMARY KEY,
        lat REAL,
        lon REAL,
        user TEXT,
        uid INTEGER,
        version INTEGER,
        changeset INTEGER,
        timestamp TEXT
        /*FOREIGN KEY (ArtistId) REFERENCES NodeTags (ArtistId) # formatting for foreign key*/
        );
        """)

# Read
with open ('C:\\Users\\LonelyMerc\\nodes.csv', 'r') as nodes_f:
    reader = csv.reader(nodes_f)
    columns = next(reader)
    query = 'INSERT INTO Nodes({0}) VALUES ({1});'
    query = query.format(','.join(columns), ','.join('?' * len(columns)))
    for data in reader:
        c.execute(query, data)
    conn.commit()

## Printing output for expectations
c.execute("SELECT lat FROM Nodes;")
results = c.fetchall()
# print results.describe()
for result in results[:25]:
    print result
    # for part in result:
    #     print type(part)


conn.commit()
conn.close()
