
import numpy as np
import colorsys

def get_colors(num_colors):
    colors=[]
    for i in np.arange(0., 360., 360. / num_colors):
        hue = i/360.
        lightness = (20 + np.random.rand() * 10)/100.
        saturation = (90 + np.random.rand() * 10)/100.
        colors.append(colorsys.hls_to_rgb(hue, lightness, saturation))
    return colors






def ask_path(wildcard="*"):
    # Ask for a file
    import wx
    app = wx.App(None)
    style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE
    dialog = wx.FileDialog(None, 'Open', wildcard=wildcard, style=style)
    if dialog.ShowModal() == wx.ID_OK:
        path = dialog.GetPaths()
    else:
        path = None
    dialog.Destroy()
    return path








def ask_string(parent=None,message="",default_value=""):
    import wx
    app = wx.App(parent)
    dlg = wx.TextEntryDialog(parent, message, defaultValue=default_value)
    res = dlg.ShowModal()
    if res==wx.ID_OK:
        result = dlg.GetValue()
        dlg.Destroy()
        return result
    else:
        return None




def show_message(message,title):
    # Ask for a file
    import wx
    app = wx.App(None)
    #style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
    wx.MessageBox(message,title,
                  wx.OK | wx.ICON_INFORMATION)
    return 











def remove_adjacent_duplicates(lst):
    ## Given a list, we remove adjacent duplicates
    result = []
    first = True
    last = None
    for x in list(lst):
        if first or last!=x:
            result.append(x)
            last=x
            first=False
    return result
            









def safe_unicode(obj, *args):
    """ return the unicode representation of obj """
    try:
        return unicode(obj, *args)
    except UnicodeDecodeError:
        # obj is byte string
        ascii_text = str(obj).encode('string_escape')
        return unicode(ascii_text)

def safe_str(obj):
    """ return the byte string representation of obj """
    s = obj
    try:
        s = str(s)
    except UnicodeEncodeError:
        # obj is unicode
        s = unicode(obj).encode('utf-8')
    return s
