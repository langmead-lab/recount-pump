#use this download the various recount dashboard metrics for each monorail run (e.g. srav3_human6, tcga, etc...)
import sys
import boto3
import glob
import json

METRICS_DIR='cloudwatch_metrics'

#start/end times (in seconds since epoch) for the various runs
#srav3_human6: May 14-22 2019
#srav3_human7: June 6-20 2019
#tcga: July 10-31 2019 
run_times={'srav3_human6':[1557806400,1558584000],'srav3_human7':[1559793600,1561089600],'tcga':[1562731200,1564545600]}

session = boto3.Session(profile_name='jhu-langmead')
cw = session.client('cloudwatch')

metric_defs = glob.glob('%s/*.json' % METRICS_DIR)
for run in run_times.keys():
    (start,end) = run_times[run]
    for metric_def_file in metric_defs:
        with open(metric_def_file,"r") as fin:
            jdef = json.load(fin) 
            resp = cw.get_metric_data(MetricDataQueries=jdef['MetricDataQueries'], StartTime=start, EndTime=end, ScanBy='TimestampAscending')
            with open("%s.%s" % (metric_def_file, run), "w") as fout:
                json.dump(resp, fout, default=str)
