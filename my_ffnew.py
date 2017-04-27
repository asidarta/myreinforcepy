#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 20:24:50 2017 @author: ae2010
This code is used for reinforcement-based motor learning. It has the same working principle 
as the "my_ffnew.tcl" code in Tcl for the old suzuki machine.

Revisions: Confirming the new code works like the old Tcl code (Apr 19) 
           Major cleanup with Floris' comments on the code (Apr 21)
           Adding a feature to replay the trajectory while the subject remains passive (Apr 24)
"""

import robot.interface as robot
import numpy as np
import os.path
import time
import json
import math


# Global definition of variables
dc = {}              # dictionary for important param
mypwd  = os.getcwd() # retrieve code current directory
w, h   = 1920,1080   # Samsung LCD size
traj   = []          # global var to contain recorded trajectory
record = False       # flag indicating a specific trial for capturing + replaying

# Global definition of constants
TARGETBAR   = True   # Showing target bar?? Set=0 to just show the target circle!
TARGETDIST  = 0.10   # move 15 cm from the center position (default!)     :::TODO::: CHANGE BACK TO 0.15
TARGETTHICK = 0.008  # 16 cm target thickness
CURSOR_SIZE = 0.009  #  9 mm start radius
WAITTIME    = 1.0    # 1000 msec general wait or delay time 
MOVE_SPEED  = 1.8    # duration (in sec) of the robot moving the subject to the center

# how big a window to use for smoothing (see tools/smoothing for details about the effects)
SMOOTHING_WINDOW_SIZE = 9 
SMOOTHING_WINDOW = np.hamming(SMOOTHING_WINDOW_SIZE)



##phase
## TODO: check that phase is written to the log file (may want to use fvv_trial_phase)
## TODO: if you want to update the phase from Python, you have to call wshm('fvv_trial_phase')

dc['post'] = 0 # (0: hand moving to start-not ready, 
#                 1: hand within/in the start position,
#                 2: hand on the way to target, 
#                 3: hand within/in the target)
dc['scores']= 0 # points for successful trials


def quit():
    """Subroutine to EXIT the program and stop everything."""
    global keep_going
    keep_going = False
    reach_target = False
    master.destroy()
    robot.unload()  # Close/kill robot process


def playAudio():
    """Play specific audio"""
    print("---Audio play initiated...")
    #p = vlc.MediaPlayer(mypwd + "/data/beep.mp3")
    #p.play()
    time.sleep(2)
    print("---Audio play finished...\n")


def getCenter():
    """To obtain and save a new center position OR load existing center position if exists"""
    print("---Getting center position. PLEASE remain still!")
    # Required to have subject name!
    if os.path.isfile(dc['logpath']+subjid.get()+"_center.txt"):
        #txt = open(mypwd + "/data/and_center.txt", "r").readlines()
        center = [[float(v) for v in txt.split(",")] for txt in open(
                      dc['logpath']+subjid.get()+"_center.txt", "r").readlines()]
        #print(center)
        print("Loading existing coordinates: %f, %f"%(center[0][0],center[0][1]))
        dc['cx'],dc['cy'] = (center[0][0],center[0][1])
    else:
        print("This is a new subject. Center position saved.")
        dc['cx'], dc['cy'] = robot.rshm('x'),robot.rshm('y')
        txt_file = open(dc['logpath']+subjid.get()+"_center.txt", "w")
        txt_file.write("%f,%f"%(dc['cx'],dc['cy']))
        txt_file.close()
    # Also useful to define center pos in the screen coordinate!       
    dc['c.scr'] = rob_to_screen(dc['cx'],dc['cy'])


def goToCenter(speed):
    """ Move to the center or start position and stay there"""
    # Ensure this is a null field first (because we will be updating the position)
    robot.controller(0)
    print("  Now moving to center: %f,%f"%(dc['cx'],dc['cy']))
    # Send command to move to cx,cy
    robot.move_stay(dc['cx'],dc['cy'],speed)
    
    #while not robot.move_is_done(): pass
    #print("  Movement completed!")
    # Put flag to 1, indicating robot handle @ center position
    dc['post'] = 1


def clickStart():
    enterStart(True)

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
    dc['logname']   = '%smotorLog_%s.txt'%(dc['logpath'],dc['logfileID'])

    # Now we will check whether log files already exist to prevent overwritting the file!
    if os.path.exists(dc['logname']):
        print ("File already exists: %s"%dc["logname"] )
        return

    if dc["filenum"] == 0:
        filepath = mypwd+"/exper_design/practice.txt"
        e3.config(state='normal')
        e4.config(state='disabled')
    else:
        filepath = mypwd+"/exper_design/" + varopt.get() + ".txt"
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
    goToCenter(MOVE_SPEED)
    showStart("white")    # Display the center (start) circle
    prepareCanvas()       # Prepare drawing canvas objects

    if dc["filenum"] == 0:
        print("\nEntering Practice Block now.........\n")
        runBlock() # This is only for filenum = 0, familiarization trials!
        # TODO: runBlock() above will be different for practice trials (TODO)
    else:
        print("\nEntering Test Block now.........\n")
        runBlock()	   # Once set, we're ready for the main loop (actual test!)



def read_design_file(mpath):
    """ Based on subj_id & block number, read experiment design file!"""
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


# Run only for the first time: familiarization trials with instruction.
def runPractice():
    print("Entering practice-Loop now.........")
    #playAudio()
    #playAudio()
    #playAudio()

    
def runBlock():
    """ The main code once 'Start' or <Enter> key is pressed """
    minvel, maxvel = dc['mydesign']['settings']["velmin"], dc['mydesign']['settings']["velmax"]

    global traj

    for xxx in dc['mydesign']['trials']:
        # For running one trial of the block....
        index  = xxx['trial']
    	FFset  = xxx['FField']
    	angle  = xxx['angle']
    	fdback = xxx['feedback']
    	bias   = [xxx["minbias"], xxx["maxbias"]]
        print("\nNew Round- %i"%index)
        angle = angle - 90   # Reference: straight-ahead is defined as 90 deg

        # (1) Signal that the subject can start moving and wait until reaches the target
        time.sleep(WAITTIME)

        # Note: To *fade out* the forces instead of releasing all of a sudden
        robot.stay_fade(dc['cx'],dc['cy'])

        to_target(angle)   
        win.itemconfig("start", fill="white")  # Make start circle white again
        
        # (2) Once reached, check end-point accuracy
        checkEndpoint(angle, fdback, bias)
        
        # (3) Reset position flag. Go back to center. Note: If the next trial is a replay,
        # it should go instead to the first position recorded.
        dc['post'] = 0    
        #goToCenter(MOVE_SPEED)

        firstx,firsty = traj[0]
        print("\nMoving to starting point %f,%f\n"%(firstx,firsty))
        #print traj[50]
        #print traj[100]
        robot.move_stay(firstx, firsty, MOVE_SPEED)
 
        # (4) Call this function to save logfile
        time.sleep(0.3)
        #saveLog()   	 

        # (5) Maybe this is the point to replay the trajectory
        showImage("test_trial.gif",700,150,2)
        time.sleep(0.5)
        replay_traj()

    print("\n#### NOTE = Test has ended!!")


def to_target(angle):
    """ This handles the whole segment when subject moves to hidden target """
    global traj
    dc['post'] = 1;  dc['subjx']= 0;  dc['subjy']= 0
    win.itemconfig("start",fill="white") 
    reach_target = False

    while not reach_target: # while the subject has not reached the target
        
        # First read out current x,y robot position
        x,y = robot.rshm('x'),robot.rshm('y')
        dc['subjx'], dc['subjy'] = x, y

    	# Compute current distance from the center/start--robot coordinate! 
    	dc['subjd'] = math.sqrt((x-dc['cx'])**2 + (y-dc['cy'])**2)
    	#print("Distance from center position= %f"%(subjd))

        showCursorBar(angle, (x,y), dc["subjd"])
        showTarget(angle)
        win.tag_lower("start", "hand")
        win.tag_lower("start", "handbar")

        # Occasionally you call update() to refresh the canvas....
        samsung.update()
        vx, vy = robot.rshm('fsoft_xvel'), robot.rshm('fsoft_yvel')
        vtot = math.sqrt(vx**2+vy**2)
        #print vtot
        #print(dc['post'])

    	# Release robot_stay() to allow movement in principle, but we haven't given 
        # subjects the signal yet that they can start moving.
        #robot.controller(0)

        # (1) When the hand was towards the center (start), check if the subject is holding 
        # still inside the start position.
        if dc["post"]==1:  
            if dc["subjd"]< 0.01 and vtot < 0.01:
                time.sleep(0.5)
                dc["post"]=2                
                win.itemconfig("start", fill="green")
		## TODO: Handle movements which are too long
                traj = robot.start_capture()   # start CAPTURING trajectory...

        # (2) If more or less stationary in the start position, check if the subject has left
        # the starting position. Timer to compute movement speed begins. 
        elif dc["post"]==2:
            if dc["subjd"] > 0.01:
                start_time = time.time()  # Used for computing movement speed
                dc["post"]=3

        # (3) If the subject has reached the the target, check if the subject has moved 
        # sufficiently far AND is coming to a stop. If yes, compute movement speed and 
        # retrieve + filter the raw trajectory.       
        elif dc["post"]==3:
            if dc["subjd"] > 0.75*TARGETDIST and vtot < 0.01:
                robot.stay()
                time.sleep(0.05)
                myspeed = 1000*(time.time() - start_time)
                print("  Movement duration = %.1f msec"%(myspeed))
                reach_target = True
                filter_traj()
                
 

def replay_traj():
    # Push the clean trajectory back to the robot memory for replaying (and set 
    # the final positions appropriately)
    #robot.prepare_replay(traj) 

    print("Ready to start replaying trajectory...")
    #raw_input("Press <ENTER> to start")
    #time.sleep(0.5)
    #robot.start_replay()

    #while not robot.replay_is_done():
    #    master.update()
    #    pass

    print("Finished replaying the trajectory...")
            
    # Important: Don't forget to go back to the center position again!
    #time.sleep(WAITTIME)
    #firstx,firsty = traj[0]
    #print("\nMoving to starting point %f,%f\n"%(firstx,firsty))
    #robot.move_stay(firstx, firsty, MOVE_SPEED)

    #time.sleep(WAITTIME)
    print("Rotating the trajectory...")
    traj_rot = rotate(traj, (dc['cx'],dc['cy']), 5)
    print traj_rot 

    robot.prepare_replay(traj_rot)
    

    print("Ready to start replaying trajectory...")
    #raw_input("Press <ENTER> to start")
    #time.sleep(0.5)
    #robot.start_replay()

    #while not robot.replay_is_done():
    #    master.update()
    #    pass

    #print("Finished replaying the trajectory...")
            
    # Important: Don't forget to go back to the center position again!
    #time.sleep(WAITTIME)
    #goToCenter(MOVE_SPEED)





def velocity_check(x,y):
    """ This function tries to find the time point in which movement velocity reaches 
    5% of the maximum velocity (velr). This is used to cut the trajectory"""

    vel = []   # declare empty list
    # obtain velocity for x and y separately
    print("Calculating maximum velocity...")
    vx,vy = np.gradient(x), np.gradient(y)
    # then compute the resultant velocity vector: velr 
    # Twist your mind with list comprehension!
    velr = [math.sqrt(xx**2 + yy**2) for xx,yy in zip(vx,vy)]
    #print velr
    vel_lim = 0.05*max(velr)     
    # try to only take > 5% of max. velocity
    j = [i for i, trials in enumerate(velr) if trials > vel_lim]
    #print min(j)
    #print max(j)


def filter_traj():
    record = True
    # retrieve the captured trajectory from the robot memory
    print("Retrieving raw trajectory...")
    raw_traj = list(robot.retrieve_trajectory()) 
    robot.prepare_replay(raw_traj)
    # separate them into x and y component
    x,y = zip(*raw_traj)
    #velocity_check(x,y)
    # Smooth it
    xfilt,yfilt = smooth(x),smooth(y)
    global traj
    traj = list(zip(xfilt,yfilt))


def smooth_window(x,window):
    """Smooth the data using a window with requested size  [From: Floris]
    
    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal 
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.

    Arguments
        x: the input signal 
        window: the window function (for example take numpy.hamming(21) ) 

    output:
        the smoothed signal
        
    original source:  http://scipy-cookbook.readthedocs.io/items/SignalSmooth.html 
    adjusted by FVV to make Python3-compatible and ensure that the length of the output is the same
    as the input.
    """

    wl = len(window)
    if x.ndim != 1: raise ValueError( "smooth only accepts 1 dimension arrays.")
    if x.size < wl: raise ValueError("Input vector needs to be bigger than window size.")
    if wl<3: return x

    # Pad the window at the beginning and end of the signal
    s=np.r_[x[wl-1:0:-1],x,x[-2:-(wl+1):-1]]
    # Length of s is len(x)+wl-1+wl-1 = len(x)+2*(wl-1)
 
    ## Convolution in "valid" mode gives a vector of length len(s)-len(w)+1 assuming that len(s)>len(w) 
    y=np.convolve(window/window.sum(),s,mode='valid')
    
    ## So now len(y) is len(s)-len(w)+1  = len(x)+2*(wl-1) - len(w)+1
    ## i.e. len(y) = len(x)+len(w)-1
    ## So we want to chop off len(w)-1 as symmetrically as possible
    frontw = int((wl-1)/2)   # how much we want to chop off on the front
    backw  = (wl-1)-frontw   # how much we want to chop off on the back
    return y[frontw:-backw]


def smooth(x):
    """ Smooth the signal x using the specified smoothing window. """
    return smooth_window(np.array(x),SMOOTHING_WINDOW)




def checkEndpoint(angle, feedback, bias):
    print("  Checking end-position inside target zone?")
    # The idea is to rotate back to make it a straight-ahead (90-deg) movement!
    # TODO: Use the rotate function
    inrad = -angle*math.pi/180
    pivot = complex(dc['cx'],dc['cy'])   # In robot coordinates...
    tx,ty = dc['subjx'], dc['subjy']
    rot  = complex(math.cos(inrad),math.sin(inrad))
    trot = rot * (complex(tx, ty) - pivot) + pivot
    #print trot
    PDy  = trot.real-dc['cx']
    print "  Lateral deviation = %f" %PDy

    # Check the condition to display explosion when required!
    if PDy > bias[0] and PDy < bias[1] and feedback:
        status = 1  # 1: rewarded, 0: failed
        dc['scores'] = dc['scores'] + 10
        print "  Explosion delivered! Current score: %d"%(dc['scores'])
        showImage("Explosion_final.gif",960,140)  
        showImage("score" + str(dc['scores']) + ".gif",965,260)
    else: 
        time.sleep(WAITTIME)
	status = 0

    # This is where I save logfile content!
    dc['logAnswer'] = "%.3f %d %d %.3f %.3f %.3f %.3f\n"%(PDy,angle,status,tx,ty,tx-dc['cx'],ty-dc['cy'])



# Function save logfile and mkdir if needed
def saveLog():
    print("---Saving trial log.....")   
    if not os.path.exists(dc['logpath']):
	os.makedirs(dc['logpath'])
    with open(dc['logname'],'w') as log_file:
        log_file.write(dc['logAnswer'])  # Save every trial as text line



######## Some parameters that specify how we draw things onto our GUI window

from Tkinter import * # Importing the Tkinter library
master  = Tk()	      # Create an empty background window for GUI
samsung = Toplevel()  # Create another one, for the robot canvas (Samsung)
                      # Interesting, you shouldn't have 2 Tk() instances, use Toplevel()
	              # and this will solve the problem of pyimage not displayed

master.geometry('%dx%d+%d+%d' % (400, 150, 500, 200))   # Nice geometry setting!!
master.title("Reward-based Sensorimotor Learning")
master.protocol("WM_DELETE_WINDOW", quit)

subjid  = StringVar()
filenum = StringVar()
mymsg   = StringVar()
varopt  = StringVar()

# Trick: Because LCD screen coordinate isn't the same as robot coordinate system, 
# we need to have a way to do the conversion so as to show the position properly.

#caldata = os.popen('./robot/ParseCalData robot/cal_data.txt').read()
#print caldata.split("\t")
coeff = "9.645104e+02    1.884507e+03    5.187605e+01    2.876710e+02    1.863987e+03    4.349610e+01 ".split()
## WARNING: THESE COEFFICIENTS ARE ACTUALLY OFF (NEED TO RE-COMPUTE THEM)

def rob_to_screen(robx, roby):
    ### TODO: NEEDS TO BE FIXED. This is off for the center position
    px = float(coeff[0]) + float(coeff[1])*robx + float(coeff[2])*robx*roby
    py = float(coeff[3]) + float(coeff[4])*roby + float(coeff[5])*robx*roby
    return (px,py)

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
    global e1, e2, e3, e4

    # Entry widget for 1st row --------------
    Label(topFrame, text="Subject ID: ").grid(row=0, sticky=E)
    e1 = Entry(topFrame, width = 6, bd =1, textvariable = subjid)
    e1.grid(row=0, column=1)
    e1.insert(END, "aes")
    Label(topFrame, text="File Number: ").grid(row=0, column=3, padx = (30,5))
    e2 = Entry(topFrame, width = 3, bd =1, textvariable = filenum)
    e2.grid(row=0, column=4, pady=5)
    e2.insert(END, "0")
    
    # Entry widget for 2nd row --------------
    Label(topFrame, text="Practice Design File: ").grid(row=1, sticky=E)
    e3 = Entry(topFrame, width = 20, bd =1)
    e3.grid(row=1, column=1, columnspan=3, sticky=W, pady=5)
    e3.insert(0, "practice")
    
    # Entry widget for 3rd row --------------
    Label(topFrame, text="Experiment Design File: ").grid(row=2, sticky=E)
    e4 = OptionMenu(topFrame, varopt, "motor_test", "training", "passive")
    e4.grid(row=2, column=1, columnspan=3, sticky=W, pady=5)
    varopt.set("motor_test") # default value
    
    # Entry widget for 4th row --------------
    Label(topFrame, textvariable=mymsg).grid(row=2, sticky=E)
    
    # Create buttons ---------------
    myButton1 = Button(bottomFrame, text="START", bg="#0FAF0F", command=clickStart)
    myButton1.grid(row=0, padx = 15)
    myButton2 = Button(bottomFrame, text=" QUIT ", bg="#AF0F0F", command=quit)
    myButton2.grid(row=0, column=2, padx = 15, pady = 5)


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
    minx, miny = rob_to_screen(dc['cx'] - CURSOR_SIZE, dc['cy'] - CURSOR_SIZE)
    maxx, maxy = rob_to_screen(dc['cx'] + CURSOR_SIZE, dc['cy'] + CURSOR_SIZE)
    # Draw a start circle. NOTE: Use 'tag' as an identity of a canvas object!
    win.create_oval( minx,miny,maxx,maxy, fill=color, tag="start" )


def prepareCanvas():
    """ This is to prepare items (objects) drawn on canvas for the first time. Put items
    that only will change their behavior in each trial of the block. In Tk, a new object 
    will be drawn on top of existing objects"""
    win.create_polygon([0,0,0,1,1,1,0,0], fill="black", width = 10, tag="target")
    win.create_oval   ([0,0,1,1],width=0, fill="black", tag="targetcir")
    win.create_polygon([0,0,0,1,1,1,0,0], fill="black", width = 10, tag="handbar")
    win.create_oval   ([0,0,1,1],width=0, fill="black", tag="hand")
 

def showCursorBar(angle, position, distance, color="yellow"):
    """ Draw the cursor at the current position (if not outside the start circle) and draw 
    a bar indicating the distance from the starting position always.
    Angle    : the angle of the target w.r.t to straight-ahead direction
    Position : the CURRENT hand position in robot coordinates
    Distance : the distance traveled by the subject
    """
    (x,y) = position  #print("Showing cursor bar!")
    
    # Prepare to draw current hand cursor in the robot coordinate
    x1, y1 = rob_to_screen(x-CURSOR_SIZE/3, y-CURSOR_SIZE/3)
    x2, y2 = rob_to_screen(x+CURSOR_SIZE/3, y+CURSOR_SIZE/3)

    # If hand position is outside the start circle, remove cursor
    if distance < CURSOR_SIZE:      
    	win.itemconfig("hand",fill=color)
        win.coords("hand",*[x1,y1,x2,y2])
    else:
    	win.itemconfig("hand",fill="black")
        win.coords("hand",*[0,0,0,0])
	
    # TODO 1.015 make constant (START_CIRCLE_RADIUS) and define it on top
    # First draw cursorbar with a rectangle assuming it's in front (straight-ahead) 
    minx, miny = -.5, y - TARGETTHICK/6
    maxx, maxy =  .5, y + TARGETTHICK/6
    origxy = [(minx,miny),(maxx,miny),(maxx,maxy),(minx,maxy)]
    
    # Then rotate each polygon corner where the pivot is the current hand position.
    # We'll get rotated screen coordinates...
    rot_item = rotate(origxy, (x,y), angle)   
    #print rot_item
    win.coords("handbar", *rot_item)       # Edit coordinates of the canvas object
    win.itemconfig("handbar",fill=color)   # Show the target by updating its fill color.


def showTarget(angle, color="white"):
    """
    Show the target at the given angle painted in the given color.
    """
    #print("  Showing target bar on the screen...")
    # First construct a set of coordinates for the polygon corners in the robot coordinates.
    minx, miny = -.5, dc['cy'] + TARGETDIST - TARGETTHICK
    maxx, maxy =  .5, dc['cy'] + TARGETDIST + TARGETTHICK
    origxy = [(minx,miny),(maxx,miny),(maxx,maxy),(minx,maxy)]

    # Then rotate each polygon corner where the pivot is the center/start positon.
    # We'll get rotated screen coordinates...
    rot_item = rotate(origxy, (dc['cx'],dc['cy']), angle)
    #print rot_item      
    win.coords("target", *rot_item)     # Edit coordinates of the canvas object
    win.itemconfig("target",fill=color) # Show the target by updating its fill color.
    

def rotate(coords, pivot, angle, rob_coord = True):
    """ Rotate the point(x,y) in coords around a pivot point by the given angle (in degrees).
    Coordinates to be rotated and pivot points will be converted to complex numbers. The function 
    returns screen coordinates (by default), unless rob_coord flag is FALSE """

    pivot = complex(pivot[0],pivot[1])
    # Convert rotation angle into radians first
    inrad  = angle*math.pi/180
    rot    = complex(math.cos(inrad),math.sin(inrad))
    newxy  = []
    for x, y in coords:
        v = rot * (complex(x,y) - pivot) + pivot
        newxy.append((v.real,v.imag))
        
    if rob_coord: # This transforms the robot coordinate to screen coordinate!
    	scr_xy = [rob_to_screen(x,y) for x,y in newxy]
        return tuple([ item for sublist in scr_xy for item in sublist ])
    else:
    	return tuple([ item for sublist in newxy  for item in sublist ])


def showImage(name, px=w/2, py=h/2, delay=1.0):
    #print "  Showing image on the canvas...."
    myImage = PhotoImage(file=mypwd + "/pictures/" +name)
    # Put a reference to image since TkImage doesn't handle image properly, image
    # won't show up! So first, I put image in a label.
    label = Label(win, bg="black", image=myImage)
    label.image = myImage # keep a reference!
    label.place(x=px, y=py)
    # Occasionally you call update() to refresh the canvas....
    samsung.update()
    time.sleep(delay)
    label.config(image='')   
    # Occasionally you call update() to refresh the canvas....
    samsung.update()
    #print "  Removing inage from the canvas...."


#from PIL import ImageTk, Image

master.bind('<Return>', enterStart)

os.system("clear")

robot.load() # Load the robot process
print("\nRobot successfully loaded...")

robot.zeroft()

print("---Now reading stiffness")
robot.rshm('plg_stiffness')

mainGUI()
robot_canvas()

keep_going   = True
reach_target = True

while keep_going:
    # Although it maintains a main loop, this routine blocks! Use update() instead...
    #master.mainloop()
    #routine_checks()
    master.update_idletasks()
    master.update()
    time.sleep(0.04) # 40 msec frame-rate of GUI update




