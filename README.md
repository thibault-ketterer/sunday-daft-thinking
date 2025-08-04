# sunday-daft-thinking

generating that gif with pillow, opengl, ffmpeg

gen the text with / texture with

    python gentext.py

    python some_gl.py

    wf-recorder -g $(slurp)

    ffmpeg -i recording.mkv -vf "fps=24,scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -loop 0 output2.gif

![daft punk style animtaion](output2.gif "daft punk style opengl animation")
