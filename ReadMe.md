OpenStreetMap - San Francisco Area Data Analysis and Report

Open Street Map data wrangling project main purpose is to work on data which is entered by public as open source. Its perfect data set for understanding data wrangling and process to approach any data to make it meaningful data and prepare analysis report.



Map Data Link:

https://mapzen.com/data/metro-extracts/metro/san-francisco_california/
http://www.openstreetmap.org/relation/111968

After auditing is complete the next step is to prepare the data to be inserted into a SQL database.
To do so need parse the elements in the OSM XML file, transforming them from document format to
tabular format, thus making it possible to write to .csv files.  These csv files can then easily be
imported to a SQL database as tables.

The process for this transformation is as follows:
- Use iterparse to iteratively step through each top level element in the XML
- Shape each element into several data structures using a custom function
- Utilize a schema and validation library to ensure the transformed data is in the correct format
- Write each data structure to the appropriate .csv files
- import .csv to sqlite3 and run sql query to extract data

Language,tools and techniques used
Python,Pandas, sqlite3, Atom, Jupyter Notebook 

Files:

readme.md                                              Readme File for detail description
san-francisco_ca.osm    size 1.4 GB                    data file extract from openstreetmap.org
sample.py                                              to extract sample from san-francisco_ca.osm datafile
sample.osm              size 3.5 MB                    sample datafile
sf_sample.osm           size 1.8 MB                    small sample datafile
data.py                                                data processor file contain python code to clean data as well as
                                                       process data from .osm to .csv
schema.py                                              schema to validate transformed data in correct format

.csv files                                             transformed data stored in individual .csv file
 - nodes.csv            size 553.6 MB
 - nodes_tags.csv       size 9.6 MB
 - ways.csv             size 50.01 MB
 - ways_tags.csv        size 58.8 MB
 - ways_nodes.csv       size 188.3 MB

Edited .csv files to import to sqlite3
- node.csv              size 553.6 MB
- node_tags.csv         size 9.6 MB
- way.csv               size 50.01 MB
- ways_tag.csv          size 58.8 MB
- ways_node.csv         size 188.3 MB

OpenStreetMap_SanFrancisco_Data_Analysis_Report.ipynb   Analysis report in Jupyter Notebook


Data Cleaning and Trasformation:

Shape Element Function (data.py)
The function should take as input an iterparse Element object and return a dictionary.

### If the element top level tag is "node":
The dictionary returned should have the format {"node": .., "node_tags": ...}

The "node" field should hold a dictionary of the following top level node attributes:
- id
- user
- uid
- version
- lat
- lon
- timestamp
- changeset
All other attributes has been ignored

The "node_tags" field should hold a list of dictionaries, one per secondary tag. Secondary tags are
child tags of node which have the tag name/type: "tag". Each dictionary should have the following
fields from the secondary tag attributes:
- id: the top level node id attribute value
- key: the full tag "k" attribute value if no colon is present or the characters after the colon if one is.
- value: the tag "v" attribute value
- type: either the characters before the colon in the tag "k" value or "regular" if a colon
        is not present.

Additionally,

- if the tag "k" value contains problematic characters, the tag should be ignored
- if the tag "k" value contains a ":" the characters before the ":" should be set as the tag type
  and characters after the ":" should be set as the tag key
- if there are additional ":" in the "k" value then and that should be ignored and kept as part of
  the tag key. For example:

  <tag k="addr:street:name" v="Lincoln"/>
  should be turned into
  {'id': 12345, 'key': 'street:name', 'value': 'Lincoln', 'type': 'addr'}

- If a node has no secondary tags then the "node_tags" field should just contain an empty list.

### If the element top level tag is "way":
The dictionary should have the format {"way": ..., "way_tags": ..., "way_nodes": ...}

The "way" field should hold a dictionary of the following top level way attributes:
- id
-  user
- uid
- version
- timestamp
- changeset

All other attributes been ignored

The "way_tags" field should again hold a list of dictionaries, following the exact same rules as
for "node_tags".

Additionally, the dictionary should have a field "way_nodes". "way_nodes" should hold a list of
dictionaries, one for each nd child tag.  Each dictionary should have the fields:
- id: the top level element (way) id
- node_id: the ref attribute value of the nd tag
- position: the index starting at 0 of the nd tag i.e. what order the nd tag appears within
            the way element

get element () and validate element()

get all elements from Nodes and ways and its child element as listed above, yeild each element if its parsed right tag

validate element as per schema.py to trasform in valid format

process_map() iterate each xml element and write it to .csv file

sqlite3 used to run sql query openstreetmap_sf.db database prepared to store .csv files and query data to get more insight init.

for more detail or any query contact
shrutichapadia@gmail.com
