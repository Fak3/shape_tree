# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# This add-on is based on "Shape keys plus" by Michael Glen Montague.

bl_info = {
    "name" : "Shape Keys Tree",
    "author" : "Evstifeev Roman",
    "version" : (0, 1),
    "blender" : (2, 82, 7),
    "location" : "Properties > Data",
    "description" : "Adds a panel with extra options for creating, sorting, viewing, and driving shape keys.",
    "category" : "Object"
}


import importlib
import bl_ui
import re

if "bpy" in locals():
    for module in main, menu, operator, listview, panel:
        importlib.reload(module)
else:
    import bpy
    from . import main, menu, operator, listview, panel


from bpy.types import bpy_struct
from bpy.app.handlers import persistent


@persistent
def depsgraph_update_post(*a):
    #print("depsgraph_update_post", a)
    for obj in bpy.context.scene.objects:
        if getattr(obj.data, 'shape_keys', None):
            keys = set(x.path for x in obj.skt.items)
            for id, shapekey in obj.data.shape_keys.key_blocks.items():
                if shapekey.name in keys:
                    continue
                print(f'{obj}, adding {shapekey.name} to shape keys tree.')
                if not shapekey.name.startswith('//'):
                    shapekey.name = '//' + shapekey.name
                item = obj.skt.items.add()
                item.is_folder = False
                item.path = shapekey.name

@persistent
def load_post(*a):
    #print("load_post", a)
    for obj in bpy.context.scene.objects:
        if getattr(obj.data, 'shape_keys', None) and not obj.skt.items:
            for id, shapekey in obj.data.shape_keys.key_blocks.items():
                shapekey.name = '//' + shapekey.name
                item = obj.skt.items.add()
                item.is_folder = False
                item.path = shapekey.name

def classes():
    for module in main, menu, operator, listview, panel:
        for name, cls in module.__dict__.items():
            if isinstance(cls, type) and issubclass(cls, bpy_struct) and 'Base' not in name:
                yield cls


def register():
    print("Register shape tree")
    
    for klass in classes():
        bpy.utils.register_class(klass)
    
    bpy.types.Object.skt = bpy.props.PointerProperty(type=main.ObjectData)

    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post)
    bpy.app.handlers.load_post.append(load_post)

    preferences = bpy.context.preferences.addons['shape_tree'].preferences
    
    if preferences.hide_default and hasattr(bpy.types, 'DATA_PT_shape_keys'):
        bpy.utils.unregister_class(bl_ui.properties_data_mesh.DATA_PT_shape_keys)
    
    

def unregister():
    print("Unregister shape tree")
    
    for klass in classes():
        bpy.utils.unregister_class(klass)
    
    if hasattr(bpy.types.Object, 'skt'):
        del bpy.types.Object.skt
        
    default_panel_exists = hasattr(bpy.types, 'DATA_PT_shape_keys')
    
    if not default_panel_exists:
        bpy.utils.register_class(bl_ui.properties_data_mesh.DATA_PT_shape_keys)


if __name__ == "__main__":
    unregister()
    register()
  
