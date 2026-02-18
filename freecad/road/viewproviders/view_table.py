# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Table objects."""

import FreeCAD
from pivy import coin


class ViewProviderTable:
    """
    This class is about Table Object view features.
    """

    def __init__(self, vobj):
        '''
        Set view properties.
        '''
        vobj.Proxy = self

    def attach(self, vobj):
        '''
        Create Object visuals in 3D view.
        '''
        # GeoCoord Node.
        self.geo_coords = coin.SoGeoCoordinate()
        self.table_borders = coin.SoLineSet()
        self.table_columns = coin.SoSeparator()

        # Highlight for selection.
        highlight = coin.SoType.fromName('SoFCSelection').createInstance()
        highlight.style = 'EMISSIVE_DIFFUSE'
        highlight.addChild(self.table_borders)
        highlight.addChild(self.table_columns)

        # Point group root.
        table_root = coin.SoSeparator()
        table_root.addChild(highlight)
        vobj.addDisplayMode(table_root,"Table")

    def onChanged(self, vobj, prop):
        '''
        Update Object visuals when a view property changed.
        '''
        return

    def updateData(self, obj, prop):
        '''
        Update Object visuals when a data property changed.
        '''
        tables = obj.getParentGroup()
        region = tables.getParentGroup()
        volume_areas = obj.getPropertyByName("VolumeAreas")

        if volume_areas:
            pos = obj.getPropertyByName("Position")
            if prop == "VolumeAreas" or prop == "TableTitle":
                self.table_columns.removeAllChildren()

                column_titles = ["KM", "Area", "Volume", "Cumulative Volume"]

                table_title = obj.getPropertyByName("TableTitle")
                offset = 50000
                font = coin.SoFont()
                font.size = 10000

                # Table title
                title = coin.SoSeparator()
                location = coin.SoTranslation()
                text = coin.SoAsciiText()

                location.translation = pos + FreeCAD.Vector(0, font.size.getValue(), 0)
                text.string.setValues([table_title])

                title.addChild(font)
                title.addChild(location)
                title.addChild(text)

                # Stations column
                sta_list = [str(round(i,2)) for i in region.StationList]
                sta_list.insert(0,column_titles[0])

                sta_column = coin.SoSeparator()
                location = coin.SoTranslation()
                text = coin.SoAsciiText()

                location.translation = pos
                text.string.setValues(sta_list)

                sta_column.addChild(font)
                sta_column.addChild(location)
                sta_column.addChild(text)

                # Area column
                face_areas = []
                for sub in obj.VolumeAreas.Shape.SubShapes:
                    face_areas.append(sub.Area)

                area_list = [str(round(i/1000000,3)) for i in face_areas]
                area_list.insert(0,column_titles[1])

                area_column = coin.SoSeparator()
                location = coin.SoTranslation()
                text = coin.SoAsciiText()

                location.translation = pos.add(FreeCAD.Vector(offset, 0, 0))
                text.string.setValues(area_list)

                area_column.addChild(font)
                area_column.addChild(location)
                area_column.addChild(text)

                # Volume column
                volumes = []
                volumes.append(0)
                for count in range(1,len(face_areas)):
                    prev_area = float(face_areas[count-1])
                    next_area = float(face_areas[count])

                    prev_km = float(sta_list[count])
                    next_km = float(sta_list[count+1])

                    volume = ((next_area + prev_area)/2)*(next_km-prev_km)
                    volumes.append(volume)

                volume_list = [str(round(i/1000000,3)) for i in volumes]
                volume_list.insert(0,column_titles[2])

                volume_column = coin.SoSeparator()
                location = coin.SoTranslation()
                text = coin.SoAsciiText()

                location.translation = pos.add(FreeCAD.Vector(offset*2, 0, 0))
                text.string.setValues(volume_list)

                volume_column.addChild(font)
                volume_column.addChild(location)
                volume_column.addChild(text)

                # Cumulative volume column
                cum_vols = []
                cum_vols.append(0)

                for count in range(1,len(volumes)):
                    prev_cumvol = float(cum_vols[-1])
                    next_vol = float(volumes[count])

                    cum_vol = prev_cumvol + next_vol
                    cum_vols.append(cum_vol)

                cumvol_list = [str(round(i/1000000,3)) for i in cum_vols]
                cumvol_list.insert(0,column_titles[3])

                cumvol_column = coin.SoSeparator()
                location = coin.SoTranslation()
                text = coin.SoAsciiText()

                location.translation = pos.add(FreeCAD.Vector(offset*3, 0, 0))
                text.string.setValues(cumvol_list)

                cumvol_column.addChild(font)
                cumvol_column.addChild(location)
                cumvol_column.addChild(text)

                self.table_columns.addChild(title)
                self.table_columns.addChild(sta_column)
                self.table_columns.addChild(area_column)
                self.table_columns.addChild(volume_column)
                self.table_columns.addChild(cumvol_column)
