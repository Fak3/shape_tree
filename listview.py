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

from . import util
from .util import op


class MESH_UL_shape_keys_tree(bpy.types.UIList):
    def draw_item(self, context, layout, data, shapenode, icon, active_data, active_propname, index):
        #obj = context.object
        #use_edit_mode = obj.use_shape_key_edit_mode and obj.type == 'MESH'
        
        prefs = context.preferences.addons['shape_tree'].preferences
        
        row = layout.row(align=True)
        
        row.alignment = 'LEFT'
        for x in range((shapenode.path.count('//') - 1) * prefs.shape_key_indent_scale):
            row.separator(factor=1)
        
        if shapenode.is_folder:
            row.separator_spacer()
            op(row, 'skt.folder_toggle', text='', emboss=len(list(shapenode.children)) > 0,
               icon='TRIA_RIGHT' if shapenode.is_collapsed else 'TRIA_DOWN', op_index=index
            )
        elif not shapenode.shapekey:
            row.prop(shapenode, 'label', text="(removed)", emboss=False)
            return
            
        #row.prop(shapenode, 'path', text="", emboss=False)
        row.prop(shapenode, 'label', text="", emboss=False)
        
        row = layout.row(align=True)
        
        if shapenode.is_folder:
            row.alignment = 'RIGHT'
            row.prop(shapenode, 'is_muted', text="", emboss=False,
                     icon='HIDE_ON' if shapenode.is_muted else 'HIDE_OFF')
            #col = row.column()
            #col.separator(factor=1)
            
        else:
            #if shapenode.shapekey.mute or (obj.mode == 'EDIT' and not use_edit_mode):
                #row.active = False
           
            row.alignment = 'RIGHT'
            
            #print(shapenode, shapenode.label, shapenode.get('PATH', 'mm'), shapenode.shapekey)
            row.enabled = shapenode.shapekey.mute is False
                
            if not shapenode.shapekey.id_data.use_relative:
                row.prop(shapenode.shapekey, 'frame', text="", emboss=False)
                
            if not shapenode.path == '//Basis':
                #print(shapenode.shapekey.id_data.animation_data.drivers[0].driver)
                #if shapenode.shapekey.id_data.animation_data.drivers[0].driver:
                row.prop(shapenode.shapekey, 'value', text="", emboss=True)
                #else:
                #row.prop(shapenode.shapekey, 'value', text="", emboss=False)
                    
                row = layout.row(align=True)
            
                row.prop(shapenode.shapekey, 'mute', text="", icon='HIDE_OFF', emboss=False)
                
                col = row.column()
                col.prop(
                    shapenode, 'is_ticked', text="", emboss=False,
                    icon='CHECKBOX_HLT' if shapenode.is_ticked else 'CHECKBOX_DEHLT',
                )
    
    
    def draw_filter(self, context, layout):
        obj = context.object
        
        row = layout.row()
        subrow = row.row(align=True)
        
        op(subrow, 'skt.clear_filter', text='', icon='X', emboss=False)
        subrow.prop(obj.extra_props, 'name_filter', text="")
        subrow.prop(obj.extra_props, 'name_filter_invert', text="",
            icon='ZOOM_OUT' if obj.extra_props.name_filter_invert else 'ZOOM_IN'
        )
        
        subrow = row.row(align=True)
        subrow.prop(obj.extra_props, 'value_filter', text="", icon='HIDE_OFF')
        
        if obj.extra_props.value_filter:
            subrow.prop(obj.extra_props, 'value_filter_threshold', text="")
            subrow.prop(
                obj.extra_props, 'value_filter_direction', text="", 
                icon='TRIA_RIGHT' if obj.extra_props.value_filter_direction else 'TRIA_LEFT'
            )
    
    
    def filter_items(self, context, data, propname):
        shapenodes = context.object.extra_props.shapenodes
        
        def sortorder(x):
            if x.path == '//Basis':
                return '0'  # Show "Basis" always on the top of the list.
            # Folders first: prepend foders with 0, shapekeys with 1
            path = '//0'.join(x.path.split('//')[:-1]) + ('//0' if x.is_folder else '//1')
            return f'1//{path}{x.label}'
        
        indices = {x.path: n for n, x in enumerate(sorted(shapenodes, key=sortorder))}
        
        visible = set(x.path for x in util.get_visible_nodes())
        return (
            [self.bitflag_filter_item if x.path in visible else 0 for x in shapenodes], 
            [indices.get(x.path) for x in shapenodes]
        )
    
    
