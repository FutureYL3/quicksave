import sys
import pathlib
import os
import subprocess
from PyQt5 import QtWidgets, QtGui, QtCore

from quicksave.core.proctree import get_process_tree
from quicksave.core.compat import check_compatibility, explain_compat
from quicksave.core.snapshot import dump

def get_pid_by_selectwindow():
    import subprocess, os
    try:
        print("DEBUG: DISPLAY=", os.environ.get("DISPLAY"))
        win_id = subprocess.check_output(["xdotool", "selectwindow"], stderr=subprocess.STDOUT).decode().strip()
        print("DEBUG: selected win_id=", win_id)
        if not win_id or not win_id.startswith("0x"):
            win_id = hex(int(win_id))  # 兼容十进制
        print("DEBUG: win_id after hex=", win_id)
        prop = subprocess.check_output(
            ["xprop", "-id", win_id, "_NET_WM_PID"], stderr=subprocess.STDOUT
        ).decode()
        print("DEBUG: xprop output:", prop)
        pid = int(prop.strip().split()[-1])
        return pid
    except subprocess.CalledProcessError as e:
        print("DEBUG: CalledProcessError output:", e.output.decode())
    except Exception as e:
        print("DEBUG: Exception:", e)
    return None


class Tray(QtWidgets.QSystemTrayIcon):
    def __init__(self, app):
        super().__init__(QtGui.QIcon.fromTheme("camera-photo"))
        self.app = app
        menu = QtWidgets.QMenu()
        act_snap = menu.addAction("Snapshot (Select Window)")
        act_snap.triggered.connect(self.snap_via_selectwindow)
        act_quit = menu.addAction("Quit")
        act_quit.triggered.connect(app.quit)
        self.setContextMenu(menu)
        self.setToolTip("QuickSave: Desktop Snapshot Tool")
        self.show()

    def snap_via_selectwindow(self):
        # QtWidgets.QMessageBox.information(
        #     None, "选择窗口", "请用鼠标点击你要快照的窗口。"
        # )
        pid = get_pid_by_selectwindow()
        if not pid:
            QtWidgets.QMessageBox.warning(
                None, "Error", "无法获取窗口 PID，操作已取消。"
            )
            return
        pids = get_process_tree(pid)
        report = check_compatibility(pids)
        msg = explain_compat(report)
        if "通过" not in msg:
            res = QtWidgets.QMessageBox.question(
                None, "兼容性警告", msg + "\n是否继续？",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if res != QtWidgets.QMessageBox.Yes:
                return
        try:
            outfile = dump([pid])
            QtWidgets.QMessageBox.information(
                None, "快照完成", f"快照已完成：{outfile}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                None, "快照失败", f"快照失败：{e}")

def main():
    app = QtWidgets.QApplication(sys.argv)
    tray = Tray(app)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()