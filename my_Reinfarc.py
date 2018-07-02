#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 18 15:24:50 2017 @author: ae2010

Revisions: Improved Reinforcement paradigm based on the discussion (Aug 18). Target bar and yellow line are removed. 
We use an arc as a reference target that will only be shown during familiarization trials. In the actual trials, no visual 
inputs will be displayed except the GO signal and the explosion to indicate the desired direction we want. Subjects
will be asked to explore the wanted direction. Task is adjusted to be more Reinforcement and WM is probeds trial-by-trial!

Revisions : Finalizing the working script (Aug 25)
            Major clean up, making the code more readable; cleaning unnecessary logfile variables (Aug 29/30)
            Introducing instruction audio files again (Sept 4)
            Minor miscellaneous edits (Sept 11)
            GUI: User has to select which lag and workspace. Filenum and experimental phase are fixed in the code (Sept 14)
            Setting up the WM test portion again; incorporating this during practice session too (Sept 14)
            Added a flag to prevent pressing LEFT/RIGHT twice. Cleaning up clutter on the terminal (Sept 21)
            Minor edits (Oct 2)
            Minor edits on trial-lag option and p_test(nn) function to reduce # WM trials (Nov 15)   
            Recalibrate encoders, update cal file (Floris). Update the rob_screen mapping using pickle (Moh).
            System migration to "Weasel". Cleaning the way we bailout main loop during quit/exit (Jul 1)     
"""


import robot.interface as robot
import numpy as np
import os.path
import time
import json
import math
import random
import subprocess
import pickle


# Global definition of variables
dc = {}               # dictionary for important param
mypwd  = os.getcwd()  # retrieve code current directory
repeatFlag = True     # keep looping in the current practice segment
w, h   = 1920,1080    # Samsung LCD size

global traj_display
traj_display = None


# Supposed there are up to 4 lags in WM test, we ought to capture the trajectory up to
# 4 movements prior. We also have a counter how many trials since the last TEST trial.
nsince_last_test = 0
showFlag     = True   # Show yellow hand cursor position throughout (default: YES)
keep_going   = True   # flag to indicate script is running, until quit button is pressed

dc["active"] = False  # Adding this flag to show that the test is currently active!!
dc["responded"] = False  # To prevent user from responding twice during WM Test (Flag=1 means responded)
test_angle = [-45,45] # Which side are we testing? Left/right?
wm_lag = ["lag-1","lag-2","lag-3","lag-4","no test"]  # The type of lag used in WM test


# Global definition for test-related parameters. This list replaces exper_design file.
VER_SOFT = "2.0"
NTRIAL_MOTOR = 25     # Relevant only for post-test
NTRIAL_TRAIN = 50     # Training trials with feedback
MINTRIAL_SET = 15     # Minimum trials before we set the actual target direction during Motor_Pre
ROT_MAG = 5           # Value of rotation angle for WM Test.
INIT_DIR_RANGE = 45   # Range in which participants can get the first explosion during Motor_Pre
YCENTER     = 0.000   # Let's fixed the Y-center position!
TARGETDIST  = 0.15    # move 15 cm from the center position (default!)
START_SIZE  = 0.008   #  8 mm start point radius
CURSOR_SIZE = 0.003   #  3 mm cursor point radius
WAITTIME    = 0.75    # 750 msec general wait or delay time 
MOVE_SPEED  = 1.0     # duration (in sec) of the robot moving the subject to the center
FADEWAIT    = 0.5     # fading duration for robot-hold/stay
ARCEXTENT   = 90      # How much the arc will span (degree)

# How big a window to use for smoothing (see tools/smoothing for details about the effects)
SMOOTHING_WINDOW_SIZE = 9 
SMOOTHING_WINDOW = np.hamming(SMOOTHING_WINDOW_SIZE)


#dc['post']= 0 # (0: hand moving to start-not ready, 
#                 1: hand within/in the start position,
#                 2: hand on the way to target, 
#                 3: hand within/in the target)



def quit():
    """Subroutine to EXIT the program and stop everything."""
    global keep_going
    keep_going = False
    print("\nQuit button is pressed. Preparing to bail out all loops!\n")


def bailout():
    samsung.destroy()
    master.destroy() # Destroy Tk
    robot.unload()   # Close/kill robot process
    print("\nOkie! Bye-bye...\n")


def playAudio (filename):
    subprocess.call(['aplay',"%s/audio/%s"%(mypwd,filename)])
    time.sleep(0.1)
    #print("---Finished playing %s..."%(filename))


def playInstruct (n):
    global playwav
    myaudio = "%s/audio/arc%d.wav"%(mypwd,n)
    if playwav.get():  # what's the play-audio checkbox status?
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
    dc["filenum"] = int(filenum.get())

    if not subjid.get() or not filenum.get().isdigit():
        print("##Error## Subject ID and/or file numbers are empty or file number is not a digit!")
        return

    dc["active"]   = True   # flag stating we are already running
    dc["subjid"]   = subjid.get()
    dc['angle']    = vardeg.get()  # This is whether in the left or right workspace
    dc['lag']      = varopt.get()
    dc['logfileID']= "%s_%i"%(dc["subjid"],dc["filenum"])
    dc['logpath']  = '%s/data/%s_data/'%(mypwd,dc["subjid"])
    dc['logname']  = '%smotorLog_%s'%(dc['logpath'],dc['logfileID'])
    dc['scores']   = 0    # have to reset the score to 0 for each run!
    dc['curtrial'] = 0    # initialize current test trial
    dc['subjd']    = 0    # initialize robot distance from the center of start position
    dc["PDmaxv"]   = np.nan
    dc['target']   = np.nan   # NEW!!! This is the subject's unique direction

    # [Sept 11] To prevent making a mistake in matching the file number and current task-block,
    # I fix the pair. Example: file 01 is for pre-training, 02 to 04 for training, and 05 for post test
    if (dc["filenum"] == 0): 
        print ("\n### Familiarization phase + instruction\n")
        dc['task'] = "instruct"
    elif (dc["filenum"] in (1,6)): 
        print ("\n### PRE_TRAINING phase\n")
        dc['task'] = "pre_train"
    elif (dc["filenum"] in (2,3,4,7,8,9)): 
        print ("\n### TRAINING phase\n")
        dc['task'] = "training"
    elif (dc["filenum"] in (5,10)): 
        print ("\n### MOTOR_POST phase\n")
        dc['task'] = "motor_post"
    else:
        print ("\nWarning: File number out of range! Please check again....\n")
        dc['task'] = []

 
    # Now we will check whether log files already exist to prevent overwritting the file!
    if os.path.exists("%s.txt"%dc['logname']):
        print ("File already exists: %s.txt"%dc["logname"] )
    	dc["active"] = False   # To mark that we are no longer running
        return

    # Disable the user interface so that the settings can't be accidentally changed.
    master.update()

    # Do this if the task is not empty!
    if dc['task']:
       # Capture the center position for new subject or load an existing center position. 
       # New subject has been instructed beforehand to place the hand in the center position.
       getCenter()
       # Go to the center position
       goToCenter(MOVE_SPEED*1.5)
       # Display the center (start) circle 
       showStart()
       GoSignal()

       global traj_display
       print "Cleaning the user interface canvas......"
       # remove old trajectory from the GUI if it's there
       if traj_display!=None: 
          wingui.delete("traj")

       # Note: If we change number of blocks per session WE NEED TO CHANGE THIS!
       dc['session'] = 1 if(dc['filenum'] < 6) else 2

       # The new design doesn't use bias shift anymore. 
       dc["baseline_pd_shift"] = 0  
       dc['baseline_angle_shift'] = 0
       prepareCanvas()       # Prepare drawing canvas objects

       # We should first run instruction trials for a straightahead direction. 
       # Once set, we're ready for the main or actual test (filenum > 0).
       runPractice() if dc['task'] == "instruct" else runBlock()

    else:
       dc["active"] = False   # flag stating we are already running



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


# This simple block is executed in sequence...
def runPractice2():
    print "FINISH!"
    dc["active"] = False     # flag stating we are already running
    showImage("curves_R.gif",550,-30,3)


def runPractice():
    """ This is a function created for familiarization trials with instructions. 
    """
    global repeatFlag
    global showFlag
    # Define reward width for our target arc. For practice session, define it as NaN.
    dc["reward_width_deg"] = np.nan   # >> Don't make it too small, too tough!

    x,y = robot.rshm('x'),robot.rshm('y')
    showCursorBar((x,y))
    showTarget(dc['angle'])     # Show the target arc at this point

    triallag = dc['lag'].split('-')[1] if dc['lag'] != "no test" else 0
    print triallag
    triallag = int(triallag) # Ensure this is numeric. If this value = 0, it means no WM Test!!  

    playInstruct(0)  # added Sept 11 for the opening speech...

    #----------------------------------------------------------------
    print("\n--- Practice stage-1: Move towards the target arc")
    showFlag = True

    # Show how to move forward and how the robot brings the arm back.
    playInstruct(1)
    to_target()
    playInstruct(2)
    showImage("curves_L.gif",570,-30,3) if dc['angle'] > 0 else showImage("curves_R.gif",570,-30,3)
    return_toStart(triallag)
    playInstruct(3)

    # 20 trials for the subjects to familiarize with the target distance + speed
    for each_trial in range(1,16):
        dc['curtrial'] = each_trial
        print("\nNew Round %i ----------------- "%each_trial)
        # This is the point where subject starts to move to the target
        to_target()    
        # Go back to center and continue to the next trial.
        return_toStart(triallag)
        each_trial = each_trial + 1

    goToCenter(MOVE_SPEED) # Bring the arm back to the center first
    #----------------------------------------------------------------
    robot.stay()
    showTarget(dc['angle'], "black")  # Don't show the target arc now
    showFlag = False

    print("\n--- Practice stage-2: Occluded arm, yellow cursor off!\n")
    dc['task'] = "motor_post"
    playInstruct(4)

    print("\n###  Press <Esc> after giving the instruction...")
    repeatFlag = True
    while repeatFlag:
        master.update_idletasks()
        master.update()
        time.sleep(0.01)  # loop every 10 msec

    # 10 trials for the subjects to familiarize with the target distance + speed
    for each_trial in range(1,10):
        dc['curtrial'] = each_trial
        # This is the point where subject starts to move to the target
        print("\nNew Round %i ----------------- "%each_trial)
        to_target()    
        # Go back to center and continue to the next trial.
        return_toStart(triallag)
        each_trial = each_trial + 1


    #----------------------------------------------------------------
    print("\n--- Practice stage-3: Showing explosion + score \n")
    playInstruct(5)
    time.sleep(2)
    playAudio("explo.wav")
    showImage("Explosion_final.gif",900,130,2)   # Show booms for 2 sec!
    showImage("score10.gif",930,260,2)
    robot.stay()

    playInstruct(6)   # Continue the instruction...
    print("\n###  Press <Esc> after giving the instruction...")    
    repeatFlag = True
    while repeatFlag:
        master.update_idletasks()
        master.update()
        time.sleep(0.01)  # loop every 10 msec

    #----------------------------------------------------------------
    print("\n--- Practice stage-4: Explaining WM Test \n")

    playInstruct(7)
    showImage("test_trial.gif",700,150,2)
    playInstruct(8)
    # Show what rotated trajectory means. This depends on whether left/right workspace.
    if dc['angle'] > 0:
	showImage("own_L1.gif",550,0,1.5)
	showImage("own_L2.gif",550,0,4)
	showImage("own_L3.gif",550,0,1)
	showImage("own_L4.gif",550,0,2) 
	showImage("own_L5.gif",550,0,2) 
    else:
        showImage("own_R1.gif",550,0,1.5)
     	showImage("own_R2.gif",550,0,4)
    	showImage("own_R3.gif",550,0,1) 
	showImage("own_R4.gif",550,0,2) 
    	showImage("own_R5.gif",550,0,2)

    playInstruct(9)

    print("###  Press <Esc> after giving the instruction...")   
    global nsince_last_test
    nsince_last_test = 0 
    repeatFlag = True
    while repeatFlag:
        master.update_idletasks()
        master.update()
        time.sleep(0.01)  # loop every 10 msec
        
    dc['task'] = "training"
    dc["reward_width_deg"] = np.nan
    #triallag = 1 if dc['lag'] == "lag-1" else 2

    for each_trial in range(1,18):
        dc['curtrial'] = each_trial
        print("\nNew Round %i ----------------- "%each_trial)
        to_target()
        return_toStart(triallag)
        each_trial = each_trial + 1
    
    print("\n\n#### Instruction block has ended! Continue with the actual experiment?? \n")
    showTarget(dc['angle'])     # Show the target arc at this point
    dc["active"] = False    # flag stating we are already running


    
    
def runBlock():
    """ The actual test runs once 'Start' or <Enter> key is pressed """

    # We don't use bias shift anymore here. Also, reward zone has a fixed 13 mm width at 15 cm (~5 deg).
    dc["reward_width_deg"] = 5   # >> Don't make it too small, too tough!

    global showFlag
    showFlag = False
    showTarget(dc['angle'], "black")  # Don't show the target arc now

    print("\n### Kindly press <Esc> to continue......\n\n")
    global repeatFlag  # Pause to remind subjects what to do before start the actual test!
    repeatFlag = True
    while repeatFlag:
        master.update_idletasks()
        master.update()
        time.sleep(0.01)  # loop every 10 msec

    # Read the lag setting from the GUI. This decides the type of WM test lag.
    triallag = dc['lag'].split('-')[1] if dc['lag'] != "no test" else 0
    print triallag
    triallag = int(triallag) # Ensure this is numeric. If this value = 0, it means no WM Test!!  

    saveLog(True)    # Write column headers in the logfile (Jun9)   

    dc['baseline_angle_shift'] = sangle.get()
    
    ntrial = NTRIAL_TRAIN if dc['task'] in ("pre_train", "training") else NTRIAL_MOTOR
    
    print ("Starting %s in the %d workspace, with WM test %s"%(dc['task'],dc['angle'],dc['lag']))

    global nsince_last_test
    nsince_last_test = 0

    # Now start logging robot data: post, vel, force, trial_phase; 11 columns
    robot.start_log("%s.dat"%dc['logname'],11)
    
    # Added so that we can separate aimless reaching and actual training
    each_trial = 1
    while dc['task'] == 'pre_train':
       dc['curtrial'] = each_trial
       print("\nNew Round %i ----------------- "%each_trial)
       robot.wshm('fvv_trial_no', each_trial)
       to_target()                   # Part 1: Reaching out to target
       return_toStart(triallag)      # Part 2: Moving back to center
       saveLog()                     # Finally, save the logged data
       each_trial = each_trial + 1
       if not keep_going: break     # After QUIT is pressed, break the loop     

    # ---------------- RUNNING FOR EACH TRIAL IN THE BLOCK ------------------
    each_trial = 1
    while each_trial < ntrial+1:
        dc['curtrial'] = each_trial
        print("\nNew Round %i ----------------- "%each_trial)
        robot.wshm('fvv_trial_no', each_trial)
        to_target()                   # Part 1: Reaching out to target
        return_toStart(triallag)      # Part 2: Moving back to center
        saveLog()                     # Finally, save the logged data 
        each_trial = each_trial + 1
        if not keep_going: break     # After QUIT is pressed, break the loop 

    # ----------------------------------------------------------------------
    print("\n\n#### Test has ended! You may continue with the NEXT block or QUIT now.....\n")
    
    robot.stop_log()   # Stop recording robot data now!
    showTarget(dc['angle'])  # In between blocks, show target arc!

    #robot.stay_fade(dc['cx'],dc['cy'])  # Commented this, we still want to activate robot_stay!
    master.update()
    dc["active"] = False     # allow us running a new block

    if not keep_going: bailout()  # run bailout function [Updated:Jul 1]




def to_target():
    """ Part 1: This handles the whole trial segment when subject moves to hidden target 
    It formally takes 2 inputs: whether you want to show feedback (reward), and 
    maximum negbias and posbias to receive feedback. By default, feedback is not shown.
    """
    dc['subjx']= 0;  dc['subjy']= 0
    vmax = 0  # maximum velocity of the movement

    # (1) Wait at center or home position first before giving the go-ahead signal.
    win.itemconfig("start",fill="white")
    reach_target = False

    # Release robot_stay() to allow movement in principle, but we haven't given 
    # subjects the signal yet that they can start moving.
    #robot.controller(0)
    showCursorBar((dc['cx'],dc['cy']))
    # Note: To *fade out* the forces instead of releasing all of a sudden
    robot.stay_fade(dc['cx'],dc['cy'])
    time.sleep(FADEWAIT)

    while keep_going and not reach_target: # while the subject has not reached the target; ADDED keep_going flag here!
        
        # (2) First get current x,y robot position and update yellow cursor location
        x,y = robot.rshm('x'),robot.rshm('y')
        dc['subjx'], dc['subjy'] = x, y
        # Compute current distance from the center/start--robot coordinate! 
    	dc['subjd'] = math.sqrt((x-dc['cx'])**2 + (y-dc['cy']) **2)
        showCursorBar((x,y))
    	#print("Distance from center position= %f"%(subjd))

        vx, vy = robot.rshm('fsoft_xvel'), robot.rshm('fsoft_yvel')
        vtot = math.sqrt(vx**2 + vy**2)
        #print("Original: %f , Floris': %f"%(vtot,robot.rshm('fvv_vel')))
        #print(robot.rshm('fvv_trial_phase'))
        samsung.update()

        # [Jun19] Ananda added this to get x,y positions during the maximum velocity...
        if vmax < vtot: 
            vmax = vtot
            # update the x,y position of the subject at maximum velocity, RELATIVE TO THE CENTER
            dc['subjxmax'], dc['subjymax'] = x-dc["cx"],y-dc["cy"] 
            
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
            if dc["subjd"] > 0.75*TARGETDIST and robot.rshm('fvv_vel') < 0.03:
                #If yes, hold the position and compute movement speed.     
                robot.wshm('fvv_trial_phase', 3)
                robot.stay() # This automatically stops capturing the trajectory!
                master.update()
                dc['speed'] = 1000*(time.time() - start_time)
                print("  Movement duration = %.1f msec"%(dc['speed']))
                filter_traj()   # Filter the captured trajectory (when stop capturing!)

            ## Revised = 2 second timeout if one cannot/never reach the target.....
            if (time.time()-start_time) > 2:
                master.update()
                goToCenter(MOVE_SPEED)
                time.sleep(0.1)
                
        elif robot.rshm('fvv_trial_phase')==3:
            # (6) Once reached the target, check end-point accuracy. Angle here means workspace direction.
            checkEndpoint(dc['angle'])
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
    Update: If triallag is 0, you selected no WM test from the GUI. So, training proceeds w/o WM test.
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
    # trajectory with a certain probability. WM Test only happens during training! 

    if (dc['task'] == "training") & (random.random() < p_test(nsince_last_test)) & triallag > 0: 
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
       showImage("test_trial.gif",700,150,1.5)
            
       # If this is test trial, now replay the rotated trajectory [left/right]
       time.sleep(0.5)
       replay_traj(True)
            
       # (7) Wait for subject's response, then go back to the center position!
       dc["responded"] = False     # make this false so that a new respond can be recorded
       RT = doAnswer()
       goToCenter(MOVE_SPEED*0.9)
       nsince_last_test = 0
 
    else: # (8) Return to the center immediately if NOT a replay or NOT a training block.
       nsince_last_test = nsince_last_test + 1
       #print nsince_last_test
       goToCenter(MOVE_SPEED)
       dc['ref'], dc['answer'], RT = 'no_wm','no_wm',0

    # (9) We concatenate the logfile content with the WM test response
    dc['logAnswer'] = "%s,%d,%s,%s,%s,%d,%d,%s\n"%(dc['logAnswer'],triallag,dc['ref'],dc['answer'],dc['task'],RT,ROT_MAG,VER_SOFT)
 
            

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
            log_file.write("%s\n"%("Trial_block,direction,boom,amount_shifted_deg,x_end,y_end,"\
            "speed,x_maxv,y_maxv,PDy,PDy_shifted,angle_end_shift,angle_maxv_deg,angle_maxv_shift,reward_width_deg,"\
            "session,lag,ref_answer,subj_answer,task,WM_RT,rot_angle,version"))


def doAnswer():
    start_time = time.time()  # To count reaction time
    print("Waiting for subject's response")
    while (not dc['responded']):
        master.update_idletasks()
        master.update()
        time.sleep(0.3)
    RT = 1000*(time.time() - start_time)  # RT in m-sec
    print "--- RESPONSE: %s    RT:%d"%(dc['answer'],RT)
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
   print ("\nRetrieving trajectory %d"%(t))
   dc['ttraj'] = dc['traj%d'%t]



def replay_traj(rotate_flag = True):
    """ This function handles the replay of the trajectory. Depending whether
    rotate_flag is True, it will either play the normal or rotated trajectory.
    After each replay, it will also bring the subject hand back to center."""

    # First, get the Test Trajectory to play from the dict.
    traj = dc['ttraj']

    if rotate_flag:
        # Flip coin whether +5deg or -5deg rotation. Convention: Positive angle is CCW (to the left) !!! 
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

    #print("Ready to start replaying trajectory...")
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
    if   nn<6: return 0
    elif nn==6: return 0.1
    elif nn==7: return 0.3
    elif nn==8: return 0.5
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



def checkEndpoint(angle):
    """ The function checks whether the movement direction is within the desired angular 
    range (degree). This reward zone range is defined w.r.t the actual target center. 
    Additionally, the function WRITES trial information into the logfile.

    """
    # Important... Let's check whether we are supposed to give feedback or not. 
    feedback = 0 if dc['task'] in ("pre_train","motor_post") else 1
    #print("  Checking end-position inside target zone?")
    
    # Now let's first look at the subject movement endpoint.
    # The idea is to rotate back to make it a straight-ahead (90-deg) movement!
    # The return values are in the robot coordinates. Both tx and ty are the endpoint coordinate.
    tx,ty = dc['subjx'], dc['subjy']
    trotx,troty  = rotate([(tx,ty)], (dc['cx'],dc['cy']), -angle)[0]

    # CONVENTION: -ve value means error to the left (CCW), +ve means error to the right (CW).\
    # PDy is computed as the lateral deviation at the movement endpoint w.r.t +/-45 deg direction
    PDy   = trotx-dc['cx']
    X_end,Y_end = tx-dc["cx"],ty-dc["cy"] # translate the subject endpoint so that it is relative to the starting point

    # CONVENTION: -ve angular value means error to the right (CCW), +ve means error to the left (CW).
    dc['angle_maxv_deg'] = math.atan2(dc["subjymax"],dc["subjxmax"])*180/math.pi - 90 - angle # compute the angle of that vector (degree)
    if dc["angle_maxv_deg"]<-180: dc["angle_maxv_deg"]+=360

    # Compute angular deviation at movement endpoint!
    dc['angle_end_deg'] = math.atan2(Y_end,X_end)*180/math.pi - 90 - angle # in degree
    if dc["angle_end_deg"]<-180: dc["angle_end_deg"]+=360

    # Compute the PDy value after applying the baseline shift (if applicable)
    PDy_shift =  PDy - dc["baseline_pd_shift"]
    dc['PDend'] = PDy_shift
    
    # Let's check whether we are within INIT_DIR_RANGE/2 around the 45 degree angle.
    # We will only update the center of the reward zone if this is true!
    is_within_range = dc['angle_maxv_deg'] < INIT_DIR_RANGE/2 and dc['angle_maxv_deg'] > -1*INIT_DIR_RANGE/2 
    
    # NEW: A special case is during Motor_Pre when ntrial reaches MINTRIAL_SET >>>>>>>>>>>>>
    #       (1) Then capture the angle/direction of that trial to be the desired test direction!
    #       (2) Show explosion indicating that it's gonna be the test direction.
    # If we are during pre, AND after a certain number of trials, AND within the range we defined, 
    # let's update the center of the reward zone! :) 
    if dc['task'] == "pre_train" and dc['curtrial'] > MINTRIAL_SET and is_within_range:
        dc['task'] = 'training'
        feedback = 1 
        dc['baseline_angle_shift'] = dc['angle_maxv_deg'] # Set current movement angle (w.r.t 45 degrees) as the new reward center.
        dc["baseline_pd_shift"] = PDy
        print("\n[Note:] Cool! Taking the new subject's bias:  %.2f deg\n"%(dc['baseline_angle_shift']))
        sangle.set("%.2f"%dc['baseline_angle_shift']);
        
        # Before we give WM Test, reset the number of trials since the last WM test.
        global nsince_last_test
        nsince_last_test = 0
 
        
    dc['angle_maxv_shift'] = dc['angle_maxv_deg'] - dc['baseline_angle_shift']
    dc['angle_end_shift']  = dc['angle_end_deg']  - dc['baseline_angle_shift']

    # Ananda added PDmaxv and angular deviation.
    #print "Theta at max velocity          = %.2f deg" % dc['angle_maxv_deg']
    print "Theta at max velocity, shifted = %.2f deg" % dc['angle_maxv_shift']
    print "Theta at endpoint, shifted     = %.2f deg" % dc['angle_end_shift']

    # Show explosion? Check the condition to display explosion when required.
    if feedback and abs(dc["angle_maxv_shift"]*2) < dc["reward_width_deg"]:
        # This trial got rewarded!
        #if dc['angle_maxv_shift'] > rbias[0] and dc['Theta_maxv_shift']< rbias[1] and feedback:
        status = 1  # 1: rewarded, 0: failed
        dc['scores'] = dc['scores'] + 10
        print ("  EXPLOSION!  Current score: %d"%(dc['scores']))
        playAudio("explo.wav")
        showImage("Explosion_final.gif",900,130,1)   # Show booms for 3 sec!
        showImage("score" + str(dc['scores']) + ".gif",930,260,0.5)
    else:
        # This trial does not get rewarded
        time.sleep(WAITTIME)
	status = 0

    # IMPORTANT = We build a string for saving movement kinematics & reward status--revised!
    dc['logAnswer'] = "%d,%d,%d,%.2f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.2f,%.2f,%.2f,%f,%d"% \
                      (dc['curtrial'],dc['angle'],status,dc['baseline_angle_shift'],X_end,Y_end,dc['speed'],dc["subjxmax"],dc["subjymax"],PDy,PDy_shift,dc['angle_end_shift'],dc['angle_maxv_deg'],dc['angle_maxv_shift'],dc['reward_width_deg'],dc['session'])





######## Some parameters that specify how we draw things onto our GUI window

from Tkinter import * # Importing the Tkinter library
master  = Tk()	      # Create an empty background window for GUI
samsung = Toplevel()  # Create another one, for the robot canvas (Samsung)
                      # Interesting, you shouldn't have 2 Tk() instances, use Toplevel()
	              # and this will solve the problem of pyimage not displayed

master.geometry('%dx%d+%d+%d' % (550, 540, 500, 200)) # Nice GUI setting: w,h,x,y   
master.title("Reward-based Sensorimotor Learning")
master.protocol("WM_DELETE_WINDOW", quit)  # When you press [x] on the GUI

### Ensuring subjectś window on the Samsung LCD!
samsung.geometry('%dx%d+%d+%d' % (1920, 1080, 1600, 0)) 


subjid  = StringVar()
filenum = StringVar()
mymsg   = StringVar()
varopt  = StringVar()
sangle  = DoubleVar()
vardeg  = IntVar()
playwav = BooleanVar()

# Trick: Because LCD screen coordinate isn't the same as robot coordinate system, 
# we need to have a way to do the conversion so as to show the position properly.

# This performs the coeff readout directly instead of hardcoding the coeff values.
#caldata = os.popen('./ParseCalData exper_design/cal_data.txt').read()
#print caldata.split("\t")
#coeff = caldata.split('\t')

#coeff="9.795386e+02,1.879793e+03,1.311361e+02,2.181227e+02,1.856681e+03,2.858053e+02".split(',') 

#def rob_to_screen(robx, roby):
#    px = float(coeff[0]) + float(coeff[1])*robx - float(coeff[2])*robx*roby
#    py = float(coeff[3]) + float(coeff[4])*roby - float(coeff[5])*robx*roby
#   return (px,py)


def load_calib():
    #fname = tkFileDialog.askopenfilename(filetypes=[('pickles','.pickle27')])
    fname = 'exper_design/' +'/visual_calib.pickle27'
    if fname!= None:
        print("Opening",fname)
        (captured,regrs) = pickle.load(open(fname,'rb'))
        global calib
        calib = regrs
	#print("calib data:",calib)
        return

def rob_to_screen(robx, roby):
    # (from Moh's). We no longer use the old ParseCalData.
    global calib
    return (int(calib["interc.x"] + (robx*calib["slope1.x"]) + (roby*calib["slope2.x"])),
            int(calib["interc.y"] + (robx*calib["slope1.y"]) + (roby*calib["slope2.y"])))




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

    # Entry widget for 1st row --------------
    Label(topFrame, text="Subject ID: ").grid(row=0, sticky=E, pady=10)
    e1 = Entry(topFrame, width = 6, bd =1, textvariable = subjid)
    e1.grid(row=0, column=1)
    #e1.insert(END, "aes")
    e1.focus()
    Label(topFrame, text="File Number: ").grid(row=0, column=2, padx=(20,0), sticky=E)
    e2 = Entry(topFrame, width = 4, bd =1, textvariable = filenum)
    e2.grid(row=0, column=3, sticky=W)
    e2.insert(END, "0")
    
    # Entry widget for 2nd row --------------
    Label(topFrame, text="Workspace: ").grid(row=1, column=0, sticky=E)
    e6 = OptionMenu(topFrame, vardeg, *test_angle, command=OptionSelectEvent)
    e6.grid(row=1, column=1, columnspan=2, sticky=W, pady=8)
    vardeg.set("45")      # set default value

    # Entry widget for 3rd row --------------
    Label(topFrame, text="WM Test Lag: ").grid(row=1, column=2, padx=(20,0), sticky=E)
    e4 = OptionMenu(topFrame, varopt, *wm_lag, command=OptionSelectEvent)
    e4.grid(row=1, column=3, columnspan=3, sticky=W)
    varopt.set("lag-1")      # set default value

    # Entry widget for 4th row --------------
    Label(topFrame, text="Test Direction: ").grid(row=2, sticky=E)
    e5 = Entry(topFrame, width=8, bd =1, textvariable = sangle)
    e5.grid(row=2, column=1, columnspan=3, sticky=W, pady=8)
    sangle.set("0")

    # Check button for playing instruction audio? --------------
    chk = Checkbutton(topFrame, text=" Play Audio?", variable=playwav)
    chk.grid(row=2, column=2, padx=(20,0), sticky=E)

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
    # the type of test parameters, e.g. angle. Put them in a dictionary.
    dc['angle'] = vardeg.get()
    dc['lag']   = varopt.get()
    print ("You have selected %s-deg workspace and %s WM test"%(dc['angle'],dc['lag']))
    #e5.config(state='normal') if (temp[0]=="training") else e5.config(state='disabled')


def clickYes(event):
    print ("Left key pressed to answer LEFT!")
    if dc["responded"]:  # Is the reply already recorded?
       print("##Error## Wrong timing to press LEFT/button already pressed....")
    dc['answer']= 'left'
    dc["responded"] = True

def clickNo(event):
    print ("Right key pressed to answer RIGHT!")
    if dc["responded"]:  # Is the reply already recorded?
       print("##Error## Wrong timing to press RIGHT/button already pressed....")
    dc['answer']= 'right'
    dc["responded"] = True



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

    # NOTE [Aug 18]: The new paradigm uses a target arc, not target bar anymore!
    win.create_arc([0,0,1,1], extent=-180, style=ARC, tag="target")

    win.create_polygon([0,0,0,1,1,1,0,0], fill="black", width = 15, tag="handbar")
    win.create_oval   ([0,0,1,1], width=1, fill="black", tag="targetcir")
    win.create_oval   ([0,0,1,1], width=1, fill="black", tag="hand")

    samsung.update()   # Update the canvas to let changes take effect

    # Also create a target in the experimenter's GUI [updated Aug 18!]
    wingui.create_arc([0,0,1,1], extent=180, style=ARC, tag="target")



def showCursorBar(position, color="yellow"):
    """ Draw the cursor at the current position. If showFlag = False, then display only when the 
    hand is within the start circle [Aug 21].
    Angle    : the angle of the target w.r.t to straight-ahead direction
    Position : the CURRENT hand position in robot coordinates
    color    : the color of the canvas object (default: yellow)
    """
    global showFlag
    (x,y) = position  #print("Showing cursor bar!")
    
    # Prepare to draw current hand cursor in the robot coordinate
    x1, y1 = rob_to_screen(x-CURSOR_SIZE, y-CURSOR_SIZE)
    x2, y2 = rob_to_screen(x+CURSOR_SIZE, y+CURSOR_SIZE)

    # If hand position is outside the start circle, remove cursor
    if not showFlag and dc['subjd'] >= START_SIZE:
        win.itemconfig("hand",fill="black")
        win.coords("hand",*[0,0,0,0])
    else:
        win.itemconfig("hand",fill=color)
        win.coords("hand",*[x1,y1,x2,y2])
    win.tag_lower("start", "hand")
    samsung.update()     # Update the canvas to let changes take effect



def showTarget(angle, color="#A5A5A5"):
    """
    Show the target at the given angle painted in the given color.
    NOTE [Aug 18]: The new paradigm uses a target arc, not target bar anymore!
                   Care should be taken when dealing with angle as the value is 
                   actually w.r.t straight-ahead direction.
    """
    newangle = angle + 90
    #print("  Showing target bar on the screen...")
    # First construct a square in which the arc is drawn. The radius = target distance!
    # We need to change these coordinates to the screen coordinates.
    minx, miny = rob_to_screen(dc['cx'] - TARGETDIST, dc['cy'] - TARGETDIST)
    maxx, maxy = rob_to_screen(dc['cx'] + TARGETDIST, dc['cy'] + TARGETDIST)

    # Show the target by updating the outline color and width.
    win.coords("target", *[minx,miny,maxx,maxy])
    win.itemconfig("target",outline=color)
    win.itemconfig("target",width=15)
    win.itemconfig("target",start =-(newangle-45))
    win.itemconfig("target",extent=-ARCEXTENT)
    samsung.update()         # Update the canvas to let changes take effect

    # Now also show the target bar in the experimenter's GUI screen
    g1x, g1y = rob_to_gui(dc['cx'] - TARGETDIST, dc['cy'] - TARGETDIST)
    g2x, g2y = rob_to_gui(dc['cx'] + TARGETDIST, dc['cy'] + TARGETDIST)
    wingui.coords    ("target", *[g1x,g1y,g2x,g2y])
    wingui.itemconfig("target", outline="white")  
    wingui.itemconfig("target",start = newangle-45)
    wingui.itemconfig("target",extent= ARCEXTENT)
    
  


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

    # Update canvas for changes to take effect. Remove the image by giving empty file.
    samsung.update()
    time.sleep(delay)
    label.place(x=0, y=0)  
    label.config(image='') 
    time.sleep(0.1)  # No need to call samsung.update() anymore!
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

os.system("clear")  # Clear the terminal


######### This is the entry point when you launch the code ################

robot.load() # Load the robot process
print("\nRobot successfully loaded...\n")

robot.zeroft()
print("\n\nPress START or <Enter> key to continue\n")

global calib
load_calib() # Load calibration file for rob_screen transformation

mainGUI()
robot_canvas()

while keep_going:
    # Although it maintains a main loop, this routine blocks! Use update() instead...
    #master.mainloop()
    #draw_robot()
    master.update_idletasks()
    master.update()
    #time.sleep(0.04) # 40 msec frame-rate of GUI update

# Run this bailout function after QUIT is pressed!! Place it at the very end of the code. 
# [Updated:Jul 1]
if not keep_going: bailout()



