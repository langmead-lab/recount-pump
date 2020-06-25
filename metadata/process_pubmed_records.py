#!/usr/bin/env python3.6
import sys
import xml.dom.minidom
import xml.etree.ElementTree as ET

#meant to process records of type
#<!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMedArticle, 1st January 2019//EN" "https://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_190101.dtd">
#assumes one pumedID/article in input

aid_types=['pii', 'doi', 'pmc']
aid_types_header = '\t'.join([aid_type.upper() for aid_type in aid_types])

fname=sys.argv[1]
fin=open(fname,"rb")
raw_xml = fin.read()
fin.close()
root = ET.fromstring(raw_xml)

def get_attr(root_element, tag, attr_str):
    subobj = root_element.find(tag)
    if subobj is not None:
        return subobj.get(attr_str, default="")
    return ""

#Top Level: PubmedArticle
for ex in root.findall('PubmedArticle'):
    medline = ex.find('MedlineCitation')
    pmid = medline.findtext('PMID',default="")
    
    #medline dates
    ##completed
    datec = medline.find('DateCompleted')
    yearc = datec.findtext('Year')
    monthc = datec.findtext('Month')
    dayc = datec.findtext('Day')
    
    ##revised
    datec = medline.find('DateRevised')
    yearr = datec.findtext('Year')
    monthr = datec.findtext('Month')
    dayr = datec.findtext('Day')

    #process nested "Article"
    article = medline.find('Article')
    journal = article.find('Journal')
    journal_issn = journal.findtext('ISSN',default="")
    journalissue = journal.find('JournalIssue')
    journalvol = journalissue.findtext('Volume',default="")
    journaliss = journalissue.findtext('Issue',default="")
    journalyear = journalissue.findtext('Year',default="")
    journalmonth = journalissue.findtext('Month',default="")
    journaltitle = journal.findtext('Title',default="")
    
    title = article.findtext('ArticleTitle',default="")
    elocID = article.findtext('ELocationID',default="")

    abst = article.find('Abstract')
    abstract = abst.findtext('AbstractText',default="")

    lang = article.findtext('Language',default="")
    
    adata = article.find('ArticleDate')
    yeara = adata.findtext('Year',default="")
    montha = adata.findtext('Month',default="")
    daya = adata.findtext('Day',default="")
    
    medlinejinfo = medline.find('MedlineJournalInfo')
    mcountry = medlinejinfo.findtext('Country',default="")
    mTA = medlinejinfo.findtext('MedlineTA',default="")
    NLMUID = medlinejinfo.findtext('NlmUniqueID',default="")
    ISSNLinking = medlinejinfo.findtext('ISSNLinking',default="")

    pmeddata = ex.find('PubmedData')
    articleidlist = pmeddata.find('ArticleIdList')
    aids = articleidlist.findall('ArticleId')
    article_ids = {}
    for aid in aids:
        id_type = aid.get('IdType', default="")
        id_text = aid.text
        article_ids[id_type]=id_text

    article_ids_text = '\t'.join([article_ids[aid] for aid in aid_types])
    header = '\t'.join(['PMID', 'Medline.DateCompleted', 'Medline.DateRevised', 'Journal.ISSN', 'Journal.Volume', 'Journal.Issue', 'Jounrnal.PubYear', 'Journal.PubMonth', 'Journal.Title', 'Article.Title', 'ELocationID', 'Language', 'Article.Date', 'Journal.Country', 'MedlineTA', 'NlmUniqueID', 'ISSNLinking', aid_types_header, 'Abstract'])
    sys.stdout.write(header+'\n')
    sys.stdout.write('\t'.join([pmid,yearc+monthc+dayc,yearr+monthr+dayr,journal_issn,journalvol,journaliss,journalyear,journalmonth,journaltitle,title,elocID,lang,yeara+montha+daya,mcountry,mTA,NLMUID,ISSNLinking,article_ids_text,abstract])+'\n')

#kept here for debugging/historical reasons, this is the XML hierarchy of tags/attributes we want to get
#<PubmedArticleSet>
    #<PubmedArticle>
        #<MedlineCitation
            ##<PMID Version="1">22368089</PMID>
            ##<DateCompleted>
            ##    <Year>2013</Year>
            ##    <Month>07</Month>
            ##    <Day>22</Day>
            ##</DateCompleted>
            ##<DateRevised>
            ##    <Year>2018</Year>
            ##   <Month>11</Month>
            ##    <Day>13</Day>
            ##</DateRevised>
            #<Article PubModel="Print-Electronic">
                #<Journal>
                ##  <ISSN IssnType="Electronic">1460-2199</ISSN>
                #   <JournalIssue CitedMedium="Internet">
                ##        <Volume>23</Volume>
                ##       <Issue>2</Issue>
                ##        <PubDate>
                ##            <Year>2013</Year>
                ##            <Month>Feb</Month>
                ##        </PubDate>
                #    </JournalIssue>
                ##    <Title>Cerebral cortex (New York, N.Y. : 1991)</Title>
                #    <ISOAbbreviation>Cereb. Cortex</ISOAbbreviation>
                #</Journal>
                ##<ArticleTitle>The development and activity-dependent expression of aggrecan in the cat visual cortex.</ArticleTitle>
                ##<ELocationID EIdType="doi" ValidYN="Y">10.1093/cercor/bhs015</ELocationID>
                ##<Abstract>
                ##    <AbstractText>The Cat-301 monoclonal antibody identifies aggrecan, a chondroitin sulfate proteoglycan in the cat visual cortex and dorsal lateral geniculate nucleus (dLGN). During development, aggrecan expression increases in the dLGN with a time course that matches the decline in plasticity. Moreover, examination of tissue from selectively visually deprived cats shows that expression is activity dependent, suggesting a role for aggrecan in the termination of the sensitive period. Here, we demonstrate for the first time that the onset of aggrecan expression in area 17 also correlates with the decline in experience-dependent plasticity in visual cortex and that this expression is experience dependent. Dark rearing until 15 weeks of age dramatically reduced the density of aggrecan-positive neurons in the extragranular layers, but not in layer IV. This effect was reversible as dark-reared animals that were subsequently exposed to light showed normal numbers of Cat-301-positive cells. The reduction in aggrecan following certain early deprivation regimens is the first biochemical correlate of the functional changes to the γ-aminobutyric acidergic system that have been reported following early deprivation in cats.</AbstractText>
                ##</Abstract>
                ##<Language>eng</Language>
                ##<ArticleDate DateType="Electronic">
                ##  <Year>2012</Year>
                ##  <Month>02</Month>
                ##  <Day>23</Day>
                ##</ArticleDate>
            ##</Article>
            ##<MedlineJournalInfo>
            ##    <Country>United States</Country>
            ##    <MedlineTA>Cereb Cortex</MedlineTA>
            ##    <NlmUniqueID>9110718</NlmUniqueID>
            ##    <ISSNLinking>1047-3211</ISSNLinking>
            ##</MedlineJournalInfo>
    ##</MedlineCitation>
    ##<PubmedData>
        ##<ArticleIdList>
        ##    <ArticleId IdType="pubmed">22368089</ArticleId>
        ##    <ArticleId IdType="pii">bhs015</ArticleId>
        ##    <ArticleId IdType="doi">10.1093/cercor/bhs015</ArticleId>
        ##    <ArticleId IdType="pmc">PMC3539452</ArticleId>
        ##</ArticleIdList>
    #</PubmedData>
#</PubmedArticle>
#</PubmedArticleSet>
