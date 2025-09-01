#!/bin/bash

#run-script-v2 ../1M_test ../out_1M_test 0 10 1 1

#an input file
srcNeuronsPath=$1
dstRednerPath=$2
RENDER_FROM=$3
RENDER_TO=$4
RENDER_STEP=$5
NODEINDEX=$6

#path to blender
blenderPath="/apps/ef/blender2.79b/blender"

#path to local python code to control blender's behavior
pythonScript="neuron-visu-v2.py"

#run blender with python script and input file
$blenderPath -b -P $pythonScript $srcNeuronsPath $dstRednerPath $RENDER_FROM $RENDER_TO $RENDER_STEP $NODEINDEX

#framerate is frames per second: - call this in slurm script when all frames are rendered - in dependent job
#ffmpeg -framerate 30 -i render/render_%04d.png -c:v libx264 -vf fps=30 -pix_fmt yuv420p out.mp4 -y

#draw legeng over. overlay=x:y
#ffmpeg -framerate 30 -i render/render_%04d.png -i render/render_legend_0001.png -filter_complex "[0:v][1:v] overlay=1600:0" -c:v libx264  out1000-30fps.mp4 -y
