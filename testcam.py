from picamera2 import Picamera2
import cv2
import time

def main():
    # Initialize the camera
    picam2 = Picamera2()
    
    # Configure the camera
    preview_config = picam2.create_preview_configuration(
        main={"size": (1280, 720)},
        buffer_count=4
    )
    picam2.configure(preview_config)
    
    # Load the face cascade classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Start the camera
    picam2.start()
    
    try:
        while True:
            # Capture frame
            frame = picam2.capture_array()
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            # Draw rectangle around faces
            for (x, y, w, h) in faces:
                # Draw rectangle
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                # Add text above rectangle
                cv2.putText(frame, 'Face Detected', (x, y-10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            # Display the frame
            cv2.imshow('Face Detection', frame)
            
            # Break loop on 'q' press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("Stopping camera...")
    
    finally:
        # Cleanup
        cv2.destroyAllWindows()
        picam2.stop()

if __name__ == '__main__':
    main()