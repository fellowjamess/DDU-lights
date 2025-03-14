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
    
    # Start the camera
    picam2.start()
    
    try:
        while True:
            # Capture frame
            frame = picam2.capture_array()
            
            # Convert from BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Add some test processing
            # Draw a rectangle
            cv2.rectangle(frame, (100, 100), (400, 400), (0, 255, 0), 2)
            
            # Add text
            cv2.putText(frame, 'Camera Test', (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Display the frame
            cv2.imshow('Camera Test', frame)
            
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