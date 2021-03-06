# Show a windows with the video stream and testing information

# Import required modules
import face_recognition
import cv2
import configparser
import os
import sys
import json
import numpy
import time

# Get the absolute path to the current file
path = os.path.dirname(os.path.abspath(__file__))

# Read config from disk
config = configparser.ConfigParser()
config.read(path + "/../config.ini")

# Start capturing from the configured webcam
video_capture = cv2.VideoCapture(int(config.get("video", "device_id")))

# Force MJPEG decoding if true
if config.get("video", "force_mjpeg") == "true":
	video_capture.set(cv2.CAP_PROP_FOURCC, 1196444237)

# Set the frame width and height if requested
if int(config.get("video", "frame_width")) != -1:
	video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, int(config.get("video", "frame_width")))

if int(config.get("video", "frame_height")) != -1:
	video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, int(config.get("video", "frame_height")))

# Let the user know what's up
print("""
Opening a window with a test feed

Press ctrl+C in this terminal to quit
Click on the image to enable or disable slow mode
""")

def mouse(event, x, y, flags, param):
	"""Handle mouse events"""
	global slow_mode

	# Toggle slowmode on click
	if event == cv2.EVENT_LBUTTONDOWN:
		slow_mode = not slow_mode

# Open the window and attach a a mouse listener
cv2.namedWindow("Howdy Test")
cv2.setMouseCallback("Howdy Test", mouse)

# Enable a delay in the loop
slow_mode = False
# Count all frames ever
total_frames = 0
# Count all frames per second
sec_frames = 0
# Last secands FPS
fps = 0
# The current second we're counting
sec = int(time.time())

# Wrap everything in an keyboard interupt handler
try:
	while True:
		# Inclement the frames
		total_frames += 1
		sec_frames += 1

		# Id we've entered a new second
		if sec != int(time.time()):
			# Set the last seconds FPS
			fps = sec_frames

			# Set the new second and reset the counter
			sec = int(time.time())
			sec_frames = 0


		# Grab a single frame of video
		ret, frame = (video_capture.read())
		# Make a frame to put overlays in
		overlay = frame.copy()

		# Fetch the frame height and width
		height, width = frame.shape[:2]

		# Create a histogram of the image with 8 values
		hist = cv2.calcHist([frame], [0], None, [8], [0, 256])
		# All values combined for percentage calculation
		hist_total = int(sum(hist)[0])
		# Fill with the overal containing percentage
		hist_perc = []

		# Loop though all values to calculate a pensentage and add it to the overlay
		for index, value in enumerate(hist):
			value_perc = float(value[0]) / hist_total * 100
			hist_perc.append(value_perc)

			# Top left pont, 10px margins
			p1 = (20 + (10 * index), 10)
			# Bottom right point makes the bar 10px thick, with an height of half the percentage
			p2 = (10 + (10 * index), int(value_perc / 2 + 10))
			# Draw the bar in green
			cv2.rectangle(overlay, p1, p2, (0, 200, 0), thickness=cv2.FILLED)

		# Draw a stripe indicating the dark threshold
		cv2.rectangle(overlay, (8, 35), (20, 36), (255, 0, 0), thickness=cv2.FILLED)

		def print_text(line_number, text):
			"""Print the status text by line number"""
			cv2.putText(overlay, text, (10, height - 10 - (10 * line_number)), cv2.FONT_HERSHEY_SIMPLEX, .3, (0, 255, 0), 0, cv2.LINE_AA)

		# Print the statis in the bottom left
		print_text(0, "RESOLUTION: " + str(height) + "x" + str(width))
		print_text(1, "FPS: " + str(fps))
		print_text(2, "FRAMES: " + str(total_frames))

		# Show that slow mode is on, if it's on
		if slow_mode:
			cv2.putText(overlay, "SLOW MODE", (width - 66, height - 10), cv2.FONT_HERSHEY_SIMPLEX, .3, (0, 0, 255), 0, cv2.LINE_AA)

		# Ignore dark frames
		if hist_perc[0] > 50:
			# Show that this is an ignored frame in the top right
			cv2.putText(overlay, "DARK FRAME", (width - 68, 16), cv2.FONT_HERSHEY_SIMPLEX, .3, (0, 0, 255), 0, cv2.LINE_AA)
		else:
			# SHow that this is an active frame
			cv2.putText(overlay, "SCAN FRAME", (width - 68, 16), cv2.FONT_HERSHEY_SIMPLEX, .3, (0, 255, 0), 0, cv2.LINE_AA)

			# Get the locations of all faces and their locations
			face_locations = face_recognition.face_locations(frame)

			# Loop though all faces and paint a circle around them
			for loc in face_locations:
				# Get the center X and Y from the rectangular points
				x = int((loc[1] - loc[3]) / 2) + loc[3]
				y = int((loc[2] - loc[0]) / 2) + loc[0]

				# Get the raduis from the with of the square
				r = (loc[1] - loc[3]) / 2
				# Add 20% padding
				r = int(r + (r * 0.2))

				# Draw the Circle in green
				cv2.circle(overlay, (x, y), r, (0, 0, 230), 2)

		# Add the overlay to the frame with some transparency
		alpha = 0.65
		cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

		# Show the image in a window
		cv2.imshow("Howdy Test", frame)

		# Quit on any keypress
		if cv2.waitKey(1) != -1:
			raise KeyboardInterrupt()

		# Delay the frame if slowmode is on
		if slow_mode:
			time.sleep(.55)

# On ctrl+C
except KeyboardInterrupt:
	# Let the user know we're stopping
	print("\nClosing window")

	# Release handle to the webcam
	video_capture.release()
	cv2.destroyAllWindows()
