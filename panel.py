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


def get_key_driver(name):
    anim = bpy.context.object.data.shape_keys.animation_data
    if anim and anim.drivers:
        for fcu in anim.drivers:
            if fcu.data_path == f'key_blocks["{name}"].value':
                return fcu.driver
    
    
class DATA_PT_shape_keys_tree(bpy.types.Panel):
    bl_label = "Shape Keys Tree"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        valid_types = {'MESH', 'LATTICE', 'CURVE', 'SURFACE'}
        
        return obj and obj.type in valid_types
    
    
    def draw(self, context):
        obj = context.object
        enable_edit = obj.mode != 'EDIT'
        enable_edit_value = False
        
        if obj.show_only_shape_key is False:
            use_edit_mode = obj.type == 'MESH' and obj.use_shape_key_edit_mode
            
            if enable_edit or use_edit_mode:
                enable_edit_value = True
        
        row = self.layout.row()
        row.alignment='LEFT'
        
        row.label(text='New', )
        op(row, 'skt.new_folder', text="Folder")
        op(row, 'skt.shape_key_add', text="Shape", op_type='DEFAULT')
        row = row.row()
        row.enabled = bool(list(main.items.filter(is_folder=False)))
        op(row, 'skt.shape_key_add', text="Shape From Mix", op_type='FROM_MIX')
        
        row = self.layout.row()
        
        row.label(text='Select', ) #icon='RESTRICT_SELECT_OFF')
        op(row, 'skt.select_all', text="All")
        op(row, 'skt.select_none', text="None")
        op(row, 'skt.select_inverse', icon='ARROW_LEFTRIGHT', text='', )
        
        subrow = row.row()
        subrow.alignment='RIGHT'
        
        if main.items.selected:
            subrow.menu('MESH_MT_skt_actions', text=f'{len(main.items.selected)} selected')
        else:
            subrow.label(text=f'0 selected')
        
        row = self.layout.row(align=True)
        row.scale_y = 0.8
        
        op(row, 'skt.expand_all', text="Expand all")
        op(row, 'skt.collapse_all', text="Collapse all")
        
        
        row = self.layout.row()
        row.template_list(
            listtype_name='MESH_UL_shape_keys_tree',
            dataptr=obj.skt,
            propname='items',
            active_dataptr=obj.skt,
            active_propname='active_item',
            list_id='SHAPE_KEYS_PLUS',
            rows=8)
        
        
        split = self.layout.split(factor=0.4, align=False)
        
        row = split.row()
        row.enabled = enable_edit
        
        if not context.object.data.shape_keys:
            return
        
        row.prop(context.object.data.shape_keys, 'use_relative')
        
        row = split.row()
        row.alignment = 'RIGHT'
        
        sub = row.row(align=True)
        sub.label()
        
        sub = sub.row(align=True)
        sub.active = enable_edit_value
        
        sub.prop(obj, 'show_only_shape_key', text="")
        sub.prop(obj, 'use_shape_key_edit_mode', text="")
        
        sub = row.row()
        
        if context.object.data.shape_keys.use_relative:
            op(sub, 'object.shape_key_clear', text="0 all")
        else:
            sub.operator('object.shape_key_retime', icon='RECOVER_LAST', text="")
        
        if not main.items.active or main.items.active.is_folder:
            return
        
        if context.object.data.shape_keys.use_relative:
            row = self.layout.row()
            row.active = enable_edit_value
            
            row.prop(main.items.active.shapekey, 'value')
            
            split = self.layout.split()
            
            col = split.column(align=True)
            col.active = enable_edit_value
            
            col.label(text="Range:")
            col.prop(main.items.active.shapekey, 'slider_min', text="Min")
            col.prop(main.items.active.shapekey, 'slider_max', text="Max")
            
            col = split.column(align=True)
            col.active = enable_edit_value
            
            col.label(text="Blend:")
            
            col.prop_search(
                data=main.items.active.shapekey,
                property='vertex_group',
                search_data=obj,
                search_property='vertex_groups',
                text="")
            
            col.prop_search(
                data=main.items.active.shapekey,
                property='relative_key',
                search_data=context.object.data.shape_keys,
                search_property='key_blocks',
                text="")
        else:
            self.layout.prop(active_key, 'interpolation')
            
            row = self.layout.column()
            row.active = enable_edit_value
            row.prop(context.object.data.shape_keys, 'eval_time')
        
        driver = get_key_driver(main.items.active.path)
        
        if not driver:
            return
        
        self.layout.separator()
        
        row = self.layout.row()
        row.prop(obj.skt, 'driver_visible')
        
        if not obj.skt.driver_visible:
            return
        
        row = self.layout.row()
        row.label(text="Type:")
        
        row = row.row()
        row.prop(driver, 'type', text="")
        row.scale_x = 2
        
        if driver.type == 'SCRIPTED':
            row = row.row()
            row.prop(driver, 'use_self')
        
        if driver.type == 'SCRIPTED':
            row = self.layout.row()
            row.label(text="Expression:")
            
            row = row.row()
            row.prop(driver, 'expression', text="")
            row.scale_x = 4
        
        for i, v in enumerate(driver.variables):
            area_parent = self.layout.row()
            area = area_parent.column(align=True)
            box = area.box()
            row = box.row()
            row.prop(driver.variables[i], 'name', text="")
            
            row = row.row()
            row.prop(driver.variables[i], 'type', text="")
            row.scale_x = 2
            
            if driver.variables[i].type == 'SINGLE_PROP':
                row = box.row(align=True)
                row.prop(driver.variables[i].targets[0], 'id_type', icon_only=True)
                
                row.prop(driver.variables[i].targets[0], 'id', text="")
                
                if driver.variables[i].targets[0].id:
                    row = box.row(align=True)
                    row.prop(
                        data=driver.variables[i].targets[0],
                        property='data_path',
                        text="",
                        icon='RNA')
            elif driver.variables[i].type == 'TRANSFORMS':
                target = driver.variables[i].targets[0]
                
                col = box.column(align=True)
                col.prop(target, 'id', text="Object", expand=True)
                
                if target and target.id and target.id.type == 'ARMATURE':
                    col.prop_search(
                        data=target,
                        property='bone_target',
                        search_data=target.id.data,
                        search_property='bones',
                        text="Bone",
                        icon='BONE_DATA')
                
                col = box.row().column(align=True)
                col.prop(driver.variables[i].targets[0], 'transform_type', text="Type")
                col.prop(driver.variables[i].targets[0], 'transform_space', text="Space")
                
            elif driver.variables[i].type == 'ROTATION_DIFF':
                for i, target in enumerate(driver.variables[i].targets):
                    col = box.column(align=True)
                    
                    col.prop(target, 'id', text="Object " + str(i + 1), expand=True)
                    
                    if target.id and target.id.type == 'ARMATURE':
                        col.prop_search(
                            data=target,
                            property='bone_target',
                            search_data=target.id.data,
                            search_property='bones',
                            text="Bone",
                            icon='BONE_DATA')
                    
                    col = box.column(align=True)
                    col.prop(target, 'transform_type', text="Type")
                    col.prop(target, 'transform_space', text="Space")
                    
            elif driver.variables[i].type == 'LOC_DIFF':
                for i, target in enumerate(driver.variables[i].targets):
                    col = box.column().column(align=True)
                    col.prop(target, 'id', text="Object " + str(i + 1), expand=True)
                    
                    if target.id and target.id.type == 'ARMATURE':
                        col.prop_search(
                            data=target,
                            property='bone_target',
                            search_data=target.id.data,
                            search_property='bones',
                            text="Bone",
                            icon='BONE_DATA')
                    
                    col.prop(target, 'transform_space', text="Space")

