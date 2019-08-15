#!/usr/bin/env python2
#parses out the full recount dashboard JSON file from AWS CloudWatch
#into separate input JSON files (one per widget) for programmatic download of metric streams
#using retrieve_cloudwatch_recount_stats.py

import sys
import json
fn = sys.argv[1]
fin = open(fn,"r")
db = json.load(fin)
fin.close()

widgets = db['widgets']
#metric ID
i = 1
#default period is an hour
default_period = 3600

#output json structure
o = {}

for w in widgets:
    mtype = w['type']
    if mtype != 'metric':
        continue
    p = w['properties']
    title = p['title']
    if title == 'Queue':
        continue
    #if title not in o['MetricDataQueries']:
    if title not in o:
        o[title]=[]
    metrics = p['metrics']
    (pnamespace, pdim_name, pdim_val, pmetric) = (None,None,None,None)
    pdims = []
    for m in metrics:
        #simple custom metric
        Id = None
        h = {}
        prefix = "m"
        period = default_period
        ilen = len(m)
        dims = []
        attrs = {}
        #user defined single metric
        if ilen == 3 and m[0] != '...':
            (namespace, metric, attrs) = m
            if namespace == '.':
                namespace = pnamespace
            pnamespace = namespace
            if 'stat' in attrs:
                stat = attrs['stat']
        #AWS service specific metric, these can have multiple "dimensions" which are Name:Value pairs
        #stored as individual entries following the namespace and metric entries but before the attribute dict if there is one
        elif ilen > 3 or m[0] == '...':
            prefix = 'a'
            (namespace, metric) = m[:2]
            dim_i = 0
            if namespace == '.':
                namespace = pnamespace
            if metric == '.':
                metric = pmetric
            if namespace == '...':
                namespace = pnamespace
                dim_name = pdims[dim_i][0]
                dim_val = metric
                if metric == '.': 
                    dim_val = pdims[dim_i][1]
                metric = pmetric
                dims.append({'Name':dim_name,'Value':dim_val})
                dim_i += 1
            pnamespace = namespace
            pmetric = metric
            #do we have attributes as well?
            if ilen % 2 != 0:
                attrs = m[-1]
                ilen -= 1
            j = 2
            while j < ilen:
                (dim_name, dim_val) = m[j:j+2]
                if dim_name == '.':
                    dim_name = pdims[dim_i][0]
                if dim_val == '.':
                    dim_val = pdims[dim_i][1]
                if len(pdims) <= dim_i:
                    pdims.append([dim_name, dim_val])
                else:
                    #case where we might need to overwrite old values
                    pdims[dim_i][0] = dim_name
                    pdims[dim_i][1] = dim_val
                dims.append({'Name':dim_name,'Value':dim_val})
                j += 2
                dim_i += 1
        #expression
        elif ilen == 1:
            prefix = 'e'
            attrs = m[0]
            h['Expression'] = attrs['expression']
            h['Label'] = attrs['label']
        #attributes shared by all (if present)
        if 'id' in attrs:
            h['Id'] = attrs['id']
        else:
            h['Id'] = 'rando_%d' % i
        i += 1
        if prefix != 'e':
            h['MetricStat'] = {'Metric': {'Namespace':pnamespace, 'MetricName':metric}, 'Period':period, 'Stat':stat}  
            if prefix == 'a':
                h['MetricStat']['Metric']['Dimensions'] = dims
        #now put into output json structure
        o[title].append(h)

for title in o.keys():
    title_fn = title
    title_fn = title_fn.replace(' ','_')
    jstruct = o[title]
    with open("%s.json" % title_fn, "w") as jfout:
        json.dump(jstruct, jfout) 
