from flask import Flask, request, jsonify,send_file
from naoqi import ALProxy, ALModule, ALBroker
import time
from threading import Event
from qi import Session,Application
import os
import threading
import time

#Flask app setup and nao connection variables
app = Flask(__name__)

nao = True
nao_IP = "192.168.34.110"
nao_port = 9559
sleep_time = 0.01

tts = ALProxy("ALTextToSpeech", nao_IP, nao_port)
tts.setVolume(1.0) # define volume of the robot
animatedSpeech = ALProxy("ALAnimatedSpeech", nao_IP, nao_port)

word_detected_event = Event()
wake_word_detected = None
partsTouched = ""

# Custom functionalities that wrap naoqi behaviour/speaker modules to define behaviour
class behavior:
    def __init__(self,session):
        self.name = ""
        self.behavior_mng_service = session.service("ALBehaviorManager")
        self.motion_service = session.service("ALMotion")
        self.posture_service = session.service("ALRobotPosture")
        self.running_flag = False

    def _run_behavior_blocking(self, behavior_name):
        """
        Internal helper: run a behavior in a separate thread and track running_flag.
        """
        try:
            self.running_flag = True
            self.behavior_mng_service.runBehavior(behavior_name)
        finally:
            self.running_flag = False

    # NEW: generic launcher used by /run_behavior
    def launch_behavior(self, behavior_name, async_run=True):
        """
        Launch any NAO behavior by its full name/path.
        Example: 'animations/Stand/Gestures/Hey_1'
        """
        self.name = behavior_name
        if async_run:
            th = threading.Thread(
                target=self._run_behavior_blocking,
                args=(behavior_name,)
            )
            th.daemon = True
            th.start()
        else:
            self._run_behavior_blocking(behavior_name)

    # NEW: hand-waving gesture using built-in NAO animations
    def wave_hand(self, hand="right"):
        """
        Trigger a hand-waving gesture. Uses built-in gesture behaviors.
        hand: 'right' or 'left'
        """
        # Make sure robot is in a safe standing posture
        try:
            self.posture_service.goToPosture("StandInit", 0.5)
        except Exception:
            # If already standing, this may fail; ignore
            pass

        if hand.lower() == "left":
            behavior_name = "animations/Stand/Gestures/Hey_3"   # left-hand wave
        else:
            behavior_name = "animations/Stand/Gestures/Hey_1"   # right-hand wave (default)

        self.launch_behavior(behavior_name, async_run=True)
    
#this class initializes the speaker and also plays the files when asked to played 
class SPEAKER:
    def __init__(self,session):
        self.aup = session.service("ALAudioPlayer")
        self.path = "/home/nao/share/nao_gpt/"
        self.buffer = []
        self.sig_play = True
        self.thread_alive = threading.Thread(target=self._thread_play,args=())

    def append(self,filename):
        self.sig_play = True
        self.buffer.append(self.aup.loadFile(os.path.join(self.path,filename)))
        
    def _thread_play(self):
        while len(self.buffer)!=0:
            if self.sig_play:
                self.aup.play(self.buffer.pop(0))
            else: break
    
    def play(self):
        if not self.thread_alive.is_alive():
            playing = threading.Thread(target=self._thread_play,args=())
            self.thread_alive = playing
            playing.start()
            
            return "playing the file"
        else:
            return "there are some files in the play queue"
    
    def stop(self):
        self.aup.stopAll()
        self.aup.unloadAllFiles()
        self.sig_play = False
    
    def isPlaying(self):
        return self.thread_alive.is_alive()


# Establish connection with robot using broker/naoqi session aided by ALproxy for broker
try:
    pythonBroker = ALBroker("pythonBroker", "0.0.0.0", 0, nao_IP, nao_port) # broker connection: essential for communicating between the module and the NAOqi runtime
    global AudioCapture
    session = Session()
    session.connect("tcp://" + nao_IP + ":" + str(nao_port))
    speaker = SPEAKER(session)
    behave = behavior(session)

except RuntimeError:
    print("Error initializing broker!")
    exit(1)


# server endpoints that utilize custom functions defined above to 

@app.route("/talk", methods=["POST"])
def talk():
    print("Received a request to talk")
    message = request.json.get("message")
    language = request.json.get("language")
    tts.say(str(message),str(language))
    return jsonify(success=True)

@app.route("/wave_hand", methods=["POST"])
def wave_hand():
    data = request.get_json(silent=True) or {}
    hand = data.get("hand", "right")
    try:
        behave.wave_hand(hand)
        return jsonify(success=True, hand=hand)

    except Exception as e:
        print("Error while waving hand:", e)
        return jsonify(success=False, error=str(e)), 500

@app.route("/bow", methods=["POST"])
def bow_down():
    try:
        behave.launch_behavior("animations/Stand/Gestures/BowShort_1")
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


# Here we host the flask server 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006)

