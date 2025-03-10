
import platform
import numpy as np
import pyaudio
import wave
import wx
import wx.lib.agw.knobctrl as KC
from threading import Thread

from src.classes.audiodata import AudioData
from src.classes.compressiondata import CompressionData

if platform.system() == "Windows":
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

# ------------------------------------------------------------
# global variables, needed for thread
# ------------------------------------------------------------

audio_data = AudioData()
compression_data = CompressionData()

CHUNK = 2048
FORMAT = pyaudio.paInt16

paudio = pyaudio.PyAudio()        
stream = None
wav = None
audio_array = np.zeros(CHUNK, dtype=np.int16)

class FrameMain(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # ------------ window config ------------ #

        self.SetTitle("Audio Compressor")
        self.SetClientSize(self.FromDIP(wx.Size(700, 500)))

        # ------------------------------------------------------------
        # main panel
        # ------------------------------------------------------------

        panel_main = wx.Panel(self)
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        panel_main.SetSizer(sizer_main)

        # ------------------------------------------------------------
        # top staticbox
        # ------------------------------------------------------------

        staticbox_top = wx.StaticBox(panel_main, label="Audio Visualization")
        sizer_staticbox_top = wx.BoxSizer(wx.VERTICAL)
        staticbox_top.SetSizer(sizer_staticbox_top)

        # -------- complete wave visuals -------- #

        self.visualization_panel_top = wx.Panel(staticbox_top, size=self.FromDIP(wx.Size(-1, 70)))
        self.visualization_panel_top.SetBackgroundColour(wx.RED)

        # ---------- real time visuals ---------- #
        
        self.visualization_panel_bottom = wx.Panel(staticbox_top, size=self.FromDIP(wx.Size(-1, 70)))
        self.visualization_panel_bottom.SetBackgroundColour(wx.BLACK)

        self.visualization_panel_bottom.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        # --------- add panels to sizer --------- #

        sizer_staticbox_top.Add(wx.Window(staticbox_top), 0, wx.EXPAND|wx.TOP, 30)
        sizer_staticbox_top.Add(self.visualization_panel_top, 0, wx.EXPAND|wx.ALL, 5)
        sizer_staticbox_top.Add(self.visualization_panel_bottom, 0, wx.EXPAND|wx.ALL, 5)

        # ------------------------------------------------------------
        # bottom staticbox
        # ------------------------------------------------------------

        staticbox_bottom = wx.StaticBox(panel_main, label="Compression properties")
        sizer_staticbox_bottom = wx.GridBagSizer()
        staticbox_bottom.SetSizer(sizer_staticbox_bottom)

        # -------------- threshold -------------- #

        compressor_panel_threshold = wx.Panel(staticbox_bottom)
        compressor_panel_threshold.SetBackgroundColour(wx.YELLOW)
        sizer_threshold = wx.BoxSizer(wx.VERTICAL)
        compressor_panel_threshold.SetSizer(sizer_threshold)

        knob_threshold = KC.KnobCtrl(compressor_panel_threshold, size=self.FromDIP(wx.Size(150, 150)))
        text_value_threshold = wx.StaticText(compressor_panel_threshold, label="0 Db")

        knob_threshold.SetTags(range(0, 151, 10))
        knob_threshold.SetAngularRange(-45, 225)
        knob_threshold.SetValue(45)

        sizer_threshold.Add(wx.StaticText(compressor_panel_threshold, label="Threshold"), flag=wx.ALIGN_CENTER_HORIZONTAL)
        sizer_threshold.Add(knob_threshold, flag=wx.ALIGN_CENTER_HORIZONTAL)
        sizer_threshold.Add(text_value_threshold, flag=wx.ALIGN_CENTER_HORIZONTAL)

        sizer_staticbox_bottom.Add(compressor_panel_threshold, pos=(0, 0), flag=wx.ALIGN_CENTER_VERTICAL)

        # ------------ attack release ------------ #

        compressor_panel_attackrelease = wx.Panel(staticbox_bottom)
        compressor_panel_attackrelease.SetBackgroundColour(wx.YELLOW)
        sizer_attackrelease = wx.BoxSizer(wx.VERTICAL)
        compressor_panel_attackrelease.SetSizer(sizer_attackrelease)

        knob_attack = KC.KnobCtrl(compressor_panel_attackrelease, size=self.FromDIP(wx.Size(70, 70)))
        knob_release = KC.KnobCtrl(compressor_panel_attackrelease, size=self.FromDIP(wx.Size(70, 70)))
        
        text_value_attack = wx.StaticText(compressor_panel_attackrelease, label="0 ms")
        text_value_release = wx.StaticText(compressor_panel_attackrelease, label="0 ms")

        knob_attack.SetTags(range(0, 151, 10))
        knob_attack.SetAngularRange(-45, 225)
        knob_attack.SetValue(45)

        knob_release.SetTags(range(0, 151, 10))
        knob_release.SetAngularRange(-45, 225)
        knob_release.SetValue(45)

        sizer_attackrelease.Add(wx.StaticText(compressor_panel_attackrelease, label="Attack"), flag=wx.ALIGN_CENTER_HORIZONTAL)
        sizer_attackrelease.Add(knob_attack, flag=wx.ALIGN_CENTER_HORIZONTAL)
        sizer_attackrelease.Add(text_value_attack, flag=wx.ALIGN_CENTER_HORIZONTAL)

        sizer_attackrelease.Add(wx.StaticText(compressor_panel_attackrelease, label="Release"), flag=wx.ALIGN_CENTER_HORIZONTAL)
        sizer_attackrelease.Add(knob_release, flag=wx.ALIGN_CENTER_HORIZONTAL)
        sizer_attackrelease.Add(text_value_release, flag=wx.ALIGN_CENTER_HORIZONTAL)

        sizer_staticbox_bottom.Add(compressor_panel_attackrelease, pos=(0, 1), flag=wx.ALIGN_CENTER_VERTICAL)

        # ---------------- ratio ---------------- #

        compressor_panel_ratio = wx.Panel(staticbox_bottom)
        compressor_panel_ratio.SetBackgroundColour(wx.YELLOW)
        sizer_ratio = wx.BoxSizer(wx.VERTICAL)
        compressor_panel_ratio.SetSizer(sizer_ratio)

        knob_ratio = KC.KnobCtrl(compressor_panel_ratio, size=self.FromDIP(wx.Size(150, 150)))
        text_value_ratio = wx.StaticText(compressor_panel_ratio, label="1:1")

        knob_ratio.SetTags(range(0, 151, 10))
        knob_ratio.SetAngularRange(-45, 225)
        knob_ratio.SetValue(45)

        sizer_ratio.Add(wx.StaticText(compressor_panel_ratio, label="Ratio"), flag=wx.ALIGN_CENTER_HORIZONTAL)
        sizer_ratio.Add(knob_ratio, flag=wx.ALIGN_CENTER_HORIZONTAL)
        sizer_ratio.Add(text_value_ratio, flag=wx.ALIGN_CENTER_HORIZONTAL)

        sizer_staticbox_bottom.Add(compressor_panel_ratio, pos=(0, 2), flag=wx.ALIGN_CENTER_VERTICAL)

        # ----------------- gain ----------------- #

        compressor_panel_gain = wx.Panel(staticbox_bottom)
        compressor_panel_gain.SetBackgroundColour(wx.YELLOW)
        sizer_gain = wx.BoxSizer(wx.VERTICAL)
        compressor_panel_gain.SetSizer(sizer_gain)

        knob_gain = KC.KnobCtrl(compressor_panel_gain, size=self.FromDIP(wx.Size(150, 150)))
        text_value_gain = wx.StaticText(compressor_panel_gain, label="0 Db")

        knob_gain.SetTags(range(0, 151, 10))
        knob_gain.SetAngularRange(-45, 225)
        knob_gain.SetValue(45)

        sizer_gain.Add(wx.StaticText(compressor_panel_gain, label="Gain"), flag=wx.ALIGN_CENTER_HORIZONTAL)
        sizer_gain.Add(knob_gain, flag=wx.ALIGN_CENTER_HORIZONTAL)
        sizer_gain.Add(text_value_gain, flag=wx.ALIGN_CENTER_HORIZONTAL)

        sizer_staticbox_bottom.Add(compressor_panel_gain, pos=(0, 3), flag=wx.ALIGN_CENTER_VERTICAL)

        # ----------- sizer properties ----------- #
        
        sizer_staticbox_bottom.AddGrowableRow(0, 1)
        sizer_staticbox_bottom.Layout()

        # ------------------------------------------------------------
        # add to main panel
        # ------------------------------------------------------------

        sizer_main.Add(staticbox_top, 0, wx.EXPAND|wx.ALL, 10)
        sizer_main.Add(staticbox_bottom, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)

        sizer_main.Layout()

        # ------------------------------------------------------------
        # menubar
        # ------------------------------------------------------------

        menubar = wx.MenuBar()

        menu_file = wx.Menu()
        menu_file.Append(101, "Open WAV file...")
        menu_file.Append(102, "Save WAV file...")
        menu_file.AppendSeparator()
        menu_file.Append(103, "Exit")

        self.Bind(wx.EVT_MENU, self._on_menu_wav_open, id=101)
        self.Bind(wx.EVT_MENU, self._on_menu_wav_save, id=102)
        self.Bind(wx.EVT_MENU, self._on_exit, id=103)

        menubar.Append(menu_file, "&File")

        self.SetMenuBar(menubar)

        # ------------------------------------------------------------
        # events
        # ------------------------------------------------------------

        self.visualization_panel_bottom.Bind(wx.EVT_PAINT, self._on_paint)
        
    def _on_menu_wav_open(self, event):
        global audio_data, wav, stream
        
        with wx.FileDialog(self, "Open WAV file", wildcard="WAV files (*.wav)|*.wav",
                       style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            try:
                if wav:
                    wav.close()
                    wav = None
                if stream:
                    stream.close()
                    stream = None
                    
                wav = wave.open(pathname, 'rb')
                audio_data.CHANNELS = wav.getnchannels()
                audio_data.RATE = wav.getframerate()

                if not audio_data.CHANNELS or not audio_data.RATE:
                    wx.LogError("Error loading channels or rate.")
                    return

                stream = paudio.open(format=FORMAT,
                                     channels=audio_data.CHANNELS,
                                     rate=audio_data.RATE,
                                     output=True)
                
            except IOError:
                wx.LogError("Cannot open file.")
            
    def _on_menu_wav_save(self, event):
        with wx.FileDialog(self, "Save WAV file", wildcard="WAV files (*.wav)|*.wav",
                       style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            try:
                with open(pathname, 'w') as file:
                    pass
            except IOError:
                wx.LogError("Cannot save file")

    def _on_exit(self, event):
        self.Close()

    def update_drawing(self, data):
        global audio_array
        audio_array = np.frombuffer(data, dtype=np.int16)
        self.visualization_panel_bottom.Refresh()

    def _on_paint(self, event):
        dc = wx.BufferedPaintDC(self.visualization_panel_bottom)
        w, h = self.visualization_panel_bottom.GetSize()

        dc.Clear()

        dc.SetPen(wx.Pen(wx.WHITE))

        middle = h // 2
        scale = h / 32768 / 2
        scaled_data = middle - (audio_array * scale)
        points = [(x, int(scaled_data[x])) for x in range(len(scaled_data))]

        dc.DrawLines(points)
        

def audio_thread(frame):
    global data, paudio, wav, stream

    if not wav or not stream:
        return
    
    data = wav.readframes(CHUNK)
    while data:

        audio_data = np.frombuffer(data, dtype=np.int16)
        filtered_data = audio_data.astype(np.int16).tobytes()
        stream.write(filtered_data) # play audio
        wx.CallAfter(frame.update_drawing, filtered_data) # update plot
        data = wav.readframes(CHUNK)

    stream.stop_stream()
    stream.close()
    paudio.terminate()
    wav.close()

def run_audio_thread(frame):
    while True:
        thread = Thread(target=audio_thread, args=(frame,))
        thread.start()
        thread.join()
        
if __name__ == "__main__":
    app = wx.App()
    frame_main = FrameMain(None)
    
    thread = Thread(target=run_audio_thread, args=(frame_main,))
    thread.start()
    
    frame_main.Show()
    app.MainLoop()
