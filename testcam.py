from picamera2 import Picamera2
import cv2
import time
import os

def main():
    # Create output directory
    output_dir = "face_detections"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Initialize the camera
    picam2 = Picamera2()
    
    # Configure the camera
    preview_config = picam2.create_preview_configuration(
        main={"size": (640, 480)},
        buffer_count=4
    )
    picam2.configure(preview_config)
    
    # Load the face cascade classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Start the camera
    picam2.start()
    
    frame_count = 0
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
            
            # Process detected faces
            if len(faces) > 0:
                # Draw rectangle around faces
                for (x, y, w, h) in faces:
                    # Draw filled rectangle with transparency
                    overlay = frame.copy()
                    cv2.rectangle(overlay, (x, y), (x+w, y+h), (0, 255, 0), -1)
                    alpha = 0.3
                    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
                    
                    # Draw border
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    # Add text with background
                    text = 'Face Detected'
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
                    cv2.rectangle(frame, (x, y-text_size[1]-10), (x+text_size[0], y), (0, 255, 0), -1)
                    cv2.putText(frame, text, (x, y-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
                
                # Save frame with detected faces
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                output_path = f"{output_dir}/face_detected_{timestamp}_{frame_count}.jpg"
                cv2.imwrite(output_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                print(f"Face detected! Saved as {output_path}")
                frame_count += 1
            
            # Small delay to prevent overwhelming the system
            time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("Stopping camera...")
    
    finally:
        picam2.stop()
        print(f"Captured {frame_count} frames with faces")

if __name__ == '__main__':
    main()