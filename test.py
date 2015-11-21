#!/usr/bin/env python

import sys
import numpy as np
import cv2
from pylepton import Lepton
import picamera

#from matplotlib import pyplot as plt
import math

def detect(filename):
  #filename='jef_right_01.jpg'
  #filename='stev_02.jpg'

  ori = cv2.imread(filename)
  img = cv2.imread(filename)
  gray = cv2.imread(filename,0)

  #Detect
  ret,thresh = cv2.threshold(gray,145,255,1)
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
        cv2.drawContours(img,[cnt]    ,0,(200,0,0), 1)
        cv2.drawContours(img,[hull]   ,0,(0,0,255), 1)
        print "inner(contour)=", len(approx), " outer(hull)=", len(hull)
        #Centroid
        M = cv2.moments(cnt)
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])
        print cx,cy
        cv2.circle(img, (cx,cy), 2, (20,200,20), 1)
        break

  ####Check detection fail
  area_cnt = cv2.contourArea(cnt)
  area_hull = cv2.contourArea(hull)
  print "area_cnt=",area_cnt , ' area_hull=', area_hull
  if (found is False) or (area_cnt < 1000) or (area_hull > 3500):
    print "\n------\nOops... you are too cool!!!"
  else:
    print "OK"
    cv2.imshow('img',img)


def capture(flip_v = False, device = "/dev/spidev0.0"):

  with picamera.PiCamera() as camera:
    camera.resolution = (640, 480)

  with Lepton(device) as l:
    a,_ = l.capture()
  if flip_v:
    cv2.flip(a,0,a)
  cv2.normalize(a, a, 0, 65535, cv2.NORM_MINMAX)
  np.right_shift(a, 8, a)
  return np.uint8(a)

if __name__ == '__main__':
  from optparse import OptionParser

  usage = "usage: %prog [options] output_file[.format]"
  parser = OptionParser(usage=usage)

  parser.add_option("-f", "--flip-vertical",
                    action="store_true", dest="flip_v", default=False,
                    help="flip the output image vertically")

  parser.add_option("-d", "--device",
                    dest="device", default="/dev/spidev0.0",
                    help="specify the spi device node (might be /dev/spidev0.1 on a newer device)")

  (options, args) = parser.parse_args()

  if len(args) < 1:
    print "You must specify an output filename"
    sys.exit(1)

  image = capture(flip_v = options.flip_v, device = options.device)
  cv2.imwrite(args[0], image)

  #Added by sco
  detect(args[0])


