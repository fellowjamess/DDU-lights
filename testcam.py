from picamera2 import Picamera2
import cv2
import time

def main():
    # Initialize the camera
    picam2 = Picamera2()
    
    # Configure the camera with smaller resolution for better performance
    preview_config = picam2.create_preview_configuration(
        main={"size": (640, 480)},  # Reduced resolution
        buffer_count=4
    )
    picam2.configure(preview_config)
    
    # Load the face cascade classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Start the camera
    picam2.start()
    
    # Create named window
    cv2.namedWindow('Face Detection', cv2.WINDOW_NORMAL)
    
    try:
        while True:
            # Capture frame
            frame = picam2.capture_array()
            
            # Convert from BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            # Draw rectangle around faces
            for (x, y, w, h) in faces:
                # Draw filled rectangle with transparency
                overlay = frame.copy()
                cv2.rectangle(overlay, (x, y), (x+w, y+h), (0, 255, 0), -1)
                alpha = 0.3  # Transparency factor
                frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
                
                # Draw border
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Add text with background
                text = 'Face Detected'
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
                cv2.rectangle(frame, (x, y-text_size[1]-10), (x+text_size[0], y), (0, 255, 0), -1)
                cv2.putText(frame, text, (x, y-10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
            
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