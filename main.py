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


import bpy
import bl_ui
from bpy.props import BoolProperty, IntProperty, CollectionProperty, StringProperty, FloatProperty


    
class NodeProxy:
    """
    This class represents Node (tree node) with a specific path.
    
    Blender's UIList has an annoying issue: when you add\delete\move items (we use custom item type, Node) 
    in it, all instances of Node will be modified in-place. I.e Node instance you got could change path:
    
        item1, item2, item3 = object.extra_props.shapenodes[0:2]
        assert(item2.path == '//Key1')
        object.extra_props.shapenodes.remove(1)
        assert(item2.path == '//Key1')  # ERROR: item2.path changed to "//Key2"
        
    So in many places it is more convenient to use this class instead of using Node. This class
    always refers to an node with a certain path, passing down attribute access to the 
    appropriate Node.
    """
    def __init__(self, path):
        self._path = path
        
    def __repr__(self):
        return f'NodeProxy({self._path})'
    
    def __setattr__(self, name, val):
        if name.startswith('_'):
            return super().__setattr__(name, val)
        setattr(bpy.context.object.extra_props.shapenodes[self.index], name, val)
        if name == 'path':
            self._path = val
            
    def __getattr__(self, name):
        if name.startswith('_'):
            return super().__getattr__(name)
        if name == 'path':
            return self._path
        if name == 'delete':
            return self.delete
        if name in self.__class__.__dict__:
            return super().__getattr__(name)
        #print(f'__getattr__ {name}')
        return getattr(bpy.context.object.extra_props.shapenodes[self.index], name)
            
    @property
    def index(self):
        for n, node in enumerate(bpy.context.object.extra_props.shapenodes):
            if node.path == self.path:
                return n

    def delete(self):
        for node in self.children:
            node.delete()
        if not self.is_folder:
            if self.path == '//Basis' and len(bpy.context.object.data.shape_keys.key_blocks) > 1:
                return
            if self.sk_index >= 0:
                print(f"Node.delete() INFO: about to remove shape key with path {self.path}.")
                bpy.context.object.active_shape_key_index = self.sk_index
                # There is an issue to keep in mind, that calling bpy.ops.object.shape_key_remove(), will
                # immediately execute depsgraph_update_post() handler, calling __init__.sync_node_shapekeys(),
                # which will see that shape key was just removed, and try to remove this tree node.
                # After tree node gets removed in __init__.sync_node_shapekeys(), this function will proceed
                # and self.index of this NodeProxy will be None.
                bpy.ops.object.shape_key_remove()
                print(f"Node.delete() INFO: shape key with path {self.path} removed.")
        if self.index:
            print(f"Node.delete() INFO: removing tree node {self.path} with index {self.index}")
            bpy.context.object.extra_props.shapenodes.remove(self.index)
    

class Node(bpy.types.PropertyGroup):
    """
    Tree node. Member of main.ExtraObjectPropsGroup.shapenodes CollectionProperty 
    (see ExtraObjectPropsGroup class below)
    """
    is_folder: BoolProperty(name="Is folder", default=False)
    is_collapsed: BoolProperty(name="Is collapsed", default=False)
    
    is_ticked: BoolProperty(
        name = "Is ticked", default = False, 
        update = lambda x, a: x.on_ticked()
    )
    
    def on_ticked(self):
        # Change focus to the node that is ticked
        if self.is_ticked:
            bpy.context.object.extra_props.focused_node_index = NodeProxy(self.path).index
    
    is_muted: BoolProperty(
        name = "Is muted", default = False,  update = lambda x, a: x.on_muted()
    )
    def on_muted(self):
        if self.is_folder:
            for node in self.children:
                node.is_muted = self.is_muted
        else:
            self.shapekey.mute = self.is_muted
        
    
    label: StringProperty(
        get = lambda x: x.path.rpartition('//')[-1],
        set = lambda x, val: setattr(x, 'path', x.path.rpartition('//')[0] + f'//{val}'), 
    )
    path: StringProperty(
        get = lambda x: x.get('PATH', ''),
        set = lambda x, val: x.on_path(val)
    )
    
    def on_path(self, new_path):
        if not new_path.startswith('//'):
            new_path = '//' + new_path
            
        if self.get('PATH') == '//Basis':
            return
        
        if self.get('PATH') == new_path:
            return
        
        if new_path == '//Basis' and self.is_folder:
            new_path += '0'
            
        while new_path in set(x.path for x in bpy.context.object.extra_props.shapenodes):
            new_path += '0'
            
        if self.get('PATH') and not self.is_folder:
            self.shapekey.name = new_path
            
        if self.is_folder:
            for node in self.children:
                node.path = f'{new_path}//{node.label}'
                
        self['PATH'] = new_path
        
        
    @property
    def parent(self):
        for node in bpy.context.object.extra_props.shapenodes:
            if node.path == self.path.rpartition('//')[0]:
                return NodeProxy(node.path)
            
    
    parents = property(lambda x: ([x.parent] + x.parent.parents) if x.parent else [])
    
    #@property
    #def parents(self):
        #if self.parent:
            #yield self.parent
            #for node in self.parent.parents:
                #yield node
    
    @property
    def children(self):
        for node in sorted(list(bpy.context.object.extra_props.shapenodes), key=lambda x: x.path):
            if self.path and node.path.rpartition('//')[0:2] == (self.path, '//'):
                yield node
                
    #@property
    #def index(self):
        #for n, node in enumerate(bpy.context.object.extra_props.shapenodes):
            ## WARNING: self.path of a Node can be implicitly changed by blender when self.shapenodes 
            ## CollectionProperty, holding list of Node instances, changes in size. Hence it is 
            ## recommended to use NodeProxy instead of Node directly. See quirks in NodeProxy.delete()
            ## method.
            #if node.path == self.path:
                #return n
            
    @property
    def shapekey(self):
        #if bpy.context.object.data.shape_keys:
        return bpy.context.object.data.shape_keys.key_blocks.get(self.path)
        #return bpy.context.object.data.shape_keys.key_blocks[self.index]
        
    @property
    def sk_index(self):
        return bpy.context.object.data.shape_keys.key_blocks.find(self.path)
    

    
class ExtraObjectPropsGroup(bpy.types.PropertyGroup):
    """ Per-object data and settings. """
    
    shapenodes: CollectionProperty(type=Node)
    focused_node_index: IntProperty(default=-1,  update = lambda x, a: x.on_focus_change())
    
    def on_focus_change(self):
        """
        Ensure blender internal object.active_shape_key_index follows focused tree node.
        """
        obj = bpy.context.object
        
        #if obj.extra_props.focused_node_index < 0:
        #focused_node = get_focused_node()
        
        if self.focused_node_index >= 0:
            focused_node = NodeProxy(self.shapenodes[self.focused_node_index].path)
            print('focused_node', focused_node, focused_node.sk_index)
            
            obj.active_shape_key_index = focused_node.sk_index
            
            # If user previously ticked only one other node, untick it. Without this, it is not
            # obvious for user which one node will be affected - ticked or focused.
            ticked = [NodeProxy(x.path) for x in obj.extra_props.shapenodes if x.is_ticked]
            if len(ticked) == 1 and not ticked[0].path == focused_node.path:
                ticked[0].is_ticked = False
                
            # Ensure focused node parent folders are expanded.
            for folder in focused_node.parents:
                folder.is_collapsed = False
        else:
            obj.active_shape_key_index = -1
            
    
    driver_visible: BoolProperty(name="Show Driver", default=True)
    
    name_filter: StringProperty(name="Name filter", default='')
    name_filter_invert: BoolProperty(name="Name filter invert", default=False)
    
    value_filter: BoolProperty(
        name="Filter shapes by value", default=False,
        description="Only show shape keys with a value above/below a certain threshold",
    )
    
    value_filter_threshold: FloatProperty(
        name="Value filter threshold", description="Only show shape keys above/below this value",
        soft_min=-1.0, soft_max=1.0, default=0.001, step=1, precision=3
    )
    
    value_filter_direction: BoolProperty(
        name="Greater/Less", default=False, description="Greater/Less",
    )

