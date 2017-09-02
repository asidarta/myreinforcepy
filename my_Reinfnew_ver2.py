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
           Using a constant Y-center position; using a picture as 'Go'-signal (May 17)
           Adding a flag to show that the test is currently active. Bugs fixed. (May 30)
           Modifying the logfile content with columns header now (Jun 12)
           Adding a function to compute PD at max velocity (Jun 19)
           Adding a function for radial velocity (Floris')
           Motor-pre changed to 30 trials, compute angular deviation, bias changed to 15 mm (Jul 10)
           Training trials changed to 60 trials. Editing the way reward shift is performed (Jul 12)
           Tweaked based on Skype chat (mid-Aug): use shaping, shift even more.
"""

### Note: Baseline bias was calculated because we want to shift the target zone with a constant value.


import robot.interface as robot
import numpy as np
import os.path
import time
import json
import math
import random
import subprocess


# Global definition of variables
dc = {}               # dictionary for important param
mypwd  = os.getcwd()  # retrieve code current directory
repeatFlag = True     # keep looping in the current practice segment
instruct   = True     # play instruction audio file?
w, h   = 1920,1080    # Samsung LCD size

# Supposed there are up to 4 lags in WM test, we ought to capture the trajectory up to
# 4 movements prior. We also have a counter how many trials since the last TEST trial.
nsince_last_test = 0

# Global definition for test-related parameters. This list replaces exper_design file.
NEGBIAS = -0.006   # 12 mm reward zone width, the variable name is legacy from Nicolo!
POSBIAS = +0.006   # 12 mm reward zone width
VELMIN  = 1200
VELMAX  = 800
NTRIAL_MOTOR = 30  # Originally set to 20...
NTRIAL_TRAIN = 60  # Originally set to 50...
ROT_MAG = 5        # Value of rotation angle for WM Test.

# Global definition for other constants
VER_SOFT    = "WM3"
YCENTER     = -0.005 # Let's fixed the Y-center position!
ANSWERFLAG  = 0      # Flag = 1 means subject has responded
TARGETBAR   = True   # Showing target bar?? Set=0 to just show the target circle!
TARGETDIST  = 0.15   # move 15 cm from the center position (default!)
TARGETTHICK = 0.010  # 20 mm target thickness
START_SIZE  = 0.009  #  9 mm start point radius
CURSOR_SIZE = 0.003  #  3 mm cursor point radius
WAITTIME    = 0.75   # 750 msec general wait or delay time 
MOVE_SPEED  = 1.5    # duration (in sec) of the robot moving the subject to the center
FADEWAIT    = 1.0

# How big a window to use for smoothing (see tools/smoothing for details about the effects)
SMOOTHING_WINDOW_SIZE = 9 
SMOOTHING_WINDOW = np.hamming(SMOOTHING_WINDOW_SIZE)


# [May 11] We decide test direction for lag-1 and lag-2 test respectively (+/-45 deg). 
# If lag-1 is selected as 45deg, then lag-2 should be -45 deg. This random selection 
# is executed once, at the very first when the code is run.
test_angle = [-45,45]
# random.shuffle(test_angle)

# Now this is contained in fvv_trial_phase variable...
#dc['post']= 0 # (0: hand moving to start-not ready, 
#                 1: hand within/in the start position,
#                 2: hand on the way to target, 
#                 3: hand within/in the target)

dc["active"] = False  ## Adding this flag to show that the test is currently active!!

# This is to shift the reward zone. It's a +/-10 mm shift from the subject's baseline bias.
# It depends on the reward width setup such that the chance is ~25% of the baseline trials.
#BIAS_SHIFT = random.choice([-1,1])*(POSBIAS-NEGBIAS)

# Update (Jul 12) = shift is fixed at 18 cm. The shift should be towards the actual 45 deg.
# Also, reward zone width changes over blocks. Note: option values has to be accessed by *

# Update (July 24 based on Skype call with Ananda, David*2 and Floris)
BIAS_SHIFT_pd = 0.03
ZONE_WIDTH_pd = [ 0.0175,
                  0.013,
                  0.01 ]

# Update (July 24; we are changing to use the point of maximum velocity as a reference
# for calculating reward, so we need to recompute what the logical amount of shift and target
# widths will be)
BIAS_SHIFT_deg = 11.31
# math.atan(BIAS_SHIFT_pd/0.15)*57.2958
ZONE_WIDTH_deg = [6.65,
		  4.95,
                  3.81
                  ]




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
        #print(center)
        print("Loading existing coordinates: %f, %f"%(center[0][0],YCENTER))
        dc['cx'],dc['cy'] = (center[0][0],YCENTER)
    else:
        if not os.path.exists(dc['logpath']): 
             os.makedirs(dc['logpath']) # For a new subject create a folder first!
        print("This is a new subject. Center position saved.")
        dc['cx'], dc['cy'] = robot.rshm('x'), YCENTER
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
    """ Start main program, taking <Enter> button as input-event """

    if dc["active"]:  # Is the test already running?
        print("##Error## Already active! -- aborting")
	return

    # First, check whether the entry fields have usable text (need subjID, a file number, etc.)
    if not subjid.get() or not filenum.get().isdigit():
        print("##Error## Subject ID and/or file numbers are empty or file number is not a digit!")
        return

    dc["active"]             = True # flag stating we are currently running
    dc['task']               = varopt.get().split()[0]  # task type
    dc['lag']                = varopt.get().split()[2]  # lag type
    dc["subjid"]             = subjid.get()
    dc["filenum"]            = int(filenum.get())
    dc['logfileID']          = "%s%i"%(dc["subjid"],dc["filenum"])
    dc['logpath']            = '%s/data/%s_data/'%(mypwd,dc["subjid"])
    dc['logname']            = '%smotorLog_%s'%(dc['logpath'],dc['logfileID'])
    dc['bbias']              = []   # deviations during baseline to compute bias
    dc['angle_maxv_history'] = [] # list that we will use as a history of previous maxv_angles (not shifted!)
    dc['scores']             = 0    # have to reset the score to 0 for each run!
    dc['curtrial']           = 0    # initialize current test trial
    dc['subjd']              = 0    # initialize robot distance from the center of start position
    dc['david']              = 0    # ?
    dc["PDmaxv"]             = np.nan
    
    # Now we will check whether log files already exist to prevent overwritting the file!
    if os.path.exists("%s.txt"%dc['logname']):
        print ("File already exists: %s.txt"%dc["logname"] )
    	dc["active"]    = False # mark that we are no longer running
        return

    # Now we will read the design file, which tells us what trials to run
    # and which targets are in each trial etc.
    #print filepath
    #stages = read_design_file(filepath) # Next stage depends if file can be loaded
    # No need to load JSON design file!!!!!

    # Disable the user interface so that the settings can't be accidentally changed.
    master.update()

    # Capture the center position for new subject or load an existing center position. 
    # New subject has been instructed beforehand to place the hand in the center position.
    getCenter()
    # Go to the center position
    goToCenter(MOVE_SPEED*1.5)
    showStart("white")    # Display the center (start) circle  
    GoSignal()

    global traj_display
    print "cleaning canvas"
    # remove old trajectory from the GUI if it's there
    if traj_display!=None: 
        wingui.delete("traj")

    dc['session'] = 1 if(dc['filenum'] < 7) else 2
    #If we change number of blocks per session WE NEED TO CHANGE THIS !!!

    # Compute how much we shift the baseline for this particular subject
    # Shift the reward zone based on the baseline bias. The new PDy would be w.r.t the 
    # shifted reward zone. This shift applies to both training and post_test.
    # [Jul 10] Crucial update: the shift is set to be always towards the actual 45 deg. 
    #          That is, if the bias sign is -ve, the shift should be +ve.
    if dc['task'] in ("training", "motor_post"): 
        dc["baseline_pd_shift"] = bbias.get() - np.sign(bbias.get())*BIAS_SHIFT_pd
        print ("  Reward zone has shifted for %f"%(BIAS_SHIFT_pd + bbias.get()))
    else:
        dc["baseline_pd_shift"] = 0
    

    # Compute how much the angle is shifted for this particular subject.
    # Note that we will shift towards 45 degrees.
    # TODO: This needs to be made accurate (currently it uses code that
    # is for shifting a PD but we need to make sure that the numbers
    # actually make sense, etc.)
    if dc['task'] in ("training", "motor_post"): 
        dc["baseline_angle_shift"] = bbias.get() - np.sign(bbias.get())*BIAS_SHIFT_deg
        print ("  Reward zone has shifted for %f"%(dc["baseline_angle_shift"]))
    else:
        dc["baseline_angle_shift"] = 0


    # Only when filenum = 0 we run familiarization trials for a straightahead direction. 
    # Once set, we're ready for the main or actual test (filenum > 0).
    if dc["filenum"] == 0:
        prepareCanvas()       # Prepare drawing canvas objects
        print("\nEntering Practice Block now.........\n")
        runPractice()   
    else:
        prepareCanvas()       # Prepare drawing canvas objects
        print("\nEntering Test Block now.........\n")
        # Once set, we're ready for the actual test!
        runBlock()



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


# Run only for the first time: familiarization trials with instructions. 
# This simple block is executed in sequence...

def runPractice():
    global repeatFlag
    global angle
    x,y = robot.rshm('x'),robot.rshm('y')
    showCursorBar(0, (x,y), "yellow", 0)

    # Setting this to NAN so that we don't get an error when we write the log file
    dc["reward_width_deg"] = np.nan

    #----------------------------------------------------------------
    print("\n--- Practice stage-1: Yellow cursor, occluded arm")
    #playInstruct(1)
    robot.stay_fade(dc['cx'],dc['cy'])
    time.sleep(FADEWAIT)

    # Keep looping until <Esc> key is pressed
    while repeatFlag:
        # Note: To *fade out* the forces instead of releasing all of a sudden
        # First read out current x,y robot position
        x,y = robot.rshm('x'),robot.rshm('y')
        # Compute current distance from the center/start--robot coordinate! 
        dc['subjd'] = math.sqrt((x-dc['cx'])**2 + (y-dc['cy'])**2)
        showCursorBar(0, (x,y), "yellow", 0)
        time.sleep(0.01)

    goToCenter(MOVE_SPEED) # Bring the arm back to the center first

    #----------------------------------------------------------------
    # Use a straight-ahead direction for familiarization trials
    angle = 0   
    showTarget(angle)

    print("\n--- Practice stage-2: Move towards target bar\n")
    dc['task'] = "motor_pre"
    triallag = 1
    #repeatFlag = True
    #playInstruct(2)
    #while repeatFlag:
    for each_trial in range(1,10):
        # This is the point where subject starts to move to the target
        to_target(angle)    
        # Go back to center and continue to the next trial.
        return_toStart(triallag)
        each_trial = each_trial + 1

    #----------------------------------------------------------------
    robot.stay()
    repeatFlag = True
    print("\n--- Practice stage-3: Exploring the space\n")
    print("\n###  Press <Esc> after giving the instruction...")
    while repeatFlag:
        master.update_idletasks()
        master.update()
        time.sleep(0.01)  # loop every 10 sec

    #playInstruct(3)
    #repeatFlag = True
    #while repeatFlag:
    for each_trial in range(1,5):
        # This is the point where subject starts to move to the target
        to_target(angle)    
        # Go back to center and continue to the next trial.
        return_toStart(triallag)

    #----------------------------------------------------------------
    robot.stay()
    repeatFlag = True
    print("\n--- Practice stage-4: Training with feedback\n")
    print("\n###  Press <Esc> after giving the instruction...")
    while repeatFlag:
        master.update_idletasks()
        master.update()
        time.sleep(0.01)  # loop every 10 sec
        
    #repeatFlag = True
    fdback = 1
    dc["reward_width_deg"] = 7.59 # reward width (deg) corresponding to 2 cm (at 15 cm reach length)
    #playInstruct(4)
    #while repeatFlag:
    for each_trial in range(1,15):
        to_target(angle,fdback)
        return_toStart(triallag)
    
    #----------------------------------------------------------------
    repeatFlag = True
    robot.stay()
    print("\n--- Practice stage-5: Training, feedback, and WM Test\n")
    print("\n###  Press <Esc> after giving the instruction...")
    while repeatFlag:
        master.update_idletasks()
        master.update()
        time.sleep(0.01)  # loop every 10 sec

    #repeatFlag = True
    dc['task'] = "training"
    fdback = 1
    triallag = 1  # Just test lag-1

    #playInstruct(5)
    #while repeatFlag:
    for each_trial in range(1,20):
        # This is the point where subject starts to move to the target....
        to_target(angle,fdback)
        # Go back to center and continue to the next trial.
        return_toStart(triallag)

    print("\n\n#### Familiarization block has ended! Press QUIT button now.....")
    dc["active"] = False # flag stating we are currently running



    

## Update [May9,2017]: I decided to move away from the exper_design used in the legacy Tcl
## code. Here, I'll declare those at the beginning of the code as constants!
    
def runBlock():
    """ The actual test runs once 'Start' or <Enter> key is pressed """

    global repeatFlag  # This is a reminder what to do before start the actual test!
    repeatFlag = True
    print("\n\n###  WARNING: If this is a Training or Motor_Post block, ensure that the Test Angle,")
    print("###  Baseline Bias, and Reward Width are properly set! Kindly press <Esc> to continue......\n\n")
    while repeatFlag:
        master.update_idletasks()
        master.update()
        time.sleep(0.01)  # loop every 10 sec

    # Reference: straight-ahead is defined as 90 deg
    #global test_angle
    triallag = 1 if dc['lag'] == "lag-1" else 2
    #angle = test_angle[triallag-1] # index of a shuffled list
    global angle
    angle = vardeg.get()

    saveLog(True)    # Write column headers in the logfile (Jun9)   

    # Set other experiment design parameters. Look how I check for two string options!!
    #rbias  = [NEGBIAS,POSBIAS]
    tempbias = varwidth.get()  ## [Jul 12] this is for different reward width for different training block!
    rbias  = [-tempbias/2, tempbias/2]
    dc["reward_width_deg"] = varwidth.get() ## the experimenter selects the target width from a dropdown box

    fdback = 0 if dc['task'] in ("motor_pre", "motor_post") else 1
    ntrial = NTRIAL_MOTOR if dc['task'] in ("motor_pre", "motor_post") else NTRIAL_TRAIN

    print("Start testing: %s, with angle %d and lag-%d"%(varopt.get(),angle,triallag))
    global nsince_last_test
    nsince_last_test = 0

    # Now start logging robot data: post, vel, force, trial_phase; 11 columns
    robot.start_log("%s.dat"%dc['logname'],11)

    # ---------------- RUNNING FOR EACH TRIAL IN THE BLOCK ------------------
    for each_trial in range(1,ntrial+1):
        dc['curtrial'] = each_trial

        # David St-Amand added this:
        if dc['task'] in ("motor_pre"): 
             dc['david'] = each_trial 
        elif dc['filenum'] < 7:
	     dc['david'] = NTRIAL_TRAIN*(dc["filenum"]-2) + NTRIAL_MOTOR + each_trial
	elif dc['filenum'] > 7:
	     dc['david'] = NTRIAL_TRAIN*(dc["filenum"]-8) + NTRIAL_MOTOR + each_trial
	else:
	     dc['david'] = 0
        
        print("\nNew Round %i ----------------------------------------------"%each_trial)
         
        to_target(angle,fdback,rbias) # Part 1: Reaching out to target!!
        return_toStart(triallag)      # Part 2: Moving back to center!!
        saveLog()                     # Finally, save the logged data!             
    # ----------------------------------------------------------------------

    #print dc['bbias']
    #print("\n[Note:] Subject's MEAN raw bias:     %.5f DON'T USE THIS"%np.mean(dc['bbias']))
    #print("\n[Note:] Subject's MEDIAN raw bias:   %.5f DON't USE THIS"%np.median(dc['bbias']))
    print("\n[Note:] Subject's MEAN   angle at vmax: %.5f deg (DON'T USE THIS)"%np.mean  (dc['angle_maxv_history']))
    print("\n[Note:] Subject's MEDIAN angle at vmax: %.5f deg"                 %np.median(dc['angle_maxv_history']))
    print("\n\n#### Test has ended! You may continue or QUIT now.....")
    
    robot.stop_log()   # Stop recording robot data now!
    time.sleep(2)
    robot.stay_fade(dc['cx'],dc['cy'])  # To release robot_stay

    master.update()
    dc["active"]    = False   # allow running a new block


def to_target(angle, fdback=0, rbias=[0,0]):
    """ Part 1: This handles the whole trial segment when subject moves to hidden target 
    It formally takes 3 inputs: angle, whether you want to show feedback (reward), and 
    maximum negbias and posbias to receive feedback. By default, feedback is not shown.
    """
    dc['subjx']= 0;  dc['subjy']= 0
    vmax = 0  # maximum velocity of the movement

    # (1) Wait at center or home position first before giving the go-ahead signal.
    win.itemconfig("start",fill="white")
    showTarget(angle)
    reach_target = False

    # Release robot_stay() to allow movement in principle, but we haven't given 
    # subjects the signal yet that they can start moving.
    #robot.controller(0)
    showCursorBar(angle, (dc['cx'],dc['cy']))
    # Note: To *fade out* the forces instead of releasing all of a sudden
    robot.stay_fade(dc['cx'],dc['cy'])
    time.sleep(FADEWAIT)

    while not reach_target: # while the subject has not reached the target
        
        # (2) First get current x,y robot position and update yellow cursor location
        x,y = robot.rshm('x'),robot.rshm('y')
        dc['subjx'], dc['subjy'] = x, y
        # Compute current distance from the center/start--robot coordinate! 
    	dc['subjd'] = math.sqrt((x-dc['cx'])**2 + (y-dc['cy']) **2)
        showCursorBar(angle, (x,y))
    	#print("Distance from center position= %f"%(subjd))

        vx, vy = robot.rshm('fsoft_xvel'), robot.rshm('fsoft_yvel')
        vtot = math.sqrt(vx**2 + vy**2)
        #print("Original: %f , Floris': %f"%(vtot,robot.rshm('fvv_vel')))
        #print(robot.rshm('fvv_trial_phase'))
        samsung.update()

        # [Jun19] Ananda added this to get x,y positions during the maximum velocity...
        if vmax < vtot: 
            vmax = vtot
            dc['subjxmax'], dc['subjymax'] = x-dc["cx"],y-dc["cy"] # update the x,y position of the subject at maximum velocity, RELATIVE TO THE CENTER
            
        # (3) When the hand was towards the center (start), check if the subject is 
        # holding still inside the start position.
        if robot.rshm('fvv_trial_phase')==1:  
            if dc["subjd"]< START_SIZE and vtot < 0.01:
                #win.itemconfig("start", fill="green")
                golabel.place(x=850,y=100)   # Show the "Go" signal here.......
                wingui.itemconfig("rob_pos",fill="yellow")
                master.update()
                robot.start_capture()   # Start capturing trajectory (for a later replay!)  

            # (4) If more or less stationary in the start position, check if the subject 
            # has left the start position. Timer to compute movement speed begins. 
            elif dc["subjd"] > 0.01:
                start_time = time.time()
                robot.wshm('fvv_trial_phase', 2)
                golabel.place(x=-100,y=-100)   

        # (5) If the subject has reached the the target, check if the subject has moved 
        # sufficiently far AND is coming to a stop.   
        elif robot.rshm('fvv_trial_phase')==2:
            if dc["subjd"] > 0.8*TARGETDIST and robot.rshm('fvv_vel') < 0.03:
                #If yes, hold the position and compute movement speed.     
                robot.wshm('fvv_trial_phase', 3)
                robot.stay() # This automatically stops capturing the trajectory!
                master.update()
                dc['speed'] = 1000*(time.time() - start_time)
                print("  Movement duration = %.1f msec"%(dc['speed']))
                filter_traj()   # Filter the captured trajectory (when stop capturing!)
            
            ## 4sec timeout if cannot/never reach the target
            if (time.time()-start_time) > 4:
                master.update()
                goToCenter(MOVE_SPEED)
                time.sleep(0.1)
                
        elif robot.rshm('fvv_trial_phase')==3:
            # (6) Once reached the target, check end-point accuracy
            checkEndpoint(angle, fdback)
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


def return_toStart(triallag):
    """ This handles the segment when hand position moves back to the center (start). It depends 
    on whether the current block is training block, and current trial is a WM test trial.
    """
    
    if "most.recent.traj" in dc: ############################
	#print("Drawing previous trajectory")
	# Draw the trajectory, the most recent one!
	trajectory = dc["most.recent.traj"]
 	# downsample the list a little and convert to screen coordinates
  	coords = [ rob_to_gui(x,y) for (x,y) in trajectory[::10] ] 

    	global traj_display
	if traj_display!=None: # remove old trajectory from the GUI if it's there
	    #wingui.delete(traj_display)
            wingui.itemconfig(traj_display,fill="gray",width=1)  # or make it grey!

        # draw a new line with a tag...
    	traj_display = wingui.create_line(*coords,fill="green",width=3,tag="traj")


    global nsince_last_test
    
    # Check if this is a training block and if the next trial is test trial to replay 
    # trajectory with a certain probability 

    if (dc['task'] == "training") & (random.random() < p_test(nsince_last_test)): 
       master.update()
       # First, retrieve the desired test trajectory to replay...
       select_traj(triallag)
       # Then get the first element indicating where to start the replay
       firstx,firsty = dc['ttraj'][0]
       print("\nMoving to starting point %f, %f\n"%(firstx,firsty))
       #print traj[150]
       #print traj[210]
       #print traj[230]
            
       # Note: If the next trial is a replay, it should go instead to 
       # the first position recorded, not the center position.
       robot.move_stay(firstx, firsty, MOVE_SPEED)
       showImage("test_trial.gif",630,150,1.5)
            
       # If this is test trial, now replay the rotated trajectory [left/right]
       time.sleep(0.5)
       replay_traj(True)
            
       # (7) Wait for subject's response, then go back to the center position!
       RT = doAnswer()
       goToCenter(MOVE_SPEED*0.5)
       nsince_last_test = 0
 
    else: # (8) Return to the center immediately if NOT a replay or NOT a training block.
       nsince_last_test = nsince_last_test + 1
       #print nsince_last_test
       goToCenter(MOVE_SPEED)
       dc['ref'], dc['answer'], RT = 'no_wm','no_wm',0

    # (9) We concatenate the logfile content with the WM test response
    dc['logAnswer'] = "%s,%d,%s,%s,%s,%d,%d\n"%(dc['logAnswer'],triallag,dc['ref'],dc['answer'],dc['task'],RT,ROT_MAG)
 
            

# This function computes the PD at the max velocity during movement! [Jun19]
def kinmax():
    """ This function is deprecated, courtesy of FVV July; the reason is
    that we need to know only the (x,y) at maximum velocity; the rest, angles
    etc we can calculate after the trial has ended. """
    #dc['subjxmax'], dc['subjymax'] = robot.rshm('x'),robot.rshm('y')
    #global angle  

    # The idea is to rotate back to make it a straight-ahead (90-deg) movement!
    # The return values are in the robot coordinates
    #trotx,troty  = rotate([(dc['subjxmax'], dc['subjymax'])], (dc['cx'],dc['cy']), -angle)[0]
    #PDy   = trotx-dc['cx']
    #dc['PDmaxv'] = PDy

    ## Compute angular deviation. Note: Should use trot as well!
    #dc['Theta_maxv'] = math.atan2(troty,trotx)*180/math.pi - (angle+90)
    #dc['Theta_maxv'] = math.atan2(troty,trotx)*180/math.pi - (angle+90)  # w.r.t to ideal direction
    #print "PDy at maximum velocity %f"% PDy
    #print "Angle at maximum velocity %f"% dc['Theta_maxv']
    pass

                

# This function saves logfile and mkdir if needed. 
# Column header is written only at the beginning! Change/add the field names if required.
def saveLog(header = False):
    # Making a new directory has been moved to getCenter()...
    #if not os.path.exists(dc['logpath']): os.makedirs(dc['logpath'])
    with open("%s.txt"%dc['logname'],'aw') as log_file:
        if (header == False):
            print("Saving trial log.....")
            log_file.write(dc['logAnswer'])  # Save every trial as text line
        else:
            print("Creating logfile header.....")
            log_file.write("%s\n"%("Trial_block,trial,PDy,target_line_angle,boom,amount_shifted_deg,tx,ty,speed,first_bias,PDy_shifted,PDvmax,angle_maxv_deg,angle_maxv_shift,maxv_target_width_deg,x_maxv,y_maxv,version,reward_width,session,lag,ref_answer,subj_answer,task,WM_RT,rot_angle"))


def doAnswer():
    start_time = time.time()  # To count reaction time
    global ANSWERFLAG
    print("Waiting for subject's response")
    while (not ANSWERFLAG):
        master.update_idletasks()
        master.update()
        time.sleep(0.3)
    RT = 1000*(time.time() - start_time)  # RT in m-sec
    print "--- ANSWER: %s    RT:%d"%(dc['answer'],RT)
    ANSWERFLAG = 0
    return(RT)


def select_traj(dd=1):
   """ This is to select which of the previous trajectory to play [ananda, May2017]
   The way it works is as follows: suppose nsince_last_test=4, then: 
         lag-1 trial corresponds to replaying 'traj3', nsince_last_test=4 
         lag-2 trial corresponds to replaying 'traj2', nsince_last_test=3 
         lag-3 trial corresponds to replaying 'traj1', nsince_last_test=2 
         lag-4 trial corresponds to replaying 'traj0', nsince_last_test=1 
   To avoid getting out of index, we set the maximum lag to nsince_last_test
   """
   global nsince_last_test
   if dd > nsince_last_test: dd = nsince_last_test
   #print nsince_last_test
   #print dd
   t = nsince_last_test - (dd-1)
   print "Retrieving trajectory %d"%(t)
   dc['ttraj'] = dc['traj%d'%t]



def replay_traj(rotate_flag = True):
    """ This function handles the replay of the trajectory. Depending whether
    rotate_flag is True, it will either play the normal or rotated trajectory.
    After each replay, it will also bring the subject hand back to center."""

    # First, get the Test Trajectory to play from the dict.
    traj = dc['ttraj']

    if rotate_flag:
        # Flip coin whether +5deg or -5deg rotation. Convention: Positive angle is CCW (to the left)! 
        rot_angle = random.choice([-1,1]) * ROT_MAG 
        traj_rot  = rotate(traj, (dc['cx'],dc['cy']), rot_angle)
        print("ROTATING the trajectory in robot coords, %d degree"%(rot_angle))
        # The rotated trajectory is in the list of tuples....
        #print traj_rot[150]
        #print traj_rot[210]
        #print traj_rot[230]
        
        # Push the clean trajectory back to the robot memory for replaying 
        # (and set the final positions appropriately)
        robot.prepare_replay(traj_rot)
        dc['ref'] = 'left' if(np.sign(rot_angle) > 0) else 'right'

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



def p_test(nn):  # nn = number of trials since the last WM test trial
    if   nn==0: return 0
    elif nn==1: return 0
    elif nn==2: return 0
    elif nn==3: return 0
    elif nn==4: return 0.2
    elif nn==5: return 0.4
    elif nn==6: return 0.6
    else: return 0.8


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
    global nsince_last_test
    print("Filtering raw trajectory %d..."%nsince_last_test)
    raw_traj = list(robot.retrieve_trajectory()) 
    #robot.prepare_replay(raw_traj)
    # separate them into x and y component
    x,y = zip(*raw_traj)
    #velocity_check(x,y)
    # Smooth it
    xfilt,yfilt = smooth(x),smooth(y)

    # Trick: save it with a key name according to nsince_last_test
    filtered_traj = list(zip(xfilt,yfilt))
    robot.prepare_replay(filtered_traj) # send the smoothed trajectory to the robot to be replayed (later)
    dc["traj%d"%(nsince_last_test)] =  filtered_traj
    dc["most.recent.traj"]=filtered_traj


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



def checkEndpoint(angle, feedback):
    """ The function checks whether the movement direction is within the desired angular 
    range (degree). The reward zone width was originally defined by a neg/pos bias w.r.t the 
    actual target center. Currently, the width is defined by an angular range. 
    Additionally, the function WRITES trial information into the logfile.

    """

    print("  Checking end-position inside target zone?")
    
    # Now let's first look at the subject movement endpoint.
    # The idea is to rotate back to make it a straight-ahead (90-deg) movement!
    # The return values are in the robot coordinates. Both tx and ty are the endpoint coordinate.
    tx,ty = dc['subjx'], dc['subjy']
    trotx,troty  = rotate([(tx,ty)], (dc['cx'],dc['cy']), -angle)[0]

    # CONVENTION: -ve value means error to the left (CCW), +ve means error to the right (CW).\
    # PDy is computed as the lateral deviation at the movement endpoint
    PDy   = trotx-dc['cx']

    tzx,tzy = tx-dc["cx"],ty-dc["cy"] # translate the subject endpoint so that it is relative to the starting point

    # Now we compute the maximum velocity point and rotate it in a similar way as
    # above, so that straight ahead means towards the target.
    # Compute the angle at maximum velocity, with zero being straight towards the
    # target line and with positive angles meaning counter-clockwise deviation.
    # So notice here no shift is being applied yet; this is a fairly raw angle.
    #dx,dy = dc["subjxmax"],dc["subjymax"] # compute the vector from the center to the vmax point
    dc['angle_maxv_deg'] = math.atan2(dc["subjymax"],dc["subjxmax"])*180/math.pi - 90 - angle # compute the angle of that vector in radians
    if dc["angle_maxv_deg"]<-180: dc["angle_maxv_deg"]+=360

    # Now shift the angle so that zero means the center of the target area.
    dc['angle_maxv_shift'] = dc['angle_maxv_deg'] - dc['baseline_angle_shift']

    # Compute the PDy value after applying the baseline shift (if applicable)
    PDy_shift =  PDy - dc["baseline_pd_shift"]

    dc['PDend'] = PDy_shift

    # Ananda added PDmaxv and angular deviation.
    print "Theta at max velocity          = %f deg" % dc['angle_maxv_deg']
    print "Theta at max velocity, shifted = %f deg" % dc['angle_maxv_shift']
    print "PD at max velocity             = %f" % dc['PDmaxv']
    print "PD at endpoint, shifted        = %f" % PDy_shift
    dc['bbias'].append(PDy)
    dc['angle_maxv_history'].append(dc['angle_maxv_deg']) # keep this angle for future reference
    

    # Show explosion? Check the condition to display explosion when required.
    if feedback and abs(dc["angle_maxv_shift"]*2) < dc["reward_width_deg"]:
        # This trial got rewarded!
        #if dc['angle_maxv_shift'] > rbias[0] and dc['Theta_maxv_shift']< rbias[1] and feedback:
        status = 1  # 1: rewarded, 0: failed
        dc['scores'] = dc['scores'] + 10
        print "  EXPLOSION!  Current score: %d"%(dc['scores'])
        showImage("Explosion_final.gif",960,140,0.5)  
        showImage("score" + str(dc['scores']) + ".gif",965,260,0.5)
    else:
        # This trial does not get rewarded
        time.sleep(WAITTIME)
	status = 0

    # IMPORTANT = We build a string for saving movement kinematics & reward status--revised!
    dc['logAnswer'] = "%d,%d,%.5f,%d,%d,%.5f,%.5f,%.5f,%d,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%s,%f,%d"% \
                      (dc['curtrial'], dc['david'], PDy, angle, status, dc['baseline_angle_shift'], tzx, tzy, dc['speed'], bbias.get(), PDy_shift, dc['PDmaxv'], dc['angle_maxv_deg'], dc['angle_maxv_shift'], dc["reward_width_deg"], dc["subjxmax"], dc["subjymax"], VER_SOFT, POSBIAS-NEGBIAS, dc['session'])


############ Added this explanation because we added too many variables to save!! #############
#  Trial_block = Trial number in each block
#  trial = Running trial number for all blocks, starting from block 1
#  PDy = PD w.r.t actual reference direction (45 deg left or right)
#  target_line_angle = reference direction (45 deg left or right)
#  boom = explosion, successfully hit the reward zone
#  amount_shifted_deg = how far the shifted target center is from the reference direction
#  tx = movement end-point X coordinate
#  ty = movement end-point Y coordinate
#  speed = movement completion time (sec)
#  first-bias = subject’s baseline bias
#  PDy_shifted = PD w.r.t the shifted target center (cm)
#  PDvmax = PD measured at max. velocity (cm)
#  angle_maxv_deg = Angular deviation at max. velocity (deg)
#  angle_maxv_shift = Angular deviation at max. velocity w.r.t the shifted target center (deg)
#  maxv_target_width_deg = width of the reward zone at the max. velocity
#  x_maxv = X coordinate at maximum velocity
#  y_maxv = Y coordinate at maximum velocity
#  version = software revision
#  reward_width = the width of the reward zone measured at the target bar
#  session = either session 1 or 2
#  file = file number, which also coincides with the block number




######## Some parameters that specify how we draw things onto our GUI window

from Tkinter import * # Importing the Tkinter library
master  = Tk()	      # Create an empty background window for GUI
samsung = Toplevel()  # Create another one, for the robot canvas (Samsung)
                      # Interesting, you shouldn't have 2 Tk() instances, use Toplevel()
	              # and this will solve the problem of pyimage not displayed

master.geometry('%dx%d+%d+%d' % (550, 540, 500, 200)) # Nice GUI setting: w,h,x,y   
master.title("Reward-based Sensorimotor Learning")
master.protocol("WM_DELETE_WINDOW", quit)  # When you press [x] on the GUI

subjid  = StringVar()
filenum = StringVar()
mymsg   = StringVar()
varopt  = StringVar()
bbias   = DoubleVar()
vardeg  = IntVar()
varwidth = DoubleVar()
playAudio = BooleanVar()

# Trick: Because LCD screen coordinate isn't the same as robot coordinate system, 
# we need to have a way to do the conversion so as to show the position properly.

#coeff = "9.645104e+02,1.884507e+03,5.187605e+01,2.876710e+02,1.863987e+03,4.349610e+01".split(',')
coeff = "9.781831e+02,1.838148e+03,4.368059e+02,2.120721e+02,1.827717e+03,3.235548e+02".split(',')

def rob_to_screen(robx, roby):
    px = float(coeff[0]) + float(coeff[1])*robx #- float(coeff[2])*robx*roby
    py = float(coeff[3]) + float(coeff[4])*roby #- float(coeff[5])*robx*roby
    return (px,py)
    # Sometimes calib is inaccurate. Hand cursor is off-center. Why?!


# For canvas on the main GUI to draw subject's trajectory
cw,ch = 550,400
robot_scale = 600


def rob_to_gui(x,y):
    # Convert robot coordinates into canvas coordinate on the GUI
    return (cw/2 + x*robot_scale, ch/2 - y*robot_scale)


def mainGUI():
    # Create two different frames on the master -----
    topFrame = Frame(master, width=550, height=100)
    topFrame.grid(column=0, row=1)
    #frame.bind('<Left>', leftKey)
    bottomFrame = Frame(master, bg="white")
    bottomFrame.grid(column=0, row=4, pady=15)
    
    # Important: This maintains frame size, no shrinking
    topFrame.pack_propagate(False)
    bottomFrame.pack_propagate(False)
    
    # Make Entry widgets global so that we can configure from outside 
    # TODO: This is a bad practice!   
    global e5, e7

    # Entry widget for 1st row --------------
    Label(topFrame, text="Subject ID: ").grid(row=0, sticky=E, pady=10)
    e1 = Entry(topFrame, width = 6, bd =1, textvariable = subjid)
    e1.grid(row=0, column=1)
    #e1.insert(END, "aes")
    e1.focus()
    Label(topFrame, text="File Number: ").grid(row=0, column=3, padx=(40,0))
    e2 = Entry(topFrame, width = 3, bd =1, textvariable = filenum)
    e2.grid(row=0, column=4)
    e2.insert(END, "0")
    
    # Entry widget for 2nd row --------------
    Label(topFrame, text="Experiment Phase: ").grid(row=1, sticky=E)
    e4 = OptionMenu(topFrame, varopt, "motor_pre + lag-1", 
                                      "training + lag-1",
                                      "motor_post + lag-1", 
                                      "motor_pre + lag-2", 
                                      "training + lag-2", 
                                      "motor_post + lag-2", command=OptionSelectEvent)
    e4.grid(row=1, column=1, columnspan=3, sticky=W)
    varopt.set("motor_pre + lag-1")      # set default value

    # Entry widget for 3rd row --------------
    Label(topFrame, text="Baseline Bias: ").grid(row=2, sticky=E)
    e5 = Entry(topFrame, width = 9, state='disabled', bd =1, textvariable = bbias)
    e5.grid(row=2, column=1, columnspan=3, sticky=W, pady=8)
    e5.insert(0,0)

    #chk = Checkbutton(topFrame, text="play Audio?", variable=playAudio)
    #chk.grid(row=2, column=3, sticky=E)

    # Entry widget for 4th row [new: May 23] --------------
    #Label(topFrame, text="Hello",textvariable=mymsg).grid(row=4, sticky=E)
    Label(topFrame, text="Test Angle: ").grid(row=2, column=3, sticky=E)
    e6 = OptionMenu(topFrame, vardeg, *test_angle)
    e6.grid(row=2, column=4, columnspan=3, sticky=W, pady=8)
    vardeg.set("-45")      # set default value

    # Make a menu where the experimenter can select the reward zone width.
    Label(topFrame, text="Reward Width (deg): ").grid(row=3, sticky=E)
    e7 = OptionMenu(topFrame, varwidth, *(ZONE_WIDTH_deg))   # use * to get the items
    e7.grid(row=3, column=1, columnspan=2, sticky=W)
    varwidth.set(0.010)    # set default value

    # Create buttons ---------------
    myButton1 = Button(bottomFrame, text="START", bg="#0FAF0F", command=clickStart)
    myButton1.grid(row=0, padx = 15)
    myButton2 = Button(bottomFrame, text=" QUIT ", bg="#AF0F0F", command=quit)
    myButton2.grid(row=0, column=2, padx = 15, pady = 5)

    # [May22] Coded a canvas to allow us check the subject's trajectory on the go!!
    global wingui
    wingui = Canvas(master, width=cw, height=ch)
    wingui.grid(column=0, row=5)  # Put on 5th row?
    wingui.create_rectangle(0, 0, cw, ch, fill="black")
    minx,miny = rob_to_gui(-.4,-.2)
    maxx,maxy = rob_to_gui( .4,.3)
    wingui.create_rectangle(minx,miny,maxx,maxy, outline="blue")
    wingui.create_oval(cw/2,ch/2,cw/2,ch/2,fill="blue",tag="rob_pos")



def draw_robot():
    global wingui
    cursor_size = 5
    # Update the cursor that indicates the current position of the robot
    rx,ry = robot.rshm("x"),robot.rshm("y")
    #print(rx,ry)
    x,y = rob_to_gui(rx, ry)
    wingui.coords("rob_pos",(x-cursor_size,y-cursor_size,x+cursor_size,y+cursor_size))
    wingui.itemconfig("rob_pos",fill="blue")



def clickStart(): # GUI button click!
    enterStart(True)


def OptionSelectEvent(event):
    # This is to extract the test type and lag of the current task which will determine
    # the type of test parameters, e.g. angle.
    temp = varopt.get().split()
    dc['task'] = temp[0]
    dc['lag']  = temp[2]
    e5.config(state='normal') if (temp[0]=="training") else e5.config(state='disabled')


def clickYes(event):
    global ANSWERFLAG
    print "Left key pressed to answer LEFT!"
    dc['answer']= 'left'
    ANSWERFLAG = 1

def clickNo(event):
    global ANSWERFLAG
    print "Right key pressed to answer RIGHT!"
    dc['answer']= 'right'
    ANSWERFLAG = 1

def contPractice(event):
    ### Pressing <Esc> will quit the while-loop of a current practice stage then move 
    ### to the next practice stage. <Esc> key has no effect during ACTUAL TASK!
    global repeatFlag
    repeatFlag = False



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

    # Also create a target in the experimenter's GUI
    wingui.create_polygon([0,0,0,1,1,1,0,0], fill="black", width = 10, tag="target")


    

def showCursorBar(angle, position, color="yellow", barflag=True):
    """ Draw the cursor at the current position if still inside the start circle and draw 
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



def showTarget(angle, color="#656565"):
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

    # Now also show the target bar in the experimenter's GUI screen
    gui_xy    = [rob_to_gui(x,y) for x,y in rot_item]
    gui_tuple = tuple([ item for sublist in gui_xy for item in sublist ])
    wingui.coords    ("target", *gui_tuple)     # Edit coordinates of the canvas object
    wingui.itemconfig("target",fill=color)  # Show the target by updating its fill color.
    
    samsung.update()         # Update the canvas to let changes take effect


def rotate(coords, pivot, angle):
    """ Rotate the point(x,y) in coords around a pivot point by the given angle. Coordinates
    to be rotated and pivot points will be converted to complex numbers.
    Arguments:
        coords: list of tuples (x,y)  <- important!! 
        pivot : pivot point of reference
        angle : angle, in degree

    Output:
        returns a list of rotated tuples in the ROBOT coordinates by default.

    Convention: 
        +ve angle means CCW, rotation to the left.
        -ve angle means CW, rotation to the right    """

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


def GoSignal(name="go_signal.gif",px=-100,py=-100):
    """ Updated: May 20, this creates an image for the subject to start moving!"""
 
    global golabel  # so we can access it from elsewhere!
    go_signal = PhotoImage(file=mypwd + "/pictures/" +name)
    golabel = Label(win, bg="black", image=go_signal)
    golabel.image = go_signal # keep a reference!
    golabel.place(x=px, y=py)
    samsung.update()



master.bind('<Return>', enterStart)   # If user presses ENTER then go to [enterStart]
master.bind('<Left>'  , clickYes)
master.bind('<Right>' , clickNo)
master.bind('<Escape>', contPractice)

os.system("clear")


######### This is the entry point when you launch the code ################

robot.load() # Load the robot process
print("\nRobot successfully loaded...\n")

robot.zeroft()

#print("---Now reading stiffness\n")
#robot.rshm('plg_stiffness')

#dc['subjx'],dc['subjy'] = robot.rshm('x'),robot.rshm('y')

print("\n\nPress START or <Enter> key to continue\n")

global traj_display
traj_display = None

mainGUI()
robot_canvas()

keep_going   = True

while keep_going:
    # Although it maintains a main loop, this routine blocks! Use update() instead...
    #master.mainloop()
    #draw_robot()
    master.update_idletasks()
    master.update()
    #time.sleep(0.04) # 40 msec frame-rate of GUI update




