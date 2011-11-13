#!/usr/bin/env python

import sys
from parrot import basedir,statedir

c={}

f=open(statedir+"/casting.txt","r")
for line in f:
    line=line.strip()
    if len(line)>0 and line[0]!="*":
        l=line.split(':')
        if len(l) > 1:
            p=l[1].strip()
            if p!='' and p !="Nobody" and p not in c:
                c[p]=0
f.close

f=open(basedir+"/chores.txt","r")

for line in f:
    if line.strip():
        b=line.split(':')
        for p in b[1].split(','):
            p=p.strip()
            if p!='':
                try:
                    c[p]+=1
                except KeyError:
                    c[p]=1

for k,v in c.items():
    print k,v
