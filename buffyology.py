#!/usr/bin/env python

#extract transcripts from buffology.com

import urllib,re,os.path

#datadir=os.path.expanduser("~/tex/scripts/buffys5/html_buffyology")
datadir=os.path.expanduser("~/tex/scripts/buffy_all")

def geteppage(which):
    url="http://www.buffyology.com/ep%d/" % which
    text=urllib.urlopen(url).read()
    match=re.search(r'<h3>Transcript:</h3>[^<]*<a href="([^"]*)">',
                    text,re.MULTILINE)
    if match != None:
        return match.group(1)
    else:
        print "Unable to find episode!"

def writeephtml(htmldir,which):
    base=geteppage(which)
    f=open("%s/%s" % (htmldir,base.split('/')[-1]),"w")
    text=urllib.urlopen("http://www.buffyology.com/%s" % base).read()
    print >>f, text
    f.close()

def getseries5():
#    for ep in range(79,101): #season 5 was episodes 79-100
    for ep in range(1,145): #every episode!
        writeephtml(datadir,ep)

if __name__=="__main__":
    getseries5()
