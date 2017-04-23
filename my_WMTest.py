#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 20:24:50 2017 @author: ae2010
This code is used for reinforcement-based motor learning. It has the same working principle 
as the "my_WMTest.tcl", "my_VisSpTest.tcl" code in Tcl for the old suzuki machine.

Revisions: Confirming the new code works like the old Tcl code (Apr 19) 
           Major cleanup on the code (Apr 21)
"""

import robot.interface as ananda
import os.path
import time
import json
import math

from Tkinter import *	# Importing the Tkinter library

# Global definition of variables
dc = {}              # dictionary for important param
mypwd = os.getcwd()  # retrieve code current directory

# Global definition of constants
ANSWERFLAG  = 0      # Flag=1 means subject has responded
TARGETBAR   = True   # Showing target bar?? Set=0 to just show the target circle!
TARGETDIST  = 0.15   # move 15 cm from the center position (default!)
TARGETTHICK = 0.008  # 16 cm target thickness
CURSOR_SIZE = 0.009  #  9 mm start radius
TARGETHOLD  = 0.5    # 500 msec delay at the target point
WAITTIME    = 1.0    # 1000 msec general wait or delay time 
MOVE_SPEED  = 0.9    # duration (in sec) of the robot moving the subject to the center
w, h  = 1920,1080

txtmsg  = ""


####### Create various functions using 'def' keyword

def quit():
    """Subroutine to EXIT the program and stop everything."""
    global keep_going
    keep_going = False
    reach_target = False
    master.destroy()
    ananda.unload()  # Close/kill robot process


def playAudio():
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
        dc['cx'], dc['cy'] = ananda.rshm('x'),ananda.rshm('y')
        txt_file = open(dc['logpath']+subjid.get()+"_center.txt", "w")
        txt_file.write("%f,%f"%(dc['cx'],dc['cy']))
        txt_file.close()
    # Also useful to define center pos in the screen coordinate!       
    dc['c.scr'] = rob_to_screen(dc['cx'],dc['cy'])


def goToCenter(speed):
    """ Move to the center or start position and stay there"""
    # Ensure this is a null field first (because we will be updating the position)
    ananda.controller(0)
    print("  Now moving to center: %f,%f"%(dc['cx'],dc['cy']))
    # Send command to move to cx,cy
    ananda.move_stay(dc['cx'],dc['cy'],speed)
    
    #while not ananda.move_is_done(): pass
    #print("  Movement completed!")
    # Put flag to 1, indicating robot handle @ center position
    dc['post'] = 1


def clickStart(event):
    """ Start main program, taking "Enter" button as input-event """
 
    # First, check whether the entry fields have usable text (need subjID, a file number, etc.)
    if not subjid.get() or not filenum.get().isdigit():
        print("##Error## Subject ID and/or file numbers are empty or file number is not a digit!")
        return

    dc['logfileID'] = subjid.get()+filenum.get()
    dc['logpath'] = mypwd+"/data/"+subjid.get()+"_data/"

    if not subjid.get() or not filenum.get():
        print("##Error## Subject ID and/or file numbers are empty!")
    else:
        print "---Loading for block %s, subject %s..." %(filenum.get(),subjid.get())
        filepath = mypwd+"/exper_design/"+dc['logfileID']+".txt"             
        #print filepath
        stages = read_design_file(filepath)   # Next stage depends if file loaded successfully
        print "Press <Enter> or Quit-button to continue!\n"

    chk.config(state='disabled')
    e1.config(state='disabled')
    e2.config(state='disabled')
    getCenter()
    goToCenter(3)

    print "Press <Enter> or Quit-button to continue!\n"
    # Added check to ensure existing logfile isn't overwritten
    wmtest="Som_" if somatic.get() else "Vis_"
    if os.path.exists("%s%s_%s.txt"%(dc['logpath'],wmtest,dc['logfileID'])):
        print "Duplicate: %s%s_%s.txt"%(dc['logpath'],wmtest,dc['logfileID']) 

    if somatic.get(): mymsg.set("Note: This is Somatic WM Test (default)") 
    else: mymsg.set("Note = This is Visuospatial WM Test .....")
    master.update()
        
    # Using tag, update 'canvas' color depending on the type of test!
    #mybg="black" if somatic.get() else mybg="white"
    #win.itemconfig("canvas", fill=mybg)

    if int(filenum.get()) == 0:
        # This is only for filenum = 0, familiarization trials!
        print("Entering Practice Loop now.........")
        runBlock(1)    
    else:
	# Once set, we're ready for the main loop (actual test!)
        print("Entering Main Loop now.........")
        runBlock(0)	   


def read_design_file(mpath):
    """ Based on subj_id & block number, read experiment design file!"""
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
    global ANSWERFLAG
    print("Waiting for subject's response")
    while (not ANSWERFLAG):
        master.update_idletasks()
        master.update()
        time.sleep(0.3)
    RT = 1000*(time.time() - start_time)  # RT in m-sec
    print "---Trial-%d   ANSWER:%d    RT:%d"%(index,dc['answer'],RT)
    ANSWERFLAG = 0
    return(RT)

def clickYes(event):
    global ANSWERFLAG
    print "Left key pressed to answer YES!"
    dc['answer']=1
    ANSWERFLAG = 1

def clickNo(event):
    global ANSWERFLAG
    print "Right key pressed to answer NO!"
    dc['answer']=0
    ANSWERFLAG = 1


def angle_pos(theta):
    """ Convert endpoint target direction to robot coordinates w.r.t center position """
    theta_rad = theta*math.pi/180 # convert to radian
    targetX = TARGETDIST * math.cos(theta_rad) + dc['cx']
    targetY = TARGETDIST * math.sin(theta_rad) + dc['cy']
    print("  Moving to %f, %f"%(targetX,targetY))
    ananda.move_stay(targetX, targetY, MOVE_SPEED)
    #ananda.status = ananda.move_is_done()
    #while not ananda.status:   # check if movement is done
    #    ananda.status = ananda.move_is_done()
        #time.sleep(0.07)
    print("  Movement completed!")


def visual_pos(theta):
    """ Convert endpoint target direction to robot coordinates w.r.t center position """
    theta_rad = theta*math.pi/180 # convert to radian
    targetX = TARGETDIST * math.cos(theta_rad) + dc['cx']
    targetY = TARGETDIST * math.sin(theta_rad) + dc['cy']
    showStart(targetX,targetY)
    time.sleep(0.07)


# Showing visual stimulus on the LCD screen coordinate, for 'TARGETHOLD' msec
def showStart(x,y,color="white"):
    print("  Showing stimulus at %f, %f"%(x,y))
    minx, miny = rob_to_screen(x - 0.008, y - 0.008)
    maxx, maxy = rob_to_screen(x + 0.008, y + 0.008)
    # Draw start circle. NOTE: Use 'tag' as an identity of a canvas object!
    win.create_oval( minx,miny,maxx,maxy, fill=color, tag="start" )
    samsung.update()
    time.sleep(TARGETHOLD)
    time.sleep(TARGETHOLD)
    win.delete("start")
    samsung.update()
    print("  Presentation completed!")


# The main code once 'Start' or <Enter> key is pressed
def runBlock (practice_flag):
    """ The main code once 'Start' or <Enter> key is pressed """
    if practice_flag: print "Familiarization Step-1"

    for xxx in dc['mydesign']:
        index  = xxx['trial']
        anchors= xxx['anchors']
        probe  = xxx['probe']
        delay  = xxx['delay']

        print("\nNew Round- " + str(index))
        showImage("newround.gif")
        time.sleep(TARGETHOLD)
        dc['log'] = str(index) + " "   # string to be saved later!

	to_target(anchors)    # <<<<<<

        print ("  Waiting for %d msec"%(delay))
        if practice_flag: print "Familiarization Step-2" 
        time.sleep(delay/1000)

	to_target(probe)      # <<<<<<

        RT = doAnswer(index)
        dc['log']=dc['log']+"  ANSWER:%d  RT:%d  DELAY:%d\n"%(dc['answer'],RT,delay)

        if practice_flag: print "Familiarization Step-3" 
        #print(dc['log'])
        saveLog()   # Call save function

    print("\n#### NOTE = Test has ended!!")


def to_target(directions):
    """ This handles the whole segment when subject moves to hidden target """
    if type(directions)==list:
        # If this is a list, it means a set of anchors
        for direction in directions:
            print("Anchor direction: " + str(direction))
            angle_pos(direction) if somatic.get() else visual_pos(direction)
            time.sleep(TARGETHOLD)
            #goToCenter(1) if somatic.get() else pass  # Go back to centre!
            time.sleep(TARGETHOLD)
            dc['log'] = dc['log'] + " " + str(direction)
    	    # Occasionally call update(). This allows us to press buttons while looping.
            master.update()
    else:
        # Else, it means just a test direction or probe!
        print("Probe direction: " + str(directions))
	angle_pos(directions) if somatic.get() else visual_pos(directions)
        time.sleep(TARGETHOLD)
        #goToCenter(1) if somatic.get() else pass  # Go back to centre!
        dc['log'] = dc['log'] + " " + str(directions)



# Function save logfile and mkdir if needed
def saveLog():
    print("---Saving trial log.....")   
    if not os.path.exists(dc['logpath']):
	os.makedirs(dc['logpath'])
    wmtest="Som_" if somatic.get() else "Vis_"
    with open(dc['logpath']+wmtest+dc['logfileID']+".txt",'aw') as log_file:
        log_file.write(dc['log'])  # Save every trial as text line


######## Some parameters that specify how we draw things onto our GUI window

from Tkinter import * # Importing the Tkinter library
master  = Tk()	      # Create an empty background window for GUI
samsung = Toplevel()  # Create another one, for the robot canvas (Samsung)
                      # Interesting, you shouldn't have 2 Tk() instances, use Toplevel()
	              # and this will solve the problem of pyimage not displayed

w, h = 1920,1080
master.geometry('%dx%d+%d+%d' % (370, 170, 500, 200))   # Nice geometry setting!!
master.protocol("WM_DELETE_WINDOW", quit)

subjid  = StringVar()
filenum = StringVar()
mymsg   = StringVar()
somatic = BooleanVar()

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
    bottomFrame = Frame(master, width=400, height=100)
    bottomFrame.pack(side=BOTTOM, expand = 1)
    
    # Important: This maintains frame size, no shrinking
    topFrame.pack_propagate(False)
    bottomFrame.pack_propagate(False)
    
    # Make Entry widgets global so that we can configure from outside    
    global e1, e2
    # Entry widget for 1st row --------------
    Label(topFrame, text="Subject ID: ").grid(row=0, sticky=E, pady=(13,20))
    e1 = Entry(topFrame, width = 6, bd =1, textvariable = subjid)
    e1.grid(row=0, column=1, pady=(13,20))
    e1.insert(END, "aes")
    Label(topFrame, text="File Number: ").grid(row=0, column=3, padx = (30,5),  pady=(13,20))
    e2 = Entry(topFrame, width = 3, bd =1, textvariable = filenum)
    e2.grid(row=0, column=4, pady=(13,20))
    e2.insert(END, "1")

    # Entry widget for 2nd row --------------
    msg = Entry(topFrame, width = 50, bd=0, textvariable=mymsg)
    msg.grid(row=2, columnspan=10)
    #msg.config(highlightbackground="red")
    mymsg.set("Enter subject ID, file #, then press <ENTER> key!")

    # Check button --------------
    global chk
    chk = Checkbutton(bottomFrame, text="Somatic?", variable=somatic)
    chk.grid(row=0, column=1, padx = 15)
    somatic.set(1)

    # Create buttons ---------------
    myButton1 = Button(bottomFrame, text=" Yes! ", bg="#0FAF0F", command=clickYes)
    myButton1.grid(row=0, padx = 10)
    myButton2 = Button(bottomFrame, text=" No! ", bg="#AF0F0F", command=clickNo)
    myButton2.grid(row=0, column=2, padx = 10)
    myButton3 = Button(bottomFrame, text="  QUIT  ", command=quit)
    myButton3.grid(row=1, column=1, padx = 10, pady = 5)
    


def robot_canvas():
    # Indicate the canvas as global so I can access it from outside....
    global win
    win = Canvas(samsung, width=w, height=h)  # 'win' is a canvas on Samsung()
    win.pack()
    win.create_rectangle(0, 0, w, h, fill="black", tag="canvas")

def showImage(name, px=650, py=450):
    #print "  Showing image on the canvas...."
    myImage = PhotoImage(file=mypwd + "/pictures/" + name)
    # Put a reference to image since TkImage doesn't handle image properly, image
    # won't show up! So first, I put image in a label.
    label = Label(win, bg="white", image=myImage)
    label.image = myImage # keep a reference!
    label.place(x=px, y=py)
    time.sleep(1.25)
    label.config(image='')   
    # Occasionally you call update() to refresh the canvas....
    samsung.update()
    #print "  Removing inage from the canvas...."


master.bind('<Return>', clickStart)
master.bind('<Left>'  , clickYes)
master.bind('<Right>' , clickNo)

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
    master.title("-- Somatic WM Test --") if somatic.get() else master.title("Visuospatial WM Test")
    time.sleep(0.1) # frame rate of our GUI update




