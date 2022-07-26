import time
from cv2 import *
import os


class CameraBase(object):
    CONFIG_BASE = {}

    def __init__(self, serial_no, config={}, settings={}, v4l2_config={}):
        self.filename = self.get_webcam_filename(serial_no)
        self._config = dict(self.CONFIG_BASE)
        self._config.update(config)
        self.settings = dict(settings)
        self.v4l2_config = v4l2_config

        self.setup_device()

    def setup_device(self):
        self._cap = VideoCapture(self.filename, apiPreference=CAP_V4L2)

        for key, value in self._config.items():
            self._cap.set(key, value)

        # dump first frame
        result, _ = self._cap.read()

        for i in range(2):
            # command = 'v4l2-ctl --device=%s --set-fmt-video=width=1280,height=720,pixelformat=MJPG' % self.filename
            # os.system(command)
            for key, value in self.v4l2_config.items():
                command = 'v4l2-ctl --device=%s --set-ctrl=%s=%d' % (
                    self.filename, key, value)
                os.system(command)

        result, _ = self._cap.read()

        assert result

    def get_webcam_filename(self, identifier):
        filename = self.FILE_FORMAT % identifier
        return filename

    def get_frame(self, pre_fetch):
        device_retries = 5
        for i in range(device_retries):
            try:
                if self._cap is None:
                    self.setup_device()

                for i in range(pre_fetch):
                    result, _ = self._cap.read()
                    assert result
                result, frame = self._cap.read()
                assert result
                return frame
            except:
                self._cap = None
                if i == device_retries - 1:
                    raise
