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

from .main import NodeProxy


def op(row, op, **kwargs):
    result = row.operator(op, **{k:v for k,v in kwargs.items() if not k.startswith('op_')})
    for key in kwargs:
        if key.startswith('op_'):
            setattr(result, key[3:], kwargs[key])
    return result
    
    
    
#def get_all_nodes(self):
    #"""
    #"""
    #ordered = sorted(bpy.context.object.extra_props.shapenodes, key=lambda x: x.path)
    #return [NodeProxy(x.path) for x in ordered]
            
            
def add_shape( path=None, from_mix=False):
    node = _add_node(path or 'Key', is_folder=False)
    shapekey = bpy.context.object.shape_key_add(from_mix=from_mix)
    shapekey.name = node.path


def add_folder(path=None):
    node = _add_node(path, is_folder=True)
    bpy.context.object.extra_props.focused_node_index = node.index
    
    
def _add_node(path, is_folder):
    if not path.startswith('//'):
        cur_folder = None
        focused = get_focused_node()
        if focused:
            cur_folder = focused if focused.is_folder else focused.parent
            
        if cur_folder:
            path = f'{cur_folder.path}//{path}'
        else:
            path = '//' + path
    
    node = bpy.context.object.extra_props.shapenodes.add()
    node.is_folder = is_folder
    node.path = path
    
    return NodeProxy(node.path)
    

def get_filtered_nodes(**kw):
    """
    Get all nodes matching keyword:
        
        folders = get_filtered_nodes(is_folder=True)
        
    """
    for node in bpy.context.object.extra_props.shapenodes:
        if all(getattr(node, key) == kw[key] for key in kw):
            yield NodeProxy(node.path)
            
            
def get_visible_nodes():
    collapsed = set(x.path+'//' for x in get_filtered_nodes(is_folder=True, is_collapsed=True))
    extra_props = bpy.context.object.extra_props
    
    for node in extra_props.shapenodes:
        if any(node.path.startswith(x) for x in collapsed):
            continue
        
        if node.is_folder:
            yield NodeProxy(node.path)   # Always show folders.
            continue
        
        if extra_props.name_filter and extra_props.name_filter.lower() not in node.label.lower():
            continue
        
        if extra_props.value_filter:
            if extra_props.value_filter_direction:
                if extra_props.value_filter_threshold > self.shapekey.value:
                    continue
            else:
                if extra_props.value_filter_threshold < self.shapekey.value:
                    continue
                
        yield NodeProxy(node.path)
        


def get_ticked_or_focused() -> list[NodeProxy]:
    """
    If any node is ticked with a checkmark in the tree, return a list of all ticked nodes.
    Otherwise return a list with single item, focused node.
    Otherwise return empty list.
    """
    objprops = bpy.context.object.extra_props

    ticked = [NodeProxy(x.path) for x in objprops.shapenodes if x.is_ticked]
    if ticked:
        return ticked
    
    if objprops.focused_node_index < 0:
        return []
    
    try:
        return [NodeProxy(objprops.shapenodes[objprops.focused_node_index].path)]
    except:
        return []


def get_focused_node() -> NodeProxy:
    objprops = bpy.context.object.extra_props

    if objprops.focused_node_index < 0:
        return None
    
    try:
        return NodeProxy(objprops.shapenodes[objprops.focused_node_index].path)
    except:
        # focused_node_index is invalid. Safely return None.
        return None
    
