#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 20:24:50 2017 @author: ae2010
This code is used for somatosensory working memory test. It has the same principle 
as the old code created in Tcl for the old suzuki machine.
"""

import robot.dummy as ananda
import os.path
import time
import json
import math

from Tkinter import *	# Importing the Tkinter library

# Declare several global variables
dc= {}                # dictionary for important param
stages  = 0           # to enter clickStart soubroutine step-by-step
answerflag = 0        # Flag=1 means subject has responded
targetdist = 0.15     # move 15 cm from the center position
targethold = 0.9      # 900 msec delay at the target point
movetime = 0.9	      # 900 msec default movement speed to a target
mypwd   = os.getcwd() # retrieve code current directory


####### Create various functions using 'def' keyword
# Subroutine to EXIT the program and stop everything.
def quit():
    root.destroy()
    global keep_going
    keep_going = False
    ananda.unload()  # Close/kill robot process


# Play specific audio
def playAudio():
    print("---Audio play initiated...")
    #p = vlc.MediaPlayer(mypwd + "/data/beep.mp3")
    #p.play()
    time.sleep(2)
    print("---Audio play finished...\n")


# This function obtains+saves a new OR loads existing center position
def getCenter():
    print("---Getting center position. Remain still!")
    # Required to have subject name!
    if (os.path.isfile(dc['logpath']+subjid.get()+"_center.txt")):
        #txt = open(mypwd + "/data/and_center.txt", "r").readlines()
        center = [[float(v) for v in txt.split(",")] for txt in open(
                      dc['logpath']+subjid.get()+"_center.txt", "r").readlines()]
        #print(center)
        print("Loading existing coordinate: %f, %f"%(center[0][0],center[0][1]))
        dc['center.pos'] = (center[0][0],center[0][1])       
    else:
        print("This is a new subject. Center position saved.")
        dc['center.pos'] = ananda.rshm('x'),ananda.rshm('y')
        txt_file = open(dc['logpath']+subjid.get()+"_center.txt", "w")
        txt_file.write("%f,%f"%dc['center.pos'])
        txt_file.close()


# Initiate movement to the center (start) coordinate
def goToCenter(speed):
    # Ensure this is a null field first (because we will be updating the position)
    ananda.controller(0)
    print("  Now moving to center: %f,%f"%dc['center.pos'])
    # Send command to move to cx,cy
    ananda.move_stay(dc['center.pos'][0],dc['center.pos'][1],speed)
    ananda.status = ananda.move_is_done()
    while not ananda.status:   # check if movement is done
        ananda.status = ananda.move_is_done()
        #time.sleep(0.07)
    print("  Movement completed!")


# Start main program, taking "Enter" button as input-event
def clickStart(event):
    global stages
    if (stages == 0):
        dc['logfileID'] = subjid.get()+filenum.get()
        dc['logpath'] = mypwd+"/data/"+subjid.get()+"_data/"

        if not(subjid.get()) or not(filenum.get()):
             print("##Error## Subject ID and/or file numbers are empty!")
        # Added check to ensure existing logfile isn't overwritten
        elif (os.path.exists(dc['logpath']+"Som_"+dc['logfileID']+".txt")):
             print "Duplicate: "+dc['logpath']+"Som_"+dc['logfileID']+".txt" 
        else:
             print "---Loading for block %s, subject %s..." %(filenum.get(),subjid.get())
             filepath = mypwd+"/exper_design/"+dc['logfileID']+".txt"             
             #print filepath
             stages = read_design_file(filepath)   # Next stage depends if file loaded successfully
             print "Press <Enter> or Quit-button to continue!\n"

    elif (stages == 1):
        e1.config(state='disabled')
        e2.config(state='disabled')
        getCenter()
        goToCenter(3)
        print "Press <Enter> or Quit-button to continue!\n"
        stages = 2

    elif (stages == 2):
        if (int(filenum.get()) == 0):
            practiceLoop() # This is only for filenum = 0, familiarization trials!      	
        else:
            mainLoop()     # Once set, we're ready for the main loop (actual test!)
    else:
        print("Current clickStart() stage = %d"%stages)


# Based on subj_id & block number, read experiment design file!
def read_design_file(mpath):
    if os.path.exists(mpath):
        with open(mpath,'r') as f:
            dc['mydesign'] = json.load(f)
        print("Design file loaded! Parsing the data...")
        return 1
    else:
        print mpath
        print("##Error## Experiment design file not found. Have you created one?")
        return 0

# Wait for subject response. You can either click the GUI button or keyboard arrow.
def doAnswer(index):
    start_time = time.time()  # To count reaction time
    global answerflag
    print("Waiting for subject's response")
    while (not answerflag):
        root.update_idletasks()
        root.update()
        time.sleep(0.3)
    RT = 1000*(time.time() - start_time)  # RT in m-sec
    RT = "%d"%RT
    print("---Trial-"+str(index)+"   ANSWER:"+str(dc['answer'])+"   RT:"+RT)
    answerflag = 0
    return(RT)

def clickYes(event):
    global answerflag
    print "Left key pressed to answer YES!"
    dc['answer']=1
    answerflag = 1

def clickNo(event):
    global answerflag
    print "Right key pressed to answer NO!"
    dc['answer']=0
    answerflag = 1


# Convert angle direction to coordinates w.r.t center position
def angle_pos(theta):
    theta_rad = theta*math.pi/180 # convert to radian
    targetX = targetdist * math.cos(theta_rad) + dc['center.pos'][0]
    targetY = targetdist * math.sin(theta_rad) + dc['center.pos'][1]
    print("  Moving to %f, %f"%(targetX,targetY))
    ananda.move_stay(targetX, targetY, movetime)
    ananda.status = ananda.move_is_done()
    while not ananda.status:   # check if movement is done
        ananda.status = ananda.move_is_done()
        #time.sleep(0.07)
    print("  Movement completed!")


# Moving to target: It takes a list of anchor/probe direction as input
def to_target(directions):
    if (type(directions)==list):
        # If this is a list, it means a set of anchors
        for direction in directions:
            print("Anchor direction: " + str(direction))
            angle_pos(direction)
            time.sleep(targethold)
            goToCenter(1)  # Go back to centre!
            time.sleep(targethold)
            dc['logAnswer'] = dc['logAnswer'] + " " + str(direction)
    else:
        # Else, it means just a test direction or probe!
        print("Probe direction: " + str(directions))
        angle_pos(directions)
        time.sleep(targethold)
        goToCenter(1)  # Go back to centre!
        dc['logAnswer'] = dc['logAnswer'] + " " + str(directions)


# Run only for the first time: familiarization trials with instruction.
def practiceLoop():
    print("Entering practice-Loop now.........")
    #playAudio()
    #playAudio()
    #playAudio()


# The main code once 'Start' or <Enter> key is pressed
def mainLoop():
    print("Entering main-Loop now.........")
    #playAudio()
    #print(ananda.status())
    for xxx in dc['mydesign']:
        index  = xxx['trial']
        anchors= xxx['anchors']
        probe  = xxx['probe']
        delay  = xxx['delay']
        print("\nNew Round- " + str(index))
        time.sleep(targethold)
        dc['logAnswer'] = str(index) + " "   # string to be saved later!
        to_target(anchors)
        print("  Waiting for " + str(delay) + "msec")
        time.sleep(delay/1000)
        to_target(probe)
        RT = doAnswer(index)
        dc['logAnswer']=dc['logAnswer']+ "  ANSWER:"+ str(dc['answer'])
        dc['logAnswer']=dc['logAnswer']+ "  RT:"    + RT
        dc['logAnswer']=dc['logAnswer']+ "  DELAY:" + str(delay) + "\n"
        #print(dc['logAnswer'])
        saveLog()   # Call save function
    print("\n#### NOTE = Test has ended!!")


# Function save logfile and mkdir if needed
def saveLog():
    print("---Saving trial log.....")   
    if not os.path.exists(dc['logpath']):
	os.makedirs(dc['logpath'])
    with open(dc['logpath']+"Som_"+dc['logfileID']+".txt",'aw') as log_file:
        log_file.write(dc['logAnswer'])  # Save every trial as text line


# Some parameters that specify how we draw things onto our window
robot_scale = 700
cursor_size = 10
target_size = 5

root = Tk()		# This creates an empty background window
root.geometry('%dx%d+%d+%d' % (370, 150, 500, 200))   # Nice geometry setting!!
root.title("Somatic Working Memory Test")
root.protocol("WM_DELETE_WINDOW", quit)

subjid  = StringVar()
filenum = StringVar()
mymsg   = StringVar()

def mainGUI():
    # Create two different frames on the root -----
    topFrame = Frame(root, width=400, height=100)
    topFrame.pack(side=TOP, expand = 1)
    #frame.bind('<Left>', leftKey)
    bottomFrame = Frame(root, bg="white", width=400, height=100)
    bottomFrame.pack(side=BOTTOM, expand = 1)
    
    # Important: This maintains frame size, no shrinking
    topFrame.pack_propagate(False)
    bottomFrame.pack_propagate(False)
    
    # Make Entry widgets global so that we can configure from outside    
    global e1, e2
    
    # Entry widget for 1st row --------------
    Label(topFrame, text="Subject ID: ").grid(row=0, sticky=E)
    e1 = Entry(topFrame, width = 6, bd =1, textvariable = subjid)
    e1.grid(row=0, column=1)
    e1.insert(END, "aes")
    Label(topFrame, text="File Number: ").grid(row=0, column=3, padx = (30,5))
    e2 = Entry(topFrame, width = 3, bd =1, textvariable = filenum)
    e2.grid(row=0, column=4, pady=5)
    e2.insert(END, "1")

    # Entry widget for 2nd row --------------
    msg = Entry(topFrame, width = 50, bd=0, textvariable=mymsg)
    msg.grid(row=2, columnspan=10, pady=10)
    #msg.config(highlightbackground="red")
    mymsg.set("Enter subject ID, file #, then press <ENTER> key!")

    # Create buttons ---------------
    myButton1 = Button(bottomFrame, text="Yes!", command=clickYes)
    myButton1.grid(row=0, padx = 10)
    myButton2 = Button(bottomFrame, text="No!", command=clickNo)
    myButton2.grid(row=0, column=2, padx = 10)
    myButton3 = Button(bottomFrame, text="Quit", command=quit)
    myButton3.grid(row=1, column=1, padx = 10, pady = 5)



root.bind('<Return>', clickStart)
root.bind('<Left>'  , clickYes)
root.bind('<Right>' , clickNo)

os.system("clear")

ananda.load() # Load the ananda process
print("\nRobot successfully loaded...")

print("---Now reading stiffness")
ananda.rshm('plg_stiffness')

mainGUI()

keep_going = True

while keep_going:
    # Although it maintains a main loop, this routine blocks! Use update() instead...
    #root.mainloop()
    #routine_checks()

    root.update_idletasks()
    root.update()
    time.sleep(0.1) # frame rate of our GUI update




