import cv2

# Create a VideoCapture object to capture video from the camera
video_capture = cv2.VideoCapture(0)

while True:
    # Capture frame-by-frame
    ret, frame = video_capture.read()
    if not ret:
        break

    # Convert the frame to LAB color space
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

    # Split the LAB image into separate channels
    l, a, b = cv2.split(lab)

    # Apply CLAHE to the L channel
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)

    # Merge the LAB channels back together
    lab = cv2.merge((l, a, b))

    # Convert the LAB image back to RGB color space
    output = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # Display the result
    cv2.imshow('Color space conversion', frame)

    # Break the loop when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the VideoCapture object and close OpenCV windows
video_capture.release()
cv2.destroyAllWindows()
