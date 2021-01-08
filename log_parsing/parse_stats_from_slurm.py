from datetime import datetime
import sys

f = sys.argv[1]

node_map = {}
with open('../all_knls.sinfo.nodes.map',"r") as fin:
    for line in fin:
        (node, platform) = line.rstrip().split('\t')
        node_map[node] = platform


d1p=None
d2p=None
node=None
start = None
end = None
counter = 0
nodes = {}
with open(f,"r") as fin:
    for line in fin:
        fields = line.rstrip().split(' ')
        slurm_file = fields[0]
        node = fields[5]
        d1 = ' '.join(fields[1:4])
        d1p = datetime.strptime("2020 "+d1, '%Y %b %d %H:%M:%S')
        if node not in nodes:
            nodes[node] = {}
            nodes[node]['count'] = 0
            nodes[node]['start'] = d1p
        nodes[node]['end'] = d1p
        nodes[node]['count'] += 1
        #short version
        #d1 = ' '.join(fields[:3])
        #d1p = datetime.strptime("2020 "+d1, '%Y %b %d %H:%M:%S')
        #fields = fin.readline().split(' ')
        #d2 = fields[9]
        #d2p=datetime.strptime(d2, '%Y-%m-%dT%H:%M:%S')
        #node = fields[6]
#dd=d2p-d1p
platforms = {}
for platform in ['KNL','SKX']:
    platforms[platform]={}
    platforms[platform]['count']=0
    platforms[platform]['hours']=0

for node in nodes.keys():
    vals = nodes[node]
    dd = vals['end'] - vals['start']
    count = vals['count']
    sec = dd.total_seconds()
    hours = sec / 3600
    days = sec / 86400
    platform = node_map[node]
    platforms[platform]['count'] += count
    platforms[platform]['hours'] += hours
    sys.stdout.write("%s\t%s\t%d\t%s\t%s\t%s\t%s\t%s\n" % (node, platform, count, hours, days, sec, vals['start'], vals['end']))

for platform in platforms.keys():
    vals = platforms[platform]
    sys.stderr.write("%s\t%d\t%d\n" % (platform, vals['count'], vals['hours']))
