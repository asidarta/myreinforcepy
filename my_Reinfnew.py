#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 20:24:50 2017 @author: ae2010
This code is used for reinforcement-based motor learning. It has the same working principle 
as the "my_ffnew.tcl" code in Tcl for the old suzuki machine.

Revisions: Adding a feature to replay the trajectory while the subject remains passive (Apr 24)
           Adding a list variable for baseline bias; and check for test block/phase (May2)
           Confirming robot data-logging and audio play features work (May 4)
           Adding a feature to replay lag-2 trajectory too! (May 5)
"""


import robot.interface as robot
import numpy as np
import os.path
import time
import json
import math
import random
import subprocess


# Global definition of variables
dc = {}              # dictionary for important param
mypwd  = os.getcwd() # retrieve code current directory
keepPrac = True      # keep looping in the current practice segment
instruct = True      # play instruction audio file?
record = False       # flag indicating a specific trial for capturing + replaying
w, h   = 1920,1080   # Samsung LCD size

# Supposed there are up to 4 lags in WM test, we ought to capture the trajectory up to
# 4 movements prior. We also have a counter how many trials since the last TEST trial.
nsince_last_test = 0


# Global definition of constants
ANSWERFLAG  = 0      # Flag = 1 means subject has responded
TARGETBAR   = True   # Showing target bar?? Set=0 to just show the target circle!
TARGETDIST  = 0.09   # move 15 cm from the center position (default!)
TARGETTHICK = 0.008  # 16 mm target thickness
START_SIZE  = 0.009  #  9 mm start point radius
CURSOR_SIZE = 0.004  #  4 mm cursor point radius
WAITTIME    = 0.75   # 750 msec general wait or delay time 
MOVE_SPEED  = 1.5    # duration (in sec) of the robot moving the subject to the center
FADEWAIT    = 1.0

# how big a window to use for smoothing (see tools/smoothing for details about the effects)
SMOOTHING_WINDOW_SIZE = 9 
SMOOTHING_WINDOW = np.hamming(SMOOTHING_WINDOW_SIZE)


#dc['post']= 0 # (0: hand moving to start-not ready, 
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
    robot.stop_log()
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

    # Now we will check whether log files already exist to prevent overwritting the file!
    if os.path.exists("%s.txt"%dc['logname']):
        print ("File already exists: %s.txt"%dc["logname"] )
        return

    if dc["filenum"] == 0:
        filepath = mypwd+"/exper_design/practice.txt"
        e3.config(state='normal')
        e4.config(state='disabled')
    else:
        filepath = mypwd+"/exper_design/" + dc['task'] + ".txt"
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
        dc['bbias'] = []      # deviations during baseline to compute bias
        robot.start_log("%s.dat"%dc['logname'],11)
        print("\nEntering Test Block now.........\n")
        runBlock()   # Once set, we're ready for the main loop (actual test!)



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
    global keepPrac
    x,y = robot.rshm('x'),robot.rshm('y')
    showCursorBar(0, (x,y), 0)

    print("--- Practice stage-1: yellow cursor")
    #playInstruct(1)
    robot.stay_fade(dc['cx'],dc['cy'])
    time.sleep(FADEWAIT)
    while keepPrac:
        # Note: To *fade out* the forces instead of releasing all of a sudden
        # First read out current x,y robot position
        x,y = robot.rshm('x'),robot.rshm('y')
        # Compute current distance from the center/start--robot coordinate! 
        d = math.sqrt((x-dc['cx'])**2 + (y-dc['cy'])**2)
        showCursorBar(0, (x,y), d)
        time.sleep(0.01)

    goToCenter(MOVE_SPEED) # Bring the arm back to the center first

    # Use a straight-ahead direction for familiarization trials
    angle = 0   
    showTarget(angle)

    print("--- Practice stage-2: move towards target bar")
    keepPrac = True
    #playInstruct(2)
    while keepPrac:
        # This is the point where subject starts to move to the target....
        to_target(angle)    
        # Go back to center and continue to the next trial.
        goToCenter(MOVE_SPEED)

    print("--- Practice stage-3: exploring the space")
    #playInstruct(3)
    keepPrac = True
    while keepPrac:
        # This is the point where subject starts to move to the target....
        to_target(angle)    
        # Go back to center and continue to the next trial.
        goToCenter(MOVE_SPEED)

    print("--- Practice stage-4: speed control")
    keepPrac = True
    #playInstruct(4)
    while keepPrac:
        # This is the point where subject starts to move to the target....
        to_target(angle)    
        # Go back to center and continue to the next trial.
        goToCenter(MOVE_SPEED)
    
    playInstruct(5)
    print("\n#### Session has ended! Press QUIT button now.....")


    
def runBlock():
    """ The main code once 'Start' or <Enter> key is pressed """
    minvel, maxvel = dc['mydesign']['settings']["velmin"], dc['mydesign']['settings']["velmax"]

    # This is to play specific block-instruction
    if playAudio.get():
        playInstruct(6) if (dc['task'] == "training") else playInstruct(7)

    global nsince_last_test

    for xxx in dc['mydesign']['trials']:
        # For running one trial of the block....
        index  = xxx['trial']
    	angle  = xxx['angle']
    	fdback = xxx['feedback']
    	rbias  = [xxx["negbias"], xxx["posbias"]]
        print("\nNew Round- %i"%index)
        # Reference: straight-ahead is defined as 90 deg
        angle = angle - 90   

        to_target(angle,fdback,rbias)   # <<<
        lag = 2

        # Check if this is a training block. Only training blocks require replay.
        if (dc['task'] == "training"):
            
            # If yes, then check if the next trial is test trial to replay 
            # trajectory using a certain probability 
            if random.random() < p_test(nsince_last_test):  # Why '<' ?
                # First, retrieve the desired test trajectory...
                select_traj(lag)
                # Then get the first element indicating where to start the replay
                firstx,firsty = dc['ttraj'][0]
                print("\nMoving to starting point %f, %f\n"%(firstx,firsty))
                #print traj[150]
                #print traj[210]
                #print traj[230]
            
                # Note: If the next trial is a replay, it should go instead to 
                # the first position recorded, not the center position.
                robot.move_stay(firstx, firsty, MOVE_SPEED)
                showImage("test_trial.gif",630,150,2)
            
                # If this is test trial, now replay the trajectory. Flip coin 
                # whether we replay the rotated or normal trajectory first...
                time.sleep(0.5)
                if random.random() < 0.5:           
		   replay_traj(False)
                   replay_traj(True)
                   dc['ref'] = 1 # Correct answer: 1st replay
                else:
		   replay_traj(True)
                   replay_traj(False)
                   dc['ref'] = 2 # Correct answer: 2nd replay
            
                # (7) Wait for subject's response, then go back to the center position!
                RT = doAnswer()
                goToCenter(MOVE_SPEED*0.5)
                nsince_last_test = 0
	    
            else:  # Increase the counter...
                nsince_last_test = nsince_last_test + 1
                print nsince_last_test
                goToCenter(MOVE_SPEED)
                lag, dc['ref'], dc['answer'],RT = 0,-1,-1,-1

            # (9) We concatenate the logfile content with the WM test response
            dc['logAnswer'] = "%s %d %d %d %d\n"%(dc['logAnswer'],lag,dc['ref'],dc['answer'],RT)
            saveLog()
        
        else: # (8) Return to the center immediately if it's NOT a training block.
            goToCenter(MOVE_SPEED)
            saveLog()               

    print dc['bbias']
    print("\n[Note:] Subject's average bias: %.5f"%np.mean(dc['bbias']))
    print("\n#### Test has ended! You may continue or QUIT now.....")
    
    time.sleep(2)  # 2-sec delay
    # Allow us to proceed to the next block without quiting
    e2.config(state='normal')  
    e4.config(state='normal')
    master.update()


def to_target(angle, fdback=0, rbias=[0,0]):
    """ This handles the whole trial segment when subject moves to hidden target 
    It formally takes 3 inputs: angle, whether you want to show feedback, and 
    negbias and posbias of the reward zone.
    """
    dc['subjx']= 0;  dc['subjy']= 0

    # (1) Wait at center or home position first before giving the go-ahead signal.
    time.sleep(0.5*WAITTIME) 
    win.itemconfig("start",fill="white")
    showTarget(angle)
    reach_target = False

    # Release robot_stay() to allow movement in principle, but we haven't given 
    # subjects the signal yet that they can start moving.
    #robot.controller(0)
    showCursorBar(angle, (dc['cx'],dc['cy']), 0)
    # Note: To *fade out* the forces instead of releasing all of a sudden
    robot.stay_fade(dc['cx'],dc['cy'])
    time.sleep(FADEWAIT)

    while not reach_target: # while the subject has not reached the target
        
        # (2) First get current x,y robot position and update yellow cursor location
        x,y = robot.rshm('x'),robot.rshm('y')
        dc['subjx'], dc['subjy'] = x, y
        showCursorBar(angle, (x,y), 0)
        # Compute current distance from the center/start--robot coordinate! 
    	dc['subjd'] = math.sqrt((x-dc['cx'])**2 + (y-dc['cy'])**2)
    	#print("Distance from center position= %f"%(subjd))

        vx, vy = robot.rshm('fsoft_xvel'), robot.rshm('fsoft_yvel')
        vtot = math.sqrt(vx**2+vy**2)
        #print(robot.rshm('fvv_trial_phase'))

        # (3) When the hand was towards the center (start), check if the subject is 
        # holding still inside the start position.
        if robot.rshm('fvv_trial_phase')==1:  
            if dc["subjd"]< START_SIZE and vtot < 0.01:
                win.itemconfig("start", fill="green")
                robot.start_capture()   # Start capturing trajectory now!  
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
                filter_traj()
            if (time.time()-start_time) > 5:
                goToCenter(MOVE_SPEED)
                time.sleep(0.1)
                
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


                
# Function save logfile and mkdir if needed
def saveLog():
    print("---Saving trial log.....")   
    if not os.path.exists(dc['logpath']):
	os.makedirs(dc['logpath'])
    with open("%s.txt"%dc['logname'],'aw') as log_file:
        log_file.write(dc['logAnswer'])  # Save every trial as text line


def doAnswer():
    start_time = time.time()  # To count reaction time
    global ANSWERFLAG
    print("Waiting for subject's response")
    while (not ANSWERFLAG):
        master.update_idletasks()
        master.update()
        time.sleep(0.3)
    RT = 1000*(time.time() - start_time)  # RT in m-sec
    print "--- ANSWER:%d    RT:%d"%(dc['answer'],RT)
    ANSWERFLAG = 0
    return(RT)


def select_traj(dd=1):
   """ This is to select which of the previous trajectory to play [ananda, May2017]
   The way it works is as follows: suppose nsince_last_test=4, then: 
         lag-1 trial corresponds to nsince_last_test=4
         lag-2 trial corresponds to nsince_last_test=3
         lag-3 trial corresponds to nsince_last_test=2
   To avoid getting out of index, we set the maximum lag to nsince_last_test
   """
   global nsince_last_test
   if dd > nsince_last_test: dd = nsince_last_test
   t = nsince_last_test - (dd-1)
   print "Retrieving trajectory %d"%(t)
   dc['ttraj'] = dc['traj%d'%t]



def replay_traj(rotate_flag = False):
    """ This function handles the replay of the trajectory. Depending whether
    rotate_flag is True, it will either play the normal or rotated trajectory.
    After each replay, it will also bring the subject hand back to center."""

    # First, get the Test Trajectory to play from the dict.
    traj = dc['ttraj']

    if rotate_flag:
        print("ROTATING the trajectory in robot coordinates!")
        # Flip coin whether +10deg or -10deg rotation 
        rot_angle = random.choice([-1,1])*10
        traj_rot  = rotate(traj, (dc['cx'],dc['cy']), rot_angle)
        # The rotated trajectory is in the list of tuples....
        #print traj_rot[150]
        #print traj_rot[210]
        #print traj_rot[230]
        
        # Push the clean trajectory back to the robot memory for replaying 
        # (and set the final positions appropriately)
        robot.prepare_replay(traj_rot)

    else:
        robot.prepare_replay(traj) # Normal, unrotated

    print("Ready to start replaying trajectory...")
    #raw_input("Press <ENTER> to start")
    time.sleep(0.5)
    robot.start_replay()

    while not robot.replay_is_done():
        master.update()
        pass

    time.sleep(WAITTIME)
    print("Finished replaying the trajectory...")
            
    # Important: Don't forget to return to the center position again!!
    firstx,firsty = traj[0]
    print("\nMoving to starting point %f, %f\n"%(firstx,firsty))
    robot.move_stay(firstx, firsty, MOVE_SPEED)
    time.sleep(WAITTIME)



def p_test(nn):  # nn = number of trials since the last test trial
    if   nn==1: return 0
    elif nn==2: return 0
    elif nn==3: return 1#0.8
    elif nn==4: return 0#0.9
    elif nn==5: return 0#0.5
    else:         return 0


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
    """ This function first retrieves the trajectory from the robot memory, then
    filter them using a smooth function. The filtered (x,y) positions are then
    passed to a dict variable with a certain key. This key is important because
    it indicates which lag the captured trajectory is w.r.t current trial.
    """    
    record = True
    print("Retrieving raw trajectory...")
    raw_traj = list(robot.retrieve_trajectory()) 
    robot.prepare_replay(raw_traj)
    # separate them into x and y component
    x,y = zip(*raw_traj)
    #velocity_check(x,y)
    # Smooth it
    xfilt,yfilt = smooth(x),smooth(y)
    # Trick: save it with a key name according to nsince_last_test
    global nsince_last_test
    dc["traj%d"%(nsince_last_test)] =  list(zip(xfilt,yfilt))


def smooth_window(x,window):
    """Smooth the data using a window with requested size   [From: Floris]
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
    adjusted by FVV to make Python3-compatible and ensure that the length of the output 
    is the same as the input.
    """

    wl = len(window)
    if x.ndim != 1: raise ValueError( "smooth only accepts 1 dimension arrays.")
    if x.size < wl: raise ValueError("Input vector needs to be bigger than window size.")
    if wl<3: return x

    # Pad the window at the beginning and end of the signal
    s=np.r_[x[wl-1:0:-1],x,x[-2:-(wl+1):-1]]
    # Length of s is len(x)+wl-1+wl-1 = len(x)+2*(wl-1)
 
    ## Convolution in "valid" mode gives a vector of length len(s)-len(w)+1 
    ## assuming that len(s)>len(w) 
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



def checkEndpoint(angle, feedback, rbias):
    """ The function checks whether the movement endpoint lands inside 
    a reward zone. The width of the reward zone is defined by the rbias that 
    consists of negbias and posbias w.r.t to the target center.
    Update = To manage 'good' subjects, we shift the target center according to the avg
    bias during baseline... 
    """

    global bbias
    print("  Checking end-position inside target zone?")
    # The idea is to rotate back to make it a straight-ahead (90-deg) movement!
    # The return values are in the robot coordinates
    tx,ty = dc['subjx'], dc['subjy']
    trot  = rotate([(tx,ty)], (dc['cx'],dc['cy']), -angle)
    PDy   = trot[0][0]-dc['cx']
    print "  Lateral deviation = %f" %PDy
    # Add deviation value to a list 
    # TODO::::::::::: DON"T RECORD FOR TRAINING BLOCKS
    dc['bbias'].append(PDy)

    # Check the condition to display explosion when required. The reward zone
    if PDy > bbias.get()+rbias[0] and PDy < bbias.get()+rbias[1] and feedback:
        status = 1  # 1: rewarded, 0: failed
        dc['scores'] = dc['scores'] + 10
        print "  Explosion delivered! Current score: %d"%(dc['scores'])
        showImage("Explosion_final.gif",960,140)  
        showImage("score" + str(dc['scores']) + ".gif",965,260)
    else: 
        time.sleep(WAITTIME)
	status = 0

    # We record the movement accuracy & reward status
    dc['logAnswer'] = "%.6f %d %d %.3f %.3f"%(PDy,angle,status,tx,ty)





######## Some parameters that specifytest how we draw things onto our GUI window

from Tkinter import * # Importing the Tkinter library
master  = Tk()	      # Create an empty background window for GUI
samsung = Toplevel()  # Create another one, for the robot canvas (Samsung)
                      # Interesting, you shouldn't have 2 Tk() instances, use Toplevel()
	              # and this will solve the problem of pyimage not displayed

master.geometry('%dx%d+%d+%d' % (400, 200, 500, 200)) # Nice setting: w,h,x,y   
master.title("Reward-based Sensorimotor Learning")
master.protocol("WM_DELETE_WINDOW", quit)

subjid  = StringVar()
filenum = StringVar()
mymsg   = StringVar()
varopt  = StringVar()
bbias   = DoubleVar()
playAudio = BooleanVar()

# Trick: Because LCD screen coordinate isn't the same as robot coordinate system, 
# we need to have a way to do the conversion so as to show the position properly.

coeff = "9.645104e+02,1.884507e+03,5.187605e+01,2.876710e+02,1.863987e+03,4.349610e+01".split(',')
## WARNING: I think this calib data is wrong... but how come???


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
    # TODO: This is a bad practice!   
    global e1, e2, e3, e4, e5

    # Entry widget for 1st row --------------
    Label(topFrame, text="Subject ID: ").grid(row=0, sticky=E, pady=10)
    e1 = Entry(topFrame, width = 6, bd =1, textvariable = subjid)
    e1.grid(row=0, column=1)
    e1.insert(END, "aes")
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
    e4 = OptionMenu(topFrame, varopt, "motor_test", "training + lag1", "training + lag2", 
              command=OptionSelectEvent)
    e4.grid(row=2, column=1, columnspan=3, sticky=W, pady=5)
    varopt.set("training + lag1")    # set default value
    dc['task'] = varopt.get().split()[0]  # task type

    # Entry widget for 4th row --------------
    Label(topFrame, text="Average bias (baseline): ").grid(row=3, sticky=E)
    e5 = Entry(topFrame, width = 9, state='disabled', bd =1, textvariable = bbias)
    e5.grid(row=3, column=1, columnspan=3, sticky=W, pady=5)
    e5.insert(0,0)

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

def OptionSelectEvent(event):
    temp = varopt.get().split()
    dc['task'] = temp[0]
    e5.config(state='normal') if (temp[0]=="training") else e5.config(state='disabled')

def clickYes(event):
    global ANSWERFLAG
    print "Left key pressed to answer FIRST!"
    dc['answer']=1
    ANSWERFLAG = 1

def clickNo(event):
    global ANSWERFLAG
    print "Right key pressed to answer SECOND!"
    dc['answer']=2
    ANSWERFLAG = 1

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
    win.create_oval   ([0,0,1,1],width=0, fill="black", tag="targetcir")
    win.create_polygon([0,0,0,1,1,1,0,0], fill="black", width = 10, tag="handbar")
    win.create_oval   ([0,0,1,1],width=0, fill="black", tag="hand")
    samsung.update()   # Update the canvas to let changes take effect
 

def showCursorBar(angle, position, distance, color="yellow"):
    """ Draw the cursor at the current position (if not outside the start circle) and draw 
    a bar indicating the distance from the starting position always.
    Angle    : the angle of the target w.r.t to straight-ahead direction
    Position : the CURRENT hand position in robot coordinates
    Distance : the distance traveled by the subject
    """
    (x,y) = position  #print("Showing cursor bar!")
    
    # Prepare to draw current hand cursor in the robot coordinate
    x1, y1 = rob_to_screen(x-CURSOR_SIZE, y-CURSOR_SIZE)
    x2, y2 = rob_to_screen(x+CURSOR_SIZE, y+CURSOR_SIZE)

    # If hand position is outside the start circle, remove cursor
    if distance <= START_SIZE:      
       win.itemconfig("hand",fill=color)
       win.coords("hand",*[x1,y1,x2,y2])
    else:
       win.itemconfig("hand",fill="black")
       win.coords("hand",*[0,0,0,0])
	
    # First draw cursorbar with a rectangle assuming it's in front (straight-ahead) 
    minx, miny = -.5, y - TARGETTHICK/8
    maxx, maxy =  .5, y + TARGETTHICK/8
    origxy = [(minx,miny),(maxx,miny),(maxx,maxy),(minx,maxy)]
    
    # Then rotate each polygon corner where the pivot is the current hand position.
    # We'll get rotated screen coordinates...
    rot_item = rotate(origxy, (x,y), angle) 
    scr_xy    = [rob_to_screen(x,y) for x,y in rot_item]
    scr_tuple = tuple([ item for sublist in scr_xy for item in sublist ])  
    #print rot_item
    win.coords("handbar", *scr_tuple)      # Edit coordinates of the canvas object
    win.itemconfig("handbar",fill=color)   # Show the target by updating its fill color.
    win.tag_lower("start", "hand")
    win.tag_lower("start", "handbar")
    samsung.update()     # Update the canvas to let changes take effect



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
master.bind('<Left>'  , clickYes)
master.bind('<Right>' , clickNo)
master.bind('<Escape>', quitPractice)

os.system("clear")

robot.load() # Load the robot process
print("\nRobot successfully loaded...\n")

robot.zeroft()

print("---Now reading stiffness\n")
robot.rshm('plg_stiffness')

mainGUI()
robot_canvas()

keep_going   = True

while keep_going:
    # Although it maintains a main loop, this routine blocks! Use update() instead...
    #master.mainloop()
    #routine_checks()
    master.update_idletasks()
    master.update()
    time.sleep(0.04) # 40 msec frame-rate of GUI update




