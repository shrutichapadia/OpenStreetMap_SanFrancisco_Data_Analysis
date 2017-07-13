#!/usr/bin/env python
# -*- coding: utf-8 -*-


import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
from collections import defaultdict
import copy
from time import time
import sqlite3

import cerberus

import schema

OSM_PATH = "san-francisco_ca.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
# street_type_re = re.compile(r'^([\w.>\-]+)', re.IGNORECASE)
SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

expected = ["Street", "Avenue", "Boulevard", "Place","Drive", "Court", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons","Highway","Way","Terrace"]

# UPDATE THIS VARIABLE
mapping = { "St": "Street",
            "St.": "Street",
            "Rd": "Road",
            "Rd.": "Road",
            "Ln": "Lane",
            "road": "Road",
            "ct": "Court",
            "Ave": "Avenue",
            "avenue": "Avenue",
            "Hwy": "Highway",
            "Pl": "Place",
            "Dr": "Drive",
            "Blvd": "Boulevard",
            "Av": "Avenue",
            "Ct": "Court",
            "CT": "Court",
            "Ter": "Terrace",
            "residential": "Residential"
            }

street_types = defaultdict(set)
# audit street name
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

def is_street_name(elem):
    return (elem.attrib['k'] == "tiger:name_type")

# audit .osm file in node and way tags
def audit(osmfile):
    osm_file = open(osmfile, "r")
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    return street_types

#update street name check if it is as expected  or map it with mapping list
def update_name(name, mapping):
    # m = street_type_re.search(name)
    street_type = street_type_re.search(name)
    if street_type not in expected:
        if street_type in mapping:
            name = re.sub(street_type_re, mapping[street_type], name)
        else:
            pass
    return name

# update postcode to get unique 5 digit code
def update_postcode(postcode):
    # seperator = '-'
    sep = '-'
    if sep in postcode:
        postcodeList = postcode.split(sep,1)
        postcode = postcodeList[0]
    if "CA" in postcode:
        postcode = postcode.replace("CA","")
    if " " in postcode:
        postcode = postcode.replace(" ","")
    if ":" in postcode:
        postcode = postcode.replace(":","")
    if "ca" in postcode:
        postcode = postcode.replace("ca","")
    if postcode:
        postcode = postcode[:5]
    return postcode

#shape each and every element in node, way and its child elements too
def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    in_list = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    if element.tag == 'node':
        for attrib in NODE_FIELDS:
            if element.get(attrib):
                node_attribs[attrib] = element.attrib[attrib]
            else:
                return None
        for node in NODE_FIELDS:
            node_attribs[node] = element.attrib[node]
        for child in element:
            tag ={}
            tag['id'] = element.attrib['id']
            tag['value'] = child.attrib['v']
            problem = PROBLEMCHARS.search(child.attrib['k'])
            match = LOWER_COLON.search(child.attrib['k'])
            if child.attrib['k'] == 'addr:postcode':
                tag['value'] = update_postcode(child.attrib['v'])
            else:
                pass
            if problem:
                continue
            elif match:
                # m = match.group()
                tag_type = child.attrib['k'].split(':',1)[0]
                tag_key = child.attrib['k'].split(':',1)[1]
                tag['key'] = tag_key
                tag['type'] = tag_type
                tags.append(tag)
            else:
                tag['key'] = child.attrib['k']
                tag['type'] = 'regular'
                tags.append(tag)

        pprint.pprint(tags)
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        for attrib in WAY_FIELDS:
            if element.get(attrib):
                way_attribs[attrib] = element.attrib[attrib]
            else:
                return
        for way in WAY_FIELDS:
            way_attribs[way] = element.attrib[way]
            count =0
        for child in element:
            tag = {}
            way_node = {}
            if child.tag == 'nd':
                if element.attrib['id'] not in in_list:
                    in_list.append(element.attrib['id'])
                    way_node['id'] = element.attrib['id']
                    way_node['node_id'] = child.attrib['ref']
                    way_node['position'] = count
                    way_nodes.append(copy.copy(way_node))
                else:
                    count +=1
                    way_node['id'] = element.attrib['id']
                    way_node['node_id'] = child.attrib['ref']
                    way_node['position'] = count
                    way_nodes.append(copy.copy(way_node))

            elif child.tag == 'tag':
                tag['id'] = element.attrib['id']
                tag['value'] = update_name(child.attrib['v'], mapping)
                problem = PROBLEMCHARS.search(child.attrib['k'])
                match = LOWER_COLON.search(child.attrib['k'])
                if child.attrib['k'] == 'addr:postcode':
                    tag['value'] = update_postcode(child.attrib['v'])
                else:
                    pass
                if problem:
                    continue
                elif match:
                    tag_type = child.attrib['k'].split(':',1)[0]
                    tag_key = child.attrib['k'].split(':',1)[1]
                    tag['type'] = tag_type
                    tag['key'] = tag_key
                    tags.append(copy.copy(tag))
                else:
                    tag['key'] = child.attrib['k']
                    tag['type'] = 'regular'
                    tags.append(copy.copy(tag))

        pprint.pprint(tags)
        pprint.pprint(way_nodes)

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
    # validated full 1.4GB data file too.
    # validate = false to run faster once validation checked on sample data to make easy 
    process_map(OSM_PATH, validate=True)

    # print time take to process 1.4GB data file
    # print 'Completed in: ' + str(time() - t0) + ' seconds'
