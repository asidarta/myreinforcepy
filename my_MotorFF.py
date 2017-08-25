#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 20:24:50 2017 @author: ae2010
This code is used for reinforcement-based motor learning. It has the same working principle 
as the "my_ffnew.tcl" code in Tcl for the old suzuki machine. You can use this to test
a simple FF learning or parallel sensorimotor with reinforcement.

Revisions: Confirming the new code works like the old Tcl code (Apr 19) 
           Major cleanup with Floris' comments on the code (Apr 21)
           Adding robot data-logging and audio play features (May 4)
"""


import robot.interface as robot
import os.path
import time
import json
import math
import subprocess


# Global definition of variables
dc = {}              # dictionary for important param
mypwd  = os.getcwd() # retrieve code current directory
keepPrac = True      # keep looping in the current practice segment
instruct = True      # play instruction audio file?trial
w, h   = 1920,1080   # Samsung LCD size

# Global definition of constants
TARGETBAR   = True   # Showing target bar?? Set=0 to just show the target circle!
TARGETDIST  = 0.15   # move 15 cm from the center position (default!)
TARGETTHICK = 0.01   # 20 mm target thickness
START_SIZE  = 0.009  #  9 mm start point radius
CURSOR_SIZE = 0.003  #  4 mm cursor point radius
WAITTIME    = 0.75   # 750 msec general wait or delay time 
MOVE_SPEED  = 1.5    # duration (in sec) of the robot moving the subject to the center
FADEWAIT    = 1.0


#dc['post']= 0 # (0: hand moving to start-not ready, 
#                 1: hand within/in the start position,
#                 2: hand on the way to target, 
#                 3: hand within/in the target)


def quit():
    """Subroutine to EXIT the program and stop everything."""
    global keep_going
    keep_going = False
    reach_target = False
    master.destroy()
    robot.unload()  # Close/kill robot process
    print("\nOkie! Bye-bye...\n")


def playAudio (filename):
    subprocess.call(['aplay',"%s/audio/%s"%(mypwd,filename)])
    time.sleep(0.75)
    print("---Finished playing %s..."%(filename))    


def playInstruct (n):
    global instruct
    myaudio = "%s/audio/motorpract%d.wav"%(mypwd,n)
    if (instruct):
       subprocess.call(['aplay',myaudio])
       time.sleep(1)
       print("Instruction audio finished ------------")

  
def getCenter():
    """To obtain and save a new center position OR load existing center position if exists"""
    print("---Getting center position. PLEASE remain still!")
    # Required to have subject name!
    if os.path.isfile(dc['logpath']+subjid.get()+"_center.txt"):
        #txt = open(mypwd + "/data/and_center.txt", "r").readlines()
        center = [[float(v) for v in txt.split(",")] for txt in open(
                      dc['logpath']+subjid.get()+"_center.txt", "r").readlines()]
        print("Loading existing coordinates: %f, %f"%(center[0][0],center[0][1]))
        dc['cx'],dc['cy'] = (center[0][0],center[0][1])
    else:
        if not os.path.exists(dc['logpath']): 
             os.makedirs(dc['logpath']) # For a new subject create a folder first!
        print("This is a new subject. Center position saved.")
        dc['cx'], dc['cy'] = robot.rshm('x'),robot.rshm('y')
        txt_file = open(dc['logpath']+subjid.get()+"_center.txt", "w")
        txt_file.write("%f,%f"%(dc['cx'],dc['cy']))
        txt_file.close()
    # Also useful to define center pos in the screen coordinate!       
    dc['c.scr'] = rob_to_screen(dc['cx'],dc['cy'])


def goToCenter(speed):
    """ Move to the center or start position and stay there"""
    robot.wshm('fvv_trial_phase', 0)

    # Ensure this is a null field first (because we will be updating the position)
    robot.controller(0)
    print("  Now moving to center: %f,%f"%(dc['cx'],dc['cy']))
    # Send command to move to cx,cy
    robot.move_stay(dc['cx'],dc['cy'],speed)
    
    #while not robot.move_is_done(): pass
    #print("  Movement completed!")
    time.sleep(0.5)
    # Put flag to 1, indicating robot handle @ center position
    robot.wshm('fvv_trial_phase', 1)



def enterStart(event):
    """ Start main program, taking "Enter" button as input-event """

    # First, check whether the entry fields have usable text (need subjID, a file number, etc.)
    if not subjid.get() or not filenum.get().isdigit():
        print("##Error## Subject ID and/or file numbers are empty or file number is not a digit!")
        return

    dc["subjid"]    = subjid.get()
    dc["filenum"]   = int(filenum.get())
    dc['logfileID'] = "%s%i"%(dc["subjid"],dc["filenum"])
    dc['logpath']   = '%s/data/%s_data/'%(mypwd,dc["subjid"])
    dc['logname']   = '%smotorLog_%s'%(dc['logpath'],dc['logfileID'])
    dc['scores']    = 0    # have to reset the score to 0 for each run!
    dc['curtrial']  = 0    # initialize current test trial
    dc['subjd']     = 0    # initialize robot distance from the center of start position

    # Now we will check whether log files already exist to prevent overwritting the file!
    if os.path.exists("%s.txt"%dc['logname']):
        print ("File already exists: %s.txt"%dc["logname"] )
        return

    # Force-field and parallel sensorimotor learning are legacy experiments.
    if dc["filenum"] == 0:
        filepath = mypwd+"/exper_design/archive/practice.txt"
        e3.config(state='normal')
        e4.config(state='disabled')
    else:
        filepath = mypwd+"/exper_design/archive/" + varopt.get() + ".txt"
        e3.config(state='disabled')
        e4.config(state='normal')

    # Now we will read the design file, which tells us what trials to run
    # and which targets are in each trial etc.
    #print filepath
    stages = read_design_file(filepath) # Next stage depends if file can be loaded

    # Disable the user interface so that the settings can't be accidentally changed.
    e1.config(state='disabled')
    e2.config(state='disabled')
    e4.config(state='disabled')
    master.update()

    # Capture the center position for new subject or load an existing center position. 
    # New subject has been instructed beforehand to place the hand in the center position.
    getCenter()
    # Go to the center position
    goToCenter(MOVE_SPEED*1.5)
    showStart("white")    # Display the center (start) circle
    prepareCanvas()       # Prepare drawing canvas objects
    
    if dc["filenum"] == 0:
        # This is only when filenum = 0; familiarization trials!
        print("\nEntering Practice Block now.........\n")
        runPractice()   
    else:
        # Now start logging robot data: post, vel, force, trial_phase; 11 columns
        robot.start_log("%s.dat"%dc['logname'],11)
        print("\nEntering Test Block now.........\n")
        runBlock()   # Once set, we're ready for the main loop (actual test!)



def read_design_file(mpath):
    """ Based on subj_id & block number, read experiment design file!"""
    print mpath
    if os.path.exists(mpath):
    	with open(mpath,'r') as f:
            dc['mydesign'] = json.load(f)
        #print dc['mydesign']
        print("Design file loaded! Parsing the data...")
        return 1
    else:
        print mpath
        print("##Error## Experiment design file not found. Have you created one?")
        return 0


# Run only for the first time: familiarization trials with instructions.
def runPractice():
    global keepPrac
    x,y = robot.rshm('x'),robot.rshm('y')
    showCursorBar(0, (x,y))

    print("--- Practice stage-1: yellow cursor")
    #playInstruct(1)
    robot.stay_fade(dc['cx'],dc['cy'])
    time.sleep(FADEWAIT)
    while keepPrac:
        # Note: To *fade out* the forces instead of releasing all of a sudden
        # First read out current x,y robot position
        x,y = robot.rshm('x'),robot.rshm('y')
        # Compute current distance from the center/start--robot coordinate! 
        dc['subjd'] = math.sqrt((x-dc['cx'])**2 + (y-dc['cy'])**2)
        showCursorBar(0, (x,y))
        time.sleep(0.01)

    goToCenter(MOVE_SPEED) # Bring the arm back to the center first

    # Use a straight-ahead direction for familiarization trials
    angle = 0   
    showTarget(angle)

    print("--- Practice stage-2: move towards target bar")
    keepPrac = True
    #playInstruct(2)
    while keepPrac:
        # Note: To *fade out* the forces instead of releasing all of a sudden
        robot.stay_fade(dc['cx'],dc['cy'])
        time.sleep(FADEWAIT)
        # This is the point where subject starts to move to the target....
        to_target(angle)    
        # Go back to center and continue to the next trial.
        goToCenter(MOVE_SPEED)

    print("--- Practice stage-3: exploring the space")
    #playInstruct(3)
    keepPrac = True
    while keepPrac:
        # Note: To *fade out* the forces instead of releasing all of a sudden
        robot.stay_fade(dc['cx'],dc['cy'])
        time.sleep(FADEWAIT)
        # This is the point where subject starts to move to the target....
        to_target(angle)    
        # Go back to center and continue to the next trial.
        goToCenter(MOVE_SPEED)

    print("--- Practice stage-4: speed control")
    keepPrac = True
    #playInstruct(4)
    while keepPrac:
        # Note: To *fade out* the forces instead of releasing all of a sudden
        robot.stay_fade(dc['cx'],dc['cy'])
        time.sleep(FADEWAIT)
        # This is the point where subject starts to move to the target....
        to_target(angle)    
        # Go back to center and continue to the next trial.
        goToCenter(MOVE_SPEED)
    
    playInstruct(5)
    print("\n#### Session has ended! Press QUIT button now.....")


    
def runBlock():
    """ The main code once 'Start' or <Enter> key is pressed """
    minvel, maxvel = dc['mydesign']['settings']["velmin"], dc['mydesign']['settings']["velmax"]
    ffstrength = dc['mydesign']['settings']["ffstrength"]    

    # This is to play specific block-instruction
    if playAudio.get():
        playInstruct(6) if (varopt.get() == "training") else playInstruct(7)

    for xxx in dc['mydesign']['trials']:
        # For running each trial of the block....
        index  = xxx['trial']
    	angle  = xxx['angle']
        ffield = xxx['FField']
    	fdback = xxx['feedback']
    	rbias  = [xxx["negbias"], xxx["posbias"]]
        print("\nNew Round- %i"%index)
        # Reference: straight-ahead is defined as 90 deg
        angle = angle - 90
     
        # (1) Check if this is a null or FF motor learning task. If FF, then compute
        # the curl value taking into account the direction (CW = +ve, CCW = -ve).
        if ffield == "null":
          ffval = 0
        elif ffield == "cwff":
          ffval = 1*ffstrength
        elif ffield == "ccwff":
          ffval = -1*ffstrength

        # (2) Wait at center or home position first before giving the go-ahead signal.
        robot.wshm('fvv_trial_phase', 1)  
        # Release robot_stay() to allow movement in principle, but we haven't given 
        # subjects the signal yet that they can start moving.
        #robot.controller(0)
        # Note: To *fade out* the forces instead of releasing all of a sudden
        robot.stay_fade(dc['cx'],dc['cy'])
        time.sleep(FADEWAIT)

        # (3) Reaching outward to the target!
        to_target(angle,ffval,fdback,rbias)
        # (4) Return to the center position. Ready for the next trial.
        goToCenter(MOVE_SPEED)

    print("\n#### Test has ended! You may continue or QUIT now.....")
    
    robot.stop_log()  # Stop data logging now!
    time.sleep(2)     # 2-sec delay
    # Allow us to proceed to the next block without quiting
    e2.config(state='normal')  
    e4.config(state='normal')
    master.update()


def to_target(angle, ffval=0, fdback=0, rbias=[0,0]):
    """ This handles the whole trial segment when subject moves to hidden target 
    It formally takes 3 inputs: angle, whether you want to show feedback (reward), and 
    maximum negbias and posbias to receive feedback. By default, feedback is not shown.
    """
    dc['subjx']= 0;  dc['subjy']= 0
    win.itemconfig("start",fill="white")
    showTarget(angle)
    showCursorBar(angle, (dc['cx'],dc['cy']))
    reach_target = False

    if ffval != 0: robot.start_curl(ffval)

    while not reach_target: # while the subject has not reached the target
        
        # (2) First get current x,y robot position and update yellow cursor location
        x,y = robot.rshm('x'),robot.rshm('y')
        dc['subjx'], dc['subjy'] = x, y
        # Compute current distance from the center/start--robot coordinate! 
    	dc['subjd'] = math.sqrt((x-dc['cx'])**2 + (y-dc['cy'])**2)
        showCursorBar(angle, (x,y))
    	#print("Distance from center position= %f"%(subjd))

        vx, vy = robot.rshm('fsoft_xvel'), robot.rshm('fsoft_yvel')
        vtot = math.sqrt(vx**2+vy**2)
        print(robot.rshm('fvv_trial_phase'))

        # (3) When the hand was towards the center (start), check if the subject is 
        # holding still inside the start position.
        if robot.rshm('fvv_trial_phase')==1:  
            if dc["subjd"]< START_SIZE and vtot < 0.01:
                win.itemconfig("start", fill="green")
            # (4) If more or less stationary in the start position, check if the subject has 
            # left the start position. Timer to compute movement speed begins. 
            elif dc["subjd"] > 0.01:
                start_time = time.time()
                robot.wshm('fvv_trial_phase', 2)

        # (5) If the subject has reached the the target, check if the subject has moved 
        # sufficiently far AND is coming to a stop.   
        elif robot.rshm('fvv_trial_phase')==2:
            if dc["subjd"] > 0.8*TARGETDIST and vtot < 0.05:
                #If yes, hold the position and compute movement speed.     
                robot.wshm('fvv_trial_phase', 3)
                robot.stay() # This automatically stops capturing the trajectory!
                time.sleep(0.05)
                myspeed = 1000*(time.time() - start_time)
                print("  Movement duration = %.1f msec"%(myspeed))

        elif robot.rshm('fvv_trial_phase')==3:
            # (6) Once reached the target, check end-point accuracy
            checkEndpoint(angle, fdback, rbias)
            master.update()
            reach_target = True  # To quit while-loop!
        
            # (7) Ready to move back. Remove hand position cursor, make start circle white. 
            win.coords("hand",*[0,0,0,0])
            win.itemconfig("hand",fill="black")
            win.coords("handbar",*[0,0,0,0])
            win.itemconfig("handbar",fill="black")
            win.itemconfig("start", fill="white")
            # Occasionally you call update() to refresh the canvas....
            samsung.update()

             

def checkEndpoint(angle, feedback, rbias):
    """ The function checks whether the movement endpoint lands inside 
    a reward zone. The width of the reward zone is defined by the rbias that 
    consists of negbias and posbias w.r.t to the target center. 
    """
    print("  Checking end-position inside reward zone?")
    # The idea is to rotate back to make it a straight-ahead (90-deg) movement!
    # The return values are in the robot coordinates
    tx,ty = dc['subjx'], dc['subjy']
    trot  = rotate([(tx,ty)], (dc['cx'],dc['cy']), -angle)
    #print trot
    PDy  = trot[0][0]-dc['cx']
    print "  Lateral deviation = %f" %PDy

    # Check the condition to display explosion when required!
    if PDy > rbias[0] and PDy < rbias[1] and feedback:
        status = 1  # 1: rewarded, 0: failed
        dc['scores'] = dc['scores'] + 10
        print "  Explosion delivered! Current score: %d"%(dc['scores'])
        showImage("Explosion_final.gif",960,140)  
        showImage("score" + str(dc['scores']) + ".gif",965,260)
    else: 
        time.sleep(WAITTIME)
	status = 0

    # This is where I save logfile content!
    dc['logAccuracy'] = "%.6f %d %d %.3f %.3f %.3f %.3f\n"%(PDy,angle,status,tx,ty,tx-dc['cx'],ty-dc['cy'])
    saveLog()



# Function save logfile and mkdir if needed
def saveLog():
    print("---Saving trial log.....")   
    # Making a new directory has been moved to getCenter()...
    #if not os.path.exists(dc['logpath']): os.makedirs(dc['logpath'])
    with open("%s.txt"%dc['logname'],'aw') as log_file:
        log_file.write(dc['logAccuracy'])  # Save every trial as text line



######## Some parameters that specifytest how we draw things onto our GUI window

from Tkinter import * # Importing the Tkinter library
master  = Tk()	      # Create an empty background window for GUI
samsung = Toplevel()  # Create another one, for the robot canvas (Samsung)
                      # Interesting, you shouldn't have 2 Tk() instances, use Toplevel()
	              # and this will solve the problem of pyimage not displayed

master.geometry('%dx%d+%d+%d' % (400, 200, 500, 200)) # Nice GUI setting: w,h,x,y   
master.title("Sensorimotor Learning User Interface")
master.protocol("WM_DELETE_WINDOW", quit)  # When you press [x] on the GUI

subjid  = StringVar()
filenum = StringVar()
mymsg   = StringVar()
varopt  = StringVar()
playAudio = BooleanVar()

# Trick: Because LCD screen coordinate isn't the same as robot coordinate system, 
# we need to have a way to do the conversion so as to show the position properly.

#caldata = os.popen('./robot/ParseCalData robot/cal_data.txt').read()
#print caldata.split("\t")

coeff = "9.781831e+02,1.838148e+03,4.368059e+02,2.120721e+02,1.827717e+03,3.235548e+02".split(',')
#coeff = "9.645104e+02    1.884507e+03    5.187605e+01    2.876710e+02    1.863987e+03    4.349610e+01 ".split()
## WARNING: THESE COEFFICIENTS ARE ACTUALLY OFF (NEED TO RE-COMPUTE THEM)


def rob_to_screen(robx, roby):
    px = float(coeff[0]) + float(coeff[1])*robx #- float(coeff[2])*robx*roby
    py = float(coeff[3]) + float(coeff[4])*roby #- float(coeff[5])*robx*roby
    return (px,py)
    # Changed after the robot moved to a new place.


def mainGUI():
    # Create two different frames on the master -----
    topFrame = Frame(master, width=400, height=100)
    topFrame.pack(side=TOP, expand = 1)
    #frame.bind('<Left>', leftKey)
    bottomFrame = Frame(master, bg="white", width=400, height=100)
    bottomFrame.pack(side=BOTTOM, expand = 1)
    
    # Important: This maintains frame size, no shrinking
    topFrame.pack_propagate(False)
    bottomFrame.pack_propagate(False)
    
    # Make Entry widgets global so that we can configure from outside 
    # TODO: This is a bad practice!   
    global e1, e2, e3, e4

    # Entry widget for 1st row --------------
    Label(topFrame, text="Subject ID: ").grid(row=0, sticky=E, pady=10)
    e1 = Entry(topFrame, width = 6, bd =1, textvariable = subjid)
    e1.grid(row=0, column=1)
    e1.insert(END, "aes")
    e1.focus()
    Label(topFrame, text="File Number: ").grid(row=0, column=3, padx=(40,0))
    e2 = Entry(topFrame, width = 3, bd =1, textvariable = filenum)
    e2.grid(row=0, column=4)
    e2.insert(END, "0")
    
    # Entry widget for 2nd row --------------
    Label(topFrame, text="Practice Design File: ").grid(row=1, sticky=E)
    e3 = Entry(topFrame, width = 20, bd =1)
    e3.grid(row=1, column=1, columnspan=3, sticky=W, pady=5)
    e3.insert(0, "practice")
    
    # Entry widget for 3rd row --------------
    Label(topFrame, text="Experiment Design File: ").grid(row=2, sticky=E)
    e4 = OptionMenu(topFrame, varopt, "motor_test", "training", "passive_traj")
    e4.grid(row=2, column=1, columnspan=3, sticky=W, pady=5)
    varopt.set("motor_test") # default value
    
    chk = Checkbutton(topFrame, text="play Audio?", variable=playAudio)
    chk.grid(row=3, column=3, sticky=E)

    # Entry widget for 5th row --------------
    #Label(topFrame, text="Hello",textvariable=mymsg).grid(row=4, sticky=E)
    
    # Create buttons ---------------
    myButton1 = Button(bottomFrame, text="START", bg="#0FAF0F", command=clickStart)
    myButton1.grid(row=0, padx = 15)
    myButton2 = Button(bottomFrame, text=" QUIT ", bg="#AF0F0F", command=quit)
    myButton2.grid(row=0, column=2, padx = 15, pady = 5)


def clickStart(): # GUI button click!
    enterStart(True)

def quitPractice(event):
    global keepPrac
    keepPrac = False



# This is to prepare robot canvas shown in Samsung LCD. All visual feedback, e.g. 
# cursor, explosion, etc are presented on this canvas.

def robot_canvas():
    # Indicate the canvas as global so I can access it from outside....
    global win
    win = Canvas(samsung, width=w, height=h) # 'win' is a canvas on Samsung()
    win.pack()
    win.create_rectangle(0, 0, w, h, fill="black")
    

def showStart(color="white"):
    #print("  Showing start position on the screen...")
    minx, miny = rob_to_screen(dc['cx'] - START_SIZE, dc['cy'] - START_SIZE)
    maxx, maxy = rob_to_screen(dc['cx'] + START_SIZE, dc['cy'] + START_SIZE)
    # Draw a start circle. NOTE: Use 'tag' as an identity of a canvas object!
    win.create_oval( minx,miny,maxx,maxy, fill=color, tag="start" )
    samsung.update()   # Update the canvas to let changes take effect


def prepareCanvas():
    """ This is to prepare items (objects) drawn on canvas for the first time. Put items
    that only will change their behavior in each trial of the block. In Tk, a new object 
    will be drawn on top of existing objects"""
    win.create_polygon([0,0,0,1,1,1,0,0], fill="black", width = 10, tag="target")
    win.create_polygon([0,0,0,1,1,1,0,0], fill="black", width = 10, tag="handbar")
    win.create_oval   ([0,0,1,1], width=1, fill="black", tag="targetcir")
    win.create_oval   ([0,0,1,1], width=1, fill="black", tag="hand")
    samsung.update()   # Update the canvas to let changes take effect
 


def showCursorBar(angle, position, color="yellow", barflag=True):
    """ Draw the cursor at the current position (if not outside the start circle) and draw 
    a bar indicating the distance from the starting position always.
    Angle    : the angle of the target w.r.t to straight-ahead direction
    Position : the CURRENT hand position in robot coordinates
    color    : the color of the canvas object (default: yellow)
    barflag  : is the hand cursor bar flag active? (default: YES)
    """
    (x,y) = position  #print("Showing cursor bar!")
    
    # Prepare to draw current hand cursor in the robot coordinate
    x1, y1 = rob_to_screen(x-CURSOR_SIZE, y-CURSOR_SIZE)
    x2, y2 = rob_to_screen(x+CURSOR_SIZE, y+CURSOR_SIZE)

    # If hand position is outside the start circle, remove cursor
    if dc['subjd'] <= START_SIZE:      
       win.itemconfig("hand",fill=color)
       win.coords("hand",*[x1,y1,x2,y2])
    else:
       win.itemconfig("hand",fill="black")
       win.coords("hand",*[0,0,0,0])
	
    # First draw cursorbar with a rectangle assuming it's in front (straight-ahead) 
    minx, miny = -.5, y - TARGETTHICK/10
    maxx, maxy =  .5, y + TARGETTHICK/10
    origxy = [(minx,miny),(maxx,miny),(maxx,maxy),(minx,maxy)]
    
    # Then rotate each polygon corner where the pivot is the current hand position.
    # We'll get rotated screen coordinates...
    rot_item = rotate(origxy, (x,y), angle) 
    scr_xy    = [rob_to_screen(x,y) for x,y in rot_item]
    scr_tuple = tuple([ item for sublist in scr_xy for item in sublist ])  
    #print rot_item
    if barflag:
       win.coords("handbar", *scr_tuple)      # Edit coordinates of the canvas object
       win.itemconfig("handbar",fill=color)   # Show the target by updating fill color.
       win.tag_lower("start", "hand")
       win.tag_lower("start", "handbar")
    samsung.update()     # Update the canvas to let changes take effect



def showTarget(angle, color="white"):
    """
    Show the target at the given angle painted in the given color.
    """
    # Construct coordinates for target circle in the robot coordinates.
    x1, y1   = dc['cx']-TARGETTHICK, dc['cy']+TARGETDIST-TARGETTHICK
    x2, y2   = dc['cx']+TARGETTHICK, dc['cy']+TARGETDIST+TARGETTHICK
    origxy = [(x1,y1),(x2,y2)]
    # Trick: Rotate twice; first rotate w.r.t its own center, then w.r.t start position
    rot_item = rotate(origxy, (dc['cx'],dc['cy']+TARGETDIST), -angle)
    rot_item = rotate(rot_item, (dc['cx'],dc['cy']), angle)
    #print rot_item
    scr_xy    = [rob_to_screen(x,y) for x,y in rot_item]
    scr_tuple = tuple([ item for sublist in scr_xy for item in sublist ])
    # Now show the target circle!
    win.coords("targetcir",*scr_tuple)
    win.itemconfig("targetcir",fill="red")

    if TARGETBAR:
    # First construct a set of coordinates for the polygon corners in the robot coordinates.
        minx, miny = -.5, dc['cy'] + TARGETDIST - TARGETTHICK
        maxx, maxy =  .5, dc['cy'] + TARGETDIST + TARGETTHICK
        origxy = [(minx,miny),(maxx,miny),(maxx,maxy),(minx,maxy)]

        # Then rotate each polygon corner where the pivot is the center/start positon.
        # We'll get rotated screen coordinates...
        rot_item  = rotate(origxy, (dc['cx'],dc['cy']), angle)
        scr_xy    = [rob_to_screen(x,y) for x,y in rot_item]
        scr_tuple = tuple([ item for sublist in scr_xy for item in sublist ])

        #print rot_item      
        win.coords("target", *scr_tuple)     # Edit coordinates of the canvas object
        win.itemconfig("target",fill=color)  # Show the target by updating its fill color.
        samsung.update()         # Update the canvas to let changes take effect


def rotate(coords, pivot, angle):
    """ Rotate the point(x,y) in coords around a pivot point by the given angle. Coordinates
    to be rotated and pivot points will be converted to complex numbers.
    Arguments
        coords: list of tuples (x,y)  <- important!! 
        pivot : pivot point of reference
        angle : angle, in degree
        rob_coord = True 

    output:
        returns a list of rotated tuples in the ROBOT coordinates by default."""

    pivot = complex(pivot[0],pivot[1])
    # Convert rotation angle into radians first
    inrad  = angle*math.pi/180
    rot    = complex(math.cos(inrad),math.sin(inrad))
    newxy  = []
    for x, y in coords:
        v = rot * (complex(x,y) - pivot) + pivot
        newxy.append((v.real,v.imag))
    return (newxy)    

    #if rob_coord:
    #    return tuple([ item for sublist in newxy for item in sublist ])
    #else:
    #    scr_xy = [rob_to_screen(x,y) for x,y in newxy]
    #    return tuple([ item for sublist in scr_xy for item in sublist ])


def showImage(name, px=w/2, py=h/2, delay=1.0):
    #print "  Showing image on the canvas...."
    myImage = PhotoImage(file=mypwd + "/pictures/" +name)
    # Put a reference to image since TkImage doesn't handle image properly, image
    # won't show up! So first, I put image in a label.
    label = Label(win, bg="black", image=myImage)
    label.image = myImage # keep a reference!
    label.place(x=px, y=py)
    # Update the canvas to let changes take effect
    samsung.update()
    time.sleep(delay)
    label.config(image='') 
    label.place(x=0, y=0)   
    time.sleep(0.1)
    samsung.update()
    #print "  Removing inage from the canvas...."



master.bind('<Return>', enterStart)
master.bind('<Escape>', quitPractice)

os.system("clear")

robot.load() # Load the robot process
print("\nRobot successfully loaded...\n")

robot.zeroft()
print("\n\nPress START or <Enter> key to continue\n")

mainGUI()
robot_canvas()

keep_going   = True
reach_target = True

while keep_going:
    # Although it maintains a main loop, this routine blocks! Use update() instead...
    #master.mainloop()
    robot.rshm("curl")
    master.update_idletasks()
    master.update()
    time.sleep(0.04) # 40 msec frame-rate of GUI update




