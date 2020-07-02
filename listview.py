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

from . import main
from .main import op


class MESH_UL_shape_keys_tree(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        #obj = context.object
        #use_edit_mode = obj.use_shape_key_edit_mode and obj.type == 'MESH'
        
        prefs = context.preferences.addons['shape_tree'].preferences
        
        row = layout.row(align=True)
        row.alignment = 'LEFT'
        for x in range((item.path.count('//') - 1) * prefs.shape_key_indent_scale):
            row.separator(factor=1)
        
        if item.is_folder:
            row.separator_spacer()
            op(row, 'skt.folder_toggle', text='', emboss=len(list(item.children)) > 0,
               icon='TRIA_RIGHT' if item.is_collapsed else 'TRIA_DOWN', op_index=index
            )
            
        #row.prop(item, 'path', text="", emboss=False)
        row.prop(item, 'label', text="", emboss=False)
        
        row = layout.row(align=True)
        
        if item.is_folder:
            row.prop(item, 'is_muted', text="", emboss=False,
                     icon='HIDE_ON' if item.is_muted else 'HIDE_OFF')
            #op(row, 'skt.folder_ungroup', text="", icon='X', emboss=False, op_index=index)
            
        else:
            #if item.shapekey.mute or (obj.mode == 'EDIT' and not use_edit_mode):
                #row.active = False
           
            row.alignment = 'RIGHT'
            
            shapekey = item.shapekey
            if not shapekey.id_data.use_relative:
                row.prop(shapekey, 'frame', text="", emboss=False)
                
            if not item.path == '//Basis':
                row.prop(shapekey, 'value', text="", emboss=False)
                row.prop(shapekey, 'mute', text="", icon='HIDE_OFF', emboss=False)
            
                row.prop(
                    item, 'is_selected', text="", emboss=False,
                    icon='CHECKBOX_HLT' if item.is_selected else 'CHECKBOX_DEHLT',
                )
    
    
    def draw_filter(self, context, layout):
        obj = context.object
        
        row = layout.row()
        subrow = row.row(align=True)
        
        op(subrow, 'skt.clear_filter', text='', icon='X', emboss=False)
        subrow.prop(obj.skt, 'name_filter', text="")
        subrow.prop(obj.skt, 'name_filter_invert', text="",
            icon='ZOOM_OUT' if obj.skt.name_filter_invert else 'ZOOM_IN'
        )
        
        subrow = row.row(align=True)
        subrow.prop(obj.skt, 'value_filter', text="", icon='HIDE_OFF')
        
        if obj.skt.value_filter:
            subrow.prop(obj.skt, 'value_filter_threshold', text="")
            subrow.prop(
                obj.skt, 'value_filter_direction', text="", 
                icon='TRIA_RIGHT' if obj.skt.value_filter_direction else 'TRIA_LEFT'
            )
    
    
    def filter_items(self, context, data, propname):
        main.items.collapsed = set(
            x.path+'//' for x in main.items.filter(is_folder=True, is_collapsed=True)
        )
        skt = context.object.skt
        
        def sortorder(x):
            if x.path == '//Basis':
                return '0'  # Show "Basis" always on the top of the list.
            # Folders first: prepend foders with 0, shapekeys with 1
            path = '//0'.join(x.path.split('//')[:-1]) + ('//0' if x.is_folder else '//1')
            return f'1//{path}{x.label}'
        
        indices = {x.path: n for n, x in enumerate(sorted(skt.items, key=sortorder))}
        
        return (
            [self.bitflag_filter_item if x.visible else 0 for x in skt.items], 
            [indices.get(x.path) for x in skt.items]
        )
    
    
