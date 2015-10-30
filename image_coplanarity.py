# -*- coding: utf-8 -*-

"""
image.py

author: Keita Nagara (University of Tokyo)

This class is called from "Main.py", and process image data.

methods:
	processData(data) <- called from "Main.py"
"""

import sys
from math import *
import cv2 as cv
import numpy as np
import Util
from keypoint_pair import KeyPointPair

class ImageCoplanarity:

	def __init__(self):
		pass

	def init(self):
		#state.py
		#self.state.init() #this is also called in sensor.py
		#variables
		pass
	
	def setState(self,_state):
		#state.py
		self.state = _state



	#Set new data and Execute all functions
	def processData(self,data):

		#if nomatch then nothing to do
		if(data[0] == "nomatch"):
			#print("nomatch"),
			return

		keypoints = []
		for d in data:
			if(d != ''):
				keypoints.append(KeyPointPair(d))

		self.state.setImageData(keypoints)
