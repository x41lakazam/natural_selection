#!/usr/local/bin/python3
#
# ns_blender.py
# Patate
#
###### PATATE MODULE ######
import sys
import bpy
import numpy as np
import mathutils

# TODO: Merge the potatoes parts into one object
# Change spawn_potatoes (currently selecting all children)

def deselect_everything():
    for obj in bpy.context.selected_objects:
        obj.select_set(state=False)

deselect_everything() # run it once in case of

def get_all_children(obj, children=[]):
    if not children:
        children = [obj] 
    for child in obj.children:
        children.append(child)
        child_children = get_all_children(child, children=children)
        children.extend(child_children)

    return children

def select_all_children(obj, prev_children=[]):
    obj.select_set(state=True)
    for child in obj.children:
        select_all_children(child, prev_children=prev_children)

def spawn_from_model(model, x, y, z):
    """
    Returns parent object
    """
    deselect_everything()

    select_all_children(model)
    bpy.ops.object.duplicate()

    # Because the duplicated object is automatically selected
    for object in bpy.context.selected_objects:
        if object.name.startswith(model.name):
            break

    object.location = (x,y,z)

    return object

def del_object(obj):
    deselect_everything()
    select_all_children(obj)
    bpy.ops.object.delete()

def hide_object(obj, frame=None):
    deselect_everything()
    for child in get_all_children(obj):
        child.hide_viewport = True
        if frame:
            child.keyframe_insert(data_path="hide_viewport", frame=frame)

def unhide_object(obj, frame=None):
    deselect_everything()
    for child in get_all_children(obj):
        child.hide_viewport = False
        if frame:
            child.keyframe_insert(data_path="hide_viewport", frame=frame)


class BlenderObjWrapper:

    @classmethod
    def spawn(cls, x, y, z=0, name='auto'):

        model = bpy.data.objects[cls.MODEL_NAME]

        object = spawn_from_model(model, x, y, z)

        if name == 'auto':
            object.name = "{}.{}".format(cls.__name__, len(cls.objects))
        else:
            object.name = name

        cls_obj = cls(object)
        return cls_obj


    def center(self):
        self.obj.location = (0,0,0)

    def unhide_at_frame(self, frame_n):
        unhide_object(self.obj, frame=frame_n)

    def hide_at_frame(self, frame_n):
        hide_object(self.obj, frame=frame_n)


    def move(self, x, y, z=0, frame=None):
        self.obj.location = (x,y,z)

        if frame:
            self.obj.keyframe_insert(data_path="location", frame=frame)

class Candy(BlenderObjWrapper):
    MODEL_NAME = "Candy base model"
    objects = []

    def __init__(self, obj):
        Candy.objects.append(self)
        self.obj = obj


class Patate(BlenderObjWrapper):

    MODEL_NAME = "Potato base model"
    objects    = []

    def __init__(self, obj):
        """
        obj is the base circle of the potato
        """
        Patate.objects.append(self)
        self.obj = obj

    def get_candy(self, candy, frame_start, frame_end):
        self.obj.keyframe_insert(data_path="location", frame=frame_start)
        self.obj.location = candy.location
        self.obj.keyframe_insert(data_path="location", frame=frame_end)

    def look_toward_candy(self, candy, frame_start, frame_end):

        assert self.obj.location != candy.location, "Potato and candy are at the same location"

        # Vecteur regard
        look_v      = self.get_face_global_normal()[:-1] # Remove Z axis
        # Vecteur vers le bonbon
        toward_v    = (
            candy.location[0] - self.obj.location[0],
            candy.location[1] - self.obj.location[1]
        )

        # Angle entre les deux
        angle       = np.arccos(
            np.dot(look_v, toward_v) / (np.linalg.norm(look_v)*np.linalg.norm(toward_v))
        )

        # Rotation
        self.obj.keyframe_insert(data_path="rotation_euler", frame=frame_start)

        self.obj.select_set(state=True)
        bpy.ops.transform.rotate(value=angle, orient_axis="Z")

        self.obj.keyframe_insert(data_path="rotation_euler", frame=frame_end)

        return

    def eat_candy(self, candy):
        deselect_all()
        candy.select_set(state=True)
        bpy.ops.object.delete()

    def get_face_local_normal(self):
        """
        Get the normal vector (look vector) in local coordinates
        """
        # Trouver 3 points du plan (v1, v2 et v3)
        face_keypoints = self.get_face_keypoints()
        v1, v2, v3 = face_keypoints[0].co, face_keypoints[1].co, face_keypoints[2].co

        # Trouver deux vecteurs du plan
        vec1       = np.subtract(v2, v1)
        vec2       = np.subtract(v2, v3)

        normal     = mathutils.Vector(np.cross(vec1, vec2))
        return normal

    def get_face_global_normal(self):
        local_look_v  = self.get_face_local_normal()
        world_mat     = self.obj.matrix_world.to_3x3()
        global_look_v = world_mat @ local_look_v

        return global_look_v

    def get_face_keypoints(self):
        grp         = self.get_grp("Face_keypoints")
        vertices    = []

        for v_ix, v in enumerate(self.body.data.vertices):
            try:
                grp.weight(v_ix)
                vertices.append(v)
            except:
                pass
        return vertices

    def get_grp(self, grp_name):
        for grp in self.body.vertex_groups:
            if grp.name == grp_name:
                return grp
        return False

    @property
    def body(self):
        return self.obj.children[0].children[1]

    @property
    def eyes(self):
        return self.obj.children[0].children[0]




######### END OF PATATE MODULE ###########

import sys
import json

sys.stdout = open('/home/eyal/documents/progammation/studies/blender/Patate/blender_log.txt', 'w')
sys.stderr = open('/home/eyal/documents/progammation/studies/blender/Patate/err_log.txt', 'w')

def clean_objects():
    start = ["Candy.", "Patate."]
    for obj in bpy.data.objects:
        for s in start:
            try:
                if obj.name.startswith(s):
                    del_object(obj)
            except:
                pass

def init_objs(state_log):
    """
    Spawn all objects with id and then hide them
    """
    for dic in state_log:
        potatoes_id = dic["potatoes_state"].keys()
        candies_id  = dic["candies_state"].keys()
        for pid in potatoes_id:
            potato_obj = Patate.spawn(0,0)
            potato_obj.hide_at_frame(0)
            blender_state['potatoes'][pid] = potato_obj

        for cid in candies_id:
            candy_obj = Candy.spawn(0,0)
            candy_obj.hide_at_frame(0)
            blender_state['candies'][cid] = candy_obj


def new_gen(state, frame):
    potatoes_id_check = {potato_id:False for potato_id in blender_state['potatoes']}
    candies_id_check = {candy_id:False for candy_id in blender_state['candies']}

    # Add new potatoes and candies
    for potato_id in state["potatoes_state"]:
        potatoes_id_check[potato_id] = True
        # Unhide them
        coords = state["potatoes_state"][potato_id]
        obj = blender_state['potatoes'][potato_id]
        obj.unhide_at_frame(frame, *coords)

    for candy_id in state["candies_state"]:
        candies_id_check[candy_id] = True
        # Unhide them
        coords = state["candies_state"][candy_id]
        obj = blender_state['candies'][candy_id]
        obj.unhide_at_frame(frame, *coords)

    # Delete dead potatoes and candies
    for potato_id, here in potatoes_id_check.items():
        if not here:
            patate = blender_state['potatoes'][potato_id]
            patate.hide_at_frame(frame)

    print("Hiding candies")
    for candy_id, here in candies_id_check.items():
        if not here:
            print("Candy {} hidden at frame".format(candy_id))
            candy = blender_state['candies'][candy_id]
            candy.hide_at_frame(frame)


clean_objects()

# Some constants
FPS = 5
FRAMES_BETWEEN_GENS = 5


# Load natural selection log
ns_log = "/home/eyal/documents/progammation/studies/blender/Patate/1-gen-1-days.json"
ns_states = json.load(open(ns_log, 'r'))

# Start animation
frame_ix = 0
previous_candies = []
prev_gen = 0
blender_state = {'potatoes':{}, 'candies':{}}

init_objs(ns_states)
#for state in ns_states:
#    gen_ix = int(state['Gen'])

#    if gen_ix != prev_gen:
#        prev_gen = gen_ix
#        new_gen(state, frame_ix)
#        frame_ix += FRAMES_BETWEEN_GENS*FPS

#    # move potatoes
#    for potato_id, move in state["potatoes_state"].items():
#        potato_obj = blender_state["potatoes"][potato_id]
#        potato_obj.move(*move, frame=frame_ix)

#    # Delete eatten candies
#    current_candies = state["candies_state"].keys()
#    if previous_candies:
#        for prev_candy in previous_candies:
#            if prev_candy not in current_candies:
#                candy_obj = blender_state["candies"][prev_candy]
#                candy_obj.hide_at_frame(frame_ix)

#    previous_candies = current_candies

#    frame_ix += FPS


