# ##### BEGIN GPL LICENSE BLOCK #####
#
#  copyright 2019-2020 Michael Glen Montague
#  copyright 2020 <someuniquename@gmail.com> Evstifeev Roman
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


    
class AddonSettings(bpy.types.AddonPreferences):
    bl_idname = 'shape_tree'
    
    shape_key_indent_scale: bpy.props.IntProperty(name="Indentation",
        description="Indentation of folder contents", min=0, max=8, default=2
    )
    
    hide_default: bpy.props.BoolProperty(name="Hide Default Panel",
        description = "Hides the default Shape Keys panel",
        default = True, update = lambda x, a: x.update_hide_default()
    )
    def update_hide_default(self):
        if self.hide_default:
            bpy.utils.unregister_class(bl_ui.properties_data_mesh.DATA_PT_shape_keys)
        else:
            bpy.utils.register_class(bl_ui.properties_data_mesh.DATA_PT_shape_keys)
    
    def draw(self, context):
        row = self.layout.row()
        row.prop(self, 'hide_default')
        row.prop(self, 'shape_key_indent_scale')


def sync_node_shapekeys():
    for obj in bpy.context.scene.objects:
        existing_nodes = set(x.path for x in obj.extra_props.shapenodes)
        existing_shapekeys = set()
        
        if getattr(obj.data, 'shape_keys', None):
            existing_shapekeys = set(x.name for x in obj.data.shape_keys.key_blocks.values())
            for id, shapekey in obj.data.shape_keys.key_blocks.items():
                if shapekey.name in existing_nodes:
                    continue
                print(f'sync_node_shapekeys() INFO: {obj}, adding {shapekey.name} to shape keys tree.')
                if not shapekey.name.startswith('//'):
                    shapekey.name = '//' + shapekey.name
                node = obj.extra_props.shapenodes.add()
                node.is_folder = False
                node.path = shapekey.name
        
        for node in list(main.NodeProxy(x.path) for x in obj.extra_props.shapenodes if not x.is_folder):
            if node.path not in existing_shapekeys:
                print(f'sync_node_shapekeys() WARN: {obj}, {node.path} shape key does not exist, removing the tree node.')
                obj.extra_props.shapenodes.remove(node.index)
                #node.delete()

@persistent
def depsgraph_update_post(*a):
    #print("depsgraph_update_post", a)
    sync_node_shapekeys()


@persistent
def load_post(*a):
    #print("load_post", a)
    sync_node_shapekeys()


def classes():
    yield AddonSettings
    for module in main, menu, operator, listview, panel:
        for name, cls in module.__dict__.items():
            if isinstance(cls, type) and issubclass(cls, bpy_struct) and 'Base' not in name:
                yield cls


def register():
    print("Register shape tree")
    
    for klass in classes():
        bpy.utils.register_class(klass)
    
    bpy.types.Object.extra_props = bpy.props.PointerProperty(type=main.ExtraObjectPropsGroup)

    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post)
    bpy.app.handlers.load_post.append(load_post)

    preferences = bpy.context.preferences.addons['shape_tree'].preferences
    
    if preferences.hide_default and hasattr(bpy.types, 'DATA_PT_shape_keys'):
        bpy.utils.unregister_class(bl_ui.properties_data_mesh.DATA_PT_shape_keys)
    
    

def unregister():
    print("Unregister shape tree")
    
    for klass in classes():
        bpy.utils.unregister_class(klass)
    
    if hasattr(bpy.types.Object, 'extra_props'):
        del bpy.types.Object.extra_props
        
    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_post)
    bpy.app.handlers.load_post.remove(load_post)

    default_panel_exists = hasattr(bpy.types, 'DATA_PT_shape_keys')
    
    if not default_panel_exists:
        bpy.utils.register_class(bl_ui.properties_data_mesh.DATA_PT_shape_keys)


if __name__ == "__main__":
    unregister()
    register()
  
