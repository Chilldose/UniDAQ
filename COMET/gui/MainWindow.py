import webbrowser
import sys, os

from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from ..utilities import ErrorMessageBoxHandler
from ..utilities import update_envrionment
from .CentralWidget import CentralWidget
from .PreferencesDialog import PreferencesDialog
from .LoggerConfig import LoggerConfig

ContentsURL = "https://chilldose.github.io/COMET/_build/html/index.html"
"""URL to primary documentation."""

ResourcePath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")


class MainWindow(QtWidgets.QMainWindow):
    """Main window containing plugin tabs as central widget."""

    def __init__(self, message_to_main, parent=None, toolbar=True):
        super(MainWindow, self).__init__(parent)
        self.message_to_main = message_to_main
        self.setWindowTitle(self.tr("COMET"))
        icon_filename = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "images", "logo.png"
        )
        self.setWindowIcon(QtGui.QIcon(icon_filename))
        # Only minimize and maximize button are active
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.resize(1600, 1000)
        # Create actions and toolbars.
        self.createActions()
        if toolbar:
            self.createMenus()
            self.createToolbar()
            self.createStatusBar()
        # Create central widget
        centralWidget = CentralWidget(self)
        centralWidget.setMinimumSize(640, 490)
        self.setCentralWidget(centralWidget)
        # Create error message dialog
        self.errMsg = ErrorMessageBoxHandler(QiD=self)

        # Init Dialogs
        self.preferencesDialog = PreferencesDialog(self)
        self.preferencesDialog.hide()

        self.loggerDialog = LoggerConfig(self)
        self.loggerDialog.hide()

    def createActions(self):
        """Create actions, for the toolbar etc"""
        # Action for quitting the program.
        self.quitAct = QtWidgets.QAction(self.tr("&Quit"), self)
        self.quitAct.setShortcut(QtGui.QKeySequence.Quit)
        self.quitAct.setStatusTip(self.tr("Quit the program"))
        self.quitAct.triggered.connect(self.close)
        # Update the software
        self.updateAct = QtWidgets.QAction(self.tr("&Update COMET"), self)
        self.updateAct.setStatusTip(self.tr("Updates the program in the background"))
        self.updateAct.triggered.connect(self.UpdateAction)
        # Preferences.
        self.preferencesAct = QtWidgets.QAction(self.tr("&Preferences"), self)
        self.preferencesAct.setStatusTip(self.tr("Configure the application"))
        self.preferencesAct.triggered.connect(self.onPreferences)
        # Load session.
        self.LoadAct = QtWidgets.QAction(self.tr("&Load saved session"), self)
        self.LoadAct.setStatusTip(self.tr("Loads a previously saved session"))
        self.LoadAct.triggered.connect(self.onLoadSession)
        # Save session.
        self.SaveAct = QtWidgets.QAction(self.tr("&Save session"), self)
        self.SaveAct.setStatusTip(self.tr("Saves the current session"))
        self.SaveAct.triggered.connect(self.onSaveSession)
        # Load alignment.
        self.LoadALAct = QtWidgets.QAction(self.tr("&Load saved alignment"), self)
        self.LoadALAct.setStatusTip(self.tr("Loads a previously saved alignment"))
        self.LoadALAct.triggered.connect(self.onLoadAlignment)
        # Save Alignment.
        self.SaveALAct = QtWidgets.QAction(self.tr("&Save alignment"), self)
        self.SaveALAct.setStatusTip(self.tr("Saves the current alignment"))
        self.SaveALAct.triggered.connect(self.onSaveAlignment)
        # Action for starting a measurement.
        self.startAct = QtWidgets.QAction(self.tr("&Start"), self)
        self.startAct.setIcon(QtGui.QIcon(os.path.join(ResourcePath, "start.svg")))
        self.startAct.setStatusTip(self.tr("Start measurement"))
        self.startAct.triggered.connect(self.onStart)
        self.startAct.setCheckable(True)
        # Action for stopping a measurement.
        self.stopAct = QtWidgets.QAction(self.tr("S&top"), self)
        self.stopAct.setIcon(QtGui.QIcon(os.path.join(ResourcePath, "stop.svg")))
        self.stopAct.setStatusTip(self.tr("Stop measurement"))
        self.stopAct.triggered.connect(self.onStop)
        self.stopAct.setCheckable(True)
        self.stopAct.setChecked(True)
        self.stopAct.setEnabled(False)
        # Action group for measurement control
        self.measureActGroup = QtWidgets.QActionGroup(self)
        self.measureActGroup.addAction(self.startAct)
        self.measureActGroup.addAction(self.stopAct)
        self.measureActGroup.setExclusive(True)
        # Open contents URL.
        self.contentsAct = QtWidgets.QAction(self.tr("&Contents"), self)
        self.contentsAct.setShortcut(QtGui.QKeySequence(Qt.Key_F1))
        self.contentsAct.setStatusTip(self.tr("Visit manual on github pages"))
        self.contentsAct.triggered.connect(self.onShowContents)
        # Create progressBar
        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        self.progressBar.setFixedWidth(400)
        self.progressBar.setValue(0)
        # Create State indicator
        self.StatusLabel = QtWidgets.QLabel()
        self.StatusLabel.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        self.StatusLabel.setFixedWidth(150)
        self.StatusLabel.setAlignment(Qt.AlignCenter)
        self.StatusLabel.setText("Start up")
        # Stream logging level.
        self.streamLogger = QtWidgets.QAction(self.tr("Set Logging Level"), self)
        self.streamLogger.setStatusTip(
            self.tr("Define the logging level of different loggers")
        )
        self.streamLogger.triggered.connect(self.onLogger)

    def createMenus(self):
        """Create menus."""
        # File menu
        self.fileMenu = self.menuBar().addMenu(self.tr("&File"))
        self.fileMenu.addAction(self.updateAct)
        self.fileMenu.addAction(self.quitAct)
        # Edit menu
        self.editMenu = self.menuBar().addMenu(self.tr("&Edit"))
        self.editMenu.addAction(self.preferencesAct)
        self.editMenu.addAction(self.LoadAct)
        self.editMenu.addAction(self.SaveAct)
        self.editMenu.addAction(self.LoadALAct)
        self.editMenu.addAction(self.SaveALAct)
        # Measurement menu
        self.measureMenu = self.menuBar().addMenu(self.tr("&Measure"))
        self.measureMenu.addActions(self.measureActGroup.actions())
        # Logging menu
        self.LogMenu = self.menuBar().addMenu(self.tr("&Logging"))
        self.LogMenu.addAction(self.streamLogger)
        # Help menu
        self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))
        self.helpMenu.addAction(self.contentsAct)

    def createToolbar(self):
        """Create main toolbar and pin to top area."""
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.addActions(self.measureActGroup.actions())
        # Add the progress bar and Status indicator to the Toolbar
        self.toolbar.addWidget(self.StatusLabel)
        self.toolbar.addWidget(self.progressBar)

        # Add a spacer
        # self.verticalSpacer = QtWidgets.QWidget()
        # self.verticalSpacer.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        # self.toolbar.addWidget(self.verticalSpacer)

    def createStatusBar(self):
        """Create status bar."""
        self.statusBar()

    def addTab(self, widget, title):
        """Add an existing widget to central tab widget, provided for convenince."""
        self.centralWidget().addTab(widget, title)

    def onPreferences(self):
        """Show preferences dialog."""
        self.preferencesDialog.show()
        self.preferencesDialog.raise_()

    def onLogger(self):
        """Shows the Logger configuration"""
        self.loggerDialog.show()
        self.loggerDialog.raise_()

    def onStart(self):
        """Starting a measurement."""
        self.startAct.setEnabled(not self.startAct.isEnabled())
        self.stopAct.setEnabled(not self.stopAct.isEnabled())
        # TODO
        self.centralWidget().onStart()

    def onStop(self):
        """Stopping current measurement."""
        self.startAct.setEnabled(not self.startAct.isEnabled())
        self.stopAct.setEnabled(not self.stopAct.isEnabled())
        # TODO
        self.centralWidget().onStop()

    def onShowContents(self):
        """Open web browser and open contents."""
        webbrowser.open_new_tab(ContentsURL)

    def onLoadSession(self):
        """Loads a previous session"""
        self.message_to_main.put({"LOAD_SESSION": True})

    def onSaveSession(self):
        """Loads a previous session"""
        self.message_to_main.put({"SAVE_SESSION": True})

    def onLoadAlignment(self):
        """Loads a previous alignment"""
        self.message_to_main.put({"LOAD_ALIGNMENT": True})

    def onSaveAlignment(self):
        """Loads a previous alignment"""
        self.message_to_main.put({"SAVE_ALIGNMENT": True})

    def closeEvent(self, event):
        """On window close event."""
        result = QtWidgets.QMessageBox.question(
            None,
            self.tr("Confirm quit"),
            self.tr("Are you sure to quit?"),
            QtWidgets.QMessageBox.Yes,
            QtWidgets.QMessageBox.No,
        )
        if result == QtWidgets.QMessageBox.Yes:
            # Send close message to main thread
            result = QtWidgets.QMessageBox.question(
                None,
                self.tr("Save session?"),
                self.tr("Do you want to save the current session?"),
                QtWidgets.QMessageBox.Yes,
                QtWidgets.QMessageBox.No,
            )
            if result == QtWidgets.QMessageBox.Yes:
                self.message_to_main.put({"SAVE_SESSION": True})
            self.message_to_main.put({"CLOSE_PROGRAM": True})
            event.accept()
        else:
            event.ignore()

    def UpdateAction(self):
        """Updates the program"""
        update_envrionment()