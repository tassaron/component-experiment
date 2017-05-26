#!/usr/bin/env python3

from PyQt4 import QtGui, QtCore, uic
import sys, os
import importlib
from contextlib import suppress
import components

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
        self.window.makePreview.setText("Make Preview")
        self.window.makePreview.clicked.connect(lambda _: self.makePreview())
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
                with suppress(AttributeError):
                    module.init()
        else:
            self.window.column1Header.setText("")
            self.window.column1Body.setText("No component selected")

    def makePreview(self):
        modules = [importComponent(component.text()) for component in getListWidgetRows(self.window.loadedComponents)]
        queue = []
        for module in modules:
            with suppress(AttributeError):
                out = module.startOfFrameRender()
                queue.append(out)
        for module in modules:
            with suppress(AttributeError):
                out = module.endOfFrameRender()
                queue.append(out)
        preview = "".join(queue)
        self.window.videoPreview.setText(preview)

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
