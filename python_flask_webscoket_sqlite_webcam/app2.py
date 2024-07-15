from flask import Flask, send_file
import cv2
import numpy as np
import io
from ultralytics import YOLO

app = Flask(__name__)

# Initialize the YOLOv8 model
model = YOLO('model/yolov8s.pt')



def plot_rectangles(image, rectangles,cls):

    #image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # Add rectangles to the plot
    for rect,c in zip(rectangles,cls):
        print(rect,c,model.names[c])
        
        if c==0:
            color=(0, 255, 0)
        else:
            color=(0, 255, 255)
            
        x1,y1,x2,y2= list(map(int,rect))

        #print(x1,y1,x2,y2)
        cv2.rectangle(image,(x1, y1), (x2, y2), color,2)
    
    return image

def process_image(image_path):
    # Load image
    image = cv2.imread(image_path)

    # Perform detection
    results = model.predict(image)
    print(results)
    frame_with_rects=plot_rectangles(image,results[0].boxes.xyxy.tolist(),results[0].boxes.cls.tolist())
    
      # Encode image to JPEG format
    _, buffer = cv2.imencode('.jpg', image)
    # Convert to base64
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    return img_base64
    
    #cv2.imshow('Video with Rectangles', frame_with_rects)




@app.route('/')
def home():
    # Process the local image
    img_base64 = process_image('upload/20240715-105305.png')  # Specify the path to your local image

    # Return the image with detections
    return send_file(image_buffer, mimetype='image/jpeg', attachment_filename='detected.jpg')

if __name__ == '__main__':
    process_image('upload/20240715-105305.png')
    app.run(debug=True)
   
