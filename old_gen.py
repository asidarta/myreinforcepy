#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 19 12:25:25 2017

@author: ae2010
"""

import random
import json
import os

myDirs  = [ 110, 120, 130, 140, 150, 160 ]  # List of direction
mypwd   = os.getcwd() # retrieve code current directory
nfile   = 6
tot     = 24
mul     = (tot/2)/4    # Half of the total trials are lures
delay   = 1000


def getHoles(var):
    # Create a temp copy of the list (not by reference!)
    temp = var[:]
    # Remove hole from the array! You finally get only 4 directions
    h1 = random.choice(temp)
    temp.remove(h1)
    h2 = random.choice(temp)
    temp.remove(h2)
    #print h1, h2, var
    return h1, h2, temp
    # List in python is mutable. Be careful!!


def generate_directions():
    fid = open('%s/exper_design/%s/%s%d.txt'%(mypwd,subj,subj,m), 'aw')  # Write a new file
    fid.write("[\n")
    mylist  = []   # a list: for all trials design
    
    for i in range (1,tot+1):
            
        flag = 0  # if flag = 1, all constraints fulfilled
        # (1) First, create a copy of the list; not by reference!
        copyDirs = myDirs[:]

        # (2) Shift each item with the same random number [-11,11]
        #print "Before " + str(tempDirs)
        myshift = random.choice(range(-11,11))
        copyDirs = [(dd + myshift) for dd in copyDirs]
        #print tempDirs
        
        while not flag:
            # (3) Randomly obtain 2 holes!
            h1, h2, temp = getHoles(copyDirs)
            #print myDirs, tempDirs  
            
            # (4) Check conditions for holes!
            # Repeat the loop as long as conditions aren't met
            delta = h2 - h1
            if (h1 == myDirs[0]) or (h2 == myDirs[0]): flag = 0
            elif (h1 == myDirs[len(myDirs)-1]) or (h2 == myDirs[len(myDirs)-1]): flag = 0
            elif (abs(delta)) <= 10: flag = 0
            else: flag = 1
         
        # (5) Create PROBE direction, the 5th direction.
        random.shuffle(temp) 	# Here, mySet shuffle the 4 anchors first
        if      ( i >= 1  and i <= 1*mul ): probe = temp[0]
        elif ( i > 1*mul  and i <= 2*mul ): probe = temp[1]
        elif ( i > 2*mul  and i <= 3*mul ): probe = temp[2]
        elif ( i > 3*mul  and i <= 4*mul ): probe = temp[3]
        else : probe = random.choice([h1,h2])

        # (6) Put it into list of numbers used for ALL trials
        temp.append(probe)
        mylist.append(temp)            
 
    # (7) After getting the list, you shuffle them
    random.shuffle(mylist)

    # (8) Construct a dict for each trial, then append it to a list. 
    # IMPORTANT: Each time you have to create a new list if not what you
    # add is just the reference to the dict.
    k = 1
    for eachtrial in mylist:
	(dir1,dir2,dir3,dir4,probe) = eachtrial
        myString = "{ \"trial\":%d,\"anchors\":[%d, %d, %d, %d]," \
	           "\"probe\":%d,\"delay\":%d }"%(k,dir1,dir2,dir3,dir4,probe,delay)
	# (9) Save the file in JSON format
    	#print myString
    	if not k == tot: fid.write(myString +",\n")
    	else: fid.write(myString + "\n")
        k+=1
        
        
    # Once design of the whole block is saved, we close the file.
    print "Saving successful for \'%s\' file #%d"%(subj,m)
    fid.write("]")
    fid.close()


# Expecting a string input
subj = raw_input("Enter 3 characters of subj names: ") 
#print subj

if not os.path.exists(mypwd+'/exper_design/'+subj):
    os.makedirs(mypwd+'/exper_design/'+subj)

    #generate_directions()
    # Now generate 12 files per subject 
    for m in range(0, nfile+1): generate_directions()  

else:
    print('## Duplicate found! Are you sure you want to overwrite?')
    pass

