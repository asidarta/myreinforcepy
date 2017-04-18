#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 20:24:50 2017 @author: ae2010
This code is used for reinforcement-based motor learning. It has the same principle 
as the old code created in Tcl for the old suzuki machine.
"""

import robot.interface as ananda
import os.path
import time
import json
import math

# Declare several global variables
mypwd = os.getcwd()  # retrieve code current directory
dc = {}              # dictionary for important param
stages  = 0          # to enter clickStart soubroutine step-by-step
answerflag = 0       # Flag=1 means subject has responded
targetdist = 0.15    # move 15 cm from the center position (default!)
movetime = 0.9	     # 900 msec default movement speed to a target

dc['post'] = 0 # (0: hand moving to start-not ready, 
#                     1: hand within/in the start position,
#                     2: hand on the way to target, 
#                     3: hand within/in the target)
dc['scores']= 0 # points for successful trials


# Subroutine to EXIT the program and stop everything.
def quit():
    master.destroy()
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
        dc['center'] = (center[0][0],center[0][1])
    else:
        print("This is a new subject. Center position saved.")
        dc['center'] = ananda.rshm('x'),ananda.rshm('y')
        txt_file = open(dc['logpath']+subjid.get()+"_center.txt", "w")
        txt_file.write("%f,%f"%dc['center'])
        txt_file.close()
    # Also useful to define center pos in the screen coordinate!       
    dc['center.scr'] = rob_to_screen(dc['center'][0],dc['center'][1])


# Initiate movement to the center (start) coordinate
def goToCenter(speed):
    # Ensure this is a null field first (because we will be updating the position)
    #ananda.controller(0)
    print("  Now moving to center: %f,%f"%dc['center'])
    # Send command to move to cx,cy
    #ananda.move_stay(dc['center'][0],dc['center'][1],speed)
    #ananda.status = ananda.move_is_done()
    #while not #ananda.status:   # check if movement is done
        #ananda.status = ananda.move_is_done()
        #time.sleep(0.07)
    print("  Movement completed!")
    # Put flag to 1, indicating robot handle @ center position
    dc['post'] = 1


# Start main program, taking "Enter" button as input-event
def clickStart(event):
    global stages
    if (stages == 0):
        dc['logfileID'] = subjid.get()+filenum.get()
        dc['logpath'] = mypwd + "/data/" + subjid.get() + "_data/"

        if not(subjid.get()) or not(filenum.get()):
            print("##Error## Subject ID and/or file numbers are empty!")
        # Added check to ensure existing logfile isn't overwritten
        elif (os.path.exists(dc['logpath']+"motorLog_"+dc['logfileID']+".txt")):
            print "Duplicate: "+dc['logpath']+"motorLog_"+dc['logfileID']+".txt" 
        else:
            if (int(filenum.get()) == 0):
                filepath = mypwd+"/exper_design/practice.txt"
                e3.config(state='normal')
                e4.config(state='disabled')
            else:
                filepath = mypwd+"/exper_design/" + varopt.get() + ".txt"
                e3.config(state='disabled')
                e4.config(state='normal')
            #print filepath
            stages = read_design_file(filepath) # Next stage depends if file can be loaded
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
            mainLoop() # This is only for filenum = 0, familiarization trials!      	
        else:
            mainLoop() # Once set, we're ready for the main loop (actual test!)
    else:
        print("Current clickStart() stage = %d"%stages)


# Based on subj_id & block number, read experiment design file!
def read_design_file(mpath):
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
def practiceLoop():
    print("Entering practice-Loop now.........")
    #playAudio()
    #playAudio()
    #playAudio()


# The main code once 'Start' or <Enter> key is pressed
def mainLoop():
    print("Entering main-Loop now.........")
    #playAudio()
    showStart("white")   # Display center position!

    # As the 1st element contains non-trial related setting, we remove it!
    for xxx in dc['mydesign'][1:]:
        index   = xxx['trial']
        FFset   = xxx['FField']
        angle   = xxx['angle']
        Feedback= xxx['feedback']
        Score   = xxx['scoreOn']
        Cursor  = xxx['cursorOn']
        homewait= xxx['homewait']
        targetwait= xxx['targetwait']

        print("\nNew Round- " + str(index))
        time.sleep(homewait/1000)
        #dc['logAnswer'] = str(index) + " "   # string to be saved later!
        to_target(105)  # <<<<<

        print("  Waiting for " + str(targetwait) + "msec")
        time.sleep(targetwait/1000)
        dc['post'] = 0    # Reset position!
        goToCenter(1.5)   # Go back to center!
        time.sleep(targetwait/1000)

	#print(dc['logAnswer'])
	#with open(dc['logpath'],'aw') as log_file:
         #      print("  Saving trial log.....")
          #     log_file.write(dc['logAnswer'])  # Save every trial as text line

    print("\nNOTE = Test has ended!")



# This handles the whole segment when subject moves to hidden target
def to_target(angle):
    notcompleted = 1
    dc['post'] = 1;  dc['subjx']= 0;  dc['subjy']= 0
    # Ref direction= If straight-ahead is defined as 90 degree
    angle = angle - 90
    showTarget(angle,"green")

    while notcompleted:
        # First read out instant x,y robot position
        x,y = ananda.rshm('x'),ananda.rshm('y')
        dc['subjx'], dc['subjy'] = x, y
        #print x,y
    	# Compute current distance from the center/start--robot coordinate! 
    	# Adjusted, because robot handle coordinate isn't really centered!
    	dc['subjd'] = math.sqrt((x-dc['center'][0]-0.0065)**2 + 
                                (y-dc['center'][1]-0.0035)**2) 
    	#print("Distance from center position= %f"%(subjd))

        # Then refresh the canvas!
        try:
	   win.delete("hand", "handbar")
	except:
	   break
        # Redraw instant visual feedback on canvas again!
        showCursorBar(angle)

        # Occasionally you call update() to refresh the canvas....
        samsung.update()
        time.sleep(0.005)

        vx, vy = ananda.rshm('fsoft_xvel'), ananda.rshm('fsoft_yvel')
        print(dc['post'])
        #print(math.sqrt(vx**2+vy**2))
        #print dc['subjd']

        if (dc['subjd'] < 0.01) & (dc['post'] == 1) & (math.sqrt(vx**2+vy**2) < 0.01):
            # Check: hand is stationary within the start position?
            win.itemconfig("start", fill="green")
            dc['post'] = 2
        elif (dc['subjd']> 0.01) & (dc['post'] == 2):
            # Check: hand is leaving start position outward?
            start_time = time.time()  # Used for computing movement speed
            dc['post'] = 3
        elif (dc['subjd'] > 0.12) & (dc['post'] == 3) & (math.sqrt(vx**2+vy**2) < 0.01):
            # Check: hand has reached target and now stationary?
            myspeed = 1000*(time.time() - start_time)
            print("Movement duration = %.1f msec"%(myspeed))
            checkEndpoint(angle,-20,20)
            notcompleted = 0


######## Some parameters that specify how we draw things onto our GUI window

from Tkinter import * # Importing the Tkinter library
master  = Tk()	      # Create an empty background window for GUI
samsung = Toplevel()  # Create another one, for the robot canvas (Samsung)
                      # Interesting, you shouldn't have 2 Tk() instances, use Toplevel()
	              # and this will solve the problem of pyimage not displayed
w, h  = 1920,1080
cursor_size  = 0.007  #  7 mm start radius
target_thick = 0.008  # 16 cm target thickness

master.geometry('%dx%d+%d+%d' % (450, 150, 500, 200))   # Nice geometry setting!!
master.title("Somatic Working Memory Test")
master.protocol("WM_DELETE_WINDOW", quit)

subjid  = StringVar()
filenum = StringVar()
mymsg   = StringVar()
varopt  = StringVar()

# Trick: Because LCD screen coordinate isn't the same as robot coordinate system, 
# we need to have a way to do the conversion so as to show the position properly.

caldata = os.popen('./robot/ParseCalData robot/cal_data.txt').read()
#print caldata.split("\t")
coeff = caldata.split('\t')

def rob_to_screen(robx, roby):
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
    varopt.set("notor_test") # default value
    
    # Entry widget for 4th row --------------
    Label(topFrame, textvariable=mymsg).grid(row=2, sticky=E)
    
    # Create buttons ---------------
    myButton1 = Button(bottomFrame, text="START", command=clickStart)
    myButton1.grid(row=0, padx = 15)
    myButton2 = Button(bottomFrame, text="Quit!", command=quit)
    myButton2.grid(row=0, column=2, padx = 15, pady = 5)


# This is to prepare robot canvas shown in Samsung LCD. All visual feedback, e.g. 
# cursor, explosion, etc are presented on this canvas.

def robot_canvas():
    # Indicate the canvas as global so I can access it from outside....
    global win
    win = Canvas(samsung, width=w, height=h)
    win.pack()
    win.create_rectangle(0, 0, w, h, fill="black")

    
def showStart(color="white"):
    #print("  Showing start position on the screen...")
    minx, miny = rob_to_screen(dc['center'][0] - cursor_size, 
                               dc['center'][1] - cursor_size)
    maxx, maxy = rob_to_screen(dc['center'][0] + cursor_size, 
                               dc['center'][1] + cursor_size)

    # Draw start circle. NOTE: Use 'tag' as an identity of a canvas object!
    win.create_oval( minx,miny,maxx,maxy, fill=color, tag="start" )

    
def showCursorBar(angle, color="yellow"):
    # Hand is now at the center? If beyond start circle, remove hand cursor
    if dc['subjd'] < 0.09:
    	# Prepare to draw current hand cursor in the screen coordinate!
    	# Edited: The robot handle coordinate isn't really centered!
    	x1, y1 = rob_to_screen(dc['subjx']-0.01,  dc['subjy']-0.007)
    	x2, y2 = rob_to_screen(dc['subjx']-0.003, dc['subjy'])
    	# Draw current hand cursor, again provide a 'tag' to it.
    	win.create_oval( x1,y1,x2,y2, fill=color, width=0, tag="hand")

    minx, miny = rob_to_screen(dc['subjx']-0.0065, dc['subjy'] - 0.0045)
    maxx, maxy = rob_to_screen(dc['subjx']-0.0065, dc['subjy'] - 0.0025)

    # First draw cursorbar with a polygon assuming it's in front (straightahead) 
    xy = [(0,miny), (w,miny), (w,maxy), (0,maxy)]
    cursorbar = win.create_polygon(xy, fill=color, tag="handbar")

    # Define pivot point as the center (start) position, but in screen coordinate!
    pivot = complex(0.5*(x1+x2), 0.5*(y1+y2))
    # We now rotate the target bar using complex number operation
    inrad  = angle*math.pi/180
    rot    = complex(math.cos(inrad),math.sin(inrad))
    newxy = []
    for x, y in xy:
        v = rot * (complex(x,y) - pivot) + pivot
        newxy.append(v.real)
        newxy.append(v.imag)
    win.coords("handbar", *newxy) # Edit coordinates by calling the tag!
    

def showTarget(angle, color="white"):
    #print("  Showing target bar on the screen...")
    minx, miny = rob_to_screen(dc['center'][0], 
                               dc['center'][1] - target_thick + targetdist)
    maxx, maxy = rob_to_screen(dc['center'][0], 
                       	       dc['center'][1] + target_thick + targetdist)
    print minx,miny,maxx,maxy
    # First draw target bar with a polygon assuming it's in front (straightahead) 
    xy = [(0,miny), (w,miny), (w,maxy), (0,maxy)]
    win.create_polygon(xy, fill=color, tag="target")

    # Then, define a pivot point as the center (start) position
    dc['pivot'] = complex(dc['center.scr'][0],dc['center.scr'][1])
    # We now rotate the target bar using complex number operation
    inrad  = angle*math.pi/180
    rot    = complex(math.cos(inrad),math.sin(inrad))
    newxy = []
    for x, y in xy:
        v = rot * (complex(x,y) - dc['pivot']) + dc['pivot']
        newxy.append(v.real)
        newxy.append(v.imag)
    win.coords("target", *newxy)  # Edit coordinates by calling the tag!
    
    # Maybe useful to capture rotated target center too!
    tx, ty = rob_to_screen(dc['center'][0], dc['center'][1] + targetdist)
    trot = rot * (complex(tx,ty) - dc['pivot']) + dc['pivot']
    dc['target.ctr'] = [trot.real, trot.imag]
    win.create_oval( trot.real, trot.imag,trot.real+2, trot.imag+2, width=5 )

    
def checkEndpoint(angle, minbias, maxbias):
    print("  Checking end-position inside target zone?")
    # The idea is to rotate back to make it a straight-ahead (90-deg) movement!
    inrad  = -angle*math.pi/180
    tx, ty = dc['subjx'], dc['subjy']
    rot    = complex(math.cos(inrad),math.sin(inrad))
    trot   = rot * (complex(tx, ty) - dc['pivot']) + dc['pivot']
    print "  Deviation from target center= %f" %trot.imag
    
    # Check the condition to display explosion when required!
    if (trot.imag > minbias) & (trot.imag < maxbias):
        dc['scores'] = dc['scores'] + 10
        print "  Explosion delivered! Current score: " + dc['scores']
        showImage("/pictures/score" + str(dc['scores']) + ".gif")
        showImage("/pictures/Explosion_final.gif")   
    

def showImage(name, px=w/2, py=h/2):
    #print "  Showing image on the canvas...."
    myImage = PhotoImage(file=mypwd + name)
    # Put a reference to image since TkImage doesn't handle image properly, image
    # won't show up! So first, I put image in a label.
    label = Label(win, bg="black", image=myImage)
    label.image = myImage # keep a reference!
    label.place(x=px, y=py)
    # Occasionally you call update() to refresh the canvas....
    samsung.update()
    time.sleep(1)
    label.config(image='')   
    # Occasionally you call update() to refresh the canvas....
    samsung.update()
    #print "  Removing inage from the canvas...."


#from PIL import ImageTk, Image

master.bind('<Return>', clickStart)

os.system("clear")

ananda.load() # Load the ananda process
print("\nRobot successfully loaded...")

print("---Now reading stiffness")
ananda.rshm('plg_stiffness')

mainGUI()
robot_canvas()

keep_going = True

while keep_going:
    # Although it maintains a main loop, this routine blocks! Use update() instead...
    #master.mainloop()
    #routine_checks()
    master.update_idletasks()
    master.update()
    time.sleep(0.01) # 10 msec frame-rate of GUI update




