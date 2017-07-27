
import wx
import wx.lib.scrolledpanel


import pandas as pd
import numpy as np
import aux
import struct

import time
import datetime
import threading




class Main(wx.Frame):


  
    def __init__(self, parent, title,participantid,runid,starttime):
        super(Main, self).__init__(parent, title=title, 
                                   size=(800, 700))

        self.current_trial = None
        self.participant = participantid
        self.runid       = runid
        self.starttime   = starttime
        
        #self.dialog = wx.FileDialog(None, 'Open', wildcard="*", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
        self.ready_for_writing = False

        self.InitUI()

        self.timer = wx.Timer(self)
        #self.timer.SetInterval(15000) # interval for autosaving
        self.Bind(wx.EVT_TIMER, self.save, self.timer)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.timer.Start(15000)

        self.Show()




    def update_enabled(self):
        """ Sets the buttons that the user is allowed to press to enabled """
        #if self.ready_for_writing and len(self.replayidt.GetValue())>0:
        #    self.saveb.Enable()
        #else:
        #    self.saveb.Disable()
        pass



    def addTextInput(self,panel,parentbox,label,size=300,units=""):
        """ Add a simple text box input to the GUI. """
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add( (10,-1) )
        txt = wx.StaticText(panel,label=label)
        txt.SetFont(self.font)
        hbox.Add( txt )
        hbox.Add( (10,-1) )
        inp = wx.TextCtrl(panel,size=(size,-1))
        inp.SetFont(self.font)
        inp.SetEditable(True)
        hbox.Add( inp )
        hbox.Add( (10,-1) )
        if units!="":
            txt = wx.StaticText(panel,label=units)
            txt.SetFont(self.font)
            hbox.Add( txt )

        parentbox.Add( (-1,10) )
        parentbox.Add(hbox)
        parentbox.Add( (-1,10) )

        self.text_inputs.append((label,inp))

        return inp



    def addMultiLineText(self,panel,parentbox,label,size=300,units=""):
        """ Add a simple text box input to the GUI. """

        hbox = wx.BoxSizer(wx.VERTICAL)
        hbox.Add( (10,-1) )
        for ln in label.split("\n"):
            txt = wx.StaticText(panel,label=ln.strip())
            txt.SetFont(self.font)
            hbox.Add( txt )
        hbox.Add( (10,-1) )
        inp = wx.TextCtrl(panel,size=(size,130),style=wx.TE_MULTILINE)
        inp.SetFont(self.font)

        inp.SetEditable(True)
        hbox.Add( inp )
        hbox.Add( (10,-1) )
        if units!="":
            txt = wx.StaticText(panel,label=units)
            txt.SetFont(self.font)
            hbox.Add( txt )

        parentbox.Add( (-1,10) )
        bx = wx.BoxSizer(wx.HORIZONTAL)
        bx.Add( (10,-1) )
        bx.Add( hbox )
        bx.Add( (10,-1) )

        parentbox.Add(bx)
        parentbox.Add( (-1,10) )

        self.text_inputs.append((label,inp))

        return inp






    def addExplanation(self,panel,parentbox,expl):
        parentbox.Add( (-1,10) )
        for ln in expl.split("\n"):
            #print "Adding %s"%ln
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            hbox.Add( (20,-1) )
            txt = wx.StaticText(panel,label=ln.strip())
            txt.SetFont(self.font)
            hbox.Add( txt )
            hbox.Add( (20,-1) )
            parentbox.Add(hbox)
        parentbox.Add( (-1,10) )





    def addRadio(self,panel,parentbox,label,options,size=300):
        return self.addRadioExtra(panel,parentbox,label,options,{},size)







    def addRadioExtra(self,panel,parentbox,label,options,extra={},size=300):
        """ Add a set of radio buttons. 

        Arguments
        extra : here you can supply a dict, where the keys are options, and if the user selects this option then a textbox appears allowing them to enter further information.
        """
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add( (10,-1) )
        txt = wx.StaticText(panel,label=label)
        txt.SetFont(self.font)
        hbox.Add( txt )
        hbox.Add( (10,-1) )

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox)

        buttons = []

        # Now comes a hack to allow none of the buttons to be selected, at least initially.
        # The hack is to add another button which is hidden and is selected by default.
        # see http://wxpython-users.1045709.n5.nabble.com/Unselecting-radiobuttons-td2362359.html
        but = wx.RadioButton(panel,
                             label="[NOTHING SELECTED]",
                             name="[NOTHING SELECTED]",style=wx.RB_GROUP)
        but.SetValue(True)
        but.Hide()
        vbox.Add(but)
        buttons.append(but)


        for i,option in enumerate(options):
            style = 0
            but = wx.RadioButton(panel,label=option,name=option,style=style)
            but.SetFont(self.font)
            #but.Bind(wx.EVT_RADIOBUTTON,eventprocessor)
            #but.SetValue(False)
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            hbox.Add( (30,-1) )
            hbox.Add( but )
            buttons.append(but)
            if option in extra.keys(): # If there are extra options for this one
                hbox.Add( (30,-1) )
                txt = wx.StaticText(panel,label=extra[option])
                txt.SetFont(self.font)
                hbox.Add( txt )
                hbox.Add( (10,-1) )
                inp = wx.TextCtrl(panel,size=(300,-1))
                inp.SetEditable(True)
                inp.SetFont(self.font)
                hbox.Add(inp)
                self.text_inputs.append((label+"->"+extra[option],inp))
            vbox.Add(hbox)


            #def eventprocessor(e):
            #rb = e.GetEventObject()
            #if rb in dependents.keys()



        #hbox.Add(vbox)

        parentbox.Add( (-1,10) )
        parentbox.Add(vbox)
        parentbox.Add( (-1,10) )

        self.radio_inputs.append((label,buttons))

        #self.text_inputs.append((label,inp))

        return








    def addHeader(self,panel,parentbox,label):
        lbl = wx.StaticText(panel,label=label)
        lbl.SetForegroundColour((0,0,255)) # set text color
        lbl.SetFont(self.boldfont)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add( (5,-1) )
        hbox.Add(lbl)
        parentbox.Add( (-1,50) )
        parentbox.Add(hbox)
        
        



    def save(self,e):
        self.dosave()


    def dosave(self):
        """ Save the information the user has entered so far to file. """
        participant = self.participant
        fname = "data/%s.%s.questionnaire.%s.yaml"%(participant,self.runid,self.starttime)
        print("Saving to %s"%fname)
        
        f = open(fname,'w')
        def writeoption(option,val):
            o = aux.safe_str(option)
            v = aux.safe_str(val)
            safeopt = o.replace('\n','\\n')
            safeval = v.replace('\n','\\n')
            f.write("\"%s\" : \"%s\"\n"%(safeopt,safeval))
         
        writeoption("Timestamp",time.time())
        writeoption("Time point",self.runid)
        writeoption("Date/Time",datetime.datetime.now().strftime("%Y-%d-%m %H:%M:%S"))
        for (label,inp) in self.text_inputs:
            writeoption(label,inp.GetValue())

        for (label,butts) in self.radio_inputs:
            # Let's simplify this a bit and look for the selected value
            for butt in butts:
                if butt.GetValue():
                    lbl = butt.GetLabel()
                    if lbl=="":
                        lbl = butt.GetName()
                    writeoption(label,lbl)

        f.close()
        




    def InitUI(self):
    
        panel = wx.lib.scrolledpanel.ScrolledPanel(self,-1,
                                                    #size=(screenWidth,400), 
                                                    style=wx.SIMPLE_BORDER)
        #panel = wx.Panel(self)
        self.text_inputs = []
        self.radio_inputs = []

        self.font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        self.font.SetPointSize(11)
        self.boldfont = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        self.boldfont.SetPointSize(14)

        vbox = wx.BoxSizer(wx.VERTICAL)
        
        self.participantid = self.addTextInput(panel,vbox,"Participant ID")
        self.participantid.SetValue(self.participant)
        self.participantid.SetEditable(False)
        self.participantid.SetBackgroundColour((0,255,0))

        

        if self.runid=="POST":

            self.addExplanation(panel,vbox,"Please fill out this questionnaire completely.\nScroll down to see additional questions.\n\nThank you in advance for your time.")

            self.addMultiLineText(panel,vbox,"You were asked to reach perpendicularly to the target line.\nIs the instruction confusing?",size=600)
            
            self.addMultiLineText(panel,vbox,"How difficult was it to get explosions?",size=600)

            self.addMultiLineText(panel,vbox,"Was it easier or harder when the target bar (i.e. the grey line that you had to reach to) \nwas on the left or right side?",size=600)

            self.addMultiLineText(panel,vbox,"When you get an explosion, did it indeed feel like you moved exactly perpendicularly\nto the target bar? Or did it feel like you were moving not exactly perpendicularly?\nWas this different between moving to the left or right side?",size=600)
            
            self.addMultiLineText(panel,vbox,"Do you have any other observations that you would like to tell us about?",size=600)




        self.addExplanation(panel,vbox,"This is the end of the questionnaire.\nPlease leave this window open and notify the experimenter that you have completed this task.\n\nThank you.")


        savebtn = wx.Button(panel, label='Save', size=(70, 30))
        savebtn.Bind(wx.EVT_BUTTON,self.save)
        vbox.Add(savebtn)


        panel.SetupScrolling()
        panel.SetSizer(vbox)
        #panel.Add(panel2)
        #panel.SetSizer(panel2)




    def OnClose(self, e):
        self.dosave()
        self.timer.Stop()
        self.Destroy()




if __name__ == '__main__':
  
    participantid = aux.ask_string(message="Please enter the participant ID")

    #runid = ""
    #while runid.upper() not in ["PRE","POST"]:
    #    runid         = aux.ask_string(message="Please enter the time point (pre/post)")
    #    if runid=="" or runid==None:
    #        sys.exit(0)
    runid="post"
            

    starttime = datetime.datetime.now().strftime("%Y-%d-%m%Hh%Mm%S")
    if participantid!="":

        app = wx.App()
        n = Main(None, title='MCL Biographical Sheet', participantid=participantid,runid=runid.upper(),starttime = starttime)
        #n.__close_callback = lambda: True
        app.MainLoop()


