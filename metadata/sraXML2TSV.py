#script to convert SRA RUN,EXPERIMENT,SAMPLE, and STUDY level metadata into single line records, one per RUN
#in a TSV output format; only looks for RNA-seq related tags/fields
import sys
import xml.dom.minidom
import xml.etree.ElementTree as ET

#SRA Xml definitions are here (as of 2019-05-03):
#https://www.ncbi.nlm.nih.gov/viewvc/v1/trunk/sra/doc/SRA/

ATTR_DELIM=';;'
ATTRS_DELIM='|'

fname=sys.argv[1]
fin=open(fname,"rb")
raw_xml = fin.read()
fin.close()
root = ET.fromstring(raw_xml)
#parse all relevant fields into a single, tab delimited line record (1 per Run [SRR])
#for SAMPLE_,RUN_ ATTRIBUTES (TAG/VALUE) put into single field, but futher delimit with single pipes (|) and double semi colons (;;)

def get_attr(root_element, tag, attr_str):
    subobj = root_element.find(tag)
    if subobj is not None:
        return subobj.get(attr_str, default="")
    return ""

def process_attributes(root_element, tag):
    #using SAMPLE_ATTRIBUTES as an example:
    #SAMPLE_ATTRIBUTES
        #SAMPLE_ATTRIBUTE
            #TAG(text)
            #VALUE(text)
    attrs = root_element.find(tag)
    if attrs is None:
        return ""
    #order attributes by TAG value
    #this way attributes from the same study 
    #which share the same TAGs will have aligned fields
    tags = []
    #loop over "TAG_ATTRIBUTE" sub tags
    for attr in attrs:
        tag = attr.findtext('TAG',default="")
        value = attr.findtext('VALUE',default="")
        tags.append(tag+ATTR_DELIM+value)
    #case insensitive search
    return ATTRS_DELIM.join(sorted(tags, key=lambda x: x.lower()))

#header
#sys.stdout.write("\t".join(["run_acc","study_acc","sample_acc","experiment_acc","submission_acc","submission_center","submission_lab","study_title","study_abstract","study_description","experiment_title","design_description","sample_description","library_name","library_strategy","library_source","library_selection","library_layout","paired_nominal_length","paired_nominal_stdev","library_construction_protocol","platform_model","sample_attributes","experiment_attributes","spot_length","sample_name","sample_title","sample_bases","sample_spots","run_published","size","run_total_bases","run_total_spots","num_reads","num_spots","read_info","run_alias","run_center_name","run_broker_name","run_center","inferred_read_length","inferred_total_read_count"])+"\n")

#Top Level: EXPERIMENT_PACKAGE
for exp in root.findall('EXPERIMENT_PACKAGE'):
##EXPERIMENT section
    #only expect one experiment here
    ex = exp.find('EXPERIMENT')
    #do accessions first
    #EXPERIMENT accession
    exp_acc = ex.get('accession', default="")
    #STUDY: accession
    study_acc = get_attr(exp, 'STUDY', 'accession')
    #STUDY_REF: accession
    exp_study_acc = get_attr(ex, 'STUDY_REF', 'accession')
    if len(study_acc) == 0 or len(exp_study_acc) == 0 or study_acc != exp_study_acc:
        sys.stderr.write("EXPERIMENT %s either has no STUDY_REF, STUDY, or the two accessions do not agree: %s vs. %s, skipping\n" %(exp_acc, exp_study_acc, study_acc))
        continue 
    #SAMPLE: accession
    sample_acc = get_attr(exp, 'SAMPLE', 'accession')
    if len(sample_acc) == 0:
        sys.stderr.write("EXPERIMENT %s has no sample accession, skipping experiment\n" % (exp_acc))
        continue
    #SUBMISSION: accession, center_name, lab_name
    sub_acc = get_attr(exp, 'SUBMISSION', 'accession')

    #TITLE(text)
    exp_title = ex.findtext('TITLE',default="")
    design = ex.find('DESIGN')
    if design is None:
        sys.stderr.write("EXPERIMENT %s has not DESIGN section, skipping experiment\n" % (exp_acc))
        continue
    #DESIGN
        #DESIGN_DESCRIPTION(text)
    design_desc = design.findtext('DESIGN_DESCRIPTION',default="")
    #LIBRARY_DESCRIPTORs
    lib_descriptor = design.find('LIBRARY_DESCRIPTOR')
    if lib_descriptor is None:
        sys.stderr.write("EXPERIMENT %s has no LIBRARY_DESCRIPTOR, skipping experiment\n" % (exp_acc))
        continue
    lib_name = lib_descriptor.findtext('LIBRARY_NAME',default="")
    lib_strat = lib_descriptor.findtext('LIBRARY_STRATEGY',default="")
    lib_src = lib_descriptor.findtext('LIBRARY_SOURCE',default="")
    lib_sel = lib_descriptor.findtext('LIBRARY_SELECTION',default="")
    lib_construct_prot = lib_descriptor.findtext('LIBRARY_CONSTRUCTION_PROTOCOL',default="")
    
    lib_layout = ""
    paired_nominal_length = ""
    paired_nominal_stdev = ""
    library_layout = lib_descriptor.find('LIBRARY_LAYOUT')
    paired = library_layout.find('PAIRED')
    if paired is not None:
        lib_layout = "paired"
        paired_nominal_length = paired.get('NOMINAL_LENGTH',default="") 
        paired_nominal_stdev = paired.get('NOMINAL_SDEV',default="") 
    elif library_layout.find('SINGLE') is not None:
        lib_layout = "single"

    #older records have ~read length stored in SPOT_LENGTH
    spot_length = design.findtext('./SPOT_DESCRIPTOR/SPOT_DECODE_SPEC/SPOT_LENGTH',default="")

    platform = ""
    model = ex.findall("./PLATFORM/*/INSTRUMENT_MODEL")
    if len(model) == 1:
        platform = model[0].text

    exp_attributes = process_attributes(ex, 'EXPERIMENT_ATTRIBUTES')

##SUBMISSION section
    sub_center = get_attr(exp, 'SUBMISSION', 'center_name')
    sub_lab = get_attr(exp, 'SUBMISSION', 'lab_name')

##STUDY section
    #DESCRIPTOR
        #STUDY_TITLE(text)
    study_title = exp.findtext('./STUDY/DESCRIPTOR/STUDY_TITLE',default="")
                #STUDY_ABSTRACT(text)
    study_abstract = exp.findtext('./STUDY/DESCRIPTOR/STUDY_ABSTRACT',default="")
    study_desc = exp.findtext('./STUDY/DESCRIPTOR/STUDY_DESCRIPTION',default="")

##SAMPLE section
            #SAMPLE_ATTRIBUTES
                #SAMPLE_ATTRIBUTE
                    #TAG(text)
                    #VALUE(text)
    sample_desc = exp.findtext('./SAMPLE/DESCRIPTION',default="")
    sample_attributes = process_attributes(exp, './SAMPLE/SAMPLE_ATTRIBUTES')

    exp_fields = [study_acc, sample_acc, exp_acc, sub_acc, sub_center, sub_lab, study_title, study_abstract, study_desc, exp_title, design_desc, sample_desc, lib_name, lib_strat, lib_src, lib_sel, lib_layout, paired_nominal_length, paired_nominal_stdev, lib_construct_prot, platform, sample_attributes, exp_attributes, spot_length]
    exp_fields_str = "\t".join(exp_fields)

##RUN_SET section
    #may be multiple RUNs
    run_set = exp.find('RUN_SET')
    exp = run_set
    for run in exp.findall('RUN'):
        run_str = []
        #RUN: accession, alias, published, size, total_bases, total_spots, center_name, run_center, broker_name
        run_acc = run.get('accession',default="")
        run_alias = run.get('alias',default="")
        run_center_name = run.get('center_name',default="")
        run_center = run.get('run_center',default="")
        run_broker_name = run.get('broker_name',default="")
        #skip any RUN whose accession isn't present
        if len(run_acc) == 0:
            continue
        published = run.get('published', default="")
        size = run.get('size', default="")
        total_bases = run.get('total_bases', default="")
        total_spots = run.get('total_spots', default="")
        #EXPERIMENT_REF: accession (tie to experiment acc)
        run_exp_acc = get_attr(run, 'EXPERIMENT_REF', 'accession')
        if len(run_exp_acc) == 0 and run_exp_acc != exp_acc:
            sys.stderr.write("RUN %s either has no EXPERIMENT_REF accession or it does not match the enclosing experiment's accession: %s vs. %s, skipping\n" %(run_acc, run_exp_acc, exp_acc))
            continue
        #Pool (tie to sample acc)
        #Member: accession (sample), bases, sample_name, sample_title, spots 
        pool = run.find('Pool')
        pool_member = None
        (run_sample_acc, run_sample_bases, run_sample_name, run_sample_title, run_sample_spots) = ("","","","","")
        if pool is not None:
            pool_member = pool.find('Member')
            if pool_member is not None:
                (run_sample_acc, run_sample_bases, run_sample_name, run_sample_title, run_sample_spots) = (pool_member.get('accession',""),pool_member.get('bases',""),pool_member.get('sample_name',""),pool_member.get('sample_title',""),pool_member.get('spots',""))
        #have to be more lenient, so comment out the sample  and/or pool/member  check
        #if pool_member is None or pool is None:
        #    sys.stderr.write("RUN %s has no sample pool members, skipping\n" % (run_acc))
        #    continue
        #if len(run_sample_acc) == 0 and run_sample_acc != sample_acc:
        #    sys.stderr.write("RUN %s either has no pool member sample accession or it does not match the enclosing experiment's sample accession: %s vs. %s, skipping\n" %(run_acc, run_sample_acc, sample_acc))
        #    continue
        #Statistics: nreads, nspots
        stats = run.find('Statistics')
        nreads = get_attr(run, 'Statistics', 'nreads')
        nspots = get_attr(run, 'Statistics', 'nspots')
        #READ: average, count, index, stdev
        #READ?
        reads_str = []
        read_length_sum = 0.0
        read_count_sum = 0.0
        read_rec_count = 0
        if stats is not None:
            for read in stats.findall('Read'):
                read_str = []
                read_count = float(read.get('count',default="0.0"))
                #either this is a single layout or we're just not getting these reads
                if read_count == 0.0:
                    continue
                read_rec_count += 1
                read_length_sum += float(read.get('average',default="0.0"))
                read_count_sum += read_count
                for attr in ['index','count','average','stdev']:
                    read_str.append(attr+':'+read.get(attr,default=""))
                reads_str.append(','.join(read_str))
        reads_str = ATTRS_DELIM.join(reads_str)

        run_title = run.findtext('TITLE',default="")
        run_attributes = process_attributes(run, 'RUN_ATTRIBUTES')

        #try to infer the most useful sequence length from the possibly used fields:
        #start with spots, this is rough
        inferred_read_length = spot_length
        #if we dont have spot_length, next try dividing the "nominal_length" by 2
        #that is based on this: https://www.ebi.ac.uk/fg/annotare/help/seq_lib_spec.html
        #which states nominal_length == insert_length for paired-end reads
        if len(inferred_read_length) == 0 and len(paired_nominal_length) > 0:
            inferred_read_length = int(paired_nominal_length) / 2.0
        readX = 1
        if lib_layout == 'paired':
            readX = 2
        inferred_total_read_count = readX * total_spots
        #better, if we have actual read stats, use them
        if read_rec_count > 0:
            inferred_read_length = read_length_sum / read_rec_count
            inferred_total_read_count = read_count_sum

        #put it all together at the level of a single RUN
        run_str = [exp_fields_str, run_sample_name, run_sample_title, run_sample_bases, run_sample_spots, published, size, total_bases, total_spots, nreads, nspots, reads_str,run_alias,run_center_name,run_broker_name,run_center,str(inferred_read_length),str(inferred_total_read_count)]
        out_str = run_acc+"\t"+"\t".join(run_str)+"\n"
        sys.stdout.write(out_str.encode('utf-8'))
