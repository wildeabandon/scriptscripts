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
    texpath="%s/ep%02d.tex" % (outdir,e)
    castpath="%s/ep%02d_cast.tex" % (outdir,e)
    htmlpath="%s/buffy-6%02d.htm" % (datadir,e)
    r=open(htmlpath,"r")
    try: #make sure we don't over-write anything
        w=open(texpath,"r")
        print >>sys.stderr, texpath, "already exists, giving up"
        c=open(castpath,"r")
        print >>sys.stderr, castpath, "already exists, giving up"
        raise RuntimeError, "Will not over-write above files"
    except IOError:
        pass
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

def castcommands(f,d):
    '''output a set of LaTeX macros for typesetting the foo: lines'''
    for k in d.iterkeys():
        name=d[k][0]
        name=name.upper().replace('(NS','') #block caps, trim "(NS)"
        texname=d[k][2]
        print >>f, "\\newcommand{\\%s}{\\textbf{%s}}" % (texname,name)

def casttable(f,d):
    '''print a LaTeX-ed cast list'''
    print >>f, """\\subsection*{Cast List}
\\begin{tabular}{ll}\\\\"""
    keys=d.keys()
    keys.sort()
    for k in keys:
        if d[k][1]!="Nobody":
            print >>f, "%s & %s\\\\" % (d[k][0],d[k][1])
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
                if x.name.lower().capitalize() not in names:
                    print >>f, "%s:" % (x.name.lower().capitalize())
                    names.append(x.name.lower().capitalize())
        print >>f
    f.close()

def load_cast():
    allparts,partsbyep,titles=get_partarrays()
    cast={}
    byperson={}
    f=open("casting.txt","r")
    #discard the first three lines
    discard=f.readline(); discard=f.readline(); discard=f.readline()
    multiples={}
    for line in f:
        line=line.strip()
        if len(line)==0:
            continue
        elif line[0]=='*':
            break
        else:
            a,b=line.split(':')
            a=a.split(')')[1].strip()
            b=b.strip()
            multiples[a.upper()]=[a,b]
    episode=1
    castthisep={}
    for line in f:
        line=line.strip()
        if len(line)==0:
            continue
        elif line[0]=='*':
            #deal with multiple-characters not re-cast for this ep.
            c=castthisep.keys()
            parts=partsbyep[episode-1]
            for p in parts:
                pnu=allparts[p].name.upper()
                if pnu not in c and allparts[p].real==True:
                    who=multiples[pnu]
                    castthisep[pnu]=who
                    if who[1] != '':
                        if who[1] in byperson:
                            try:
                                byperson[who[1]][episode].append(\
                                who[0])
                            except KeyError:
                                byperson[who[1]][episode]=[who[0]]
                        else:
                            byperson[who[1]]={episode:[who[0]]}
            cast[episode]=castthisep
            episode+=1
            castthisep={}
        else: #actually a casting :)
            line=line.split(':')
            a=line[0]; b=line[1]
            b=b.strip()
            if len(line)==3: #over-ride how the name should appear
                c=line[2]
                c=c.strip()
            else:
                c=a
            castthisep[a.upper()]=[c,b]
            if b != '':
                if b in byperson:
                    if episode in byperson[b]:
                        byperson[b][episode].append(c)
                    else:
                        byperson[b][episode]=[c]
                else:
                    byperson[b]={episode:[c]}
    f.close()
    del byperson['Nobody']
    return cast,byperson

def writecast():
    'write out a by-episode and by-person cast list'
    cast,byperson=load_cast()
    allparts,partsbyep,titles=get_partarrays()

    f=open("casting_byepisode.txt","w")
    for ep in range(1,23):
        print >>f, "*%d: %s*" % (ep,titles[ep-1])
        showep(ep,f)
        print >>f
    f.close()

    f=open("casting_byperson.txt","w")
    people=byperson.keys()
    people.sort()
    for who in people:
        print >>f, "* %s *" % who
        showperson(who,f)
        print >>f
    f.close()

def showperson(who,f=sys.stdout):
    cast,byperson=load_cast()
    p=byperson[who]
    for ep in range(1,23):
        print >>f, "%d:" % ep,
        if ep in p:
            for x in range(len(p[ep])-1):
                print >>f, "%s," % (p[ep][x]),
            print >>f, p[ep][-1]
        else:
            print >>f, "episode off"

def showep(e,f=sys.stdout):
    cast,byperson=load_cast()
    parts=cast[e].keys()
    parts.sort()
    #show cast parts first
    for p in parts:
        a=cast[e][p][0] #part name
        b=cast[e][p][1] #person
        if b!='' and b!='Nobody':
            print >>f, "%s: %s" % (a,b)
    #then the uncast
    for p in parts:
        a=cast[e][p][0] #part name
        b=cast[e][p][1] #person
        if b=='':
            print >>f, a, "uncast"
    #then who hasn't been used?
    slack=[]
    for p in byperson:
        if e not in byperson[p]:
            slack.append("%s (%d)" %(p,len(byperson[p].keys())))
    if len(slack)>0:
        print >>f, "episode off:",
        for x in range(len(slack)-1):
            print >>f, "%s," % slack[x],
        print >>f, slack[-1]
                        

def unused():
    cast,byperson=load_cast()
    people=byperson.keys()
    people.sort()
    for p in people:
        if len(byperson[p].keys())<22:
            print "%s is in %s episodes" % (p,len(byperson[p].keys()))
    
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

def second_pass(fh,ft,epcast,allparts):
    '''converts the html lines in fh into TeX in ft'''
    #italics regexp (?i)==make case-insensitive
    itreg=r'(?i)<i>([^<]*)</i>'
    #match open or close blockquote/code tags, which we discard
    bqreg=r'(?i)(</?blockquote>)|(</?code>)'
    #go forward to the <hr> element that marks the episode start
    for line in fh:
        if line.strip()[0:14].upper()=="<hr width=400>".upper():
            break
    lines=make_lines(fh)
    for l in lines:
        if '<b>' in l or '<B>' in l:
            print >>ft, "\\scene"
        elif '<hr' in l or '<HR' in l:
            pass
        else:
            l=re.sub(itreg,r"\text{\1}",l) #anything in <i> gets italiced
            l=re.sub(bqreg,"",l) #discard blockquote/code tags
            if '<' in l or '>' in l:
                raise ValueError, "undealt with tags in line: %s" % l
            #Is this line a spoken line?
            ls=l.split(':')
            if len(ls)>1:
                part=' '.join(ls[0].split())
                rest=': '.join(ls[1:]) #re-assemble rest of line
            if len(ls)>1 and part.upper()==part: #spoken part
                if part in allparts and allparts[part] in epcast:
                    print >>ft, "\\{%s}: %s" % (epcast[allparts[part]][2],rest)
                else:
                    print >>ft, "\\textbf{%s}: %s" %(part,rest)
            else: #not-spoken part
                print >>ft, "\\ti{%s}" % l
                
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

def texcast(d):
    '''texcast(d): returns d with LaTeX-suitable command names

    each value in the dictionary d should be a 2-element array.
    A third element is added, which is a LaTeX-suitable command name
    '''
    #replace numbers with letters
    tt=string.maketrans('1234567890','abcdefghij')
    for k in d.iterkeys():
        if len(d[k])==3: #already done
            continue
        name=d[k][0]
        tex=name.upper()
        if tex.isalpha()==False:
            #translate numbers to letters, and trim .-/()#' and space characters
            tex=tex.translate(tt,' ./-()#\'')
            if tex.isalpha()==False:
                raise ValueError, tex
        d[k].append(tex)
    return d

def htmltotex(e):
    cast,byperson=load_cast()
    allparts,partsbyep,titles=get_partarrays()
    fh,ft,fc=preamble(e)
    cast[e]=texcast(cast[e])
    castcommands(fc,cast[e])
    fc.close()
    print >>ft, """\\title{Episode %d: %s}
\\author{}
\\date{}
\\maketitle
""" % (e,titles[e+1])
    casttable(ft,cast[e])
    second_pass(fh,ft,cast[e],allparts)
    print >>ft, "\\end{document}"
    fh.close()
    ft.close()
    
