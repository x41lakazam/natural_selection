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

def select_all_children(obj):
    obj.select_set(state=True)
    for child in obj.children:
        select_all_children(child)

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
        
    def unhide_at_frame(self, frame_n, x, y, z=0):
        self.obj.location = (x,y,z)
        self.obj.keyframe_insert(data_path="location", frame=frame_n)

    def hide_at_frame(self, frame_n, hide_loc=(0,0,-100)):
        self.obj_location = hide_loc
        self.obj.keyframe_insert(data_path="location", frame=frame_n)

    def move(self, x, y, z=0):
        self.obj.location = (x,y,z)

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
    
       
        
