import sys
import xml.dom.minidom
fname=sys.argv[1]
fin=open(fname,"rb")
fout=open(fname+".nice","w")
raw_xml = fin.read()
fin.close()
fout.write(xml.dom.minidom.parseString(raw_xml).toprettyxml().encode('utf-8'))
fout.close()
