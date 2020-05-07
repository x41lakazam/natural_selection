#!/usr/local/bin/python3
#
# script.py
# Patate
#
# Created by Eyal Shukrun on 04/22/20.
# Copyright 2020. Eyal Shukrun. All rights reserved.

import bpy
import bgl
import sys
import numpy as np
import mathutils
import math

file = open('/home/eyal/documents/progammation/studies/blender/Patate/blender_log.txt', 'w')
sys.stdout = file
sys.stderr = open('/home/eyal/documents/progammation/studies/blender/Patate/err_log.txt', 'w')


for a in bpy.data.actions: a.user_clear()


def vec_angle(v1, v2):
    print('vecs:', v1, v2)
    return np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

def find_grp_by_name(obj, grp_name):
    for grp in obj.vertex_groups:
        if grp.name == grp_name:
            return grp

def get_grp_polygons(obj, grp):

    polygons = []

    for p_ix, p in enumerate(obj.data.polygons):
        in_grp = True

        for v_ix, v in enumerate(p.vertices):
            try:
                s = grp.weight(v_ix)
            except:
                in_grp = False

        if in_grp:
            polygons.append(p)

    return polygons


def get_grp_vertices(obj, grp):
    vertices = []
    for v_ix, v in enumerate(obj.data.vertices):
        try:
            s = grp.weight(v_ix)
            vertices.append(v)
        except:
            pass
    return vertices

def anim_move_obj_toward(obj, to_obj, frames_nb, start_frame=0):
    obj.keyframe_insert(data_path='location', frame=start_frame)
    obj.location = to_obj.location
    end_frame = start_frame + frames_nb
    obj.keyframe_insert(data_path='location', frame=end_frame)
    
def vec_toward_obj(obj, to_obj):
    toward_v = (to_obj.location[0] - obj.location[0], to_obj.location[1] - obj.location[1])
    return toward_v

def distance(p1, p2):
    return math.sqrt(math.pow(p1.location[0]-p2.location[0],2) + math.pow( p1.location[1]-p2.location[1],2))

def spiral_toward(obj, to_obj, frame_start=0, hide_at_end=False, crazy_potato=False, frames_wait=1):
    
    obj.keyframe_insert(data_path='location', frame=frame_start)

    frame_n = frame_start
    for t in np.linspace(20,0,500):

        # Position
        
        px = t * np.sin(t) + to_obj.location[0]
        py = t * np.cos(t) + to_obj.location[1]
        
        obj.location = (px, py, obj.location[2])
        obj.keyframe_insert(data_path='location', frame=frame_n)
        
        # Rotation
        if crazy_potato:
            obj.rotation_euler[2] += 0.3
            obj.keyframe_insert(data_path='rotation_euler', frame=frame_n)
        
        frame_n += 1

    if hide_at_end:
        obj.location[2] = -100
        obj.keyframe_insert(data_path='location', frame=frame_n)
    
        
def duplicate_obj(obj, n=1):
    obj.select_set(state=True)
    bpy.ops.object.duplicate()

class Potato:

    def __init__(self, obj):
        self.obj = obj

    def get_face_vertices(self):
        return get_grp_vertices(self.body, self.face_grp)
    
    def get_face_local_normal(self):
        face_vertices = self.get_face_vertices()
        v1, v2, v3  = face_vertices[0].co, face_vertices[1].co, face_vertices[2].co
        vec1        = np.subtract(v1, v2)
        vec2        = np.subtract(v1, v3)
        
        le_vecteur_normal_de_la_patate = mathutils.Vector(np.cross(vec1, vec2))
        
        return le_vecteur_normal_de_la_patate
    
    def get_face_global_normal(self):
        local_look_v   = self.get_face_local_normal()
        global_look_v  = self.obj.matrix_world.to_3x3() @ local_look_v
        return global_look_v
        
    def get_face_polygons(self):
        return get_grp_polygons(self.body, self.face_grp)
    
    def get_pupil_vertices(self):
        return get_grp_vertices(self.eyes, self.pupil_grp)

    def look_vector(self):
        pupil_v = self.get_pupil_vertices()[0]
        return pupil_v.normal
    
    def get_candy(self, candy):
        anim_move_obj_toward(self.obj, candy, 80)
        
    def look_toward(self, obj):
        toward_v        = vec_toward_obj(self, obj)
        global_look_v   = self.get_face_global_normal()[:-1] # Remove z axis
        angle           = vec_angle(global_look_v, toward_v)
        self.obj.select_set(state=True)
        self.obj.keyframe_insert(data_path='rotation_euler', frame=0)
        
        bpy.ops.transform.rotate(value=angle, orient_axis='Z')

        self.obj.keyframe_insert(data_path='rotation_euler', frame=5)
    
    def reset_bones_rotation(self):
        self.top_bone.rotation_mode = 'XYZ'
        self.top_bone.rotation_euler[2] = 0
        
    def dance(self, frames_n, frame_start=0, frame_jump=1, dance_speed=0.03, dance_length=0.15):
        self.reset_bones_rotation()
        angle_per_frame = dance_speed
        max_angle       = dance_length
        current_angle   = 0
        direction       = 1
        frame_ix = frame_start
        bpy.ops.object.mode_set(mode='POSE')
        for n in range(frames_n):
            
            current_angle += angle_per_frame*direction
            
            self.top_bone.rotation_euler[2] = current_angle
            self.mid_bone.rotation_euler[2] = - current_angle 
            print(self.mid_bone.rotation_euler[2])
            if abs(current_angle) >= max_angle:
                direction = -np.sign(current_angle)
            
 
            self.top_bone.keyframe_insert(data_path='rotation_euler', frame=frame_ix)
            self.mid_bone.keyframe_insert(data_path='rotation_euler', frame=frame_ix)
            frame_ix += frame_jump      
        bpy.ops.object.mode_set(mode='OBJECT')      
        
    @property
    def top_bone(self):
        return self.armature.pose.bones["top"]
    
    @property
    def mid_bone(self):
        return self.armature.pose.bones["mid"]
    
    @property
    def low_bone(self):
        return self.armature.pose.bones["low"]
    
    @property
    def armature(self):
        return self.obj.children[0]
          
    @property
    def pupil_grp(self):
        return find_grp_by_name(self.eyes, 'Pupil')

    @property
    def face_grp(self):
        return find_grp_by_name(self.body, 'PotatoFace')

    @property
    def rotation_euler(self):
        return self.obj.rotation_euler

    @property
    def location(self):
        return self.obj.location

    @property
    def x(self):
        return self.obj.location[0]

    @property
    def y(self):
        return self.obj.location[1]

    @property
    def z(self):
        return self.obj.location[2]

    @property
    def eyes(self):
        return self.obj.children[0].children[1]

    @property
    def body(self):
        return self.obj.children[0].children[0]


        
potato = Potato(bpy.data.objects['potato_base'])
candy  = bpy.data.objects['candy_circle']

#potato.look_toward(candy)
#potato.get_candy(candy)

potatoes_n      = 100
frames_space    = 5
original_potato = 'potato_joined'
original = bpy.data.objects[original_potato]

for obj in bpy.data.objects:
    if obj.name.startswith(original_potato+'.'):
        obj.select_set(state=True)
        bpy.ops.object.delete() 
         
original.select_set(state=True)

#potato.dance(400)
## Duplicate
for _ in range(potatoes_n):
    bpy.ops.object.duplicate()

for i in range(potatoes_n):

    copy_name = original_potato + '.' + str(i+1).zfill(3)
    
    # Select new obj
    obj = bpy.data.objects[copy_name]
    obj.location = [15.0, 15.0, 0.0]
    
    spiral_toward(obj, candy, frame_start=frames_space*i, hide_at_end=True, crazy_potato=True)
    
    

    


sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__
file.close()



