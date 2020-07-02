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


def op(row, op, **kwargs):
    result = row.operator(op, **{k:v for k,v in kwargs.items() if not k.startswith('op_')})
    for key in kwargs:
        if key.startswith('op_'):
            setattr(result, key[3:], kwargs[key])
    return result
    
    
class AddonProperties(bpy.types.AddonPreferences):
    bl_idname = 'shape_tree'
    
    shape_key_indent_scale : bpy.props.IntProperty(name="Indentation",
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




class Items:
    """
    This is convenience class that represents bpy.context.object.skt collection. Provides
    methods to add/retieve/select nodes of the shape keys tree.
    """
    def __iter__(self):
        ordered = sorted(bpy.context.object.skt.items, key=lambda x: x.path)
        return iter([ItemProxy(x.path) for x in ordered])
            
    def __getitem__(self, path):
        """
        Get item by path:
            
            main.items['//Basis']
            
        """
        if not path:
            return None
        for item in bpy.context.object.skt.items:
            if item.path == path:
                return ItemProxy(item.path)
            
    @property
    def active(self):
        if bpy.context.object.skt.active_item < 0:
            return None
        try:
            return ItemProxy(bpy.context.object.skt.items[bpy.context.object.skt.active_item].path)
        except:
            pass
        return None
    
    @active.setter
    def active(self, item):
        if not item:
            selected = list(self.get_selected())
            if len(selected) == 1:
                #item = selected[0]
                bpy.context.object.skt.active_item = selected[0].index
                return
            else:
                bpy.context.object.skt.active_item = -1
                return
        for folder in item.parents:
            folder.is_collapsed = False
        bpy.context.object.skt.active_item = item.index
        
    def get_selected(self):
        for item in bpy.context.object.skt.items:
            if item.is_selected:
                yield ItemProxy(item.path)
        
    @property
    def selected(self):
        selected = list(self.get_selected())
        if self.active and not selected:
            return [self.active]
        return selected
    
    def filter(self, **kw):
        """
        Get all items matching keyword:
            
            folders = list(main.items.filter(is_folder=True))
            
        """
        for item in bpy.context.object.skt.items:
            if all(getattr(item, key) == kw[key] for key in kw):
                yield ItemProxy(item.path)
            
    def keys(self):
        return set(x.path for x in bpy.context.object.skt.items)
        
    @property
    def active_folder(self):
        if not self.active:
            return None
        return self.active if self.active.is_folder else self.active.parent
    
    def add_shape(self, path=None, from_mix=False):
        item = self._add(path or 'Key', is_folder=False)
        shapekey = bpy.context.object.shape_key_add(from_mix=from_mix)
        shapekey.name = item.path
    
    def add_folder(self, path=None):
        item = self._add(path, is_folder=True)
        self.active = item
        
    def _add(self, path, is_folder):
        if not path.startswith('//'):
            if self.active_folder:
                path = f'{self.active_folder.path}//{path}'
            else:
                path = '//' + path
        
        item = bpy.context.object.skt.items.add()
        item.is_folder = is_folder
        item.path = path
        
        return ItemProxy(item.path)
    
    @property
    def visible(self):
        items.collapsed = list(x.path+'//' for x in items.filter(is_folder=True, is_collapsed=True))
        return self.filter(visible=True)
        
    
items = Items()


class ItemProxy:
    """
    This class represents Item (tree node) with a specific path.
    
    Blender's UIList has an annoying issue: when you add\delete\move items in it, all instances
    of Item will be modified in-place. I.e Item you got could change path:
    
        item1, item2, item3 = object.skt.items[0:2]
        assert(item2.path == '//Key1')
        object.skt.items.remove(1)
        assert(item2.path == '//Key1')  # ERROR: item2.path changed to "//Key2"
        
    So in many places it is more convenient to use this class instead of using Item. This class
    always refers to an item with a certain path, passing down attribute access to the 
    appropriate Item.
    """
    def __init__(self, path):
        self._path = path
        
    def __setattr__(self, name, val):
        if name.startswith('_'):
            return super().__setattr__(name, val)
        setattr(bpy.context.object.skt.items[self.index], name, val)
        if name == 'path':
            self._path = val
            
    def __getattr__(self, name):
        if name.startswith('_'):
            return super().__getattr__(name)
        if name == 'path':
            return self._path
        if name in self.__class__.__dict__:
            return super().__getattr__(name)
        #print(f'__getattr__ {name}')
        return getattr(bpy.context.object.skt.items[self.index], name)
            
    @property
    def index(self):
        for n, item in enumerate(bpy.context.object.skt.items):
            if item.path == self.path:
                return n


class Item(bpy.types.PropertyGroup):
    """
    Tree node. Member of main.ObjectData.items CollectionProperty (see ObjectData class below)
    """
    is_folder: bpy.props.BoolProperty(name="Is folder", default=False)
    is_collapsed: bpy.props.BoolProperty(name="Is collapsed", default=False)
    is_selected: bpy.props.BoolProperty(
        name = "Is selected", default = False, 
        update = lambda x, a: setattr(items, 'active', x) if x.is_selected else None
    )
    
    is_muted: bpy.props.BoolProperty(
        name = "Is muted", default = False,  update = lambda x, a: x.on_muted()
    )
    def on_muted(self):
        if self.is_folder:
            for item in self.children:
                item.is_muted = self.is_muted
        else:
            self.shapekey.mute = self.is_muted
        
    
    label: bpy.props.StringProperty(
        get = lambda x: x.path.rpartition('//')[-1],
        set = lambda x, val: setattr(x, 'path', x.path.rpartition('//')[0] + f'//{val}'), 
    )
    path: bpy.props.StringProperty(
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
            
        while new_path in items.keys():
            new_path += '0'
            
        if self.get('PATH') and not self.is_folder:
            self.shapekey.name = new_path
            
        if self.is_folder:
            for item in self.children:
                item.path = f'{new_path}//{item.label}'
                
        self['PATH'] = new_path
        
        
    @property
    def parent(self):
        return items[self.path.rpartition('//')[0]] or None
    
    parents = property(lambda x: ([x.parent] + x.parent.parents) if x.parent else [])
    
    #@property
    #def parents(self):
        #if self.parent:
            #yield self.parent
            #for item in self.parent.parents:
                #yield item
    
    def delete(self):
        for item in self.children:
            item.delete()
        if not self.is_folder:
            if self.path == '//Basis' and len(bpy.context.object.data.shape_keys.key_blocks) > 1:
                return
            bpy.context.object.active_shape_key_index = self.sk_index
            bpy.ops.object.shape_key_remove()
        bpy.context.object.skt.items.remove(self.index)
    
    @property
    def children(self):
        for item in items:
            if self.path and item.path.rpartition('//')[0:2] == (self.path, '//'):
                yield item
                
    @property
    def index(self):
        for n, item in enumerate(bpy.context.object.skt.items):
            if item.path == self.path:
                return n
            
    @property
    def shapekey(self):
        #if bpy.context.object.data.shape_keys:
        return bpy.context.object.data.shape_keys.key_blocks.get(self.path)
        #return bpy.context.object.data.shape_keys.key_blocks[self.index]
        
    @property
    def sk_index(self):
        return bpy.context.object.data.shape_keys.key_blocks.find(self.path)
    
    @property
    def visible(self):
        skt = bpy.context.object.skt
        #collapsed = list(x.path+'//' for x in items.filter(is_folder=True, is_collapsed=True))
        
        if any(self.path.startswith(x) for x in items.collapsed):
            return False
        
        if self.is_folder:
            return True   # Always show folders.
        
        if skt.name_filter and skt.name_filter.lower() not in self.label.lower():
            return False
        
        if skt.value_filter and not self.is_folder:
            if skt.value_filter_direction:
                return bool(skt.value_filter_threshold < self.shapekey.value)
            else:
                return bool(skt.value_filter_threshold > self.shapekey.value)
        
        return True


    
class ObjectData(bpy.types.PropertyGroup):
    """ Per-object data and settings. """
    
    driver_visible: bpy.props.BoolProperty(name="Show Driver", default=True)
    
    name_filter: bpy.props.StringProperty(name="Name filter", default='')
    name_filter_invert: bpy.props.BoolProperty(name="Name filter invert", default=False)
    
    value_filter: bpy.props.BoolProperty(
        name="Filter shapes by value", default=False,
        description="Only show shape keys with a value above/below a certain threshold",
    )
    
    value_filter_threshold: bpy.props.FloatProperty(
        name="Value filter threshold", description="Only show shape keys above/below this value",
        soft_min=-1.0, soft_max=1.0, default=0.001, step=1, precision=3
    )
    
    value_filter_direction: bpy.props.BoolProperty(
        name="Greater/Less", default=False, description="Greater/Less",
    )

    items: bpy.props.CollectionProperty(type=Item)
    active_item: bpy.props.IntProperty(default=-1,  update = lambda x, a: x.on_active())
    
    def on_active(self):
        if items.active:
            bpy.context.object.active_shape_key_index = items.active.sk_index
            
            selected = list(items.get_selected())
            if len(selected) == 1 and not selected[0].path == items.active.path:
                selected[0].is_selected = False
        else:
            bpy.context.object.active_shape_key_index = -1
            
    
