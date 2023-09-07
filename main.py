# Creating a Flask web server:
# pip install Flask
# pip install flask-socketio

# Flask initialization
# Imports: flask, socketio, random and string
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase, digits

app = Flask(__name__) # Creating app object
app.config["SECRET_KEY"] = "randomkey4657"
socketIO = SocketIO(app) # Socketio integration
rooms = {} # Dictionary for existing rooms

# For unique chat room code generation
def room_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase + digits)

        if code not in rooms:
            break
    return code

@app.route("/", methods=["POST","GET"]) # Route 1: for index
def index():
    session.clear() # Ending session before creating a new one
    # Collecting form data for chat room entry:
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        # Generating errors for incomplete data while retaining the data already entered
        if not name:
            return render_template("index.html", error="Please enter a Name.", code=code, name=name)
        if join != False and not code:
            return render_template("index.html", error = "Please enter a Room Code.", code=code, name=name)
        
        # Checking whether room code entered already exists
        room = code

        if create != False:
            room = room_code(5)
            rooms[room] = {"members":0, "messages":[], "chats":[]}
        elif code not in rooms:
             return render_template("index.html", error = "Room does not exist.", code=code, name=name)
                
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("index.html")

@app.route("/room") # Route 2: for entering a chat room
def room():
    room = session.get("room")
    # Return to index if room is not generated/does not exist
    if room is None or session.get("name") is None or room not in rooms:
        return redirect (url_for("index"))
    return render_template("chat-room.html", room_code=room, messages=rooms[room]["messages"])

# Socket functions
# Entering the specified chat room (Flask-SocketIO connection)
@socketIO.on("connect")
def userConnect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    join_room(room)
    send({"name":name, "message": "Entered the room"}, to=room)
    rooms[room]["members"]+=1
    print(f"{name} joined Room #{room}")

# Leaving the chat room (Flask-Socketio disconnection)
@socketIO.on("disconnect")
def UserDisconnect():
    room = session.get("room")
    name = session.get("name")    
    leave_room(room)
    send({"name":name, "message":"Left the room"}, to=room)
    print(f"{name} left Room #{room}") 
    if room in rooms:
        rooms[room]["members"]-=1
        if rooms[room]["members"]<=0:
            del rooms[room]
            print(f"Deleted Room #{room}")
            

# Handling and transmitting messages from the server to the clients
@socketIO.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return
    # Generating message content
    content = { 
        "name": session.get("name"),
        "message": data["data"],
    }
    # Sending the message
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')}: {data['data']}")

if __name__ == "__main__":
    socketIO.run(app, debug=True)

