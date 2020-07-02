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

from .main import op
from . import main

        
class MESH_MT_skt_actions(bpy.types.Menu):
    bl_label = "Do ..."
    
    def draw(self, context):
        selected = main.items.selected
        col = self.layout
        
        if len(selected) == 1 and selected[0].path == '//Basis':
            col.enabled = False
        
        if col.enabled:
            col.menu('MESH_MT_skt_move', icon='FILE_PARENT')
            
        if len(selected) == 1 and not selected[0].is_folder:
            op(col, 'object.shape_key_mirror', icon='ARROW_LEFTRIGHT', op_use_topology=False)
            op(col, 'object.shape_key_mirror', icon='ARROW_LEFTRIGHT', op_use_topology=True,
                text="Mirror Shape Key (Topology)")
            
            op(col, 'object.shape_key_transfer', icon='COPY_ID')
            op(col, 'object.join_shapes', icon='COPY_ID')
        
        col = col.column()
        if len(selected) == 1 and selected[0].path == '//Basis':
            col.enabled = True
        col.separator()
        op(col, 'skt.mute', icon='HIDE_ON')
        op(col, 'skt.unmute', icon='HIDE_OFF')
        col.separator()
        op(col, 'skt.delete', icon='X')
        

class MESH_MT_skt_move(bpy.types.Menu):
    bl_label = "Move to"
    
    def draw(self, context):
        selected = main.items.selected
        if len(selected) == 1:
            self.layout.label(text=f'Move {selected[0].label} to ...')
        op(self.layout, 'skt.move', text='/', op_dst='')
                
        for item in sorted(main.items.filter(is_folder=True), key=lambda x: x.path):
            if len(selected) == 1 and item.path == selected[0].path:
                continue
                #import ipdb; ipdb.sset_trace()
            op(self.layout, 'skt.move', text=item.path.replace('//', ' / '), op_dst=item.path)
                    

