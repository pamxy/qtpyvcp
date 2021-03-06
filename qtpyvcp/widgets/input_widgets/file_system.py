import os
import subprocess
import pyudev
import psutil

from qtpy.QtCore import Slot, Property, Signal, QFile, QFileInfo, QDir, QIODevice
from qtpy.QtWidgets import QFileSystemModel, QComboBox, QTableView, QMessageBox, \
    QApplication, QAbstractItemView

from qtpyvcp.actions.program_actions import load as loadProgram
from qtpyvcp.utilities.info import Info
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.lib.decorators import deprecated

LOG = getLogger(__name__)

IN_DESIGNER = os.getenv('DESIGNER') != None

class TableType(object):
    Local = 0
    Remote = 1


class RemovableDeviceComboBox(QComboBox):
    """ComboBox for choosing from a list of removable devices."""

    def __init__(self, parent=None):
        super(RemovableDeviceComboBox, self).__init__(parent)
        # self.refreshDeviceList()

    def showEvent(self, event=None):
        self.refreshDeviceList()

    def showPopup(self):
        # refresh the device list just before showing popup
        self.refreshDeviceList()
        super(RemovableDeviceComboBox, self).showPopup()

    @Slot()
    def refreshDeviceList(self):
        # clear existing items
        self.clear()

        context = pyudev.Context()

        removable = [device for device in context.list_devices(subsystem='block', DEVTYPE='disk') if
                     device.attributes.asstring('removable') == "1"]

        for device in removable:
            partitions = [device.device_node for device in
                          context.list_devices(subsystem='block', DEVTYPE='partition', parent=device)]

            # print("All removable partitions: {}".format(", ".join(partitions)))
            # print("Mounted removable partitions:")
            for p in psutil.disk_partitions():
                if p.device in partitions:
                    # print("  {}: {}".format(p.device, p.mountpoint))
                    # self.model.append_item(p.mountpoint)
                    self.addItem(p.mountpoint, p.device)

        if not self.count():
            self.addItem("No Device Found", "NONONONONO")

        self.setCurrentIndex(0)

    @Slot()
    def ejectDevice(self):
        mount_point = self.currentData()

        if mount_point == "NONONONONO":
            return

        os.system("udisksctl unmount --block-device {}".format(mount_point))
        os.system("udisksctl power-off --block-device {}".format(mount_point))

        self.refreshDeviceList()

        self.setCurrentIndex(0)


class FileSystemTable(QTableView, TableType):

    if IN_DESIGNER:
        from PyQt5.QtCore import Q_ENUMS
        Q_ENUMS(TableType)


    gcodeFileSelected = Signal(bool)
    filePreviewText = Signal(str)
    transferFileRequest = Signal(str)
    rootChanged = Signal(str)

    def __init__(self, parent=None):
        super(FileSystemTable, self).__init__(parent)

        self._table_type = TableType.Local
        self._hidden_columns = ''

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        if parent is None:
            return

        self.parent = parent
        self.path_data = dict()
        self.doubleClicked.connect(self.openSelectedItem)
        self.selected_row = None
        self.clipboard = QApplication.clipboard()

        self.model = QFileSystemModel()
        self.model.setReadOnly(True)
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot | QDir.AllEntries)

        self.setModel(self.model)

        self.verticalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.selection_model = self.selectionModel()
        self.selection_model.selectionChanged.connect(self.onSelectionChanged)

        self.info = Info()
        self.editor = self.info.getEditor()
        self._nc_file_dir = self.info.getProgramPrefix()
        self.nc_file_exts = self.info.getProgramExtentions()
        self.setRootPath(self._nc_file_dir)

    def showEvent(self, event=None):
        self.rootChanged.emit(self._nc_file_dir)

    def onSelectionChanged(self, selected, deselected):

        if len(selected) == 0:
            return

        index = selected.indexes()[0]
        path = self.model.filePath(index)

        if os.path.isfile(path):
            self.gcodeFileSelected.emit(True)
            with open(path, 'r') as fh:
                content = fh.read()
            self.filePreviewText.emit(content)
        else:
            self.gcodeFileSelected.emit(False)
            self.filePreviewText.emit('')

    @Slot()
    def openSelectedItem(self, index=None):
        """If ngc file, opens in LinuxCNC, if dir displays dir."""
        if index is None:
            selection = self.getSelection()
            if selection is None:
                return
            index = selection[0]

        path = self.model.filePath(self.rootIndex())
        name = self.model.filePath(index)

        absolute_path = os.path.join(path, name)

        file_info = QFileInfo(absolute_path)
        if file_info.isDir():
            self.model.setRootPath(absolute_path)
            self.setRootIndex(self.model.index(absolute_path))
            self.rootChanged.emit(absolute_path)

        elif file_info.isFile():
            # if file_info.completeSuffix() not in self.nc_file_exts:
            #     LOG.warn("Unsuported NC program type with extention .%s",
            #              file_info.completeSuffix())
            loadProgram(absolute_path)

    @Slot()
    def editSelectedFile(self):
        """Open the selected file in editor."""
        selection = self.getSelection()
        if selection is not None:
            path = self.model.filePath(selection[0])
            subprocess.Popen([self.editor, path])
        return False

    @Slot()
    def loadSelectedFile(self):
        """Loads the selected file into LinuxCNC."""
        selection = self.getSelection()
        if selection is not None:
            path = self.model.filePath(selection[0])
            loadProgram(path)
            return True
        return False

    @Slot()
    def selectPrevious(self):
        """Select the previous item in the view."""
        selection = self.getSelection()
        if selection is None:
            # select last item in view
            self.selectRow(self.model.rowCount(self.rootIndex()) - 1)
        else:
            self.selectRow(selection[0].row() - 1)
        return True

    @Slot()
    def selectNext(self):
        """Select the next item in the view."""
        selection = self.getSelection()
        if selection is None:
            # select first item in view
            self.selectRow(0)
        else:
            self.selectRow(selection[-1].row() + 1)
        return True

    @Slot()
    def newFile(self):
        """Create a new empty file"""
        path = self.model.filePath(self.rootIndex())
        new_file_path = os.path.join(path, "New File.ngc")

        count = 1
        while os.path.exists(new_file_path):
            new_file_path = os.path.join(path, "New File {}.ngc".format(count))
            count += 1

        new_file = QFile(new_file_path)
        new_file.open(QIODevice.ReadWrite)

    @Slot()
    def newFolder(self):
        path = self.model.filePath(self.rootIndex())

        new_name = 'New Folder'

        count = 1
        while os.path.exists(os.path.join(path, new_name)):
            new_name = "New Folder {}".format(count)
            count += 1

        directory = QDir(path)
        directory.mkpath(new_name)
        directory.setPath(new_name)

    @Slot()
    @deprecated(replaced_by='newFolder',
                reason='for consistency with newFile method name')
    def createDirectory(self):
        self.newFolder()

    @Slot()
    def deleteItem(self):
        """Delete the selected item (either a file or folder)."""
        # ToDo: use Move2Trash, instead of deleting the file
        index = self.selectionModel().currentIndex()
        path = self.model.filePath(index)
        if path:
            fileInfo = QFileInfo(path)
            if fileInfo.isFile():
                if not self.ask_dialog("Do you wan't to delete the selected file?"):
                    return
                file = QFile(path)
                file.remove()

            elif fileInfo.isDir():
                if not self.ask_dialog("Do you wan't to delete the selected directory?"):
                    return
                directory = QDir(path)
                directory.removeRecursively()

    @Slot()
    @deprecated(replaced_by='deleteItem',
                reason='because of unclear method name')
    def deleteFile(self):
        self.deleteItem()

    @Slot(str)
    def setRootPath(self, root_path):
        """Sets the currently displayed path."""

        self.rootChanged.emit(root_path)
        self.model.setRootPath(root_path)
        self.setRootIndex(self.model.index(root_path))

        return True

    @Slot()
    def viewParentDirectory(self):
        """View the parent directory of the current view."""

        path = self.model.filePath(self.rootIndex())

        file_info = QFileInfo(path)
        directory = file_info.dir()
        new_path = directory.absolutePath()

        currentRoot = self.rootIndex()

        self.model.setRootPath(new_path)
        self.setRootIndex(currentRoot.parent())
        self.rootChanged.emit(new_path)

    @Slot()
    @deprecated(replaced_by='viewParentDirectory')
    def goUP(self):
        self.viewParentDirecotry()

    @Slot()
    def viewHomeDirectory(self):
        self.setRootPath(os.path.expanduser('~/'))

    @Slot()
    def viewNCFilesDirectory(self):
        # ToDo: Make preset user definable
        path = os.path.expanduser('~/linuxcnc/nc_files')
        self.setRootPath(path)

    @Slot()
    def viewPresetDirectory(self):
        # ToDo: Make preset user definable
        preset = os.path.expanduser('~/linuxcnc/nc_files')
        self.setRootPath(preset)

    @Slot()
    def doFileTransfer(self):
        index = self.selectionModel().currentIndex()
        path = self.model.filePath(index)
        self.transferFileRequest.emit(path)

    @Slot(str)
    def transferFile(self, src_path):
        dest_path = self.model.filePath(self.rootIndex())

        src_file = QFile()
        src_file.setFileName(src_path)

        src_file_info = QFileInfo(src_path)

        dst_path = os.path.join(dest_path, src_file_info.fileName())

        src_file.copy(dst_path)

    @Slot()
    def getSelection(self):
        """Returns list of selected indexes, or None."""
        selection = self.selection_model.selectedIndexes()
        if len(selection) == 0:
            return None
        return selection

    @Slot()
    def getCurrentDirectory(self):
        return self.model.rootPath()

    @Property(TableType)
    def tableType(self):
        return self._table_type

    @tableType.setter
    def tableType(self, table_type):
        self._table_type = table_type
        if table_type == TableType.Local:
            self.setRootPath(self._nc_file_dir)
        else:
            self.setRootPath('/media/')

    @Property(str)
    def hiddenColumns(self):
        """String of comma separated column numbers to hide."""
        return self._hidden_columns

    @hiddenColumns.setter
    def hiddenColumns(self, columns):
        try:
            col_list = [int(c) for c in columns.split(',') if c != '']
        except:
            return False

        self._hidden_columns = columns

        header = self.horizontalHeader()
        for col in range(4):
            if col in col_list:
                header.hideSection(col)
            else:
                header.showSection(col)

    def ask_dialog(self, message):
        box = QMessageBox.question(self.parent,
                                   'Are you sure?',
                                   message,
                                   QMessageBox.Yes,
                                   QMessageBox.No)
        if box == QMessageBox.Yes:
            return True
        else:
            return False
