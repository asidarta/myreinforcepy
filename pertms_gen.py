#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on April 1, 2018. This is a modified version of the original code to better suit TMS 46v study!
Here, we have 2 lags to be tested. Each block consists of 24 trials, 12 lures + 6 lag1 + 6 lag2.
There will be 4 blocks PRE and POST TMS manipulation. Hence, each lag has 4 x 6 = 24 data points per session.

@author: ae2010
"""

import random
import json
import os

myDirs  = [ 110, 120, 130, 140, 150 ]  # List of direction
mypwd   = os.getcwd() # retrieve code current directory
nfile   = 8
tot     = 24
mul     = (tot/2)/2    # Half of the total trials are lures, we have 2 lags only!
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
    mylist = []   # a list: for all trials design
    
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
            
            # (4) Check conditions for holes! Use delta to compute the difference of 2 holes.
            # Repeat the loop as long as conditions aren't met.
            delta = h2 - h1
            if (h1 == myDirs[0]) or (h2 == myDirs[0]): flag = 0       # if the hole is from the first extreme end
            elif (h1 == myDirs[-1]) or (h2 == myDirs[-1]): flag = 0   # Note how I get the LAST index!
            elif (abs(delta)) <= 10: flag = 0         # or if by mistake the holes are adjacent with each other...
            else: flag = 1
                
            #### To modify: why don't we feed the list of directions with both ends already removed!
            #### For easy debugging, you should add the shift later, after the selection of anchors + hole.
         
        # (5) Create PROBE direction, the 4th direction.
        random.shuffle(temp) 	# Here, mySet shuffle the 2 anchors first. We only need to test lag1 and lag2!
        if      ( i >= 1  and i <= 1*mul ): probe = temp[1]
        elif ( i > 1*mul  and i <= 2*mul ): probe = temp[2]
        else : probe = random.choice([h1,h2])

        # (6) Put it into list of numbers used for ALL trials
        temp.append(probe)
        mylist.append(temp)            
 
    # (7) After getting the list, you shuffle them
    random.shuffle(mylist)

    # (8) Construct a dict for each trial, then append it to a list. 
    # IMPORTANT: Each time you have to create a new list if not what you
    # add is just a reference to the dict. Each has 3 anchor dirs, 1 probe.
    k = 1
    for eachtrial in mylist:
	(dir1,dir2,dir3,probe) = eachtrial
        myString = "{ \"trial\":%d,\"anchors\":[%d, %d, %d]," \
	           "\"probe\":%d,\"delay\":%d }"%(k,dir1,dir2,dir3,probe,delay)
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
    os.makedirs(mypwd+'/exper_design/'+subj)   # This is to create a FOLDER.

    #generate_directions()
    # Now generate 12 files per subject 
    for m in range(0, nfile+1): generate_directions()  

else:
    print('## Duplicate found! Are you sure you want to overwrite?')
    pass

