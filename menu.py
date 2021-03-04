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

from .util import op
from . import util
#from . import main

        
class MESH_MT_skt_actions(bpy.types.Menu):
    bl_label = "Do ..."
    
    def draw(self, context):
        affected = util.get_ticked_or_focused()
        col = self.layout
        
        if len(affected) == 1 and affected[0].path == '//Basis':
            col.enabled = False
        
        if col.enabled:
            col.menu('MESH_MT_skt_move', icon='FILE_PARENT')
            
        if len(affected) == 1 and not affected[0].is_folder:
            op(col, 'object.shape_key_mirror', icon='ARROW_LEFTRIGHT', op_use_topology=False)
            op(col, 'object.shape_key_mirror', icon='ARROW_LEFTRIGHT', op_use_topology=True,
                text="Mirror Shape Key (Topology)")
            
            op(col, 'object.shape_key_transfer', icon='COPY_ID')
            op(col, 'object.join_shapes', icon='COPY_ID')
        
        col = col.column()
        if len(affected) == 1 and affected[0].path == '//Basis':
            col.enabled = True
        col.separator()
        op(col, 'skt.mute', icon='HIDE_ON')
        op(col, 'skt.unmute', icon='HIDE_OFF')
        col.separator()
        op(col, 'skt.delete', icon='X')
        

class MESH_MT_skt_move(bpy.types.Menu):
    bl_label = "Move to"
    
    def draw(self, context):
        affected_nodes = util.get_ticked_or_focused()
        
        if len(affected_nodes) == 1:
            self.layout.label(text=f'Move {affected_nodes[0].label} to ...')
            
        op(self.layout, 'skt.move', text='/', op_dst='')
        
        for folder in sorted(util.get_filtered_nodes(is_folder=True), key=lambda x: x.path):
            if len(affected_nodes) == 1 and folder.path == affected_nodes[0].path:
                continue  # Don't allow to move folder into itself
                
            op(self.layout, 'skt.move', text=folder.path.replace('//', ' / '), op_dst=folder.path)
                    

