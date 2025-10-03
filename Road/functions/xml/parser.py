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

"""
Importer for Alignments in landxml files
"""
import FreeCAD

import math
from xml.etree import ElementTree as etree

from PySide import QtGui

from . import functions
from .. import support
from .key_maps import KeyMaps as maps

C = support.Constants

class Parser(object):
    """
    landxml parsing class
    """

    def __init__(self):

        self.errors = []

    def validate_units(self, _units):
        """
        Validate the alignment units, ensuring they match the document
        """

        if _units is None:
            print('Missing units')
            return ''

        xml_units = _units[0].attrib['linearUnit']

        #match?  return units
        system_units = support.get_doc_units()[1]
        if xml_units == system_units:
            return xml_units

        #otherwise, prompt user for further action
        msg_box = QtGui.QMessageBox()

        msg = "Document units do not match the units selected in the system"\
            + " preferences."

        query = "Change current units ({0}) to match document units ({1}?"\
            .format(system_units, xml_units)

        msg_box.setText(msg)
        msg_box.setInformativeText(query)
        msg_box.setStandardButtons(
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)

        msg_box.setDefaultButton(QtGui.QMessageBox.Yes)

        response = msg_box.exec()
        result = xml_units

        if response == QtGui.QMessageBox.Yes:

            _value = 7 #Civil Imperial

            if xml_units == 'meter':
                _value = 1 #MKS

            FreeCAD.ParamGet(
                'User parameter:BaseApp/Preferences/Units'
                ).SetInt('UserSchema',_value)

        else:
            self.errors.append(
                'Document units of ' + support.get_doc_units()[1]
                + ' expected, units of ' + xml_units + 'found')

            result = ''

        return result

    @staticmethod
    def get_name(alignment, obj_keys, obj_type):
        """
        Return valid alignment name if not defined, otherwise duplicate
        """

        obj_name = alignment.attrib.get('name')

        #alignment name is requiredand must be unique
        if obj_name is None:
            obj_name = 'Unkown ' + obj_type

        #test for key uniqueness
        counter = 0
        while obj_name in obj_keys:
            counter+=1
            obj_name += str(counter)

        return obj_name

    def _parse_data(self, align_name, tags, attrib, bearing_ref=0):
        """
        Build dictionary keyed to the internal attribute names from XML
        """

        result = {}

        #test to ensure all required tags are in the imported XML data
        missing_tags = set(
            tags[0]).difference(set(list(attrib.keys())))

        #report error and skip alignment if required tags are missing
        if missing_tags:

            self.errors.append(
                'The required XML tags were not found in alignment %s:\n%s'
                % (align_name, missing_tags)
            )

            return None

        #merge the required / optional tag lists and iterate them
        for _tag in tags[0] + tags[1]:
            attr_val = functions.convert_token(_tag, attrib.get(_tag))

            if attr_val is None:

                if _tag in tags[0]:
                    self.errors.append(
                        'Missing or invalid %s attribute in alignment %s'
                        % (_tag, align_name)
                    )

            #test for angles and convert to radians
            elif _tag in maps.XML_TAGS['angle']:
                attr_val = support.to_float(attrib.get(_tag))

                if attr_val:
                    attr_val = math.radians(attr_val)

                    if _tag in ['dir', 'dirStart', 'dirEnd']:

                        attr_val = support.validate_bearing(
                            attr_val, bearing_ref
                        )

            #test for lengths to convert to mm
            elif _tag in maps.XML_TAGS['length']:
                attr_val = support.to_float(attrib.get(_tag))

                if attr_val:
                    attr_val = attr_val * support.scale_factor()

            #convert rotation from string to number
            elif _tag == 'rot':

                attr_val = 0.0

                if attrib.get(_tag) == 'cw':
                    attr_val = 1.0

                elif attrib.get(_tag) == 'ccw':
                    attr_val = -1.0

            result[maps.XML_MAP[_tag]] = attr_val

        return result

    def _parse_meta_data(self, align_name, alignment):
        """
        Parse the alignment elements and strip out meta data for each
        alignment, returning it as a dictionary keyed
        to the alignment name
        """

        result = self._parse_data(
            align_name, maps.XML_ATTRIBS['Alignment'], alignment.attrib
            )

        _start = functions.get_child_as_vector(alignment, 'Start')

        if _start:
            _start.multiply(support.scale_factor())

        result['Start'] = [_start.x, _start.y, _start.z] if _start else None

        return result

    def _parse_station_data(self, align_name, alignment):
        """
        Parse the alignment data to get station equations and
        return a list of equation dictionaries
        """

        equations = functions.get_children(alignment, 'StaEquation')

        result = []

        for equation in equations:

            _dict = self._parse_data(
                align_name, maps.XML_ATTRIBS['StaEquation'], equation.attrib
            )

            _dict['Alignment'] = align_name

            result.append(_dict)

        return result

    def _parse_coord_geo_data(self, align_name, alignment, bearing_ref=0):
        """
        Parse the alignment coordinate geometry data to get curve
        information and return as a dictionary
        """

        coord_geo = functions.get_child(alignment, 'CoordGeom')

        if not coord_geo:
            print('Missing coordinate geometry for ', align_name)
            return None

        result = []

        for geo_node in coord_geo:

            node_tag = geo_node.tag.split('}')[1]

            if not node_tag in ['Curve', 'Spiral', 'Line']:
                continue

            points = []

            for _tag in ['Start', 'End', 'Center', 'PI']:

                _pt = functions.get_child_as_vector(geo_node, _tag)

                points.append(None)

                if _pt:
                    points[-1] = (_pt.multiply(support.scale_factor()))
                    continue

                if not (node_tag == 'Line' and _tag in ['Center', 'PI']):
                    continue
                    self.errors.append(
                        'Missing %s %s coordinate in alignment %s'
                        % (node_tag, _tag, align_name)
                    )

            hash_value = None

            if len(points) >= 2 and all(points):
                hash_value = hash(tuple(points[0]) + tuple(points[1]))

            coords = {
                'Hash': hash_value,
                'Type': node_tag,
                'Start': [points[0].x, points[0].y, points[0].z] if points[0] else None,
                'End': [points[1].x, points[1].y, points[1].z] if points[1] else None,
                'Center': [points[2].x, points[2].y, points[2].z] if points[2] else None,
                'PI': [points[3].x, points[3].y, points[3].z] if points[3] else None
                }

            result.append({
                **coords,
                **self._parse_data(
                    align_name, maps.XML_ATTRIBS[node_tag], geo_node.attrib, bearing_ref
                )
            })

        return result

    def _update_alignment(self, geometry):
        _truth = [True]*8

        for curve in geometry:
            bearing_in = curve.get('BearingIn') if curve.get('BearingIn') else 0.0
            start = curve.get('Start') if curve.get('Start') else 0.0
            end = curve.get('End') if curve.get('End') else 0.0
            pi = curve.get('PI') if curve.get('PI') else 0.0

            #test bearing if a bearing is found
            if bearing_in: self.test_bearing(bearing_in, start, end, pi, _truth)

        bearing_ref = [_i for _i, _v in enumerate(_truth) if _v]

        if not bearing_ref:
            self.errors.append('Inconsistent angle directions - unable to determine bearing reference')
            return

        return bearing_ref[0]

    def test_bearing(self, bearing, start_pt, end_pt, pi, truth):
        """
        Test the bearing direction to verify it's definition
        """

        #if the start point isn't a vector, default to true for N-CW
        if not isinstance(start_pt, FreeCAD.Vector):
            return [True] + [False]*7

        #calculate the vector from the PI where possible, otherwise
        #use the end point.  If both fail, default to N-CW
        if not isinstance(pi, float):
            _vec = pi.sub(start_pt)

        elif isinstance(end_pt, FreeCAD.Vector):
            _vec = end_pt.sub(start_pt)

        else:
            return [True] + [False]*7

        #calculate the bearings of the vector against each axis
        #direction, both clockwise and counter-clockwise

        #CW CALCS
        _b = [
            support.get_bearing(_vec),
            support.get_bearing(_vec, FreeCAD.Vector(1.0, 0.0, 0.0)),
            support.get_bearing(_vec, FreeCAD.Vector(0.0, -1.0, 0.0)),
            support.get_bearing(_vec, FreeCAD.Vector(-1.0, 0.0, 0.0))
        ]

        #CCW CALCS
        _b += [C.TWO_PI - _v for _v in _b]

        #compare each calculation against the original bearing, storing
        #whether or not it's within tolerance for the axis / direction
        _b = [support.within_tolerance(_v, bearing, 0.01) for _v in _b]

        #Update truth table, invalidating bearings that don't compare
        for _i, _v in enumerate(_b):
            truth[_i] = truth[_i] and _v

    def parse_points(self, all_points):
        points = {}
        for point in all_points:
            if point.text:
                name = point.get("name")
                text = point.text.strip().split(' ')
                northing = float(text[0])
                easting = float(text[1])
                elevation = float(text[2]) if len(text) > 2 else 0.0
                description = point.get("code") if point.get("code") else ""

                points[name] = {"Northing": northing, "Easting": easting, "Elevation": elevation, "Description": description}

        return points

    def parse_surface(self, surface):
        definition = functions.get_child(surface, 'Definition')
        pts = functions.get_child(definition, 'Pnts')
        fcs = functions.get_child(definition, 'Faces')

        points = {}
        for p in pts:
            id = int(p.get("id"))
            pt = p.text.strip().split(' ')
            pt = [float(v) for v in pt]
            vec = FreeCAD.Vector(pt[1], pt[0], pt[2])
            points[id] = vec.multiply(1000)

        faces = []
        for f in fcs:
            fc = f.text.strip().split(' ')
            fc = [int(v) for v in fc]
            faces.append(fc)

        return points, faces

    def load_file(self, filepath):
        """
        Import a landxml and build the Python dictionary fronm the
        appropriate elements
        """

        #get element tree and key nodes for parsing
        doc = etree.parse(filepath)
        root = doc.getroot()

        project = functions.get_child(root, 'Project')
        units = functions.get_child(root, 'Units')
        cg_points = functions.get_children(root, 'CgPoints')
        surfaces = functions.get_child(root, 'Surfaces')
        alignments = functions.get_child(root, 'Alignments')

        #aport if key nodes are missing
        if not units:
            self.errors.append('Missing project units')
            return None

        unit_name = self.validate_units(units)

        if not unit_name:
            self.errors.append('Invalid project units')
            return None

        #default project name if missing
        project_name = 'Unknown Project'

        if not project is None:
            project_name = project.attrib['name']

        #build final dictionary and return
        result = {}
        result['Project'] = {}
        result['Project'][maps.XML_MAP['name']] = project_name
        result['CgPoints'] = {"All_Points": {}, "Groups": {}}
        result['Surfaces'] = {}
        result['Alignments'] = {}

        if cg_points:
            result['CgPoints']["Groups"] = {}
            for point_group in cg_points:
                name = point_group.get('name')
                if not name:
                    result['CgPoints']["All_Points"] =  self.parse_points(point_group)
                else:
                    result['CgPoints']["Groups"][name] =  [point.get("pntRef") for point in point_group]

        if surfaces:
            for surface in surfaces:
                name = self.get_name(
                    surface, result.keys(), "Surface")

                surf_dict = {}
                result['Surfaces'][name] = surf_dict
                surf_dict['Points'], surf_dict['Faces'] = self.parse_surface(surface)

        if alignments:
            for alignment in alignments:
                name = self.get_name(alignment, result.keys(), "Alignment")

                align_dict = {}
                result['Alignments'][name] = align_dict
                align_dict['meta'] = self._parse_meta_data(name, alignment)
                align_dict['station'] = self._parse_station_data(name, alignment)
                geometry = self._parse_coord_geo_data(name, alignment)
                bearing_referance = self._update_alignment(geometry)
                align_dict['geometry'] = self._parse_coord_geo_data(name, alignment, bearing_referance)

        return result
