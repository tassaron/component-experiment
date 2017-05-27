#!/usr/bin/env python3

from PyQt4 import QtGui, QtCore, uic
import sys, os
import importlib
import core
from PIL import Image
import subprocess as sp


class Worker:
  def __init__(self, modules):
    self.core = core.Core()
    self.modules = modules
    
  def createVideo(self,
                   bgImage='/.png',      #  PUT YOUR FILEPATH HERE
                   inputFile='/.ogg',    #  PUT YOUR FILEPATH HERE
                   outputFile='/.mkv'):  #  PUT YOUR FILEPATH HERE
    def loadBackgroundImg():
        backgroundImg = Image.open(bgImage)
        im = Image.new("RGB", (1280, 720), "black")
        im.paste(backgroundImg, (0, 0))
        return im
        
    completeAudioArray = self.core.readAudioFile(inputFile)

    # test if user has libfdk_aac
    encoders = sp.check_output(self.core.FFMPEG_BIN + " -encoders -hide_banner", shell=True)
    if b'libfdk_aac' in encoders:
      acodec = 'libfdk_aac'
    else:
      acodec = 'aac'

    ffmpegCommand = [ self.core.FFMPEG_BIN,
       '-y', # (optional) means overwrite the output file if it already exists.
       '-f', 'rawvideo',
       '-vcodec', 'rawvideo',
       '-s', '1280x720', # size of one frame
       '-pix_fmt', 'rgb24',
       '-r', '30', # frames per second
       '-i', '-', # The input comes from a pipe
       '-an',
       '-i', inputFile,
       '-acodec', acodec, # output audio codec
       '-b:a', "192k",
       '-vcodec', "libx264",
       '-pix_fmt', "yuv420p",
       '-preset', "medium",
       '-f', "mp4"]

    if acodec == 'aac':
      ffmpegCommand.append('-strict')
      ffmpegCommand.append('-2')

    ffmpegCommand.append(outputFile)
    
    out_pipe = sp.Popen(ffmpegCommand,
        stdin=sp.PIPE,stdout=sys.stdout, stderr=sys.stdout)
    for module in self.modules:
        module.init()

    # create video for output
    sampleSize = 1470
    backgroundImage = loadBackgroundImg()
    frame = loadBackgroundImg()
    for i in range(0, len(completeAudioArray), sampleSize):
      for module in self.modules:
          if hasattr(module, 'frameRender'):
              frame = module.frameRender(i, frame, backgroundImage, completeAudioArray, sampleSize)
      # write to out_pipe
      try:
        out_pipe.stdin.write(frame.tobytes())
      finally:
        True

    out_pipe.stdin.close()
    if out_pipe.stderr is not None:
      print(out_pipe.stderr.read())
      out_pipe.stderr.close()
    # out_pipe.terminate() # don't terminate ffmpeg too early
    out_pipe.wait()
    print("Video file created")

class MainState:
    def __init__(self):
        self.possibleComponents = [component for component in self.findComponents()]

    def findComponents(self):
        srcPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'components')
        if os.path.exists(srcPath):
            for f in os.listdir(srcPath):
                name, ext = os.path.splitext(f)
                if name.startswith("__"):
                    continue
                elif ext == '.py':
                    yield name

class Main(QtCore.QObject):
    def __init__(self, window):
        super().__init__()
        self.state = MainState()
        self.window = window
        self.window.setWindowTitle('Component Experiment')
        self.window.column2Header.setText("Loaded components:")
        self.window.buttonAdd.setText("Load Component")
        self.window.buttonAdd.clicked.connect( \
            lambda _: self.addComponent(self.window.comboBox.currentText())
        )
        self.window.buttonRemove.setText("Remove Component")
        self.window.buttonRemove.clicked.connect(lambda _: self.removeComponent())
        self.window.loadedComponents.clicked.connect(lambda _: self.drawComponentDetails())
        self.window.makePreview.setText("Make Video")
        self.window.makePreview.clicked.connect(lambda _: self.makePreview())
        self.window.videoPreview.setText('')
        self.construct(window)

    def construct(self, window):
        # combobox of possible components to add
        for component in self.state.possibleComponents:
            window.comboBox.addItem(component)

        # component details area
        self.drawComponentDetails()
        window.show()

    def addComponent(self, moduleName):
        self.window.loadedComponents.addItem(moduleName)

    def removeComponent(self):
        for selected in self.window.loadedComponents.selectedItems():
            selected.setHidden(True)
    
    def drawComponentDetails(self):
        if self.window.loadedComponents.selectedItems():
            self.window.column1Header.setText("Component details:")
            for selected in self.window.loadedComponents.selectedItems():
                module = importComponent(selected.text())
                self.window.column1Body.setText(module.__doc__)
        else:
            self.window.column1Header.setText("")
            self.window.column1Body.setText("No component selected")

    def makePreview(self):
        modules = [importComponent(component.text()) for component in getListWidgetRows(self.window.loadedComponents)]
        videoWorker = Worker(modules)
        videoWorker.createVideo()

def importComponent(name):
    return importlib.import_module('components.%s' % name)

def getListWidgetRows(self):
    for i in range(self.count()):
        if self.item(i).isHidden():
            continue
        yield self.item(i)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = uic.loadUi("main.ui")
    Main(window)
    quit(app.exec_())
