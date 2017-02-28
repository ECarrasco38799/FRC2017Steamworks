import cv2
import numpy as np
import math
from targetdata import TargetData

class GearLift:
    """
    An OpenCV pipeline generated by GRIP.
    """
    
    def __init__(self, networkTable):
        """initializes all values to presets or None if need to be set
        """
        self.targetData = TargetData()
        self.networkTable = networkTable
        
        self.__resize_image_width = 320.0
        self.__resize_image_height = 240.0
        self.__resize_image_interpolation = cv2.INTER_CUBIC

        self.resize_image_output = None

        self.__hsl_threshold_input = self.resize_image_output
        self.__hsl_threshold_hue = [51.798561151079134, 93.99317406143345]
        self.__hsl_threshold_saturation = [71.08812949640287, 255.0]
        self.__hsl_threshold_luminance = [36.690647482014384, 255.0]

        self.hsl_threshold_output = None

        self.__find_contours_input = self.hsl_threshold_output
        self.__find_contours_external_only = True

        self.find_contours_output = None

        self.__filter_contours_contours = self.find_contours_output
        self.__filter_contours_min_area = 20.0
        self.__filter_contours_min_perimeter = 0.0
        self.__filter_contours_min_width = 0.0
        self.__filter_contours_max_width = 1000.0
        self.__filter_contours_min_height = 0.0
        self.__filter_contours_max_height = 1000.0
        self.__filter_contours_solidity = [0, 100]
        self.__filter_contours_max_vertices = 1000000.0
        self.__filter_contours_min_vertices = 0.0
        self.__filter_contours_min_ratio = 0.0
        self.__filter_contours_max_ratio = 1000.0

        self.filter_contours_output = None


    def process(self, source0):
        """
        Runs the pipeline and sets all outputs to new values.
        """
##        # Step Blur:
        self.__blur_image_input = source0
        (self.blur_image_output) = self.__blur_image_input #self.__blur_image(self.__blur_image_input, self.__resize_image_width)

        # Step HSL_Threshold0:
        self.__hsl_threshold_input = self.blur_image_output
        (self.hsl_threshold_output) = self.__hsl_threshold(self.__hsl_threshold_input, self.__hsl_threshold_hue, self.__hsl_threshold_saturation, self.__hsl_threshold_luminance)

        # Step Find_Contours0:
        self.__find_contours_input = self.hsl_threshold_output
        (self.find_contours_output) = self.__find_contours(self.__find_contours_input, self.__find_contours_external_only)

        # Step Filter_Contours0:
        self.__filter_contours_contours = self.find_contours_output
        (self.filter_contours_output) = self.__filter_contours(self.__filter_contours_contours, self.__filter_contours_min_area, self.__filter_contours_min_perimeter, self.__filter_contours_min_width, self.__filter_contours_max_width, self.__filter_contours_min_height, self.__filter_contours_max_height, self.__filter_contours_solidity, self.__filter_contours_max_vertices, self.__filter_contours_min_vertices, self.__filter_contours_min_ratio, self.__filter_contours_max_ratio)

        # TODO: Optionally draw the contours for debug
        # For now, just uncomment as needed
        #cv2.drawContours(source0, self.find_contours_output, -1, (0,255,0), 3)

        # Find the bounding rectangles
        # Two types of rectangles, straight and rotated
        # Staight is always oriented to the image view
        # Rotated find the minimum area rectangle that may be oriented
        # at some angle (i.e, not aligned to screen)
        # In either case we can use the information to identify
        # our intended target
        detection = []        # List for items that have both angle and shape we want
        detectionType = []
        other = []            # List for other objects that have correct angle, but are wrong shape
        for cnt in self.filter_contours_output:

            # Striaght rectangle thusly
            #x,y,w,h = cv2.boundingRect(cnt)

            # Minimum area rectangle (i.e., rotated)
            rect = cv2.minAreaRect(cnt)

            # Rectangle format is: ( center (x,y), (width, height), angle of rotation )
            x = rect[0][0]
            y = rect[0][1]
            w = rect[1][0]
            h = rect[1][1]
            angle_deg = abs(rect[2])
        
            # width and height also depend on angle to determine
            # orientation; angles near 0 we will accept the width
            # and height as-is, but near 90 we will swap the height
            # and width to keep things normalized
        
            if (angle_deg >= 85.0):
                w,h = h,w    # swap
                angle_deg -= 90.0
            
            # Objects large than certain sizes should be ignored complete
            # since they are likely reflections saturating the image
            # This may leave us with nothing to look at, but that is okay
            # as the image is useless at this point
            #
            # NOTE: Limits are based on empircal data of approx 9 inches
            if ((w >= 50) or (h >= 120)):
                continue
            
            ratio = w / h

            rect = ((x,y),(w,h),angle_deg)
            
            # only accept detections that are with 5 degrees of level
            # and have the correct aspect ratio to be the 2" x 5"
            # retro tape
            #
            # NOTE: This currently does NOT account for the possibility
            # that the spring is splitting or truncating one of the 
            # pieces of retro tape in the image. When this happens we
            # would see that the ratios are getting closer to square
            # or horizontal, but the center values of the pieces
            # indicates that they are aligned vertically and the ratio
            # of the extent of the pieces combined do make the desired
            # ratio. We DON'T solve that problem here; we will do that
            # after determining that we have a missing detection
            if (angle_deg <= 5.0):
                if (0.25 <= ratio <= 0.45):        # 2"/5" --> 0.4 + tolerance

                    detection.append(rect)
                    detectionType.append('Strong')
                    
                    # Identify angled bounding box and display
                    box = cv2.boxPoints(rect)
                    box = np.int0(box)
                    
                    # Draw strong candidate in green
                    cv2.drawContours(source0,[box],0,(0,255,0),2)
                    
                elif (0.45 < ratio <= 0.55):
                                      
                    # Could one of two different rectangles, but in this
                    # case we are looking for top/bottom truncations
                    # i.e., the rectangle looks wider or shorter than
                    # we expect
                    
                    # Assuming the truncation is at the bottom (spring obscuring
                    # the object) we will compute the top from available data
                    # and assume the width is correct.
                    h2 = h/2

                    top = (y - h2)        # 0 is top of image
                    
                    # Extend the rectangle to be close to the expected size
                    # This include computing a new center value for y
                    hnew = w / 0.4    # Desired height if this was a real target
                    ynew = top + hnew/2 # New center
                    
                    rect = ((x,ynew),(w,hnew),angle_deg)
                    detection.append(rect)
                    detectionType.append('Truncated')
                
                    # Identify angled bounding box and display
                    box = cv2.boxPoints(rect)
                    box = np.int0(box)
                    
                    # Draw this candidate in yellow
                    # so we can see the differences in the different candidates
                    cv2.drawContours(source0,[box],0,(0,255,255),2)
                    
                else:
                    # Save this off just in case we need to build a
                    # faux detection from the pieces of smaller objects
                    other.append(rect)
                    
                    # Identify angled bounding box and display
                    box = cv2.boxPoints(rect)
                    box = np.int0(box)
                    
                    # Draw these pieces in red
                    cv2.drawContours(source0,[box],0,(0,0,255),2)
 
        # Having only 1 detection is problematic as it means that any of the following
        #    1. we just aren't seeing the object, for which we can do nothing more
        #    2. one of the objects is split or truncated by the spring
        #
        # If there are other items that are aligned but did not meet the initial
        # ratio check then we want to create a faux detection by extending the
        # object. Again there are two possibilities: one truncated object, or
        # two smaller objects that are aligned vertically
        # We want to merge proximal pairs first, then look for truncations
        numOthers = len(other)
        
        # NOTE: We may make this more efficient, later
        # by recording only the unmatched index in a list
        # but the logic is somewhat more complicated to
        # understand, and we are going for easy to understand, first
        matchFound = [False] * numOthers
            
        if (numOthers >= 2):
            # NOTE: Only assuming a single split of an object
            # We don't need to merge objects that are split more than twice
            # But the traversal to accumulate all objects along a line is
            # fairly stright forward
            i = -1
            for oi in other:
                i = i + 1
                # If already matched, skip it
                if (matchFound[i] == True):
                    continue
                    
                xi = oi[0][0]
                yi = oi[0][1]
                wi = oi[1][0]
                hi = oi[1][1]
                hi2 = hi/2
                ai = abs(oi[2])
                topi = (yi - hi2)        # 0 is top of image
                boti = (yi + hi2)
               
                j = -1
                for oj in other[i:]:
                    j = j + 1
                    # If already matched, skip it
                    if (matchFound[j + i] == True):
                        continue
                
                    # Does this pair look like they came from the same object?
                    xj = oj[0][0]
                    yj = oj[0][1]
                    wj = oj[1][0]
                    hj = oj[1][1]
                    hj2 = hj/2
                    aj = abs(oj[2])
                    topj = (yj - hj2)
                    botj = (yj + hj2)
                    
                    # Assuming that only objects with tilts less than
                    # 5 deg are present we will apply the same criteria 
                    # for proximal items... 
                    # this means that the vertical alignment
                    # must be within 0.5" over 5" or a factor of 0.1 based on
                    # the sum of the heights... we will allow a little extra (1" --> 0.2)
                    # as a margin against pixel granularity for object further away
                    deltaX = abs(xj - xi)
                    distanceRatioX = deltaX / (hi + hj)
                    if (distanceRatioX < 0.2):
                                            
                        # Build a composite retangle from the two pieces
                        # as a faux observation then apply the final ratio
                        # criteria to determine if it is a detection
                        x = (xi + xj)/2
                        y = (yi + yj)/2
                        w = (wi + wj)/2
                        a = (ai + aj)/2
                        
                        # Height is composed of the upper and lower extents
                        # of the two pieces
                        # Remembering that (x,y) = (0,0) is top-left corner
                        # lower values of y are above higher values of y
                        if (topi < topj):
                            h = (botj - topi)
                        else:
                            h = (boti - topj)
                        
                        ratio = w / h
                        
                        if (0.25 <= ratio <= 0.45):        # 2"/5" --> 0.4 + tolerance
                        
                            matchFound.pop(i)
                            matchFound.insert(i,True)
                            matchFound.pop(j + i)
                            matchFound.insert(j + i,True)
                            
                            rect = ((x,y),(w,h),a)
                            detection.append(rect)
                            detectionType.append('Merged')
                        
                            # Identify angled bounding box and display
                            box = cv2.boxPoints(rect)
                            box = np.int0(box)
                            
                            # Draw this candidate in magenta
                            cv2.drawContours(source0,[box],0,(255,0,255),2)

        # If there are any detections we need to sift through them for a pair
        # that is on the same horizon but below the highest expected point on the image
        numDetections = len(detection)
        

        # If there are more than 2 candidates we need to remove items that don't
        # correspond to each other.
        #
        # In particular, candidates need to be within the correct ratios
        # to each other and on the same horizon (again within our 5 degree tolerance)
        #
        # TODO: For now we will just assume two, but we may want to add this later
        
        # Draw thin line down center of screen
        cv2.line(source0,(320/2,0),(320/2,240),(255,0,0),1)
        
        if (numDetections == 2):
            # Having exactly two (2) detections is the easy case
        
            # Verify that the y positions are on the same level (within tolerance)
            # and that distance between the targets (x) agrees with the documented
            # distance of 10.25" (outer edges), again within tolerance
            
            x1 = detection[0][0][0]
            y1 = detection[0][0][1]
            w1 = detection[0][1][0]
            h1 = detection[0][1][1]
            
            
            x2 = detection[1][0][0]
            y2 = detection[1][0][1]
            w2 = detection[1][1][0]
            h2 = detection[1][1][1]
            
            # Using abs() since we don't care which detection is right or left
            deltaX = abs(x2 - x1)
            distanceRatioX = deltaX / ((w1 + w2)/2)  # Distance ratio using retro tape width as common factor
            expectedRatioX = 4.125             # (10.25 - 2.0) / 2.0 inches
            ratioToleranceX = 0.5            # Corresponds to 1" over the 2" baseline
            lowRatioX = expectedRatioX - ratioToleranceX
            highRatioX = expectedRatioX + ratioToleranceX
            
            #self.networkTable.putNumber("GearDeltaX",deltaX)
            #self.networkTable.putNumber("GearRatioX",distanceRatioX)
            
            # Expect the centers to be close to each other
            # Allowing for up to a 5 degree camera tilt there
            # could be as much as a 0.75" difference in center
            #         tan(5 deg) * 8.25" = 0.72"
            # Allowing for some tolerance anything less than 1" out of 5" (--> 0.2)
            # is acceptable
            deltaY = abs(y2 - y1)
            distanceRatioY = deltaY / ((h1 + h2)/2)
            expectedRatioY = 0.2
            
            #self.networkTable.putNumber("GearDeltaY",deltaY)
            #self.networkTable.putNumber("GearRatioY",distanceRatioY)
            
            #self.networkTable.putNumber("GearSide1_x",x1)
            #self.networkTable.putNumber("GearSide1_y",y1)
            #self.networkTable.putNumber("GearSide1_w",w1)
            #self.networkTable.putNumber("GearSide1_h",h1)
            #self.networkTable.putNumber("GearSide1_A",h1 * w1)
            
            #self.networkTable.putNumber("GearSide2_x",x2)
            #self.networkTable.putNumber("GearSide2_y",y2)
            #self.networkTable.putNumber("GearSide2_w",w2)
            #self.networkTable.putNumber("GearSide2_h",h2)
            #self.networkTable.putNumber("GearSide2_A",h2 * w2)
            
            
            if ((lowRatioX <= distanceRatioX <= highRatioX) and
                (distanceRatioY <= expectedRatioY)):
                # Target confidence is high
                self.networkTable.putNumber("GearConfidence",1.0)
                
                # Estimate distance from power curve fit (R-squared = 0.9993088900150656)
                distance_inches = 2209.78743431602 * (deltaX ** -0.987535082840163)
                self.networkTable.putNumber("GearDistance_inches",distance_inches)
                centerX = (x1+x2)/2
                centerY = (y1+y2)/2
                          
                radius = 0.1*(h1+h2)/2      # w/h = 2/5 = 0.4 thus 0.5" is 0.1
                
                centerFraction = ((2.0*centerX)/320.0) - 1.0 # cam res is 320, avg & scale cancel
                center_deg = 31.6 * centerFraction
                self.networkTable.putNumber("GearCenterX",centerFraction)
                self.networkTable.putNumber("GearCenter_deg",center_deg)

                # Target center within radius if screen center will be green
                # otherwise yellow until center is beyond middle 1/3rd of FOV
                if (abs(320/2 - centerX) <= radius):
                    color = (0,255,0)
                elif (abs(centerFraction) <= (1.0/3.0)):
                    color = (0,255,255)
                else:
                    color = (0,0,255)

                cv2.circle(source0, (int(centerX), int(centerY)), int(radius), color, 2)
                
            else:
                
                self.networkTable.putNumber("GearConfidence",0.0)
                self.networkTable.putNumber("GearDistance_inches",float('NaN'))
                self.networkTable.putNumber("GearCenterX",float('NaN'))
                self.networkTable.putNumber("GearCenter_deg",float('NaN'))

                # Things don't appear to be what we think they are
                # several things could be wrong
                #    1.    Spring could be obscuring one side splitting
                #       the image into two smaller pieces
        elif (numDetections == 1):
            # Do a single target distance estimate
            x1 = detection[0][0][0]
            y1 = detection[0][0][1]
            w1 = detection[0][1][0]
            h1 = detection[0][1][1]
            self.networkTable.putNumber("GearConfidence",0.5)
            distance_inches = 1441.45246948352 * (h1 ** -1.014995518927)
            self.networkTable.putNumber("GearDistance_inches",distance_inches)
            
            centerX = x1
            centerY = y1
            radius = 0.1*h1     # w/h = 2/5 = 0.4 thus 0.5" is 0.1
            
            centerFraction = ((2.0*centerX)/320.0) - 1.0    # cam res is 320, avg & scale cancel
            center_deg = 31.6 * centerFraction
            self.networkTable.putNumber("GearCenterX",centerFraction)
            self.networkTable.putNumber("GearCenter_deg",center_deg)

            # circle with arrows
            centerX = int(centerX)
            centerY = int(centerY)
            cv2.circle(source0, (centerX, centerY), int(radius), (0,255,255),1)
            w1 = int(w1)
            cv2.arrowedLine(source0, (centerX,centerY), (centerX + 2*w1, centerY), (0,255,255),2)
            cv2.arrowedLine(source0, (centerX,centerY), (centerX - 2*w1, centerY), (0,255,255),2)
                        
        else:
            self.networkTable.putNumber("GearConfidence",0.0)
            self.networkTable.putNumber("GearDistance_inches",float('NaN'))
            self.networkTable.putNumber("GearCenterX",float('NaN'))
            self.networkTable.putNumber("GearCenter_deg",float('NaN'))    
            
        return (self.find_contours_output, self.filter_contours_output)

    @staticmethod
    def __resize_image(input, width, height, interpolation):
        """Scales and image to an exact size.
        Args:
            input: A numpy.ndarray.
            Width: The desired width in pixels.
            Height: The desired height in pixels.
            interpolation: Opencv enum for the type fo interpolation.
        Returns:
            A numpy.ndarray of the new size.
        """
        return cv2.resize(input, ((int)(width), (int)(height)), 0, 0, interpolation)

    @staticmethod
    def __hsl_threshold(input, hue, sat, lum):
        """Segment an image based on hue, saturation, and luminance ranges.
        Args:
            input: A BGR numpy.ndarray.
            hue: A list of two numbers the are the min and max hue.
            sat: A list of two numbers the are the min and max saturation.
            lum: A list of two numbers the are the min and max luminance.
        Returns:
            A black and white numpy.ndarray.
        """
        out = cv2.cvtColor(input, cv2.COLOR_BGR2HLS)
        return cv2.inRange(out, (hue[0], lum[0], sat[0]),  (hue[1], lum[1], sat[1]))

    @staticmethod
    def __find_contours(input, external_only):
        """Sets the values of pixels in a binary image to their distance to the nearest black pixel.
        Args:
            input: A numpy.ndarray.
            external_only: A boolean. If true only external contours are found.
        Return:
            A list of numpy.ndarray where each one represents a contour.
        """
        if(external_only):
            mode = cv2.RETR_EXTERNAL
        else:
            mode = cv2.RETR_LIST
        method = cv2.CHAIN_APPROX_SIMPLE
        im2, contours, hierarchy =cv2.findContours(input, mode=mode, method=method)
        return contours

    @staticmethod
    def __filter_contours(input_contours, min_area, min_perimeter, min_width, max_width,
                        min_height, max_height, solidity, max_vertex_count, min_vertex_count,
                        min_ratio, max_ratio):
        """Filters out contours that do not meet certain criteria.
        Args:
            input_contours: Contours as a list of numpy.ndarray.
            min_area: The minimum area of a contour that will be kept.
            min_perimeter: The minimum perimeter of a contour that will be kept.
            min_width: Minimum width of a contour.
            max_width: MaxWidth maximum width.
            min_height: Minimum height.
            max_height: Maximimum height.
            solidity: The minimum and maximum solidity of a contour.
            min_vertex_count: Minimum vertex Count of the contours.
            max_vertex_count: Maximum vertex Count.
            min_ratio: Minimum ratio of width to height.
            max_ratio: Maximum ratio of width to height.
        Returns:
            Contours as a list of numpy.ndarray.
        """
        output = []
        for contour in input_contours:
            x,y,w,h = cv2.boundingRect(contour)
            if (w < min_width or w > max_width):
                continue
            if (h < min_height or h > max_height):
                continue
            area = cv2.contourArea(contour)
            if (area < min_area):
                continue
            if (cv2.arcLength(contour, True) < min_perimeter):
                continue
            hull = cv2.convexHull(contour)
            solid = 100 * area / cv2.contourArea(hull)
            if (solid < solidity[0] or solid > solidity[1]):
                continue
            if (len(contour) < min_vertex_count or len(contour) > max_vertex_count):
                continue
            ratio = (float)(w) / h
            if (ratio < min_ratio or ratio > max_ratio):
                continue
            output.append(contour)
        return output



