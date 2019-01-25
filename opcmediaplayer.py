import os
import signal
import subprocess
import sys
import time
import datetime
from opcua import ua, Server

if __name__ == "__main__":
    # redirect stdout to logfile
    sys.stdout = open('/var/log/opcmediaplayer.log', 'a')

    print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Change OS processname.")
    if sys.platform == 'linux2':
        import ctypes
        libc = ctypes.cdll.LoadLibrary('libc.so.6')
        libc.prctl(15, 'opcmediaplayer', 0, 0, 0)

    print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), " Setup OPC UA Server")
    dir_path = os.path.dirname(os.path.realpath(__file__))
    server = Server(shelffile=dir_path + "/cache")

    print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Set OPC UA Server endpoint")
    server.set_endpoint("opc.tcp://0.0.0.0:4842/opcmediaplayer/")

    uri = "http://cherrypi"
    print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "setup OPC UA server namespace.")
    idx = server.register_namespace(uri)

    print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Get OPC UA Objects node.")
    objects = server.get_objects_node()

    print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Populating address space.")
    myobj = objects.add_object(idx, "MyObject")

    print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Create OPC UA vars.")
    opcmediaplayerloopcounter = myobj.add_variable(idx, "opcmediaplayerloopcounter", 0)
    opcmediaplayerloopcounter.set_writable()    # Set opcmediaplayerloopcounter to be writable by clients

    media = myobj.add_variable(idx, "media", "")
    media.set_writable()    # Set media to be writable by clients

    SendKeys = myobj.add_variable(idx, "SendKeys", "")
    SendKeys.set_writable()    # Set SendKeys to be writable by clients

    cmd = ["omxplayer", "./media/silence.mp3"]
    pro = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE)

    if pro.poll() != None:
        print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Cannot start omxplayer, quitting.")
    else:
        print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "starting OPC server")
        server.start()

        print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Start main loop")
        try:
            while True:
                time.sleep(1)
                opcmediaplayerloopcounter.set_value(opcmediaplayerloopcounter.get_value() + 1)

                #if SendKeys.get_value() != "" and pro.poll() != 0 and pro.poll() != 3:
                if SendKeys.get_value() != "":
                    try:
                        pro.stdin.write(SendKeys.get_value())
                    except:
                        print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "error sending key '", SendKeys.get_value(), "' to omxplayer thread via pipe with poll code '", str(pro.poll()), "'")
                    SendKeys.set_value("")

                if media.get_value() != "":
                    if pro.poll() == None and pro.poll() != 3:
                        pro.stdin.write("q")
                        time.sleep(1.5)
                    if media.get_value().count('/') > 0:
                        cmd = ["omxplayer", media.get_value()]
                    else:
                        cmd = ["omxplayer", "/root/media/" + media.get_value()]
                    pro = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
                    time.sleep(1)
                    media.set_value("")
        finally:
            server.stop()
