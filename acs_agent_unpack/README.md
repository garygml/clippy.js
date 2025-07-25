The python code will read the ACS file to get animation list

1. Put your ACS at the root directory, 
2. Run the ACS decompiler, I downloaded from http://www.lebeausoftware.org/software/decompile.aspx, after that you will have a Decompiled directory with /Audio, /Images and a .acd file. 
3. The python code I wrote uses ACS file to get the animation list, but uses thed Decompiled Audio .wav files to generate sounds-mp3.js, and uses Images .bmp files to generate map.png

4. Install Python (if you don't have it): https://www.python.org/downloads/")
5. Install FFmpeg (required by pydub for audio conversion):
   - Windows: https://www.gyan.dev/ffmpeg/builds/
   - macOS: `brew install ffmpeg` (using Homebrew)
   - Linux: `sudo apt update && sudo apt install ffmpeg` (Debian/Ubuntu)

6. 
```python3 -m venv venv```
```source venv/bin/activate```
```pip install -r requirements.txt```

7. You may need to change main.py for the agent name and your ACS file name in the main method
Finally do
```python main.py```
a ```agent.js``` file and a ```sounds-mp3.js``` file will be generated, a ```map.png``` will also be generated in the Images directory (I still use other software to get rid of the background transparency color separately but these files can then be used in the clippy js)


