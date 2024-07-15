from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import base64
import datetime
import json
import cv2
from ultralytics import YOLO
from PIL import Image
from gevent.pywsgi import WSGIServer

app = Flask(__name__,static_folder='web/')

# http://127.0.0.1:3000

@app.route('/')
def index():
   #return render_template('index.html')
   return app.send_static_file('index.html')
    
    
@app.route('/hello/<name>')  # locate all pages that starts with /hello/
def hello(name):
    return render_template('page.html', name=name)
    
@app.route('/video')
def goto_video():
    return render_template('html5_camera.html')
    


# Open the camera
camera = cv2.VideoCapture(0)
model = YOLO('model/yolov8s.pt')


def plot_rectangles(image,results):

    rectangles=results[0].boxes.xyxy.tolist()
    cls=results[0].boxes.cls.tolist()
    conf=results[0].boxes.conf.tolist()
    # Add rectangles to the plot
    for rect,c,prob in zip(rectangles,cls,conf):
        print(rect,c,model.names[c],prob)
        
        if c==0:
            color=(0, 255, 0)
        else:
            color=(0, 255, 255)
            
        x1,y1,x2,y2= list(map(int,rect))

        #print(x1,y1,x2,y2)
        cv2.rectangle(image,(x1, y1), (x2, y2), color,2)
    
    return image

    

def detecte_objects(image_path):
    # Load image
    image = cv2.imread(image_path)

    # Perform detection+
    # model.predict("bus.jpg", save=True, imgsz=320, conf=0.5)
    results = model.predict(image, conf=0.5) 
   
    frame_with_rects=plot_rectangles(image,results)


    
      # Encode image to JPEG format
    _, buffer = cv2.imencode('.jpg', image)
    # Convert to base64
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    return img_base64
    
    #cv2.imshow('Video with Rectangles', frame_with_rects)


@app.route('/item')
def goto_item():
    return render_template('list_item.html')
    
    
def get_current_user():
    return {'name':'joseph','password':'1234'}
    
@app.route("/me")  #http://127.0.0.1:3000/me
def me_api():
    user = get_current_user()
    print(user)
    return {
        "username": user['name'],
        "password": user['password']
    }

#-------------websocket------------------------    
socketio = SocketIO(app)
socketio.init_app(app, cors_allowed_origins="*")


def save_img(msg):

    filename=datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+'.png'
    base64_img_bytes = msg.encode('utf-8')
    with open('./upload/'+filename, "wb") as save_file:
        save_file.write(base64.decodebytes(base64_img_bytes))
    
    return './upload/'+filename


#user defined event 'client_event'
@socketio.on('client_event')
def client_msg(msg):
    #print('received from client:',msg['data'])
    emit('server_response', {'data': msg['data']}, broadcast=False) #include_self=False

#user defined event 'connect_event'
@socketio.on('connect_event')   
def connected_msg(msg):
    print('received connect_event')
    emit('server_response', {'data': msg['data']})
    
    
#user defined event 'capture_event'
@socketio.on('capture_event')   
def connected_msg(msg):
    print('received capture_event')
    #print(msg)
    filepath=save_img(msg)
    
    img_base64=detecte_objects(filepath)
  
    
    #here we just send back the original image to browser.
    #maybe, you can do image processinges before sending back 
    emit('object_detection_event', img_base64, broadcast=False)
    

    
#------SQLite stuff-----------------

from sqlite_utils import *


@socketio.on('get_allitem_event')   
def  trigger_allitem_item(msg):
     print('trigger_allitem_item')
     newitems=query_db_json(db,select_sql)
     emit('new_item_event', {'data': newitems }, broadcast=False)
     

@socketio.on('new_item_event')   
def  trigger_new_item(msg):
     print('trigger new_item')
     newitems=[{'pid':'1234','p_name':'拿鐵咖啡','p_price':50},
              {'pid':'1235','p_name':'焦糖咖啡','p_price':80}]
     newitems=json.dumps(newitems)
     emit('new_item_event', {'data': newitems }, broadcast=False)

    
if __name__ == '__main__':
    #socketio.run(app, debug=True, host='127.0.0.1', port=3000)

    http_server = WSGIServer(('0.0.0.0', 5000), socketio.run(app, debug=True, host='127.0.0.1', port=3000))
    http_server.serve_forever()
    
 
