
# OpenStreetMap 

# San Francisco Area Data Analysis and Report


Open Street Map data wrangling project main purpose is to work on data which is
entered by public as open source. Its perfect data set for understanding data wrangling and 
process to approach any data to make it meaningful data and prepare analysis report.

## Map Area

https://mapzen.com/data/metro-extracts/metro/san-francisco_california/

http://www.openstreetmap.org/relation/111968

### Reasons behind selection of San-Francisco Data set

San Francisco is heart of Bay Area. Person belongs to Bay Area Loves San Francisco, that is why I am excited to see what data revels about San Francisco. 
Its best opportunity to understand and contribute to improve data set on openstreetmap.org


## Problem Encountered during Data Wrangling


Initially as per small Sample data set from San Francisco metro extract data set, mainly encountered below listed problems/issues which need to be taken care to clean and read data.

• abbreviated street names , Street_type in second level "K" tags data from tiger:(Tiger GPS) used abbreviated street names as listed. Abbreviated street names like("st","St","Ln","Rd","Ter","Ave","Ct".....)

• Street data splited in segment as per below format and name_type street names are abbreviated as listed above


```python
<tag k="tiger:cfcc" v="A41" />
<tag k="tiger:county" v="Alameda, CA" />
<tag k="tiger:name_base" v="Mariposa" />
<tag k="tiger:name_type" v="Ave" />
```

• Inconsistent postcode(Zipcode) for expample  (944023025,94122-1515,CA94107, CA 94080,CA,CA:94103,ca)


```python
    id      Postcode
2998801779  944023025   
4365583731  94122-1515 
3049651523  CA94107     
2609120447  CA 94080
262260718   CA 
33194422    CA:94103    
279256784   ca           
```

• Area surrounding san francisco also covered like Oakland,Redwood City etc because of postcode begins with "94****"

• Missing attributes / Null value in uid,user element 

### Abbreviated Street Name

As per sample data few abbreviated street name data revealed but when SQL query revealed street name under Tiger GPS is in segment as well as abbreviated completely. So to maintain consistency in street name below function used to update street name in node tags as well as way tags mapping each with expected name in data.py


```python
def update_name(name, mapping):
    street_type = street_type_re.search(name)
    if street_type not in expected:
        if street_type in mapping:
            name = re.sub(street_type_re, mapping[street_type], name)
        else:
            pass
    return name
```

such update function returns street name from ("Mariposa","Ave") to ("Mariposa Avenue") 

### Postcode needs to Update

Postcode string having differnent kind of pattern which need to taken care to maintain 5 digit consistent 
postcode. Below update_postcode function is used for triming postcode leading and trailing characters from (CA94107,CA 94560 , 944023025, CA, 94103-3124)


```python
def update_postcode(postcode):
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

```

Even after standardizing inconsistent with update_postcode, when queried with aggregator postcode appeared in variant format as listed above and cleaned to maintain consistency. 


```python
sqlite> SELECT tags.value, COUNT(*) as count FROM (SELECT * FROM node_tags UNION ALL SELECT * FROM way_tags) tags WHERE tags.key='postcode'GROUP BY tags.value ORDER BY count DESC;
```


```python
value       count
----------  ----------
94122       5115
94611       2988
94116       2397
94117       1455
94610       1355
94118       1115
94133       1099
94103       801
94127       743
94109       464

only top ten result for view purpose.
```

Now all post code are neat, cleaned and consistent 5 digit numbers in node_tags as well a way_tags.

At the moment postcode contained ("CA","ca") has been removed and kept empty, anyway such data are hardly 
4 in complete 2GB data set so have not assign any value to such postcode. If its really more than we have to workout postcode according to area or something.

This result consist Tiger GPS data as well and such way - tag "k" value has been considered to count all postcode.



```python
sqlite> SELECT tags.value, COUNT(*) as count FROM (SELECT * FROM node_tags UNION ALL SELECT * FROM way_tags) tags WHERE tags.key LIKE '%city' GROUP BY tags.value ORDER BY count DESC;
```


```python
value         count
------------  ----------
Redwood City  23508
San Francisc  18927
Berkeley      5628
Piedmont      3811
Palo Alto     1642
Oakland       1364
Richmond      1353
```

This query confirmed that in metro extract for San Francisco they consider surrounding area with zipcode 94*** such impact
postal code data and couting of city so this city or postcode are not incorrect but its bit unexpected.


### Missing attributes / Null Value in dataset

SQL query revealed uid and user element contain null value such null value was not captured in sample data set. To overcome from this issue there are two options

• Omit the element with the missing attribute

• Replace the missing attribute with a placeholder

As very few attributes were missing so I choose Omit the element with missing attribute. Can not leave with null value because user and uid are not null value in database.



```python
#from shape_element only relevant code copied here
if element.tag == 'node':
        for attrib in NODE_FIELDS:
            if element.get(attrib):
                node_attribs[attrib] = element.attrib[attrib]
            else:
                return
elif element.tag == 'way':
        for attrib in WAY_FIELDS:
            if element.get(attrib):
                way_attribs[attrib] = element.attrib[attrib]
            else:
                return
```

# Data Overview

This section contains basic statistics about dataset. To highlight main dataset size and quantity of data consist in bifergated data in to csv file.
SQL query make it easy to fetch such quantitative data about dataset.

### File Sizes


```python
File                                         Size
san-francisco_ca.osm                         1.4 GB
openstreetmap_sf.db                          1.05 GB
sample.osm                                   3.5 MB
nodes.csv                                    553.6 MB
nodes_tags.csv                               9.6 MB
ways.csv                                     50.1 MB
ways_nodes.csv                               188.3 MB
ways_tags.csv                                58.8 MB
```

### Number of Nodes in nodes.csv


```python
sqlite> SELECT COUNT(*) FROM nodes;
```

6600934

### Number of Ways in ways.csv


```python
sqlite> SELECT COUNT(*) FROM way;
```

819636

### Unique Users


```python
sqlite> SELECT COUNT(DISTINCT(n.uid)) as unique_user FROM(SELECT uid FROM nodes UNION ALL SELECT uid FROM way) n;
```

2733

### Users appears once


```python
sqlite> SELECT COUNT(*) FROM (SELECT e.user, COUNT(*) as num FROM (SELECT user FROM nodes UNION ALL SELECT user FROM way) e GROUP BY e.user HAVING num=1)  u;
```

688

### Users appears morethan once


```python
sqlite> SELECT COUNT(*) FROM (SELECT e.user, COUNT(*) as num FROM (SELECT user FROM nodes UNION ALL SELECT user FROM way) e GROUP BY e.user HAVING num >1)  u;
```

2050

### Top 10 Contributer 


```python
sqlite> SELECT n.user, COUNT(*) as count FROM (SELECT user FROM nodes UNION ALL SELECT user FROM way) n GROUP BY n.user ORDER BY count DESC LIMIT 10;
```


```python
user        count
----------  ----------
andygol     1496633
ediyes      887771
Luis36995   675899
dannykath   545973
RichRico    415801
Rub21       383504
calfarome   190820
oldtopos    165929
KindredCod  148790
karitotp    139861
```

### Yearly Highest Constribution by user 


```python
sqlite> SELECT n.user, strftime('%Y', timestamp) as year, COUNT(*) count FROM (SELECT user, timestamp FROM nodes UNION ALL SELECT user, timestamp FROM way) n GROUP BY n.user, year ORDER BY count DESC LIMIT 10;
```


```python
user                  year        count
--------------------  ----------  ----------
andygol               2017        1450038
ediyes                2014        653588
Luis36995             2014        492802
dannykath             2017        468093
Rub21                 2014        379145
RichRico              2017        193265
ediyes                2015        161053
Luis36995             2015        124088
RichRico              2016        123867
oldtopos              2013        117844
```

### Contribution in 2017 


```python
sqlite> SELECT n.user, strftime('%Y', timestamp) as year, COUNT(*) count FROM (SELECT user, timestamp FROM nodes UNION ALL SELECT user, timestamp FROM way) n WHERE year = '2017'GROUP BY n.user, year ORDER BY count DESC LIMIT 10;
```


```python
user                            year        count
------------------------------  ----------  ----------
andygol                         2017        1450038
dannykath                       2017        468093
RichRico                        2017        193265
hmkandrey                       2017        55244
BharataHS                       2017        46609
Ludmila Gladkova                2017        46000
TheDutchMan13                   2017        37457
ramyaragupathy_sfimport         2017        23772
saikabhi_sfimport               2017        19449
oba510                          2017        19445
```

Hightest contribution is 22% in year 2017 is by user andygol that is highest in all over time period too

### Top Contributors contribution in Percentage

Yearly Contribution in % partcularly in Nodes


```python
sqlite> SELECT nodes.user, strftime('%Y', nodes.timestamp) as year, COUNT(nodes.user) as count,(SELECT COUNT(*) FROM nodes) as total, COUNT(nodes.user)*100/(SELECT COUNT(*) FROM nodes) as percentage FROM nodes GROUP BY nodes.user ORDER BY count DESC LIMIT 10;
```


```python
user                            year        count       total       percentage
------------------------------  ----------  ----------  ----------  ----------
andygol                         2017        1316395     6600934     19
ediyes                          2017        854021      6600934     12
Luis36995                       2017        650748      6600934     9
dannykath                       2017        481948      6600934     7
Rub21                           2017        378308      6600934     5
RichRico                        2017        368970      6600934     5
calfarome                       2017        171728      6600934     2
KindredCoda                     2017        145290      6600934     2
oldtopos                        2014        138175      6600934     2
karitotp                        2017        126677      6600934     1
```

Andygol who is highest contributor allover contribution 22% out of which 19% in Nodes only.

Combined top 4 contributors which is 10% and morethan 10% individual contribution and 50% of all over contribution. Such contribution distribution
very surprising as only 4 users make 50% contribution. Their contribution in 2017 and 2014 are incredible. Their contribution is motivating to rest of 2729 users and new users too. 

I observed that content of dataset is improved a lot as compare to Chicago dataset. This is best exampleof power users contribution make big difference.


## Additional Data Exploration

### Top 10 amenities in San Francisco


```python
sqlite> SELECT value, COUNT(*) as count FROM node_tags WHERE key='amenity'GROUP BY value ORDER BY count DESC LIMIT 10;
```


```python
value                 count
--------------------  ----------
restaurant            2963
bench                 1187
cafe                  995
place_of_worship      692
post_box              687
school                582
fast_food             580
bicycle_parking       567
drinking_water        528
toilets               411
```

Reataurant is one of the most popular amenity in San Francisco this resault is not surprising at all.

### Most Popular Cuisine in San Francisco


```python
sqlite> SELECT node_tags.value, COUNT(*) as count FROM node_tags JOIN (SELECT DISTINCT(id) FROM node_tags WHERE value='restaurant') n ON node_tags.id=n.id WHERE node_tags.key='cuisine' GROUP BY node_tags.value ORDER BY count DESC LIMIT 10;
```


```python
value                 count
--------------------  ----------
mexican               197
chinese               166
pizza                 154
japanese              141
italian               127
thai                  109
american              99
vietnamese            70
indian                60
sushi                 59
```

No surprise Mexican food is in highest demand in San Francisco.

### Most common Religion in San Francisco 


```python
sqlite> SELECT node_tags.value, COUNT(*) as num FROM node_tags JOIN (SELECT DISTINCT(id) FROM node_tags WHERE value='place_of_worship') e ON node_tags.id=e.id WHERE node_tags.key='religion' GROUP BY node_tags.value ORDER BY num DESC LIMIT 10;
```


```python
value                 num
--------------------  ----------
christian             629
buddhist              15
jewish                10
muslim                5
unitarian_universali  2
bahai                 1
eckankar              1
hindu                 1
scientologist         1
taoist                1
```

Christian 629 top most popular religion and its obvious no doubt on it.

## Conclusion

During data warngling and analysing its seems still data is imcomplete and there is open sky to improve it. 
I try to clean more fairly for the purpose of this report. While working on dataset individual contributor efforts for editing data particularly Tiger GPS need more attention as compare to other data such are fairly clean. 

I believe scripting data with GPS data processor and users efforts with more robust data processor like data.py, its possible to improve quality of dataset at OpenStreetMap.org very easily. Such cleaned imporved quality data with as much as more relevant information rewards each and every contributors efforts. Such efforts inspire more and more contribitors too.
