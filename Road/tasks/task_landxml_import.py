# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2025 Hakan Seven <hakanseven12@gmail.com>               *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

"""Provides the task panel code for the Cluster Importer tool."""

import FreeCAD, FreeCADGui

import Part, Mesh

from .task_panel import TaskPanel
from ..make import make_terrain, make_alignment

import xml.etree.ElementTree as ET
from PySide2.QtWidgets import (QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTreeWidget, 
                             QTreeWidgetItem, QFileDialog, QMessageBox)
from PySide2.QtCore import Qt
import FreeCAD

class TaskLandXMLImport(TaskPanel):
    def __init__(self):
        super().__init__()
        self.form = QWidget()
        self.xml_data = None
        self.selected_file = None
        self.initUI()
        
    def initUI(self):
        main_layout = QVBoxLayout(self.form)
        
        # Üst kısım - Dosya seçimi
        top_layout = QHBoxLayout()
        
        # Sol taraf - Dosya adı etiketi
        self.file_label = QLabel('Dosya seçilmedi')
        top_layout.addWidget(self.file_label)
        top_layout.addStretch()
        
        # Sağ taraf - Browse butonu
        self.browse_btn = QPushButton('Browse')
        self.browse_btn.clicked.connect(self.browse_file)
        top_layout.addWidget(self.browse_btn)
        
        main_layout.addLayout(top_layout)
        
        # Ortadaki TreeView
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Öğe', 'Tip', 'Detay'])
        self.tree.setSelectionMode(QTreeWidget.MultiSelection)
        main_layout.addWidget(self.tree)
        
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.form, 
            'LandXML Dosyası Seç', 
            '', 
            'LandXML Files (*.xml);;All Files (*.*)'
        )
        
        if file_path:
            self.selected_file = file_path
            # Sadece dosya adını göster
            file_name = file_path.split('/')[-1]
            self.file_label.setText(file_name)
            self.load_landxml(file_path)
            
    def load_landxml(self, file_path):
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            self.xml_data = root
            
            # TreeWidget'ı temizle
            self.tree.clear()
            
            # Root item - LandXML
            root_item = QTreeWidgetItem(self.tree)
            root_item.setText(0, 'LandXML')
            root_item.setText(1, 'Root')
            root_item.setExpanded(True)
            
            # Units
            units = root.find('.//{*}Units')
            if units is not None:
                units_item = QTreeWidgetItem(root_item)
                units_item.setText(0, 'Units')
                units_item.setText(1, 'Units')
                
                for attr, value in units.attrib.items():
                    attr_item = QTreeWidgetItem(units_item)
                    attr_item.setText(0, attr)
                    attr_item.setText(2, value)
                    attr_item.setFlags(attr_item.flags() & ~Qt.ItemIsSelectable)
                
            # Project
            project = root.find('.//{*}Project')
            if project is not None:
                proj_item = QTreeWidgetItem(root_item)
                proj_item.setText(0, f"Project: {project.get('name', 'Unnamed')}")
                proj_item.setText(1, 'Project')
                proj_item.setFlags(proj_item.flags() & ~Qt.ItemIsSelectable)
                
            # Application
            app = root.find('.//{*}Application')
            if app is not None:
                app_item = QTreeWidgetItem(root_item)
                app_name = app.get('name', 'Unknown')
                app_desc = app.get('desc', '')
                app_item.setText(0, f"Application: {app_name}")
                app_item.setText(1, 'Application')
                app_item.setText(2, app_desc)
                app_item.setFlags(app_item.flags() & ~Qt.ItemIsSelectable)
            
            # Surfaces (Yüzeyler)
            surfaces_item = QTreeWidgetItem(root_item)
            surfaces_item.setText(0, 'Yüzeyler')
            surfaces_item.setText(1, 'Category')
            surfaces_item.setExpanded(True)
            surfaces_item.setFlags(surfaces_item.flags() & ~Qt.ItemIsSelectable)
            
            for surface in root.findall('.//{*}Surface'):
                surf_item = QTreeWidgetItem(surfaces_item)
                surf_name = surface.get('name', 'Unnamed Surface')
                surf_item.setText(0, surf_name)
                surf_item.setText(1, 'Surface')
                surf_item.setText(2, f"Surface - {surf_name}")
                surf_item.setData(0, Qt.UserRole, ('surface', surface))
                
            # Alignments
            alignments_item = QTreeWidgetItem(root_item)
            alignments_item.setText(0, 'Alignments')
            alignments_item.setText(1, 'Category')
            alignments_item.setExpanded(True)
            alignments_item.setFlags(alignments_item.flags() & ~Qt.ItemIsSelectable)
            
            for alignment in root.findall('.//{*}Alignment'):
                align_item = QTreeWidgetItem(alignments_item)
                align_name = alignment.get('name', 'Unnamed Alignment')
                align_item.setText(0, align_name)
                align_item.setText(1, 'Alignment')
                align_item.setText(2, f"Alignment - {align_name}")
                align_item.setData(0, Qt.UserRole, ('alignment', alignment))
            
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Dosya yüklenirken hata oluştu:\n{str(e)}')
            
    def process_selected(self):
        print("Processing selected items...")
        selected_items = self.tree.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self.form, 'Uyarı', 'Lütfen en az bir öğe seçin!')
            return
            
        surfaces_to_process = []
        alignments_to_process = []
        
        for item in selected_items:
            data = item.data(0, Qt.UserRole)
            if data:
                item_type, element = data
                if item_type == 'surface':
                    surfaces_to_process.append(element)
                elif item_type == 'alignment':
                    alignments_to_process.append(element)
        
        # Yüzeyleri işle
        for surface in surfaces_to_process:
            self.convert_surface_to_mesh(surface)
            
        # Alignment'ları işle
        for alignment in alignments_to_process:
            alignment_data = self.parse_alignment(alignment)
            if alignment_data:
                # get_geometry fonksiyonunu çağır
                points, wire = self.get_geometry(alignment_data)
                if wire:
                    Part.show(wire)
                    
        QMessageBox.information(self.form, 'Başarılı', 
                              f'{len(surfaces_to_process)} yüzey ve {len(alignments_to_process)} alignment FreeCAD\'e aktarıldı!')
    
    def convert_surface_to_mesh(self, surface):
        """Yüzeyi FreeCAD Mesh objesine dönüştür"""
        try:
            mesh_obj = Mesh.Mesh()
            
            # TIN yüzeyler için faces'leri al
            faces = surface.findall('.//{*}Faces/{*}F')
            pnts = surface.findall('.//{*}Pnts/{*}P')
            
            # Nokta dictionary'si oluştur
            points_dict = {}
            for pnt in pnts:
                pid = pnt.get('id')
                coords = pnt.text.strip().split()
                if len(coords) >= 3:
                    x, y, z = float(coords[1]), float(coords[0]), float(coords[2])
                    points_dict[pid] = FreeCAD.Vector(x * 1000, y * 1000, z * 1000)
            
            # Yüzleri ekle
            for face in faces:
                vertices_str = face.text.strip().split()
                if len(vertices_str) >= 3:
                    try:
                        v1 = points_dict[vertices_str[0]]
                        v2 = points_dict[vertices_str[1]]
                        v3 = points_dict[vertices_str[2]]
                        mesh_obj.addFacet(v1, v2, v3)
                    except KeyError:
                        continue
                        
            # Mesh'i göster
            if mesh_obj.CountFacets > 0:
                terrain = make_terrain.create(label = surface.get('name', 'Surface'))
                terrain.Mesh = mesh_obj
                FreeCAD.ActiveDocument.recompute()
                
        except Exception as e:
            print(f"Yüzey dönüştürme hatası: {e}")
    
    def parse_alignment(self, alignment):
        """Alignment'ı parse et ve alignment_data formatına dönüştür"""
        alignment_data = {}
        
        try:
            # CoordGeom içindeki PI noktalarını bul
            coord_geom = alignment.find('.//{*}CoordGeom')
            if coord_geom is None:
                return None
                
            pi_index = 0
            for element in coord_geom:
                tag = element.tag.split('}')[-1]
                
                if tag == 'Line':
                    # Line elemanından başlangıç ve bitiş noktalarını al
                    start = element.find('.//{*}Start')
                    end = element.find('.//{*}End')
                    
                    if start is not None:
                        coords = start.text.strip().split()
                        if len(coords) >= 2:
                            alignment_data[f'PI_{pi_index}'] = {
                                'X': coords[1],  # Northing
                                'Y': coords[0],  # Easting
                                'Curve Type': 'None',
                                'Spiral Length In': '0',
                                'Spiral Length Out': '0',
                                'Radius': '0'
                            }
                            pi_index += 1
                            
                elif tag == 'Curve':
                    # Curve elemanını işle
                    radius = element.get('radius', '0')
                    alignment_data[f'PI_{pi_index}'] = {
                        'X': element.get('centerN', '0'),
                        'Y': element.get('centerE', '0'),
                        'Curve Type': 'Curve',
                        'Spiral Length In': '0',
                        'Spiral Length Out': '0',
                        'Radius': radius
                    }
                    pi_index += 1
                    
                elif tag == 'Spiral':
                    # Spiral elemanını işle
                    length = element.get('length', '0')
                    radius_start = element.get('radiusStart', 'INF')
                    radius_end = element.get('radiusEnd', 'INF')
                    
                    # Spiral-Curve-Spiral kombinasyonunu kontrol et
                    alignment_data[f'PI_{pi_index}'] = {
                        'X': '0',  # Koordinatlar spiral'dan hesaplanmalı
                        'Y': '0',
                        'Curve Type': 'Spiral-Curve-Spiral',
                        'Spiral Length In': length,
                        'Spiral Length Out': length,
                        'Radius': radius_end if radius_end != 'INF' else radius_start
                    }
                    pi_index += 1
                    
        except Exception as e:
            print(f"Alignment parse hatası: {e}")
            return None
            
            alignment = make_alignment.create(label = alignment.get('name', 'Alignment'))
            terrain.Mesh = mesh_obj
    
    def accept(self):
        """Accept and process the selected files for import."""
        self.process_selected()

        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()

    def needsFullSpace(self):
        return True
