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
from . import util


class Base(bpy.types.Operator):
    bl_options = {'REGISTER', 'UNDO'}


class OBJECT_OT_move(Base):
    bl_idname = 'skt.move'
    bl_label = bl_description = "Move"

    dst: bpy.props.StringProperty(options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return context.object.mode != 'EDIT'

    def execute(self, context):
        for node in util.get_ticked_or_focused():
            if node.path not in ('//Base', self.dst):
                node.path = f'{self.dst}//{node.label}'
        for node in list(NodeProxy(x.path) for x in context.object.extra_props.shapenodes):
            node.is_ticked = False

        return {'FINISHED'}


class OBJECT_OT_new_folder(Base):
    bl_idname = 'skt.new_folder'
    bl_label = bl_description = "New folder"

    def execute(self, context):
        util.add_folder('Folder')
        return {'FINISHED'}


class OBJECT_OT_skt_shape_key_add(Base):
    bl_idname = 'skt.shape_key_add'
    bl_label = bl_description = "Add Shape Key"

    type: bpy.props.EnumProperty(
        items=(('DEFAULT', "", ""), ('FROM_MIX', "", "")),
        default='DEFAULT',
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        obj = context.object
        valid_types = {'MESH', 'LATTICE', 'CURVE', 'SURFACE'}

        return obj and obj.mode != 'EDIT' and obj.type in valid_types

    def execute(self, context):
        if not list(util.get_filtered_nodes(is_folder=False)):
            util.add_shape(path="//Basis")
        util.add_shape(from_mix=bool(self.type == 'FROM_MIX'))
        return {'FINISHED'}


class OBJECT_OT_delete(Base):
    bl_idname = 'skt.delete'
    bl_label = bl_description = "Delete"

    @classmethod
    def poll(cls, context):
        return context.object.mode != 'EDIT'

    def execute(self, context):
        for node in util.get_ticked_or_focused():
            print(f'Operator delete: {context.object}, {node.path}')
            node.delete()
        print('\n'.join(sorted([x.path for x in context.object.extra_props.shapenodes])))
        return {'FINISHED'}



class OBJECT_OT_select_inverse(Base):
    bl_idname = 'skt.select_inverse'
    bl_label = bl_description = "Invert selection"
    def execute(self, context):
        for node in context.object.extra_props.shapenodes:
            if node.is_folder or node.path == '//Basis':
                node.is_ticked = False
            else:
                node.is_ticked = not node.is_ticked
        return {'FINISHED'}


class OBJECT_OT_select_all(Base):
    bl_idname = 'skt.select_all'
    bl_label = bl_description = "Select all"

    def execute(self, context):
        for node in util.get_visible_nodes():
            if node.is_folder or node.path == '//Basis':
                node.is_ticked = False
            else:
                node.is_ticked = True
        return {'FINISHED'}


class OBJECT_OT_select_none(Base):
    bl_idname = 'skt.select_none'
    bl_label = bl_description = "Select none"

    def execute(self, context):
        context.object.extra_props.focused_node_index = -1

        for node in context.object.extra_props.shapenodes:
            node.is_ticked = False
        return {'FINISHED'}




class OBJECT_OT_select_toggle(Base):
    bl_idname = 'skt.select_toggle'
    bl_label = bl_description = "Select/Deselect"

    index: bpy.props.IntProperty(options={'HIDDEN'})

    def execute(self, context):
        node = context.object.extra_props.shapenodes[self.index]
        node.is_ticked = not node.is_ticked
        return {'FINISHED'}


class OBJECT_OT_skt_mute(bpy.types.Operator):
    bl_idname = 'skt.mute'
    bl_label = bl_description = "Mute"

    def execute(self, context):
        for node in util.get_ticked_or_focused():
            if node.is_folder:
                node.is_muted = True
            else:
                node.shapekey.mute = True
        return {'FINISHED'}


class OBJECT_OT_skt_unmute(bpy.types.Operator):
    bl_idname = 'skt.unmute'
    bl_label = bl_description = "Unmute"

    def execute(self, context):
        for node in util.get_ticked_or_focused():
            if node.is_folder:
                node.is_muted = False
            else:
                node.shapekey.mute = False
        return {'FINISHED'}


class OBJECT_OT_skt_folder_toggle(bpy.types.Operator):
    bl_idname = 'skt.folder_toggle'
    bl_label = bl_description = "Expand/Collapse"

    index: bpy.props.IntProperty(options={'HIDDEN'})

    def execute(self, context):
        node = NodeProxy(context.object.extra_props.shapenodes[self.index].path)
        node.is_collapsed = not node.is_collapsed
        #print(f'toggle {node.path} now {node.is_collapsed}')
        context.object.extra_props.focused_node_index = node.index
        return {'FINISHED'}


class OBJECT_OT_skt_expand_all(bpy.types.Operator):
    bl_idname = 'skt.expand_all'
    bl_label = bl_description = "Expand all"

    def execute(self, context):
        for node in context.object.extra_props.shapenodes:
            node.is_collapsed = False
        return {'FINISHED'}

class OBJECT_OT_skt_collapse_all(bpy.types.Operator):
    bl_idname = 'skt.collapse_all'
    bl_label = bl_description = "Collapse all"

    def execute(self, context):
        for node in context.object.extra_props.shapenodes:
            node.is_collapsed = True
        return {'FINISHED'}


class OBJECT_OT_skt_clear_filter(bpy.types.Operator):
    bl_idname = 'skt.clear_filter'
    bl_label = bl_description = "Clear filter"

    def execute(self, context):
        context.object.extra_props.name_filter = ''
        return {'FINISHED'}


