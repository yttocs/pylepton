#!/usr/bin/env python
#FLIR HK HACK

import time
import picamera
import numpy as np
import cv2
import traceback
from pylepton import Lepton
import math

# Create an array representing a 1280x720 image of
# a cross through the center of the display. The shape of
# the array must be of the form (height, width, color)
a = np.zeros((240, 320, 3), dtype=np.uint8)
lepton_buf = np.zeros((60, 80, 1), dtype=np.uint16)
blank_buf = np.zeros((60, 80, 1), dtype=np.uint16)
gray_thres = 120

def detect(filename):
  img = cv2.imread(filename)
  gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

  #Detect
  ret,thresh = cv2.threshold(gray, gray_thres, 255 ,1)
  contours,h = cv2.findContours(thresh,1,2)

  found = False
  for cnt in contours:
    approx = cv2.approxPolyDP(cnt,0.01*cv2.arcLength(cnt,True),True)
    #print len(approx)
    if len(approx)==5:
        print "pentagon"
        #cv2.drawContours(img,[cnt],0,255,-1)
    elif len(approx)==3:
        print "triangle"
        #cv2.drawContours(img,[cnt],0,(0,255,0),-1)
    elif len(approx)==4:
        print "square"
        #cv2.drawContours(img,[cnt],0,(0,0,255),-1)
    elif len(approx) == 9:
        print "half-circle"
        #cv2.drawContours(img,[cnt],0,(255,255,0),-1)
    elif len(approx) > 9:
        found = True
        print "circle"
        hull = cv2.convexHull(cnt)
        #ellipse = cv2.fitEllipse(cnt)
        #cv2.ellipse(img,ellipse,(0,255,0),1)
        cv2.drawContours(img,[cnt]    ,0,(255,0,0), 1)
        cv2.drawContours(img,[hull]   ,0,(0,0,255), 1)
        print "inner(contour)=", len(approx), " outer(hull)=", len(hull)
        #Centroid
        M = cv2.moments(cnt)
	if M['m00'] != 0:
	  cx = int(M['m10']/M['m00'])
          cy = int(M['m01']/M['m00'])
	else:
	  cx = int(M['m10']/1)
          cy = int(M['m01']/1)
        print cx,cy
        cv2.circle(img, (cx,cy), 2, (0,255,255), 1)

        ###Calc dist between each point and centroid
        dist_map = {}
        for xy in cnt:
            x = xy[0][0]
            y = xy[0][1]
            dist = math.hypot(cx - x, cy - y)
            dist_map[dist] = xy

        ### Find the distinct nearest N points
        N=3
        anchors_map = {}
        for d in sorted(dist_map):
            if len(anchors_map) >= N:
                break
            x = dist_map[d][0][0]
            y = dist_map[d][0][1]

            #Only take this point if distance from previous anchors
            too_close = False
            for f in anchors_map:
                xPrev = anchors_map[f][0][0]
                yPrev = anchors_map[f][0][1]
                distPrev = math.hypot( xPrev - x, yPrev - y)
                if(distPrev <= 4):
                    too_close = True
                    break

            if(too_close):
                continue
            else:
                #If still looking for points, take this point
                if len(anchors_map) < N:
                    anchors_map[d] = dist_map[d]
        #Draw the anchor lines
        for d in anchors_map:
            closest_xy = (anchors_map[d][0][0],anchors_map[d][0][1])
            cv2.circle(img,closest_xy , 1, (20,200,20), 1)
            cv2.line(img, closest_xy , (cx,cy), (20,200,20), 1)
            #print closest_xy, d
        break

  ####Check detection fail
  if found is False:
    print "\n------\nOops... you are too cool!!!"
    return blank_buf

  area_cnt = cv2.contourArea(cnt)
  area_hull = cv2.contourArea(hull)
  print "area_cnt=",area_cnt , '\n area_hull=', area_hull
  if (area_cnt < 900) or (area_hull > 3500):
    print "\n------\nOops... you are too cool!!!"
    return blank_buf
  else:
    print "OK"
    cv2.imwrite('output_'+filename, img)
    return img

def capture(flip_v = False, device = "/dev/spidev0.0"):
  with Lepton(device) as l:
    lepton_buf,_ = l.capture()
  if flip_v:
    cv2.flip(lepton_buf,0,lepton_buf)
  cv2.normalize(lepton_buf, lepton_buf, 0, 65535, cv2.NORM_MINMAX)
  np.right_shift(lepton_buf, 8, lepton_buf)
  return np.uint8(lepton_buf)


def main(flip_v = False, alpha = 128, device = "/dev/spidev0.0"):
  with picamera.PiCamera() as camera:
    #camera.resolution = (640, 480)
    camera.resolution = (80, 60)
    camera.framerate = 12
    camera.vflip = flip_v
    camera.start_preview()
    camera.fullscreen = False
    # Add the overlay directly into layer 3 with transparency;
    # we can omit the size parameter of add_overlay as the
    # size is the same as the camera's resolution
    o = camera.add_overlay(np.getbuffer(a), size=(320,240), layer=3, alpha=int(alpha), crop=(0,0,80,60), vflip=flip_v)
    try:
      time.sleep(0.2) # give the overlay buffers a chance to initialize
      with Lepton(device) as l:
        while True:
          time.sleep(0.5) #slow down

          tmpfile = "tmp.png"
          image = capture(flip_v = False)
          cv2.imwrite(tmpfile, image)
          #Added by sco
          img = detect(tmpfile)

          #a[:lepton_buf.shape[0], :lepton_buf.shape[1], :] = lepton_buf
          if img is not None:
             a[:img.shape[0], :img.shape[1], :] = img
             o.update(np.getbuffer(a))
    except Exception:
      traceback.print_exc()
    finally:
      camera.remove_overlay(o)

if __name__ == '__main__':
  from optparse import OptionParser

  usage = "usage: %prog [options] output_file[.format]"
  parser = OptionParser(usage=usage)

  parser.add_option("-f", "--flip-vertical",
                    action="store_true", dest="flip_v", default=False,
                    help="flip the output images vertically")

  parser.add_option("-a", "--alpha",
                    dest="alpha", default=128,
                    help="set lepton overlay opacity")

  parser.add_option("-d", "--device",
                    dest="device", default="/dev/spidev0.0",
                    help="specify the spi device node (might be /dev/spidev0.1 on a newer device)")

  (options, args) = parser.parse_args()

  main(flip_v = options.flip_v, alpha = options.alpha, device = options.device)
