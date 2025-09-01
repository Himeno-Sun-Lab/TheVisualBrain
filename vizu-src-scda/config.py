# -*- coding: utf-8 -*-
#Pavel Puchenkov, Scientific Computing and Data Analysis Section, 2019
#--------------------------------------------------------------------------

BASE_ALPHA = 0.05

SPIKE_ALPHA = 1

EMISSION = 20               # ~ brightness of the points

SIZE = 0.05                 #0.05  size of the non spiked neuron  

SIZE_SPIKE = 0.7            #0.7  size of the spikes neuron

RESOLUTION_SCALE = 100      #100% is 1920x1080

BASE_SCENE_FILE = "start-particles.blend"   # starting file - empty scene with camera (you can add camera animation - to circle around neurons, for example)

DRAW_LEGEND = False         #if True: legend saved as saparate *.png image file and added to *.blend file

SKIP_RENDER = True          #if True: it skips render - saving file with positioned neurons to the OUT_POSITIONS_FILE

OUT_LEGEND_FILE = "out_legend.blend"

OUT_NEURONS_FILE = "out_neurons.blend"  

OUT_POSITIONS_FILE = "out_neurons_positions.blend"  
