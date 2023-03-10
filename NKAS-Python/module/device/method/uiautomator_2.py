import subprocess

import cv2
import numpy as np

import glo
from common.enum.enum import Path
from module.device.connection import Connection


class Uiautomator2(Connection):
    # def screenshot(self):
    #     image = self.u2.screenshot(format='raw')
    #     image = np.frombuffer(image, np.uint8)
    #     self.image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    #
    # def _screenshot(self):
    #     address = 'emulator-5554'
    #     result = subprocess.run(f"adb -s {address} exec-out screencap -p", stdout=subprocess.PIPE, shell=True)
    #     self.image = cv2.imdecode(np.frombuffer(result.stdout, np.uint8), cv2.IMREAD_UNCHANGED)
    #     return self.image

    def uiautomator_click(self, x, y):
        self.u2.click(x, y)
        return True

    def swipe(self, sx, sy, ex, ey, duration=0.3):
        self.u2.swipe(sx, sy, ex, ey, duration)
        return True

    def drag(self, sx, sy, ex, ey, duration=0.3):
        self.u2.drag(sx, sy, ex, ey, duration)
        return True

    def app_start_uiautomator2(self, package_name=None):
        if not package_name:
            if self.jp_package in self.u2.app_list():
                package_name = self.jp_package

            elif self.tw_package in self.u2.app_list():
                package_name = self.tw_package

        if package_name is not None:
            self.u2.app_start(package_name)
            return False
        elif package_name in self.u2.app_list_running():
            return False

        glo.getNKAS().socket.emit('insertLog', glo.getNKAS().socket.getLog('ERROR', '没有找到NIKKE'))
        return True
