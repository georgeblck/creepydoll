from picamera import PiCamera
import os

def record_video(destination):
    filename = os.path.join(
        destination, datetime.now().strftime('%Y-%m-%d_%H.%M.%S.h264'))
    camera.start_preview()
    camera.start_recording(filename)


def finish_video():
    camera.stop_recording()
    camera.stop_preview()
