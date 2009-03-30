"""
"""

from __future__ import absolute_import

import logging
import sys
import os

from PyQt4 import QtCore, QtGui

from xpaxs import __version__
from .ui import ui_mainwindow
from .phynx import FileModel
from xpaxs.io import phynx
from .notifications import NotificationsDialog


logger = logging.getLogger(__file__)


class MainWindowBase(QtGui.QMainWindow):

    """
    """

    def __init__(self, parent=None):
        super(MainWindowBase, self).__init__(parent)

    def _setupDockWindows(self):
        pass

    def _restoreSettings(self):
        settings = QtCore.QSettings()
        settings.beginGroup(str(self.__class__))
        self.restoreGeometry(settings.value('Geometry').toByteArray())
        self.restoreState(settings.value('State').toByteArray())

    def _configureDockArea(self):
        """
        Private method to configure the usage of the dockarea corners.
        """
        self.setCorner(QtCore.Qt.TopLeftCorner, QtCore.Qt.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomLeftCorner, QtCore.Qt.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.TopRightCorner, QtCore.Qt.RightDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomRightCorner, QtCore.Qt.BottomDockWidgetArea)
        self.setDockNestingEnabled(True)

    def _createDockWindow(self, name):
        """
        Private method to create a dock window with common properties.

        @param name object name of the new dock window (string or QString)
        @return the generated dock window (QDockWindow)
        """
        dock = QtGui.QDockWidget()
        dock.setObjectName(name)
        dock.setFeatures(QtGui.QDockWidget.DockWidgetFeatures(\
                                    QtGui.QDockWidget.AllDockWidgetFeatures))
        return dock

    def _setupDockWindow(self, dock, where, widget, caption):
        """
        Private method to configure the dock window created with _createDockWindow().

        @param dock the dock window (QDockWindow)
        @param where dock area to be docked to (Qt.DockWidgetArea)
        @param widget widget to be shown in the dock window (QWidget)
        @param caption caption of the dock window (string or QString)
        """
        if caption is None:
            caption = QtCore.QString()
        self.addDockWidget(where, dock)
        dock.setWidget(widget)
        dock.setWindowTitle(caption)
        action = dock.toggleViewAction()
        action.setText(caption)
        self.menuView.addAction(action)
        dock.show()

    @QtCore.pyqtSignature("")
    def on_actionAboutQt_triggered(self):
        QtGui.qApp.aboutQt()

    @QtCore.pyqtSignature("")
    def on_actionAboutXpaxs_triggered(self):
        from xpaxs import __version__
        QtGui.QMessageBox.about(self, self.tr("About XPaXS"),
            self.tr("XPaXS Application, version %s\n\n"
                    "XPaXS is a user interface for controlling synchrotron "
                    "experiments and analyzing data.\n\n"
                    "XPaXS depends on several programs and libraries:\n\n"
                    "    spec: for controlling hardware and data acquisition\n"
                    "    SpecClient: a python interface to the spec server\n"
                    "    PyMca: a set of programs and libraries for analyzing "
                    "X-ray fluorescence spectra"%__version__))

    def closeEvent(self, event):
        settings = QtCore.QSettings()
        settings.beginGroup(str(self.__class__))
        settings.setValue('Geometry', QtCore.QVariant(self.saveGeometry()))
        settings.setValue('State', QtCore.QVariant(self.saveState()))
        event.accept()


class MainWindow(ui_mainwindow.Ui_MainWindow, MainWindowBase):
    """Establishes a Experiment controls

    1) establishes week connection to specrunner
    2) creates ScanIO instance with Experiment Controls
    3) Connects Actions from Toolbar

    """

    def __init__(self, parent=None):
        super(MainWindowBase, self).__init__(parent)

        self.setupUi(self)

        self._configureDockArea()

        self._specFileRegistry = {}
        self.fileModel = FileModel(self)
        self.fileView = QtGui.QTreeView(self)
        self.fileView.setModel(self.fileModel)
        self.fileView.setColumnWidth(0, 250)

        self.setCentralWidget(self.fileView)


        self.expInterface = None
        self.openScans = []

        self.statusBar.showMessage('Ready', 2000)

        self._setupDockWindows()
        self._connectSignals()
        self._restoreSettings()

        import xpaxs
        # TODO: this should be a factory function, not a method of the main win:
        xpaxs.application.registerService('ScanView', self.newScanWindow)
        xpaxs.application.registerService('FileInterface', self)

    def _setupDockWindows(self):
        self._setupEmailDlg()

    def _setupEmailDlg(self):
        self.menuSettings.addAction("Email Settings",self._startEmailDlg )

    def _startEmailDlg(self):
        email = NotificationsDialog(self).show()

    def _restoreSettings(self):
        settings = QtCore.QSettings()
        settings.beginGroup('MainWindow')
        self.restoreGeometry(settings.value('Geometry').toByteArray())
        self.restoreState(settings.value('State').toByteArray())

    def _configureDockArea(self):
        """
        Private method to configure the usage of the dockarea corners.
        """
        self.setCorner(QtCore.Qt.TopLeftCorner, QtCore.Qt.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomLeftCorner, QtCore.Qt.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.TopRightCorner, QtCore.Qt.RightDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomRightCorner, QtCore.Qt.BottomDockWidgetArea)
        self.setDockNestingEnabled(True)

    def _createDockWindow(self, name):
        """
        Private method to create a dock window with common properties.

        @param name object name of the new dock window (string or QString)
        @return the generated dock window (QDockWindow)
        """
        dock = QtGui.QDockWidget()
        dock.setObjectName(name)
        dock.setFeatures(QtGui.QDockWidget.DockWidgetFeatures(\
                                    QtGui.QDockWidget.AllDockWidgetFeatures))
        return dock

    def _setupDockWindow(self, dock, where, widget, caption):
        """
        Private method to configure the dock window created with _createDockWindow().

        @param dock the dock window (QDockWindow)
        @param where dock area to be docked to (Qt.DockWidgetArea)
        @param widget widget to be shown in the dock window (QWidget)
        @param caption caption of the dock window (string or QString)
        """
        if caption is None:
            caption = QtCore.QString()
        self.addDockWidget(where, dock)
        dock.setWidget(widget)
        dock.setWindowTitle(caption)
        action = dock.toggleViewAction()
        action.setText(caption)
        self.menuView.addAction(action)
        dock.show()

    def _connectSignals(self):
        self.connect(
            self.actionOpen,
            QtCore.SIGNAL("triggered()"),
            self.openFile
        )
        self.connect(
            self.actionImportSpecFile,
            QtCore.SIGNAL("triggered()"),
            self.importSpecFile
        )
        self.connect(
            self.actionSpec,
            QtCore.SIGNAL("toggled(bool)"),
            self.connectToSpec
        )
        self.connect(
            self.actionAbout_Qt,
            QtCore.SIGNAL("triggered()"),
            QtGui.qApp,
            QtCore.SLOT("aboutQt()")
        )
        self.connect(
            self.actionAbout_SMP,
            QtCore.SIGNAL("triggered()"),
            self.about
        )
        self.connect(
            self.menuTools,
            QtCore.SIGNAL("aboutToShow()"),
            self.updateToolsMenu
        )
        self.connect(
            self.menuAcquisition,
            QtCore.SIGNAL("aboutToShow()"),
            self.updateAcquisitionMenu
        )
        self.connect(
            self.actionOffline,
            QtCore.SIGNAL("triggered()"),
            self.setOffline
        )
        self.connect(
            self.fileView,
            QtCore.SIGNAL('activated(QModelIndex)'),
            self.fileModel.itemActivated
        )
        self.connect(
            self.fileView,
            QtCore.SIGNAL('collapsed(QModelIndex)'),
            self.fileModel.clearRows
        )
        self.connect(
            self.fileModel,
            QtCore.SIGNAL('fileAppended'),
            self.fileView.doItemsLayout
        )
        self.connect(
            self.fileModel,
            QtCore.SIGNAL('scanActivated'),
            self.newScanWindow
        )

    def about(self):
        QtGui.QMessageBox.about(self, self.tr("About XPaXS"),
            self.tr("XPaXS Application, version %s\n\n"
                    "XPaXS is a user interface for controlling synchrotron "
                    "experiments and analyzing data.\n\n"
                    "XPaXS depends on several programs and libraries:\n\n"
                    "    spec: for controlling hardware and data acquisition\n"
                    "    SpecClient: a python interface to the spec server\n"
                    "    PyMca: a set of programs and libraries for analyzing "
                    "X-ray fluorescence spectra"%__version__))

    def closeEvent(self, event):
        if self.openScans:
            warning = '''Are you sure you want to close all your open scans?'''
            res = QtGui.QMessageBox.question(self, 'closing...', warning,
                                             QtGui.QMessageBox.Yes,
                                             QtGui.QMessageBox.No)
            if res == QtGui.QMessageBox.Yes:
                for i in self.openScans:
                    if not i.close():
                        return event.ignore()
            else:
                return event.ignore()

        self.connectToSpec(False)
        settings = QtCore.QSettings()
        settings.beginGroup("MainWindow")
        settings.setValue('Geometry', QtCore.QVariant(self.saveGeometry()))
        settings.setValue('State', QtCore.QVariant(self.saveState()))
        self.fileModel.close()
        if self.expInterface: self.expInterface.close()
        return event.accept()

    def connectToSpec(self, bool):
        if bool:
            from xpaxs.instrumentation.spec.specinterface import ConnectionAborted

            try:
                from xpaxs.instrumentation.spec.specinterface import SpecInterface
                self.expInterface = SpecInterface(self)

            except ConnectionAborted:
                return

            if self.expInterface:
                self.actionConfigure.setEnabled(True)
                for key, (item, area, action) in \
                        self.expInterface.dockWidgets.iteritems():
                    self.menuView.addAction(action)
                    self.addDockWidget(area, item)
            else:
                self.actionOffline.setChecked(True)
        else:
            if self.expInterface:
                self.actionConfigure.setEnabled(False)
                for key, (item, area, action) in \
                        self.expInterface.dockWidgets.iteritems():
                    self.removeDockWidget(item)
                    self.menuView.removeAction(action)
                self.expInterface.close()
                self.expInterface = None

    def getH5FileFromKey(self, key):
        h5File = self._specFileRegistry.get(key, None)

        if not h5File:
            default = key.split(os.path.sep)[-1] + '.h5'
            h5File = self.saveFile(default)
            self._specFileRegistry[key] = h5File

        return h5File

    def getScanView(self, scan):
        # this is a shortcut for now, in the future the view would be
        # an overview of the entry with ability to open different analyses
        if isinstance(scan, phynx.registry['Entry']):
            from .mcaanalysiswindow import McaAnalysisWindow
            if len(scan['measurement'].mcas) > 0:
                return McaAnalysisWindow(scan, self)
            else:
                msg = QtGui.QErrorMessage(self)
                msg.showMessage(
                    'The entry you selected has no MCA data to process'
                )

    def importSpecFile(self, force=False):
        f = '%s'% QtGui.QFileDialog.getOpenFileName(self, 'Open File', '.',
                    "Spec datafiles (*.dat *.mca);;All files (*)")
        if f:
            h5_filename = str(
                QtGui.QFileDialog.getSaveFileName(
                    self,
                    'Save HDF5 File',
                    './'+f+'.h5',
                    'HDF5 files (*.h5 *.hdf5)'
                )
            )
            if h5_filename:
                self.statusBar.showMessage('Converting spec data...')
                QtGui.qApp.processEvents()
                from xpaxs.io.spec import convert_to_phynx
                f = convert_to_phynx(f, h5_filename=h5_filename, force=True)
                f.close()
                del f
                self.statusBar.clearMessage()
                self.openFile(h5_filename)

    def newScanWindow(self, scan):
        self.statusBar.showMessage('Configuring New Analysis Window ...')
        scanView = self.getScanView(scan)
        if scanView is None:
            self.statusBar.clearMessage()
            return
        self.connect(scanView, QtCore.SIGNAL("scanClosed"), self.scanClosed)

        self.openScans.append(scanView)

        scanView.show()
        self.statusBar.clearMessage()

        return scanView

    def openFile(self, filename=None):
        if filename is None:
            filename = '%s'% QtGui.QFileDialog.getOpenFileName(self,
                            'Open File', '.', "hdf5 files (*.h5 *.hdf5)")
        if filename:
            self.fileModel.openFile(str(filename))

    def saveFile(self, filename=None):
        if os.path.isfile(filename):
            return self.fileModel.openFile(filename)
        else:
            newfilename = QtGui.QFileDialog.getSaveFileName(self.mainWindow,
                    "Save File", filename, "hdf5 files (*.h5 *.hdf5 *.nxs)")
            if newfilename:
                newfilename = str(newfilename)
                if newfilename.split('.')[-1] not in ('h5', 'hdf5', 'nxs'):
                    newfilename = newfilename + '.h5'
                self.fileModel.openFile(newfilename)
            else: self.saveFile(filename)

    def scanClosed(self, scan):
        self.openScans.remove(scan)

    def setOffline(self):
        if self.expInterface is None: return
        if self.expInterface.name == 'spec':
            self.connectToSpec(False)

    def updateAcquisitionMenu(self):
        self.menuAcquisition.clear()
        acquisitionGroup = QtGui.QActionGroup(self)
        acquisitionGroup.addAction(self.actionOffline)
        self.menuAcquisition.addAction(self.actionOffline)
        # TODO: will acquisition work on other platforms?
        if sys.platform == 'linux2':
            acquisitionGroup.addAction(self.actionSpec)
            self.menuAcquisition.addAction(self.actionSpec)
        if self.expInterface is None:
            self.actionOffline.setChecked(True)
        elif self.expInterface.name == 'spec':
            self.actionSpec.setChecked(True)

    def updateToolsMenu(self):
        self.menuTools.clear()
#        try:
#            window = self.mdi.currentSubWindow().widget()
#            actions = window.getMenuToolsActions()
#            for action in actions:
#                self.menuTools.addAction(action)
#        except AttributeError:
#            pass


def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    app.setOrganizationName('XPaXS')
    form = MainWindowBase()
    form.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
