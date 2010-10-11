#!/usr/bin/env python
#Code to (hopefully) un-HTML and TeX up Buffy scripts

import os,string,sys,os.path,re,cPickle

#edit these as appropriate
basedir=os.path.expanduser("~/tex/scripts/buffys6")
datadir=basedir+"/html"
outdir=basedir+"/tex"

#beware of namespace clashes doing this
#from casting import *

#part -> person mapping
thiscast={}
#part -> LaTeX command mapping
texparts={}

def preamble(e):
    '''preamble(e)->get ready to start an episode

    \inputes preamble.tex in the appropriate .tex file,
    and opens that for writing, and the html for reading,
    along with a file to write cast-related LaTeX
    return is (html,tex,cast)
    '''
    texpath="texified/ep%02d.tex" % e
    castpath="texified/ep%02d_cast.tex" % e
    htmlpath="buffy-2%02d.htm" % e
    r=open(htmlpath,"r")
    w=open(texpath,"w")
    c=open(castpath,"w")
    print >>w, "\input{preamble}"
    print >>w, "\input{ep%02d_cast}" % e
    return (r,w,c)

def eptoindex(e):
    '''returns the index in the eps array that corresponds to an episode

    Calculates which subscript in eps[] you want for episode number e
    '''
    if e==12 or e==20:
        raise ValueError("We don't have episodes 12 or 20")
    #take into account the missing episodes
    if e>20:
        e-=1
    if e>12:
        e-=1
    e-=1
    return e

def frobcast(e):
    '''convert casting.py notation to suitable for script notation'''
    global thiscast
    multiples={}
    loadcast()
    thisep=eval("ep%d" % e)
    for p in thisep:
        #we want to frob characters with numbers in their names
        #this strips spaces and checks for only letters remaining
        if p.replace(' ','').isalpha():
            thiscast[p]=cast[p]
        else:
            what=p.rstrip(string.digits+'.')
            dictapp(multiples,what,p)
    for what in multiples.iterkeys():
        l=multiples[what]
        l.sort()
        if what=="Vamp":
            s="Vampire"
        else:
            s=what
        if len(l) > 1:
            for n in range(len(l)):
                thiscast["%s %d" % (s,n+1)]=cast[l[n]]
        else:
            thiscast["%s" % s]=cast[l[0]]
    
def castcommands(f):
    '''output a set of LaTeX macros for typesetting the foo: lines'''
    tt=string.maketrans('1234567890','abcdefghij')
    for p in thiscast.iterkeys():
        if p.find('(ns)')==-1: #exclude non-speakers
            print >>f, "\\newcommand{\\%s}{\\textbf{%s}}" % \
                  (p.upper().translate(tt,' '),p.upper())
            texparts[p]="\\%s" % p.upper().translate(tt,' ')
        #special case for Jenny, who appears as Jenny C in our casting
            if p=="Jenny C":
                texparts["Jenny"]=texparts["Jenny C"]


def casttable(f):
    '''print a LaTeX-ed cast list'''
    print >>f, """\\subsection*{Cast List}
\\begin{tabular}{ll}\\\\"""
    keys=thiscast.keys()
    keys.sort()
    for k in keys:
        print >>f, "%s & %s\\\\" % (k,thiscast[k])
    print >>f, "\\end{tabular}"

def ord_list():
    '''returns a list of the .htm files'''
    x=["%s/buffy-6%02d.htm" % (datadir,x) for x in range(1,23) ]
    return x

def guess_parts(lines):
    '''guesses what the parts in lines are'''
    parts=[]
    for l in lines:
        l=l.split(':')
        if len(l)>1:
            p=' '.join(l[0].split())
            if p.upper()==p:
                if p[:12]=="<BLOCKQUOTE>":
                    p=p[12:]
                if p not in parts:
                    parts.append(p)
    return parts

class Part:
    def __init__(self,name,episode,multiple=None):
        self.name=name
        if ' ' in self.name:
            ans=raw_input("%s a real part? " % name)
            if ans.upper().strip()=="Y":
                self.real=True
            else:
                self.real=False
        else:
            if name=="ALL" or name=="BUFFYBOT" \
                   or name=="BOTH" or '/' in name:
                self.real=False
            else:
                self.real=True
        self.firstep=episode
        self.checked=False #multiple state unknown
        self.appearances=[episode]
        if multiple is not None:
            self.checked=True
            self.multiple=multiple
    def appear(self,episode):
        if self.checked==True or ( self.firstep==1 and episode==2 ) \
               or ( self.firstep==21 and episode==22 ) :
            self.appearances.append(episode)
        elif self.real==False: #We assume any not-real parts aren't multiple
            self.checked=True
            self.multiple=False
            self.appearances.append(episode)
        else:
            ans=raw_input("%s appears in %d and %d (at least). Same part? " \
                          % (self.name,self.firstep,episode))
            if ans.upper().strip()=="Y":
                self.multiple=False
            else:
                self.multiple=True
            self.checked=True
            self.appearances.append(episode)

#like a tuple, but the first element (an int) may be used for sorting
class EpCount(tuple):
    def __cmp__(self,other):
        return(other[0]-self[0])

def add_part(name,episode,allparts,multiple=None):
    '''either adds episode to parts list of episodes, or creates new part'''
    if name in allparts:
        allparts[name].appear(episode)
    else:
        if multiple is not None:
            p=Part(name,episode,multiple)
        else:
            p=Part(name,episode)
        allparts[name]=p
    return allparts

def get_partarrays():
    '''either loads or generates the allparts,partsbyep and titles arrays'''
    try:
        f=open("allparts.dat","rb")
        pickle=cPickle.Unpickler(f)
        allparts=pickle.load()
        partsbyep=pickle.load()
        titles=pickle.load()
    except IOError:
        allparts,partsbyep,titles=gen_partarrays()
    return allparts,partsbyep,titles
        
def gen_partarrays():
    '''creates arrays of parts and titles'''
    allparts={}
    partsbyep=[]
    titles=[]
    htmls=ord_list()
    ep=1
    for f in htmls:
        title,parts=first_pass(f)
        #add a narrator
        allparts=add_part("NARRATOR",ep,allparts,True)
        for p in parts:
            allparts=add_part(p,ep,allparts)
        parts.append("NARRATOR")
        partsbyep.append(parts)
        titles.append(title)
        ep+=1
    f=open("allparts.dat","wb")
    pickle=cPickle.Pickler(f,-1)
    pickle.dump(allparts)
    pickle.dump(partsbyep)
    pickle.dump(titles)
    f.close()
    return allparts,partsbyep,titles


def get_castlist():
    '''write out a single list of the entire cast'''
    print >>sys.stderr, "Cast list already exists. Don't over-write it!"
    return
    allparts,partsbyep,titles=get_partarrays()
    byapp=[]
    parts=allparts.keys()
    for p in parts:
        x=allparts[p]
        n=len(x.appearances)
        #deal with parts that are just in 1,2 or 21,22
        if ( x.appearances==[1,2] or x.appearances==[21,22] ) \
           and x.checked==False:
            x.multiple=False
        if x.real==True and n>1 and x.multiple==False:
            byapp.append( EpCount( (n,x.name.lower().capitalize()) ) )
    byapp.sort(reverse=True)
    f=open("casting.txt","w")
    print >>f, "Buffy Season 6 - Cast List\n\nRecurring parts:"
    prev=None
    for p in byapp:
        if prev and p==prev:
            pass
        else:
            print >>f, "(%d) %s:" % (p[0],p[1])
        prev=p
    print >>f
    for ep in range(1,23):
        print >>f, "* %s *" % (titles[ep-1])
        parts=partsbyep[ep-1]
        parts.sort()
        names=[]
        for p in parts:
            x=allparts[p]
            n=len(x.appearances)
            if x.real==True and (n==1 or x.multiple==True):
                if x.name.lower().capitalize not in names:
                    print >>f, "%s:" % (x.name.lower().capitalize())
                    names.append(x.name.lower().capitalize())
        print >>f
    f.close()

def fix_parts():
    '''apply changes to the parts lists'''
    allparts,partsbyep,titles=get_partarrays()
    #make changes
    
    #this one is a typo
    allparts["DANW"]=allparts["DAWN"]
    #these are the same part,but both appear in the ep14 script
    #LSD is in 5,14
    allparts["CLEM"].appearances.append(5)
    allparts["LOOSE-SKINNED DEMON"]=allparts["CLEM"]
    #I don't think we can really have this as a part name
    allparts["WITCHY-POO"].name="GIRL DRESSED AS WITCH"
    #not a real part
    allparts["BOTH"].real=False
    #Narrator appears in this script
    allparts["NARRATOR"].appearances.remove(12)
    #Another typo
    allparts["RICARD"]=allparts["RICHARD"]        
    #not a real part
    allparts["GUESTS"].real=False
    #another typo
    allparts["D"]=allparts["DAWN"]
    #this is the voice of "Demon" in eps19-22
    allparts["VOICE"].real=False
    
    #now save the new versions
    os.rename("allparts.dat","allparts.dat.bak")
    f=open("allparts.dat","wb")
    pickle=cPickle.Pickler(f,-1)
    pickle.dump(allparts)
    pickle.dump(partsbyep)
    pickle.dump(titles)
    f.close()


def first_pass(ph):
    '''opens ph (HTML file) and does some first-pass stuff

    specifically, it extracts the episode title, and works out what
    the cast list should be
    '''
    f=open(ph,"r")
    #look for the title
    for line in f:
        if line.strip()[0:7]=="<title>":
            title=line.strip().split('|')[2].split('<')[0].strip()
            break
    #now go forward to the <hr> element that marks the episode start
    for line in f:
        if line.strip()[0:14].upper()=="<hr width=400>".upper():
            break
    lines=make_lines(f)
    parts=guess_parts(lines)
    return title,parts

def make_lines(f):
    '''make_lines(f) -> array of lines from f

    rather than lines based on \n, this is based on <p> or <br> tags,
    in any case
    '''
    splitre=re.compile("(?:<br>)|(?:<p>)",re.I)
    lines=[]
    midline=False
    for s in f:
        if 'Executive Producers' in s or 'End of episode' in s:
            break
        l=splitre.split(s)
        if len(l)==0:
            continue
        if midline:
            lines.append(part+' '+l[0])
            midline=False
            l=l[1:]
        if len(l)==0:
            continue
        for x in l[:-1]:
            x=x.strip()
            if len(x) > 0:
                lines.append(x)
        #if the last entry is non-zero-length, then it's a partial line
        x=l[-1].strip()
        if len(x) > 0:
            part=x
            midline=True
    return lines

def parse_html(fh,ft):
    '''turns fh (HTML file) into ft (TeX output)

    removes garbage, macros up speech lines, etc.
    '''
    #first, pass over all the initial junk
    for line in fh:
        if line.strip()=="~~~~~~~~~~ Prologue ~~~~~~~~~~":
            break
    #then divide the rest into speech and staging, and output accordingly
    speech=0
    for line in fh:
        if line.strip()=="":
            print >>ft
            speech=0
        elif ': ' in line:
            p=line.split(':')[0]
            if len(p.split())>2:
                continue #handle lines that don't start foo: 
            if p=="Lyrics":
                continue
            #Some other special cases:
            elif p=="Angelus":
                p="Angel"
            elif p=="Chief":
                p="Police Chief"
            elif p=="Mrs. Epps":
                p="Mrs Epps"
            #turn #s into spaces
            p=p.replace('#',' ')
            try:
                print >>ft, "%s:" % texparts[p],
            except KeyError:
                print >>sys.stderr, "Warning, %s uncast(!)" % p
                print >>ft, "\\textbf{%s}:" % p.upper(),
            for l in line.split(':')[1:]:
                print >>ft, l.strip(),
            print >>ft
            speech=1
        elif "~~~" in line:
            pass #ignore these lines
        elif "</PRE>"==line.strip():
            break #end of episode
        else: #normal lines
            if speech:
                print >>ft, line.strip()
            else:
                print >>ft, "\\textit{%s}" % line.strip()

def htmltotex(e):
    #make sure these are blanked each time
    global thiscast
    thiscast={}
    global texparts
    texparts={}
    #we may want to personalise scripts at some point...    
    fh,ft,fc=preamble(e)
    frobcast(e)
    castcommands(fc)
    fc.close()
    print >>ft, """\\title{Episode %d(%d): %s}
\\author{}
\\date{}
\\maketitle
""" % (e,eptoindex(e)+1,titles[eptoindex(e)])
    casttable(ft)
    parse_html(fh,ft)
    print >>ft, "\\end{document}"
    fh.close()
    ft.close()
    
