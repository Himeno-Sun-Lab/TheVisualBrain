# -*- coding: utf-8 -*-
#Pavel Puchenkov, Scientific Computing and Data Analysis Section, 2019
#--------------------------------------------------------------------------


import bpy  #for blender's python api 
import bmesh

import sys
from os import path, walk, listdir, makedirs
import colorsys as cs
import numpy as np



'''
===============================================================================
This version is a little more optimised - 
# 1. create one object, where verticies are all the neurons from the data
# 2. attached modified: ParticleSystem
# 3. create or pick cfomr the start-scene the render object for the particle system with material
# 4. update material: node ['Divide'], input[1] = (number of neurons-1)  -test this
# 5. update material: node ['ColorRamp'], add elements - each neuron - is an element, if blender can handle it, animated.
# 6. ['colorRamp'] element - color is base color for this neuron type & group, alpha==1 (spike) or alpha~0 - no spike
# 7. for frame, for each neuron - update color of the colorRamp element - Alpha - depending on the spikes at this frame.
# 8. render (or save animation)  
# 9. animation of the vertice using shape keys or the other method - basicly animates the position of the particle - born at this vertex 
===============================================================================
'''


for i in range(0, len(sys.argv)):
    print(i,sys.argv[i])

inputDataPath = sys.argv[4]
outputRenderPath = sys.argv[5]
#some default values:
renderFrom = 0 
renderTo = 100 # max 
renderStep = 1 # every frame
nodeIndex = 1 # 1 index based
print('total args', len(sys.argv))
if len(sys.argv) == 9:
    renderFrom = int(sys.argv[6])
    renderTo = int(sys.argv[7])
    renderStep = int(sys.argv[8])
    nodeIndex = int(sys.argv[9])
    
ABSOLUTE_PATH = path.join(path.dirname(path.realpath(__file__)), inputDataPath)
SOURCE_PATH = path.dirname(path.realpath(__file__))

#==============================================================================


import importlib.util
configMod = importlib.util.spec_from_file_location("configuration", path.join(SOURCE_PATH,"config.py" ))
cfg = importlib.util.module_from_spec(configMod)
configMod.loader.exec_module(cfg)


BASE_ALPHA = cfg.BASE_ALPHA
SPIKE_ALPHA = cfg.SPIKE_ALPHA
EMISSION = cfg.EMISSION       
SIZE = cfg.SIZE                 
SIZE_SPIKE = cfg.SIZE_SPIKE    
RESOLUTION_SCALE = cfg.RESOLUTION_SCALE #100% is 1920x1080
SKIP_RENDER = cfg.SKIP_RENDER

#if we're not rendering - then exit on all other nodes except for the first one (starts with 1 index based)
if SKIP_RENDER:
    if nodeIndex > 1:
        sys.exit()
    

targetDirectory = path.join(SOURCE_PATH,outputRenderPath)
if not path.isdir(targetDirectory):
    try:
        makedirs(targetDirectory)
    except OSError as e:
        pass

#==============================================================================



#open the default start up file.  (overwrite for parametrical input)
bpy.ops.wm.open_mainfile(filepath=cfg.BASE_SCENE_FILE)


#==============================================================================

#has position id and spike time  -------------------------------------------
class Neuron():
    EXCITATORY='I'
    INHIBITORY='E'
    def __init__(self, sID, vXYZ, neuronType, neuronState):
        self.sID = sID
        self.pos = vXYZ
        self.spikeTimes = []        #list of spike times, as float
        self.neuronType = neuronType
        self.rampElement = None     #reference to color ramp element in blender cycles material
        self.neuronState = neuronState  #EXCITATORY / INHIBITORY
        
    def __repr__(self):
        return str(self.sID) + ' ' + str(self.pos) + ' ' + str(self.spikeTimes)
    
    def IsSpiked(self, timeFrame):
        return timeFrame in self.spikeTimes

#neuron type has neurons  ---------------------------------------------------      
class NeuronType():
    def __init__(self, typeName, neuronGroup):
        self.name = typeName
        self.neurons = []
        self.neuronGroup = neuronGroup
        self.color = (0,0,0)
    
    def GetSpiked(self, timeFrame):
        return [n for n in self.neurons if n.IsSpiked(timeFrame)]
    
    def __repr__(self):
        return self.name + ' ' + str(self.neurons)


#group of neuron types   ---------------------------------------------------
class NeuronGroup():    # BG, M1, S1, TH_M1
    def __init__(self, groupName):
        self.name = groupName
        self.neuronTypes = []
    
    def GetSpiked(self, timeFrame):
        allSpiked = [] 
        for nt in self.neuronTypes:
            spiked = nt.GetSpiked(timeFrame)
            if len(spiked) > 0:
                allSpiked.extend(spiked)
        return allSpiked 

    def __repr__(self):
        return self.name + ' ' + str(self.neuronTypes)

#==============================================================================

#returns list of Neurons
def readNeuronData(filePath, neuronType):
    neurons = []
    with open(filePath, 'r') as f:
        lines = f.readlines()
        for line in lines:
            data = line.split(' ')
            sID = str(float(data[0]))
            fx = float(data[1])
            fy = float(data[2])
            fz = float(data[3])  
            neuronState = str(data[4]) 
            neuron = Neuron(sID, (fx,fy,fz), neuronType, neuronState)
            neurons.append(neuron)
    return neurons

#==============================================================================


#returns dictionary - key is string repr of neurond ID, value - spike time, float
def readSpikeData(filePath):
    spikes={}
    with open(filePath, 'r') as f:
        lines = f.readlines()
        for line in lines:
            data = line.split(' ')
            if len(data) != 2:
                continue
            key = str(float(data[0]))
            spikeTime = float(data[1])
            if key not in spikes.keys():
                spikes[key] = []            # createa list of spikes for this key     
            spikes[key].append(spikeTime)   #append spike to this key
    return spikes


#==============================================================================

#matches spikes values to each neuron.spike time
def addSpikesToNeurons(neurons, spikes, refTimeFrames):
    for neuron in neurons:
        key = neuron.sID
        if key in spikes.keys():
            neuron.spikeTimes = spikes[key]
            refTimeFrames.extend(neuron.spikeTimes)


#==============================================================================

def GetColorKey(neuronGroup, neuronType):
    return neuronGroup.name +'-' + neuronType.name

#==============================================================================

#returns material
def CreateMaterial(name, color):
    scene_legend = bpy.data.scenes["flat"]
    plane = scene_legend.objects['Plane']
    matSRC = plane.active_material
    mat = matSRC.copy()
    mat.node_tree.nodes["Emission"].inputs[0].default_value = (color[0], color[1], color[2], 1)
    mat.name = name
    return mat 



#==============================================================================













#==============================================================================
#this data has neuron types and neurons with spike times for each neuron
neuronGroups = []
SPIKES = 'spikes'

for dirname, dirnames, filenames in walk(ABSOLUTE_PATH):
    # print path to all subdirectories first.
    for subdirname in dirnames:
        if SPIKES == subdirname:
            continue        
        else:
            neuronGroups.append(NeuronGroup(subdirname))
print('\n', neuronGroups,'\n')

timeFrames = [] # add time frames to the list to get max & total time for the simulation
#read data for each neuronGroup:
for neuronGroup in neuronGroups:  
    pathGroup = path.join(ABSOLUTE_PATH, neuronGroup.name)
    dirs = listdir(pathGroup)    

    # if spikes - are in the separate text files 'BG_neurons_type'        
    # This would print all the files and directories
    for file in dirs:
        if file.endswith('.txt'):
            neuronTypeName = file.split('.')[0]
            print(neuronTypeName) 
            neuronType = NeuronType(neuronTypeName, neuronGroup)
            neuronGroup.neuronTypes.append(neuronType)
            neuronType.neurons = readNeuronData(path.join(pathGroup, file), neuronType)          
            spikes = readSpikeData(path.join(pathGroup, SPIKES, neuronTypeName + '_' + SPIKES + '.txt'))  
            addSpikesToNeurons(neuronType.neurons, spikes, timeFrames)
   
    
    
#==============================================================================
            
TIME_LIST = list(dict.fromkeys(timeFrames))
TIME_MIN = min(TIME_LIST)
TIME_MAX = max(TIME_LIST)
TOTAL_FRAMES = len(TIME_LIST)

#==============================================================================
print(TIME_MIN, TIME_MAX, TOTAL_FRAMES)
#==============================================================================




#IMPORTANT set the last frame in the scene now - need it for particles! 
#particles start is latest canbe 
scene = bpy.context.scene
scene.frame_start = -1
scene.frame_end = TOTAL_FRAMES





#==============================================================================
#------ Put all neurons in one list -------------------------------------------  
allNeurons = []
groupsAndTypesCount = 0
for neuronGroup in neuronGroups: 
    for neuronType in neuronGroup.neuronTypes:
        groupsAndTypesCount+=1
        for n in neuronType.neurons:
            allNeurons.append(n)    

print('total neurons:', len(allNeurons))
print('Min Time:', TIME_MIN)
print('Max Time:', TIME_MAX)
print('total time', TOTAL_FRAMES)
if SKIP_RENDER == False:
    print('THIS RENDER:[', renderFrom, ',', renderTo, ']')
#==============================================================================








#==============================================================================
#------ CREATE COLORS & MATERIALS for all groups all types------------------------------            
hueStep = 0.9/groupsAndTypesCount
hue = 0 
MATERIALS = {}
for neuronGroup in neuronGroups: 
    for neuronType in neuronGroup.neuronTypes:
        key = GetColorKey(neuronGroup, neuronType)
        color = cs.hsv_to_rgb(hue,1,1)
        neuronType.color = color
        MATERIALS[key] = CreateMaterial(key, color)
        hue += hueStep
#==============================================================================







#==============================================================================
#---------update and render the legend in scene 'flat'----------------------------------------
def CreateLegendItem(scn, oText, oPlane, name, material, pos):
    oTextNew = oText.copy()                             # copy base object
    oTextNew.data = oText.data.copy();
    oTextNew.data.body = name
    before = oTextNew.location
    oTextNew.location = (before[0] + pos[0], before[1] + pos[1], before[2] + pos[2]) # set the position, parameter pos
    oTextNew.hide_render=False
    scn.objects.link(oTextNew)                          # link this object to the scene
    
    oPlaneNew = oPlane.copy()
    oPlaneNew.data = oPlane.data;
    before = oPlaneNew.location
    oPlaneNew.location = (before[0] + pos[0], before[1] + pos[1], before[2] + pos[2]) # set the position, parameter pos
    oPlaneNew.hide_render=False
    oPlaneNew.material_slots[0].material = material     # update material
    oPlaneNew.active_material    
    scn.objects.link(oPlaneNew)

scene_legend = bpy.data.scenes["flat"]
textBase = scene_legend.objects['Text']
textBase.hide_render=True
plane = scene_legend.objects['Plane']
plane.hide_render=True

#draw legend if needed
if cfg.DRAW_LEGEND == True:
    offsetX = 0
    offsetY = 0
    for neuronGroup in neuronGroups: 
        #print(neuronGroup.name)
        CreateLegendItem(scene_legend, textBase, plane, neuronType.name, MATERIALS[key], (offsetX, offsetY, 0))
        offsetX = 0
        offsetY -= 1
        for neuronType in neuronGroup.neuronTypes:
            #print("   ", neuronType.name)
            key = GetColorKey(neuronGroup, neuronType)
            CreateLegendItem(scene_legend, textBase, plane, neuronType.name, MATERIALS[key], (offsetX, offsetY, 0))
            offsetX = 1
            offsetY -= 1
        
    #--------- RENDER LEGEND---------------------------------ENDER------------------------
    if nodeIndex == 1:                                  # for the first now - render the legend (we do it once , we need just one frame for it) & save as debug-legend.blend
        #render legend separately
        sceneBefore = bpy.context.scene    
        bpy.context.screen.scene = scene_legend         # set the legend scene is a main scene
        scene_legend.frame_set(1)                       # Sets scene frame to nFrame.
        scene_legend.update()
        
        outputFile = path.join(SOURCE_PATH,  outputRenderPath, "_legend_" + str(1).zfill(4) + ".png" ) 
        #outputFile = "//" + RENDER_PATH + "/" + RENDER_PATH + "_legend_" + str(1).zfill(4) + ".png" # saves to relative path: "//file/file_####.png" where #### is a frame index, e.g 0001
        scene_legend.render.filepath = outputFile       # update render output path
        bpy.ops.render.render( write_still=True )
        bpy.context.screen.scene = sceneBefore          # set the base scene as default
    
        #Save the blend file for debugging:
        
        bpy.ops.wm.save_as_mainfile(filepath = path.join(SOURCE_PATH, outputRenderPath, cfg.OUT_LEGEND_FILE))
    
    #--------end-update Legend in scene 'flat'----------------------------------------
#==============================================================================








#returns created object, dupli - is an object to be cloned if non None. - 
#for the performance we use the same mesh data of this dupli object (DUPLI_MESH)  


#------------------------------------------------------------------------------
def CreateNeuralNetwork(neurons, totalFrames):
    bpy.context.screen.scene = bpy.data.scenes["Scene"]
    obj = bpy.data.objects.new("NeuralNetwork", bpy.data.meshes.new("mesh"))  # add a new object using the mesh
    scene = bpy.context.scene
    scene.objects.link(obj)             # put the object into the scene (link)
    mesh = obj.data
    bm = bmesh.new()
    #create verticies for this mesh
    for neuron in neurons:
        bm.verts.new(neuron.pos)        # add a new vert
    bm.to_mesh(mesh)  
    bm.free()                           # always do this when finished 
    #neuron view object
    renderObject = scene.objects['neuron-render']
    neuralMaterial = renderObject.material_slots[0].material
    obj.data.materials.append(neuralMaterial)
    obj.material_slots[0].link = 'OBJECT'    

    return obj, neuralMaterial

#==============================================================================










#==============================================================================

def CreateParticlesForFrame(nFrame, obj, neurons, totalFrames, size):
    obj.modifiers.clear()
    
    scene = bpy.context.scene    
    renderObject = scene.objects['neuron-render']
    #add particle system, set number of points to be exact as number of vertices (neurons)
    obj.modifiers.new("particles", type='PARTICLE_SYSTEM')
    
    #particle system:
    particleSystem = obj.particle_systems[0]
    settings = particleSystem.settings
      
    settings.emit_from = 'VERT'
    settings.use_emit_random = True #  True or False - doesnt matter - we set location every frame anyway.    
    settings.physics_type = 'NEWTON' #'NO' #'NEWTON'   FLUID  #IMPORTANT! neded this to activate caching otherwise we cannot set particles position/size 
    settings.particle_size = size
    settings.render_type = 'OBJECT' 
    settings.dupli_object = renderObject 
    settings.show_unborn = False
    settings.use_dead = True
    settings.count = len(neurons)
    settings.frame_start = -1 #totalFrames - resets to 200??? 
    settings.frame_end = -1 #totalFrames
    settings.lifetime = 1
    settings.draw_percentage = 1 # 1% - to draw 
    settings.normal_factor = 0
    settings.mass = 0
    
    #to use cache - file mustbe saved first!
    #bpy.ops.wm.save_as_mainfile(filepath="_debug_node_" + str(nodeIndex) + ".blend")
    particleSystem.point_cache.use_disk_cache = False
    particleSystem.point_cache.use_library_path = False
    
    bpy.context.scene.frame_current = -1
    scene.update()                      #IMPORTANT! this will spawn and update particles
    
    #position particles - clear particle cache
    particleSystem.seed+=1
    particleSystem.seed-=1

    particles = particleSystem.particles
    neuronLocations = np.array([0,0,0]*len(particles), dtype='float')
    for index, neuron in enumerate(neurons):
        neuronLocations[index*3] = neuron.pos[0]
        neuronLocations[index*3 + 1] = neuron.pos[1]
        neuronLocations[index*3 + 2] = neuron.pos[2]
    particles.foreach_set("location", neuronLocations)

    scene.update()                      #IMPORTANT! this will spawn and update particles

    return particleSystem, neuronLocations
    

#==============================================================================





NeuralObject, NeuralMaterial = CreateNeuralNetwork(allNeurons, TOTAL_FRAMES) # create vertices & particle system to visualize non spiked neurons
ParticleSystem, neuronLocations = CreateParticlesForFrame(0, NeuralObject, allNeurons, TOTAL_FRAMES, size = SIZE)

NeuralMaterial.node_tree.nodes["Math"].inputs[1].default_value = len(allNeurons) - 1
NeuralMaterial.node_tree.nodes['Emission'].inputs[1].default_value = EMISSION

#neuron colors & alpha - spikes are encoded into texture, index based -- create texture, total pixels >= number of neurons
# bpy.ops.image.new(name="untitled", width=1024, height=1024, color=(0.0, 0.0, 0.0, 1.0), alpha=True, uv_test_grid=False, float=False)
imageColors = bpy.data.images.new(name='NeuronsColors', width=len(allNeurons), height=1, alpha=True)
ImageTextureNode = NeuralMaterial.node_tree.nodes["Image Texture"]
ImageTextureNode.image = imageColors

#==============================================================================








#==============================================================================

def UpdateSpikedNeuronsForFrame(localPixels, neuronSizes, nFrame, imageColors, allNeurons, neuronsSpiked):
    for index, neuron in enumerate(allNeurons):
        (r,g,b) = neuron.neuronType.color
        color = (r, g, b, BASE_ALPHA)
        neuronSizes[index] = SIZE
        #if spiked then - recolor with aplha and update particle size:
        if neuron in neuronsSpiked:
            color = (r, g, b, SPIKE_ALPHA)
            neuronSizes[index] = SIZE_SPIKE        
        #pixel value is rgba, so we offsetting by 4 and write sequentially r,g,b,a values:
        for n in range(0, 4):
            localPixels[index * 4 + n] = color[n]   
    imageColors.pixels = localPixels[:]
    
#==============================================================================









#==============================================================================
# movie resolution 
scene = bpy.context.scene
scene.render.resolution_percentage = RESOLUTION_SCALE #50 # 100 for 1920x1080

localPixels = np.array(imageColors.pixels[:])
neuronSizes = np.array([0]*len(allNeurons), dtype='float')

if SKIP_RENDER == False:
    print("----start render frames------")

timeFrame = TIME_LIST[renderFrom]

for nFrame in range(renderFrom, TOTAL_FRAMES, renderStep):                  # frame is actual blender related frame, frame which will be rendered 
    
    if nFrame >= renderFrom and nFrame <= renderTo:                         # if within render range - then compute spiked neurons and render:
        timeFrame = TIME_LIST[nFrame]                                       # get the value of timeStep
        neuronsSpiked = [n for n in allNeurons if n.IsSpiked(timeFrame)]    # get spikes - for this time step
        
        UpdateSpikedNeuronsForFrame(localPixels, neuronSizes, nFrame, imageColors, allNeurons, neuronsSpiked) 
        ParticleSystem.seed+=1
        ParticleSystem.seed-=1      

        ParticleSystem.particles.foreach_set("location", neuronLocations)
        ParticleSystem.particles.foreach_set("size", neuronSizes) 

        bpy.context.scene.frame_current = nFrame + 2 #IMPORTANT make sure we never render <= 1 frame, because frame 1 is broken for particles
        scene.update() 
         
        if SKIP_RENDER == False:
            outputFile = path.join(SOURCE_PATH, outputRenderPath, "render-frames", "render_" + str(nFrame).zfill(4) + ".png")
            scene.render.filepath = outputFile                                  # update render output path
            bpy.ops.render.render( write_still = True )
            print(timeFrame,nFrame)
        else:
            break

if nodeIndex == 1:  # for the first now - save the file for debug (it won's save the spikes - they are created per frame basis) 
    imageColors.filepath_raw =  path.join(SOURCE_PATH, outputRenderPath, "spikes-map-debug-only.bmp")
    imageColors.file_format = 'BMP'
    imageColors.save()
    #Save the blend file for debugging:
    if SKIP_RENDER == False: 
        bpy.ops.wm.save_as_mainfile( filepath = path.join(SOURCE_PATH, outputRenderPath, cfg.OUT_NEURONS_FILE))
    else:
        bpy.ops.wm.save_as_mainfile( filepath = path.join(SOURCE_PATH, outputRenderPath, cfg.OUT_POSITIONS_FILE))

#---------------------------------------------------------------------------------
#when all finished - in the dependent slurm job - run:
#ffmpeg -framerate 30 -i render/render_%04d.png -i render/render_legend_0001.png -filter_complex "[0:v][1:v] overlay=1600:0" -c:v libx264  out1000-30fps.mp4 -y
# to overlay the legend and to render frames to the video file
