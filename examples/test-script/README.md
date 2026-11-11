Example project data from the engine's self-test (synthetic voice, stand-in footage).
Every style pack's `index.html` is written against these anchors, so to smoke-test a pack:
  espeak-ng -v en-us+m3 -s 165 -w voice.wav "$(cat script.txt)"      # or any voice
  ffmpeg -loop 1 -i <any portrait photo or clip> -i voice.wav -shortest ... raw_test.mp4
then run the normal pipeline (ingest → transcribe → cut → frames → captions → stills).
