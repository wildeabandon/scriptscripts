#!/usr/bin/env python
#Code to (hopefully) un-HTML and TeX up Buffy scripts

import os,string,sys

#beware of namespace clashes doing this
from casting import *

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
    
