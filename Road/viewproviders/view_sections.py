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

"""Provides the viewprovider code for Section objects."""
import FreeCAD

from pivy import coin
import math

from ..utils.get_group import georigin


class ViewProviderSections:
    """
    This class is about Point Group Object view features.
    """

    def attach(self, vobj):
        '''
        Create Object visuals in 3D view.
        '''
        self.Object = vobj.Object

        # Lines root.
        self.line_coords = coin.SoGeoCoordinate()
        self.lines = coin.SoLineSet()
        self.gl_labels = coin.SoSeparator()

        # Line style.
        line_color = coin.SoBaseColor()
        line_color.rgb = (0.0, 1.0, 1.0)
        line_style = coin.SoDrawStyle()
        line_style.style = coin.SoDrawStyle.LINES
        line_style.lineWidth = 2

        # Highlight for selection.
        highlight = coin.SoType.fromName('SoFCSelection').createInstance()
        highlight.style = 'EMISSIVE_DIFFUSE'
        highlight.addChild(line_style)
        highlight.addChild(self.line_coords)
        highlight.addChild(self.lines)

        # Surface root.
        guidelines_root = coin.SoSeparator()
        guidelines_root.addChild(self.gl_labels)
        guidelines_root.addChild(line_color)
        guidelines_root.addChild(highlight)
        vobj.addDisplayMode(guidelines_root,"Lines")

    def updateData(self, obj, prop):
        '''
        Update Object visuals when a data property changed.
        '''
        if prop == "Position" or prop == "Group":
            self.gl_labels.removeAllChildren()
            if not obj.Group: return

            position = obj.getPropertyByName("Position")
            h = obj.Height.Value
            w = obj.Width.Value
            ver = obj.Vertical.Value
            hor = obj.Horizontal.Value
            geometry = [h, w]
            gaps = [ver, hor]

            # Set System.
            origin = georigin()
            geo_system = ["UTM", origin.UtmZone, "FLAT"]
            self.line_coords.geoSystem.setValues(geo_system)

            counter = 0
            pos = position
            region = obj.getParentGroup()

            points = []
            line_vert = []
            sta_list = region.StationList
            multi_views_nor = math.ceil(len(region.Shape.Wires)**0.5)

            for sta in sta_list:
                font = coin.SoFont()
                font.size = 5000
                gl_label = coin.SoSeparator()
                location = coin.SoTranslation()
                text = coin.SoAsciiText()

                header = FreeCAD.Vector(w/2, h+1000, 0)
                location.translation = position.add(header)
                text.string.setValues([str(round(sta, 3))])
                gl_label.addChild(font)
                gl_label.addChild(location)
                gl_label.addChild(text)
                self.gl_labels.addChild(gl_label)

                org = position.add(origin.Origin)
                up_left = org.add(FreeCAD.Vector(0, h, 0))
                up_right = org.add(FreeCAD.Vector(w, h, 0))
                down_right = org.add(FreeCAD.Vector(w, 0, 0))

                points.extend([org, up_left, up_right, down_right, org])
                line_vert.append(5)

                if counter == multi_views_nor:
                    shifting = position.x - pos.x + gaps[1]
                    reposition = FreeCAD.Vector(geometry[1] + shifting, 0, 0)
                    position = pos.add(reposition)
                    counter = 0

                else:
                    reposition = FreeCAD.Vector(0, -(geometry[0] + gaps[0]), 0)
                    position = position.add(reposition)
                    counter += 1

            self.line_coords.point.values = points
            self.lines.numVertices.values = line_vert

    def getDisplayModes(self, vobj):
        '''
        Return a list of display modes.
        '''
        modes=[]
        modes.append("Lines")

        return modes

    def getDefaultDisplayMode(self):
        '''
        Return the name of the default display mode.
        '''
        return "Lines"

    def setDisplayMode(self,mode):
        '''
        Map the display mode defined in attach with 
        those defined in getDisplayModes.
        '''
        return mode

    def dumps(self):
        """Called during document saving"""
        return None

    def loads(self, state):
        """Called during document restore."""
        return None
