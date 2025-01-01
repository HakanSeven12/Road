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

"""Provides the viewprovider code for Volume objects."""

from pivy import coin
import random

from variables import icons_path
from ..utils.get_group import georigin


class ViewProviderVolume:
    """
    This class is about Volume Object view features.
    """

    def __init__(self, vobj):
        '''
        Set view properties.
        '''
        (r, g, b) = (random.random(), random.random(), random.random())

        vobj.addProperty(
            "App::PropertyColor", "AreaColor", "Base",
            "Color of the volume areas").AreaColor = (r, g, b)

        vobj.Proxy = self

    def attach(self, vobj):
        '''
        Create Object visuals in 3D view.
        '''
        # Face root.
        self.face_coords = coin.SoGeoCoordinate()
        self.faces = coin.SoIndexedFaceSet()
        self.area_color = coin.SoBaseColor()

        # Highlight for selection.
        highlight = coin.SoType.fromName('SoFCSelection').createInstance()
        highlight.style = 'EMISSIVE_DIFFUSE'
        highlight.addChild(self.face_coords)
        highlight.addChild(self.faces)

        # Volume root.
        volume_root = coin.SoSeparator()
        volume_root.addChild(self.area_color)
        volume_root.addChild(highlight)
        vobj.addDisplayMode(volume_root,"Volume")

        # Take features from properties.
        self.onChanged(vobj,"AreaColor")

    def onChanged(self, vobj, prop):
        '''
        Update Object visuals when a view property changed.
        '''
        if prop == "AreaColor":
            color = vobj.getPropertyByName("AreaColor")
            self.area_color.rgb = (color[0],color[1],color[2])

    def updateData(self, obj, prop):
        '''
        Update Object visuals when a data property changed.
        '''
        if prop == "Shape":
            shape = obj.getPropertyByName("Shape")

            # Set System.
            origin = georigin()
            geo_system = ["UTM", origin.UtmZone, "FLAT"]
            self.face_coords.geoSystem.setValues(geo_system)

            idx = 0
            points = []
            face_vert = []
            for face in shape.Faces:
                tri = face.tessellate(1)
                for v in tri[0]:
                    points.append(v.add(origin.Origin))
                for f in tri[1]:
                    face_vert.extend([f[0]+idx,f[1]+idx,f[2]+idx,-1])
                idx += len(tri[0])

            #Set contour system.
            self.face_coords.point.values = points
            self.faces.coordIndex.values = face_vert

    def getDisplayModes(self,vobj):
        '''
        Return a list of display modes.
        '''
        modes=[]
        modes.append("Volume")

        return modes

    def getDefaultDisplayMode(self):
        '''
        Return the name of the default display mode.
        '''
        return "Volume"

    def setDisplayMode(self,mode):
        '''
        Map the display mode defined in attach with 
        those defined in getDisplayModes.
        '''
        return mode

    def getIcon(self):
        '''
        Return object treeview icon.
        '''
        return icons_path + '/volume.svg'

    def dumps(self):
        """Called during document saving"""
        return None

    def loads(self, state):
        """Called during document restore."""
        return None
