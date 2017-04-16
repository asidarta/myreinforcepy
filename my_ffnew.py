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
mypwd   = os.getcwd() # retrieve code current directory
mydict  = {}          # dictionary for important param
stages  = 0           # to enter clickStart soubroutine step-by-step
answerflag = 0        # Flag=1 means subject has responded
targetdist = 0.15     # move 15 cm from the center position (default!)
movetime = 0.9	      # 900 msec default movement speed to a target

mydict['post'] = 0 # (0: hand moving to start-not ready, 
#                     1: hand within/in the start position,
#                     2: hand on the way to target, 
#                     3: hand within/in the target)


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
    if (os.path.isfile(mydict['logpath']+subjid.get()+"_center.txt")):
        #txt = open(mypwd + "/data/and_center.txt", "r").readlines()
        center = [[float(v) for v in txt.split(",")] for txt in open(
                      mydict['logpath']+subjid.get()+"_center.txt", "r").readlines()]
        #print(center)
        print("Loading existing coordinate: %f, %f"%(center[0][0],center[0][1]))
        mydict['center.pos'] = (center[0][0],center[0][1])
    else:
        print("This is a new subject. Center position saved.")
        mydict['center.pos'] = ananda.rshm('x'),ananda.rshm('y')
        txt_file = open(mydict['logpath']+subjid.get()+"_center.txt", "w")
        txt_file.write("%f,%f"%mydict['center.pos'])
        txt_file.close()
    # Also useful to define center pos in the screen coordinate!       
    mydict['center.scr'] = rob_to_screen(mydict['center.pos'][0], 
                                         mydict['center.pos'][1])

# Initiate movement to the center (start) coordinate
def goToCenter(speed):
    # Ensure this is a null field first (because we will be updating the position)
    #ananda.controller(0)
    print("  Now moving to center: %f,%f"%mydict['center.pos'])
    # Send command to move to cx,cy
    #ananda.move_stay(mydict['center.pos'][0],mydict['center.pos'][1],speed)
    #ananda.status = ananda.move_is_done()
    #while not #ananda.status:   # check if movement is done
        #ananda.status = ananda.move_is_done()
        #time.sleep(0.07)
    print("  Movement completed!")
    # Put flag to 1, indicating robot handle @ center position
    mydict['post'] = 1


# Start main program, taking "Enter" button as input-event
def clickStart(event):
    global stages
    if (stages == 0):
        mydict['logfileID'] = subjid.get()+filenum.get()
        mydict['logpath'] = mypwd + "/data/" + subjid.get() + "_data/"

        if not(subjid.get()) or not(filenum.get()):
            print("##Error## Subject ID and/or file numbers are empty!")
        # Added check to ensure existing logfile isn't overwritten
        elif (os.path.exists(mydict['logpath']+"motorLog_"+mydict['logfileID']+".txt")):
            print "Duplicate: "+mydict['logpath']+"motorLog_"+mydict['logfileID']+".txt" 
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
            mydict['mydesign'] = json.load(f)
        #print mydict['mydesign']
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
    #print(ananda.status())
    showStart("white")
    showTarget(135,"green")
    # As the 1st element contains non-trial related setting, we remove it!
    for xxx in mydict['mydesign'][1:]:
        index   = xxx['trial']
        FFset   = xxx['FField']
        angle   = xxx['angle']
        Feedback= xxx['Feedback']
        Score   = xxx['Score']
        Cursor  = xxx['Cursor']
        homewait= xxx['homewait']
        targetwait= xxx['targetwait']
        print("\nNew Round- " + str(index))
        time.sleep(homewait/1000)
        #mydict['logAnswer'] = str(index) + " "   # string to be saved later!
        to_target()
        checkEndpoint(135,-20,20)
        print("  Waiting for " + str(targetwait) + "msec")
        time.sleep(targetwait/1000)
        goToCenter(1.5)  # Go back to center!
        time.sleep(targetwait/1000)
	#print(mydict['logAnswer'])
	#with open(mydict['logpath'],'aw') as log_file:
         #      print("  Saving trial log.....")
          #     log_file.write(mydict['logAnswer'])  # Save every trial as text line
    print("\nNOTE = Test has ended!")


# This handles the whole segment when subject moves to hidden target
def to_target():
    notcompleted = 1
    mydict['subjx']=0
    mydict['subjy']=0
    
    while notcompleted:
        # Occasionally you call update() to refresh the canvas....
        master.update()
        showStart("white")
        showTarget(135,"green")
        # Occasionally you call update() to refresh the canvas....
        samsung.update()
        showCursor()

        # Hand position at the center. When subject hand is also stationary 
    	# and below 0.005 from the center point, then ready to move!
        vx, vy = ananda.rshm('fsoft_xvel'), ananda.rshm('fsoft_yvel')
        time.sleep(0.05) # frame rate of our canvas update
        print(mydict['post'])
        print(math.sqrt(vx**2+vy**2))
        subjd = math.sqrt(mydict['subjx'] **2 + mydict['subjy'] **2)
        if (subjd < 20) & (mydict['post'] == 1) & (math.sqrt(vx**2+vy**2) < 0.01):
            mydict['post'] = 2
        elif (subjd > 100) & (mydict['post'] == 2):
            start_time = time.time()  # Used for computing movement speed
            mydict['post'] = 3
        elif mydict['post'] == 3:
            myspeed = 1000*(time.time() - start_time)  # speed in m-sec
            print("Movement duration = %.1f msec"%(myspeed))
            notcompleted = 0


######## Some parameters that specify how we draw things onto our GUI window

from Tkinter import *	# Importing the Tkinter library
master  = Tk()		# Create an empty background window for GUI
samsung = Toplevel()    # Create another one, for the robot canvas (Samsung)
                        # Interesting, you shouldn't have 2 Tk() instances, use Toplevel()
			# and this will solve the problem of pyimage not displayed
w, h  = 1920,1080
cw,ch = w/2,h/2

robot_scale  = 700
cursor_size  = 10
start_size   = 0.02   # 1 cm start radius
target_thick = 0.02   # 1 cm target thickness

master.geometry('%dx%d+%d+%d' % (450, 150, 500, 200))   # Nice geometry setting!!
master.title("Somatic Working Memory Test")
master.protocol("WM_DELETE_WINDOW", quit)

subjid  = StringVar()
filenum = StringVar()
mymsg   = StringVar()
varopt  = StringVar()

# Trick: Because visual information on LCD screen depends on robot position, we need 
# to have a system to convert robot coordinates into screen coordinates, vice-versa!
def rob_to_screen(x,y):
    return (cw + x*robot_scale, ch + y*robot_scale)

def screen_to_rob(x,y):
    return ( (x-cw)/float(robot_scale),
             (y-ch)/float(-robot_scale) )


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
    #minx,miny = rob_to_screen(-.4,-.2)  #  ?????
    #maxx,maxy = rob_to_screen( .4,.3)

    
def showStart(color="white"):
    #print("  Showing start position on the screen...")
    minx, miny = rob_to_screen(mydict['center.pos'][0] - start_size, 
                               mydict['center.pos'][1] - start_size)
    maxx, maxy = rob_to_screen(mydict['center.pos'][0] + start_size, 
                               mydict['center.pos'][1] + start_size)

    # Draw start circle using oval
    win.create_oval( minx, miny, maxx, maxy, fill=color, width=0 )

    
def showTarget(angle, color="white"):
    #print("  Showing target bar on the screen...")
    minx, miny = rob_to_screen(mydict['center.pos'][0], 
                               mydict['center.pos'][1] - target_thick + targetdist)
    maxx, maxy = rob_to_screen(mydict['center.pos'][0], 
                               mydict['center.pos'][1] + target_thick + targetdist)
    # Draw a circle using a polygon
    xy = [(-minx*3,miny), (minx*3,miny), (maxx*3,maxy), (-maxx*3,maxy)]
    polygon_item = win.create_polygon(xy, fill=color)

    # Define pivoting point as the center (start) position.
    pivot  = complex(mydict['center.scr'][0],mydict['center.scr'][1])
    # We now rotate the target bar using complex number operation
    inrad  = angle*math.pi/180
    rot    = complex(math.cos(inrad),math.sin(inrad))
    newxy = []
    for x, y in xy:
        v = rot * (complex(x, y) - pivot) + pivot
        newxy.append(v.real)
        newxy.append(v.imag)
    win.coords(polygon_item, *newxy)
    
    # Maybe useful to capture rotated target center too!
    tx, ty = rob_to_screen(mydict['center.pos'][0], mydict['center.pos'][1] + targetdist)
    trot = rot * (complex(tx, ty) - pivot) + pivot
    mydict['target.ctr'] = [trot.real, trot.imag]
    win.create_oval( trot.real, trot.imag,trot.real+2, trot.imag+2, width=5 )

    
def showCursor():
    #print("  Showing current hand position on the screen...")
    #x,y = 0.03,0.09
    x,y = ananda.rshm('x'),ananda.rshm('y')
    mydict['subjx'], mydict['subjy'] = x, y

    # Compute current distance from the center/start--robot coordinate! 
    subjd = math.sqrt(x **2 + y **2) 
    #print("Distance from center position= %f"%(subjd))
    # Prepare to draw current hand cursor--screen coordinate!
    minx, miny = rob_to_screen(x-start_size/2, y-start_size/2)
    maxx, maxy = rob_to_screen(x+start_size/2, y+start_size/2)
    #print minx, miny
    # Occasionally you call update() to refresh the canvas....
    samsung.update()
    if subjd > 50:
        mycursor = win.create_oval( minx, miny, maxx, maxy, fill="green" )
    else:
        mycursor = win.create_oval( minx, miny, maxx, maxy, fill="yellow" )
    #time.sleep(0.1)
    # Occasionally you call update() to refresh the canvas....
    samsung.update()
    win.delete(mycursor)
    # Occasionally you call update() to refresh the canvas....
    samsung.update()        

    
def checkEndpoint(angle, minbias, maxbias):
    print("  Checking end-position inside target zone?")
    # The idea is to rotate back to make it a straight-ahead (90-deg) movement!
    cx, cy = mydict['center.pos'][0], mydict['center.pos'][1]
    pivot  = complex(cx, cy)
    inrad  = angle*math.pi/180
    tx, ty = mydict['subjx'], mydict['subjy']
    rot    = complex(math.cos(inrad),math.sin(inrad))
    trot = -rot * (complex(tx, ty) - pivot) + pivot
    print "  Deviation from target center= %f" %trot.imag
    
    # Check the condition to display explosion when required!
    if (trot.imag > minbias) & (trot.imag < maxbias):
        showImage("caution.gif")   
    
def showImage(name, px=500, py=500):
    #print "  Showing image on the canvas...."
    myImage = PhotoImage(file=mypwd + "/misc/" + name)
    # Put a reference to image since TkImage doesn't handle image properly, image
    # won't show up! So first, I put image in a label.
    label = Label(win, bg="black", image=myImage)
    label.image = myImage # keep a reference!
    label.place(x=px, y=py)
    time.sleep(0.75)
    # Occasionally you call update() to refresh the canvas....
    samsung.update()
    label.config(image='')   
    #print "  Removing inage from the canvas...."


#from PIL import ImageTk, Image

master.bind('<Return>', clickStart)
#samsung.bind("<Button-1>", showCursor) # click callback


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




