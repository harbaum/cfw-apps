#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#

# TODO: Add kinetic scrolling
# http://blog.codeimproved.net/posts/kinetic-scrolling.html

import sys, subprocess, stat
from TouchStyle import *

LOCAL_PATH = os.path.dirname(os.path.realpath(__file__))

# currently on TXT the mpg123 tools are stored below the app directory
if platform.machine() == "armv7l":
    ID3_DUMP = os.path.join(LOCAL_PATH, "mpg123", "mpg123-id3dump")
    MPG123 = os.path.join(LOCAL_PATH, "mpg123", "mpg123") + " -q --stdout --encoding u8 --rate 22050 --mono"
    TXT_PLAY = os.path.join(LOCAL_PATH, "txt_snd_cat")

    # dirs to scan for songs
    # since the app dir itself is on sd card we don't need to look there
    DIRS=["/media/sdcard"]

    # check if the executables really are executable
    # as the file came from a zip during installation it
    # may not have the executable flag set
    EXECS = [ ID3_DUMP, MPG123.split()[0], TXT_PLAY ]
    for e in EXECS:
        st = os.stat(e)
        if not (st.st_mode & stat.S_IEXEC):
            os.chmod(e, st.st_mode | stat.S_IEXEC)
else:
    # on a PC play through sox and use the same encoding for 
    # authentic sound (minus the TXTs static noise ...)
    ID3_DUMP = "mpg123-id3dump"
    MPG123 = "mpg123 --stdout --encoding u8 --rate 22050 --mono"
    TXT_PLAY = "play -q -t raw -b 8 -e unsigned -r 22050 -c 1 -"

    DIRS=[LOCAL_PATH,"~/Music"]
None

class SongListWidget(QListWidget):
    play = pyqtSignal(bool)
 
    def __init__(self, parent=None):
        super(SongListWidget, self).__init__(parent)
        self.songs = self.scan()
        self.proc_mpg123 = None
        self.proc_txt_snd_cat = None
        
        for i in self.songs:
            item = QListWidgetItem(i["title"])
            item.setData(Qt.UserRole, i)
            self.addItem(item)

        self.itemClicked.connect(self.onItemClicked)

    def __del__(self):
        self.stop_player()

    def stop_player(self):        
        # stop all player processes
        if self.proc_txt_snd_cat:
            self.proc_txt_snd_cat.terminate()

        if self.proc_mpg123:
            self.proc_mpg123.terminate()

        if self.proc_mpg123:
            self.proc_mpg123.wait()
            self.proc_mpg123 = None

        if self.proc_txt_snd_cat:
            # kill sox/txt_snd_cat if it's still running
            if not self.proc_txt_snd_cat.poll():
                self.proc_txt_snd_cat.kill()

            self.proc_txt_snd_cat.wait()
            self.proc_txt_snd_cat = None

    def stop(self):
        self.stop_player()
        self.clearSelection()
        self.play.emit(False)

    def onItemClicked(self, item):
        # stop whatever is currently playing
        self.stop_player()

        tags = item.data(Qt.UserRole)
        mpg123_cmd = MPG123.split() + [ tags["file"] ]
        # make sure the local mpg123/lib directory is being searched
        # for libraries
        env = os.environ.copy()
        env["LD_LIBRARY_PATH"] = os.path.join(LOCAL_PATH, "mpg123", "lib")
        self.proc_mpg123 = subprocess.Popen(mpg123_cmd, env=env, stdout=subprocess.PIPE)
        self.proc_txt_snd_cat = subprocess.Popen(TXT_PLAY.split(), stdin=self.proc_mpg123.stdout, stdout=subprocess.PIPE)
        self.proc_mpg123.stdout.close()  # Allow mpg123 to receive a SIGPIPE if txt_play exits.

        self.play.emit(True)
        
    def get_id3(self, file):
        tags = { }

        # make sure the local mpg123/lib directory is being searched
        # for libraries
        env = os.environ.copy()
        env["LD_LIBRARY_PATH"] = os.path.join(LOCAL_PATH, "mpg123", "lib")
        process = subprocess.Popen([ID3_DUMP, file], env=env, stdout=subprocess.PIPE)
        (output, err) = process.communicate()
        if process.wait() == 0:
            lines = output.decode("utf-8").splitlines()
            for line in lines:
                parts = line.split(':')
                if len(parts) > 1:
                    id = parts[0].strip()
                    val = ":".join(parts[1:]).strip()
                    tags[id.lower()] = val
        return tags

    def scan(self):
        songs = []
        mp3_files = []
        for i in DIRS:
            mp3_files += self.scan_dir(i)

        # try to fetch id3 tags for all files
        for i in mp3_files:
            tags = self.get_id3(i)
            tags["file"] = i
            # if there was no title in the id3
            # tags then use the filename
            if not "title" in tags:
                tags["title"] = i
            songs.append(tags)
            
        # sort by title
        return sorted(songs, key=lambda k: k['title']) 

    def scan_dir(self, dir):
        mp3_files = []
        dir = os.path.expanduser(dir)  # path may start with ~

        try:
            files = os.listdir(dir)
            for i in files:
                fullpath = os.path.join(dir, i)
                if os.path.isfile(fullpath):
                    if fullpath.lower().endswith(('.mp3','.mpeg3')):
                        mp3_files.append(fullpath)
                elif os.path.isdir(fullpath):
                    mp3_files += self.scan_dir(fullpath)
        except FileNotFoundError:
            pass

        return mp3_files

class FtcGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)

        # create the empty main window
        self.w = TouchWindow("MP3")

        self.vbox = QVBoxLayout()

        self.songlist = SongListWidget(self.w)
        self.songlist.play[bool].connect(self.play)
        self.vbox.addWidget(self.songlist)

        self.stop_but = QPushButton("Stop")
        self.stop_but.setDisabled(True)
        self.stop_but.clicked.connect(self.songlist.stop)
        self.vbox.addWidget(self.stop_but)

        self.w.centralWidget.setLayout(self.vbox)

        self.w.show()

        self.exec_()        

    def play(self, on):
        self.stop_but.setEnabled(on)

if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
