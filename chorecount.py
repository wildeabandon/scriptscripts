#!/usr/bin/env python

f=open("chores.txt","r")

c={}

for line in f:
    if line.strip():
        b=line.split(':')
        for p in b[1].split(','):
            p=p.strip()
            try:
                c[p]+=1
            except KeyError:
                c[p]=1

for k,v in c.items():
    print k,v
