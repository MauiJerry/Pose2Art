import sys
import time
import numpy as np
import cv2 as cv
import NDIlib as ndi

def main():
    print("ndi setup start")
    if not ndi.initialize():
        return 0

    #cap = cv.VideoCapture(0)
    cap = cv.VideoCapture('videos/Fred Astaire Oscars.mov')
    #  cap = cv.VideoCapture('videos/BakingBrains_a.mp4')

    if cap is None or not cap.isOpened():
        print('Could not open file')
        return 0

    send_settings = ndi.SendCreate()
    send_settings.ndi_name = 'ndi-python'

    ndi_send = ndi.send_create(send_settings)

    video_frame = ndi.VideoFrameV2()
    #video_frame.frame_rate_N = 60

    start = time.time()
    print("Start Loop", start)
    frameCount = 0
    numToSent = 300
    while time.time() - start < 60 * 5:
        start_send = time.time()
        for _ in reversed(range(numToSent)):
            ret, img_a = cap.read()
            if ret:
                img_a = cv.cvtColor(img_a, cv.COLOR_BGR2BGRA)

                video_frame.data = img_a
                video_frame.FourCC = ndi.FOURCC_VIDEO_TYPE_BGRX
                # muck with frame rate
                #video_frame.frame_rate_D = 1
                #video_frame.frame_rate_N = 200
                ndi.send_send_video_v2(ndi_send, video_frame)
            else:
                print("Failed to read frame", frameCount)
                break
            frameCount += 1
            # Check if 'q' key is pressed to exit
            if cv.waitKey(1) & 0xFF == ord('q'):
                break

        print('200 frames sent, at %1.2ffps' % (float(numToSent) / (time.time() - start_send)))

    ndi.send_destroy(ndi_send)

    ndi.destroy()
    print("end loop")
    return 0

if __name__ == "__main__":
    sys.exit(main())
