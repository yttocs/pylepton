import numpy as np
import cv2
from matplotlib import pyplot as plt
import math


filename='jef_right_01.jpg'
filename='stev_02.jpg'

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


    ### Preview
    fig = plt.figure()

    a=fig.add_subplot(1,3,1)
    plt.imshow(ori)
    a.set_title('original')

    a=fig.add_subplot(1,3,2)
    plt.imshow(gray)
    a.set_title('gray')

    a=fig.add_subplot(1,3,3)
    plt.imshow(img)
    a.set_title('contour+hull')

    #cv2.imshow('img',img)
    #cv2.waitKey(0)
    cv2.destroyAllWindows()
