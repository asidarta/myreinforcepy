"#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 18 15:24:50 2017 @author: ae2010

This new code does the motor copy test paradigm: subjects to repeat the trajectory presented to them.
Revisions : Initial design (Oct 2)

"""


import robot.interface as robot
import numpy as np
import os.path
import time
import math
import random
import subprocess


# Global definition of variables
dc = {}               # dictionary for important param
mypwd  = os.getcwd()  # retrieve code current directory
repeatFlag = True     # keep looping in the current practice segment
w, h   = 1920,1080    # Samsung LCD size


# Supposed there are up to 4 lags in WM test, we ought to capture the trajectory up to
# 4 movements prior. We also have a counter how many trials since the last TEST trial.
test_angle = [-45,45] # Which side are we testing? Left/right?
showFlag     = True   # Show yellow hand cursor position throughout (default: YES)
dc["active"] = False  # Adding this flag to show that the test is currently active!!

# Global definition for test-related parameters. This list replaces exper_design file.
YCENTER     = -0.005  # Let's fixed the Y-center position!
TARGETDIST  = 0.15    # move 15 cm from the center position (default!)
START_SIZE  = 0.008   #  8 mm start point radius
CURSOR_SIZE = 0.003   #  3 mm cursor point radius
WAITTIME    = 0.75    # 750 msec general wait or delay time 
MOVE_SPEED  = 1.0     # duration (in sec) of the robot moving the subject to the center
FADEWAIT    = 0.5     # fading duration for robot-hold/stay
ARCEXTENT   = 90      # How much the arc will span (degree)

# Define the test directions (degree). We divide the whole ARCEXTENT into 10 parts equally.
# This also depends on which workspace, left/right. 
SET_TESTDIR = np.array([0,9,18,27,36,45,54,63,72,81,90])  ## numpy!



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

    # First, check whether the entry fields have usable text (need subjID, etc.)
    if not subjid.get():
        print("##Error## Subject ID and/or file numbers are empty or file number is not a digit!")
        return

    dc["active"]   = True   # flag stating we are already running
    dc["subjid"]   = subjid.get()
    dc['angle']    = vardeg.get()  # This is whether in the left or right workspace
    dc['phase']    = varopt.get()
    dc['logfileID']= "%s_%s"%(dc["subjid"],dc["phase"])
    dc['logpath']  = "%s/data/%s_data/"%(mypwd,dc["subjid"])
    dc['logname']  = "%smotorCopy_%s"%(dc['logpath'],dc['logfileID'])
    dc['curtrial'] = 0    # initialize current test trial
    dc['subjd']    = 0    # initialize robot distance from the center of start position
    dc["PDmaxv"]   = np.nan

    # Now we will check whether log files already exist to prevent overwritting the file!
    if os.path.exists("%s.txt"%dc['logname']):
        print ("File already exists: %s.txt"%dc["logname"] )
    	dc["active"] = False   # To mark that we are no longer running
        return

    # Disable the user interface so that the settings can't be accidentally changed.
    master.update()

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
        wingui.delete(traj_display)

    # The new design doesn't use bias shift anymore. 
    dc["baseline_pd_shift"] = 0  
    dc['target_angle'] = 0
    prepareCanvas()       # Prepare drawing canvas objects

    # We should first run instruction trials for a straightahead direction. 
    # Once set, we're ready for the main or actual test (filenum > 0).
    runPractice() if dc['phase'] == "Instruct" else runBlock()


def angle_pos(theta):
    """ Convert endpoint target direction to robot coordinates w.r.t center position.
        At the same, this will draw the target on the user's wingui for illustration purpose.
    """
    theta_rad = theta*math.pi/180   # First, convert theta to radian
    targetX = TARGETDIST * math.cos(theta_rad) + dc['cx']
    targetY = TARGETDIST * math.sin(theta_rad) + dc['cy']

    # Then draw where the target is so that we can see on the wingui!
    xtarget, ytarget = rob_to_gui(targetX,targetY)
    wingui.create_oval(*[xtarget-5,ytarget-5,xtarget+5,ytarget+5],width=2,fill="red",tag="motortarget")
    samsung.update()

    # Finally, move the robot to the designated target position!
    print("  Moving to %f, %f"%(targetX,targetY))
    robot.move_stay(targetX, targetY, MOVE_SPEED)
    master.update()
    print("  Movement completed!")




# Run only for the first time: familiarization trials with instructions. 
# This simple block is executed in sequence...
def runPractice():
    print "FINISH!"
    dc["active"] = False     # flag stating we are already running
    showImage("curves_R.gif",550,-30,3)

def runPractice2():
    global repeatFlag
    global showFlag
    x,y = robot.rshm('x'),robot.rshm('y')
    showCursorBar((x,y))

    playInstruct(0)  # added Sept 11 for the opening speech...

    #----------------------------------------------------------------
    print("\n--- Practice stage-1: Move towards the target arc")
    showFlag = True
    showTarget(dc['angle'])     # Show the target arc at this point

    # Show how to move forward and how the robot brings the arm back.
    playInstruct(1)
    to_target()
    playInstruct(2)
    showImage("curves_L.gif",550,-30,3) if dc['angle'] > 0 else showImage("curves_R.gif",550,-30,3)
    return_toStart()
    playInstruct(3)

    # 20 trials for the subjects to familiarize with the target distance + speed
    for each_trial in range(1,21):
        dc['curtrial'] = each_trial
        print("\nNew Round %i ----------------- "%each_trial)
        # This is the point where subject starts to move to the target
        to_target()    
        # Go back to center and continue to the next trial.
        return_toStart()
        each_trial = each_trial + 1

    goToCenter(MOVE_SPEED) # Bring the arm back to the center first
    #----------------------------------------------------------------
    robot.stay()
    showTarget(dc['angle'], "black")  # Don't show the target arc now
    showFlag = False

    print("\n--- Practice stage-2: Occluded arm, yellow cursor off!\n")
    playInstruct(4)

    print("\n###  Press <Esc> after giving the instruction...")
    repeatFlag = True
    while repeatFlag:
        master.update_idletasks()
        master.update()
        time.sleep(0.01)  # loop every 10 msec

    # 10 trials for the subjects to familiarize with the target distance + speed
    for each_trial in range(1,11):
        dc['curtrial'] = each_trial
        # This is the point where subject starts to move to the target
        print("\nNew Round %i ----------------- "%each_trial)
        to_target()    
        # Go back to center and continue to the next trial.
        return_toStart()
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
	showImage("own_L1.gif",550,0,1)
	showImage("own_L2.gif",550,0,3)
	showImage("own_L3.gif",550,0,1)
	showImage("own_L4.gif",550,0,3) 
    else:
        showImage("own_R1.gif",550,0,1)
     	showImage("own_R2.gif",550,0,3)
    	showImage("own_R3.gif",550,0,1) 
    	showImage("own_R4.gif",550,0,3)

    playInstruct(9)

    print("###  Press <Esc> after giving the instruction...")    
    repeatFlag = True
    while repeatFlag:
        master.update_idletasks()
        master.update()
        time.sleep(0.01)  # loop every 10 msec
        
    for each_trial in range(1,16):
        dc['curtrial'] = each_trial
        print("\nNew Round %i ----------------- "%each_trial)
        to_target()
        return_toStart()
        each_trial = each_trial + 1
    
    print("\n\n#### Instruction block has ended! Continue with the actual experiment?? \n")
    dc["active"] = False    # flag stating we are already running


    
    
def runBlock():
    """ The actual test runs once 'Start' or <Enter> key is pressed """

    global repeatFlag  # This is a pause to remind subjects what to do before start the actual test!
    global showFlag
    showFlag = False
    showTarget(dc['angle'], "black")  # Don't show the target arc now

    print("\n### Kindly press <Esc> to continue......\n\n")
    repeatFlag = True
    while repeatFlag:
        master.update_idletasks()
        master.update()
        time.sleep(0.01)  # loop every 10 msec

    saveLog(True)    # Write column headers in the logfile (Jun9)   


    # Now start logging robot data: post, vel, force, trial_phase; 11 columns
    robot.start_log("%s.dat"%dc['logname'],11)
 
    # ---------------- RUNNING FOR EACH TRIAL IN THE BLOCK ------------------
    theta = 45
    each_trial = 0
    for i in range(2): # Repeat the set twice!
        # Generate test directions (which workspace?)
        testdir=180-SET_TESTDIR if dc['angle'] > 0 else 90-SET_TESTDIR
        # Then, shuffle the members inside it
        random.shuffle(testdir)
        for theta in testdir:  # Cycle through each test direction!
           each_trial = each_trial + 1
           dc['curtrial'] = each_trial
           dc['target_angle'] = theta  # This is the subject's target direction!!
       	   print("\nNew Round %i, moving to %d ----------------- "%(each_trial,theta))
           time.sleep(WAITTIME*1.2) 
           angle_pos(theta)       # Part 1: Robot brings the arm out to target
           return_toStart()       # Part 2: Moving back to center
           to_target()            # Part 3: Reaching out to target
           return_toStart()	  # Part 4: Moving back to center
           saveLog()              # Finally, save the logged data
           wingui.delete("motortarget")

    # ----------------------------------------------------------------------
    print("\n\n#### Test has ended! Kindly QUIT the program now.....\n")
    
    robot.stop_log()   # Stop recording robot data now!
    time.sleep(2)
    #robot.stay_fade(dc['cx'],dc['cy'])  # Commented this, we still want to activate robot_stay!
    master.update()
    dc["active"] = False    # allow us running a new block



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

    while not reach_target: # while the subject has not reached the target
        
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
                list_traj()   # Filter the captured trajectory (when stop capturing!)

            ## Revised = 2 second timeout if one cannot/never reach the target.....
            if (time.time()-start_time) > 2:
                master.update()
                goToCenter(MOVE_SPEED)
                time.sleep(0.1)
                
        elif robot.rshm('fvv_trial_phase')==3:
            # (6) Once reached the target, check end-point accuracy
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


def return_toStart():
    """ This handles the segment when hand position moves back to the center (start). It depends 
    on whether the current block is training block, and current trial is a WM test trial.
    """
    
    if "most.recent.traj" in dc: # Check whether the key is present in dict!
	trajectory = dc["most.recent.traj"]
 	# downsample the list a little and convert to screen coordinates
  	coords = [ rob_to_gui(x,y) for (x,y) in trajectory[::20] ] 
    	global traj_display
        if traj_display!=None:
            wingui.itemconfig(traj_display,fill="#1F1F1F",width=1)

        # draw a new line with a tag...
    	traj_display = wingui.create_line(*coords,fill="green",width=3,tag="traj")
        # also now delete the red target
        samsung.update()

    # (8) Return to the center!
    time.sleep(WAITTIME)
    goToCenter(MOVE_SPEED)
    
            


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
            log_file.write("%s\n"%("trial,workspace,target_dir,x_end,y_end,speed,x_maxv,y_maxv,PDy,PDy_shifted,angle_end_shift,angle_maxv_deg,angle_maxv_shift"))

    

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



def list_traj():
    raw_traj = list(robot.retrieve_trajectory()) 
    #robot.prepare_replay(raw_traj)
    # separate them into x and y component
    x,y = zip(*raw_traj)

    # Trick: save it with a key name according to nsince_last_test
    filtered_traj = list(zip(x,y))
    dc["most.recent.traj"]=filtered_traj



def checkEndpoint(angle):
    """ The function checks whether the movement direction is within the desired angular 
    range (degree). This reward zone range is defined w.r.t the actual target center. 
    Additionally, the function WRITES trial information into the logfile.

    """
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
    print (dc['angle_end_deg'])
    if dc["angle_end_deg"]<-180: dc["angle_end_deg"]+=360

    # Compute the PDy value after applying the baseline shift (if applicable)
    PDy_shift =  PDy - dc["baseline_pd_shift"]
    dc['PDend'] = PDy_shift
    
    # Target direction. Here my convention is w.r.t to the straight-ahead, 90deg direction.
    dc['angle_maxv_shift'] = dc['angle_maxv_deg'] - (dc['target_angle'] - 90 - angle)
    dc['angle_end_shift']  = dc['angle_end_deg']  - (dc['target_angle'] - 90 - angle)

    # Ananda added PDmaxv and angular deviation.
    print "Theta at max velocity w.r.t. target = %.2f deg" % dc['angle_maxv_shift']
    print "Theta at endpoint w.r.t target      = %.2f deg" % dc['angle_end_shift']

    dc['logAnswer'] = "%d,%d,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n"% \
                      (dc['curtrial'],dc['angle'],dc['target_angle'],X_end,Y_end,dc['speed'],dc["subjxmax"],dc["subjymax"],PDy,PDy_shift,dc['angle_end_shift'],dc['angle_maxv_deg'],dc['angle_maxv_shift'])





######## Some parameters that specify how we draw things onto our GUI window

from Tkinter import * # Importing the Tkinter library
master  = Tk()	      # Create an empty background window for GUI
samsung = Toplevel()  # Create another one, for the robot canvas (Samsung)
                      # Interesting, you shouldn't have 2 Tk() instances, use Toplevel()
	              # and this will solve the problem of pyimage not displayed

master.geometry('%dx%d+%d+%d' % (550, 500, 500, 200)) # Nice GUI setting: w,h,x,y   
master.title("Reward-based Sensorimotor Learning")
master.protocol("WM_DELETE_WINDOW", quit)  # When you press [x] on the GUI

subjid  = StringVar()
filenum = StringVar()
mymsg   = StringVar()
varopt  = StringVar()
sangle  = DoubleVar()
vardeg  = IntVar()
playwav = BooleanVar()

# Trick: Because LCD screen coordinate isn't the same as robot coordinate system, 
# we need to have a way to do the conversion so as to show the position properly.

### Updated coefficient we just moved to a new lab!
coeff = "1.004991e+03,1.848501e+03,4.531727e+02,2.106822e+02,1.877361e+03,1.084496e".split(',')

def rob_to_screen(robx, roby):
    px = float(coeff[0]) + float(coeff[1])*robx #- float(coeff[2])*robx*roby
    py = float(coeff[3]) + float(coeff[4])*roby #- float(coeff[5])*robx*roby
    return (px,py)


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

    # Check button for playing instruction audio? --------------
    chk = Checkbutton(topFrame, text=" Play Audio?", variable=playwav)
    chk.grid(row=0, column=2, padx=(20,0), sticky=E)
    
    # Entry widget for 2nd row --------------
    Label(topFrame, text="Workspace: ").grid(row=1, column=0, sticky=E)
    e6 = OptionMenu(topFrame, vardeg, *test_angle, command=OptionSelectEvent)
    e6.grid(row=1, column=1, columnspan=2, sticky=W, pady=8)
    vardeg.set("45")      # set default value

    Label(topFrame, text="Test phase: ").grid(row=1, column=2, padx=(20,0), sticky=E)
    e4 = OptionMenu(topFrame,varopt,"Instruct","Pre","Post",command=OptionSelectEvent)
    e4.grid(row=1, column=3, columnspan=3, sticky=W)
    varopt.set("Pre")      # set default value

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
    dc['angle'] = vardeg.get()
    dc['lag']   = varopt.get()
    print ("You have selected %s phase with %s-deg workspace"%(dc['lag'],dc['angle']))
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
