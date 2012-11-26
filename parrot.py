#!/usr/bin/env python
#Code to (hopefully) un-HTML and TeX up Buffy scripts

import os,string,sys,os.path,re,cPickle,glob, codecs

#edit these as appropriate
basedir=os.path.expanduser("~/tex/scripts/buffys7")
statedir=basedir+"/state"
datadir=basedir+"/html_buffyology"
outdir=basedir+"/latex"
defenc="iso-8859-1"

htmlpaths=[]

def preamble(e,force=False):
    '''preamble(e,force=False)->get ready to start an episode

    \inputs preamble.tex in the appropriate .tex file,
    and opens that for writing, and the html for reading,
    along with a file to write cast-related LaTeX
    return is (html,tex,cast)
    if force is True, over-write existing files
    '''
    global htmlpaths

    if htmlpaths==[]:
        htmlpaths=ord_list()

    texpath="%s/ep%02d.tex" % (outdir,e)
    castpath="%s/ep%02d_cast.tex" % (outdir,e)
    htmlpath=htmlpaths[e-1]
    r=codecs.open(htmlpath,"r",defenc)
    if force==False: 
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

def castcommands(f,d):
    '''output a set of LaTeX macros for typesetting the foo: lines'''
    done=[]
    for k in d.iterkeys():
        name=d[k][0]
        name=name.upper().replace('(NS)','') #block caps, trim "(NS)"
        texname=d[k][2]
        if texname not in done: #avoid duplicates
            print >>f, "\\newcommand{\\%s}{\\textbf{%s}}" % (texname,name)
            done.append(texname)

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
    paths=[]
    for x in range(1,23):
        pattern="%s/%03d-7-%02d-*.html" % (datadir,x+122,x)
        g=glob.glob(pattern)
        if len(g)!=1:
            sys.exit("Pattern %s matched %d paths" % (pattern,len(g)))
        paths.append(g[0])
    return paths

#complications: spurious part (I--), and some parts end up in <p> tags
#e.g. 911 operator in "the body" (actually, that may be the only one)
#grep -E '<p>[[:upper:] 01-9]+</p>' ~/tex/scripts/buffys5/html_buffyology/* | less
#(?:) is a non-capturing grouping operator
def guess_parts(f):
    '''guesses what the parts in f are'''
    #parts are in <h4> tags
    partre=re.compile(r'<h4>([^<]+)</h4>',re.I)
    parts=[]
    for line in f:
        m=partre.search(line)
        if m:
            part=m.group(1)
            if part not in parts and part != "I--":
                parts.append(part)
        elif "<p>911 OPERATOR</p>" in line and "911 OPERATOR" not in parts:
            parts.append("911 OPERATOR")
    return parts

class Part:
    def __init__(self,name,episode,multiple=None):
        self.name=name
        if self.name[-3:]==" VO" or "VOICEOVER" in self.name:
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
        if self.checked==True:
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
        f=open(statedir+"/allparts.dat","rb")
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
    f=open(statedir+"/allparts.dat","wb")
    pickle=cPickle.Pickler(f,-1)
    pickle.dump(allparts)
    pickle.dump(partsbyep)
    pickle.dump(titles)
    f.close()
    return allparts,partsbyep,titles


def get_castlist():
    '''write out a single list of the entire cast'''
    if os.path.exists(statedir+"/casting.txt") \
            or os.path.exists(statedir+"/verbosecasting.txt"):
        print >>sys.stderr, "Casting files exist; will not over-write"
        return
    allparts,partsbyep,titles=get_partarrays()
    byapp=[]
    parts=allparts.keys()
    for p in parts:
        x=allparts[p]
        n=len(x.appearances)
        if x.real==True and n>1 and x.multiple==False:
            byapp.append( EpCount( (n,x.name.lower().capitalize()) ) )
    byapp.sort(reverse=True)
    f=open(statedir+"/casting.txt","w")
    g=open(statedir+"/verbosecasting.txt","w")
    print >>f, "Buffy Season 7 - Cast List\n\nRecurring parts:"
    print >>g, "Buffy Season 7 - Cast List\n\n"
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
        print >>g, "* %s *" % (titles[ep-1])
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
            if x.real==True:
                print >>g, x.name.lower().capitalize()
        print >>f
        print >>g
    print >>f, "* End of casting *" #load_cast needs this
    f.close()
    g.close()

def load_cast():
    allparts,partsbyep,titles=get_partarrays()
    cast={}
    byperson={}
    f=open(statedir+"/casting.txt","r")
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

    f=open(basedir+"/casting_byepisode.txt","w")
    for ep in range(1,23):
        print >>f, "*%d: %s*" % (ep,titles[ep-1])
        showep(ep,f,showslack=False)
        print >>f
    f.close()

    f=open(basedir+"/casting_byperson.txt","w")
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

def showep(e,f=sys.stdout,showslack=True):
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
    if len(slack)>0 and showslack:
        print >>f, "episode off:",
        for x in range(len(slack)-1):
            print >>f, "%s," % slack[x],
        print >>f, slack[-1]

def writecastchanges():
    'write out a list of all cast changes'
    allparts,partsbyep,titles=get_partarrays()
    f=open(basedir+"/castchanges.txt","w")

    for ep in range(1,23):
        print >>f, "*%d: %s*" % (ep,titles[ep-1])
        castchanges(ep,f)
    f.close()
                        
def castchanges(e,f=sys.stdout):
    '''castchanges(e) -> casting changes for episode e

    This extracts the cast list for e as per casting.txt and then
    parses the script .tex file for the cast list in the script,
    then outputting a summary of the changes.
    '''
    #first, the "old" cast.
    cast,byperson=load_cast()
    ops=cast[e].keys()
    ops.sort()
    opnames=set()
    opcast={}
    for p in ops:
        a=cast[e][p][0] #name
        b=cast[e][p][1] #person
        if b!="Nobody": #excludes some non-parts
            opnames.add(a)
            opcast[a]=b
    #now the new cast
    npnames,npcast=readtexcast("%s/ep%02d.tex" % (outdir,e))

    newonly=npnames-opnames
    oldonly=opnames-npnames
    both=set.intersection(npnames,opnames)

    if len(newonly) > 0:
        print >>f, "New parts:"
        for x in newonly:
            print >>f, "%s: %s" % (x,npcast[x])
        print >>f

    if len(oldonly) > 0:
        print >>f, "Lost parts:"
        for x in oldonly:
            print >>f, "%s: %s" % (x,opcast[x])
        print >>f

    #lazy, 2-pass approach
    changes=False
    for p in both:
        if opcast[p] != npcast[p]:
            changes=True
            break
    if changes:
        print >>f, "Casting changes:"
        for p in both:
            if opcast[p] != npcast[p]:
                print >>f, "%s: %s -> %s" % (p,opcast[p],npcast[p])
        print >>f 

    if changes==False and len(newonly)==0 and len(oldonly)==0:
        print >>f, "No changes\n"

def readtexcast(path):
    '''readtexcast(path) -> returns names (set) and cast (dict)

    parses the cast-list table at the beginning of path, and creates
    a set of the part-names and a dictionary of who is playing what.
    '''
    f=open(path,"r")
    names=set()
    cast={}
    for line in f:
        if line.strip()==r"\begin{tabular}{ll}\\":
            break
    for line in f:
        if line.strip()==r"\end{tabular}":
            break
        pname,pwho=line.split('&')
        pname=pname.strip()
        pwho=pwho.strip()[:-2] #remove trailing backslashes
        names.add(pname)
        cast[pname]=pwho
    f.close()
    return names,cast

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
    os.rename(basedir+"/allparts.dat",basedir+"/allparts.dat.bak")
    f=open(basedir+"/allparts.dat","wb")
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
    titlere=re.compile(r'<h1>([^<]+)</h1>',re.I)
    f=open(ph,"r")
    #look for the title
    for line in f:
        tm=titlere.search(line)
        if tm:
            title=tm.group(1)
            break
    parts=guess_parts(f)
    f.close()
    return title,parts

def second_pass(fh,ft,epcast,pbe,allparts):
    '''converts the html lines in fh into TeX in ft

    We assume the following things about tags:
    <h1> = episode title
    <h2> = Act break (discard)
    <h3> = scene title (also marks scene break)
    <h4> = part name => beginning of line (excepting I--, which is a line)
    <h5> = stage directions about this line
    <h6> = "cut to", "fade to black", etc, which we can discard
    <i> = stage direction (usually within a line)
    <blockquote> = a line (follow these with a blank line, to make a paragraph)
    <p> = stage direction ; descriptions (except 911 OPERATOR, which is a part)
'''
    #set of characters that are OK
    okchars=string.ascii_letters+string.digits+string.whitespace+string.punctuation
    #italics regexp (?i)==make case-insensitive
    itreg=r'(?i)<i>([^<]*)</i>'
    #scene titles are in <h3> tags
    streg=r'(?i)<h3>(.*)</h3>'
    #match open or close blockquote/code/ul/li tags, which we discard
    #Also unpaired <i> tags, and the very rare </P>
    bqreg=r'(?i)(</?blockquote>)|(</?code>)|(</?ul>)|(</?li>)|(</?i>)|(</p>)'
    #""regex, so we can make them tex-quotes ``''
    qreg=r'"([^"]*)"'
    #Now build a list of find,replace pairs for the stage directions
    #so we can convert them to their upper-case versions
    relist=[]
    inrelist=[]
    #Make sure we include all the parts in an episode - those we knew about,
    #and any we added in casting.txt
    names=[]
    for p in pbe:
        if allparts[p].name not in names:
            names.append(allparts[p].name)
    for n in epcast.keys():
        if n not in names:
            names.append(n)
#    for p in pbe:
#        name=allparts[p].name
    for name in names:
        #Two regexps per part - one that matches "part ", and one that
        #matches more complex things
        if name in epcast and name not in inrelist:
            #(?!foo) is a negative lookahead assertion
            #The (?= )?(?!#) construction is almost certainly a bug...
            rf=r'(?i)(^| )%s(\'s|\.|,|\))(?= )?(?!#)' % name
            rfn=r'(?i)(^| )%s (?!#)' % name
            rr=r'\1\%s\2~' % epcast[name][2]
            rrn=r'\1\%s ~' % epcast[name][2]

#            rf=r'(?i)(^| )%s(\'s |\. | |, |\.$|\))(?!#)' % name
#            rfn=r'(?i)(^| )%s (?!#)' % name
#            rr=r'\1\%s\2~' % epcast[name][2]
#            rrn=r'\1%s ~' % epcast[name][2]
            inrelist.append(name)
            relist.append( (rf,rr) )
            relist.append( (rfn,rrn) )
    #every episode begins with a Prologue
    for line in fh:
        if line.strip()=="<h2>Prologue</h2>":
            break
    lines=make_lines(fh)
    prev=""
    for l in lines:
        orig=l #before we start mangling it
        l=l.replace("$","\$")
        l=l.replace(u'\xa3',"\\pounds")
        l=l.replace(u'\xc8',"\\'{e}")# typo in the script, I think
        l=l.replace(u'\xe9',"\\'{e}")
        l=l.replace(u'\xe7',"\\c{c}")
        l=l.replace(u'\xf1',"\\~{n}")
        l=l.replace(u'\xbe ',"\\ae~")
        l=l.replace(u'\xbe',"\\ae")
        l=l.replace(u'\xe0',"\\`{a}")
        l=l.replace("&amp;","\\&")
        l=re.sub(r'([^- ])- ',r'\1-',l) #foo- bar -> foo-bar
        if "<h2>" in l or "<h6>" in l:
            pass
        elif "<h3>" in l: #scene titles
            print >>ft, "\n\\scene\n"
            l=re.sub(streg,r"\\textit{\1}",l)
            print >>ft, l.replace("-- ","---"), "\n"
        elif "<h5>" in l: #stage direction in a line
            l=l.replace('#','')
            print >>ft, "\\ti{%s}" % (l[4:-5]),
        #start of line
        elif ("<h4>" in l and l!="<h4>I--</h4>") or l=="<p>911 OPERATOR</p>": 
            if "<h4>" in l:
                part=l[4:-5] #trim <h4> and </h4>
            else:
                part="911 OPERATOR"
            if part in allparts and allparts[part].name in epcast:
                print >>ft, "\\%s:" % (epcast[allparts[part].name][2]),
            else:
                print >>ft, "\\textbf{%s}:" % (part),
        elif "<blockquote>" in l or l=="<h4>I--</h4>" or \
                ("<p>" in l and prev[0]=='('): #actually a line!
            if l=="<h4>I--</h4>":
                print >>ft, "I--\n"
                continue
            elif l[:3]=="<p>":
                l=l[3:-4]
            else:
                l=l[12:-13] #trim the tags
            l=re.sub(itreg,r"\\ti{\1}",l)
            l=l.replace("-- ","---")
            l=re.sub(qreg,r"``\1''",l) #"" -> ``''
            l=l.replace('...',r'$\ldots$') #... -> tex ldots
            l=l.replace('#','')
            if '<' in l or '>' in l:
                raise ValueError, "%s: undealt with tags in line: '%s'"\
                    % (fh.name,l)
            for ch in l:
                if ch not in okchars:
                    print >>sys.stderr, "%s: bad char in %s" % (fh.name,l)
                    break #only 1 warning per line!
            print >>ft, l, "\n"
        elif "<p>" in l or "<i>" in l:
            l=l[3:-4] #trim tags
            l=l.replace('_','\\_')
            for rf,rr in relist:
                #try and spot all the cast in stage directions
                #and replace with the block-bold command
                try:
                    l=re.sub(rf,rr,l)
                except:
                    print l, rf, rr
                    raise
            for ch in l:
                if ch not in okchars:
                    print >>sys.stderr, "%s: bad char in %s" % (fh.name,l)
                    break #only 1 warning per line!
            print >>ft, "\\ti{%s}\n" % l
        #stage-direction in line, but not inside <i>
        elif "<" not in l and "<h4>" in prev and l[0]=='(': 
            print >>ft, "\\ti{%s}" % l,
        else:
            raise ValueError, "%s: unknown line type: '%s'" % (fh.name,l)
        prev=orig
        
def make_lines(f):
    '''make_lines(f) -> array of lines from f

    rather than lines based on \n, this is based on text enclosed in
    <hx>, <p>, <i> or <blockquote>. Also accepts lines teminated with <br />.
    Inside a particular tag, other close-tags are ignored - so if you have
    <p>foo<i>(bar)</i>baz</p>, that's one line
    '''
    startre=re.compile(r"^(<h[1-9]>)|(<p>)|(<i>)|(<blockquote>)|",re.I)
    lines=[]
    midline=""
    thisend="" #end tag to look for
    for s in f:
        s=s.strip()
        if s=="<h6>END</h6>":
            break
        if midline=="":
            l=startre.search(s)
            if l.group()!="":
                thisend=l.group().replace("<","</")
            else:
                if s.endswith("<br />"):
                    lines.append(s[:-6]) #trim the <br />
                    continue #done with this physical and logical line
                else:
                    raise ValueError, "unstarted line: %s" % s
        else:
            midline+=" " #put a space between concatenated lines
        s=midline+s
        if s.endswith(thisend):
            lines.append(s)
            midline=""
        elif s.endswith(thisend+"<br />"):
            lines.append(s[:-6]) #trim the <br />
            midline=""
        elif thisend in s:
            raise ValueError, "invalid line: %s (%s)" % (s,thisend)
        else:
            midline=s
    return lines

#testing function - print a line-count for each episode
def testlines():
 for x in ord_list():
     f=open(x,"r")
     for line in f:
         if line.strip()=="<h2>Prologue</h2>":
             break
     l=make_lines(f)
     g=open("/tmp/testout.txt","w")
     for line in l:
         print >>g, line
     g.close()
     return
     print x, len(l)
     f.close()

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

def htmltotex(e,force=False):
    cast,byperson=load_cast()
    allparts,partsbyep,titles=get_partarrays()
    fh,ft,fc=preamble(e,force)
    cast[e]=texcast(cast[e])
    castcommands(fc,cast[e])
    fc.close()
    print >>ft, """\\title{Episode %d: %s}
\\author{}
\\date{}
\\maketitle
""" % (e,titles[e-1])
    casttable(ft,cast[e])
    second_pass(fh,ft,cast[e],partsbyep[e-1],allparts)
    print >>ft, "\\end{document}"
    fh.close()
    ft.close()
    
