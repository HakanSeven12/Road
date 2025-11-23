# SPDX-License-Identifier: LGPL-2.1-or-later

"""
LandXML Parser Configuration
Contains all mapping configurations for parsing LandXML elements.
"""

# LandXML namespaces
LANDXML_NAMESPACES = {
    'landxml': 'http://www.landxml.org/schema/LandXML-1.2',
    '': 'http://www.landxml.org/schema/LandXML-1.2'
}

import math

# Units configuration
UNITS_CONFIG = {
    'Metric': {
        'attr_map': {
            'areaUnit': ('areaUnit', str),
            'linearUnit': ('linearUnit', str),
            'volumeUnit': ('volumeUnit', str),
            'temperatureUnit': ('temperatureUnit', str),
            'pressureUnit': ('pressureUnit', str),
            'diameterUnit': ('diameterUnit', str),
            'widthUnit': ('widthUnit', str),
            'heightUnit': ('heightUnit', str),
            'elevationUnit': ('elevationUnit', str),
            'angularUnit': ('angularUnit', str),
            'directionUnit': ('directionUnit', str),
            'latLongAngularUnit': ('latLongAngularUnit', str)
        }
    },
    'Imperial': {
        'attr_map': {
            'areaUnit': ('areaUnit', str),
            'linearUnit': ('linearUnit', str),
            'volumeUnit': ('volumeUnit', str),
            'temperatureUnit': ('temperatureUnit', str),
            'pressureUnit': ('pressureUnit', str),
            'diameterUnit': ('diameterUnit', str),
            'widthUnit': ('widthUnit', str),
            'heightUnit': ('heightUnit', str),
            'elevationUnit': ('elevationUnit', str),
            'angularUnit': ('angularUnit', str),
            'directionUnit': ('directionUnit', str),
            'latLongAngularUnit': ('latLongAngularUnit', str)
        }
    }
}

# Supported angular units and their conversion to radians
ANGULAR_UNITS = {
    'radians': 1.0,
    'decimal degrees': math.pi / 180,   # π/180
    'degrees': math.pi / 180,           # π/180
    'decimal dd.mmss': math.pi / 180,   # Convert to decimal degrees first
    'dd.mmss': math.pi / 180,           # Convert to decimal degrees first
    'grads': math.pi / 200,             # π/200
    'mils': math.pi / 3200              # π/3200
}

# Converter function types
CONVERTER_TYPES = {
    'float': 'float',
    'int': 'int',
    'str': str,
    'rotation': 'rotation',  # Converts 'cw'/'ccw' to 1/-1
    'radius': 'radius',      # Converts 'INF' to float('inf')
    'angle': 'angle'         # Converts angle to radians based on unit system
}

# Geometry element configurations
GEOMETRY_CONFIG = {
    'Line': {
        'point_tags': ['Start', 'End'],
        'attr_map': {
            'name': ('name', str),
            'desc': ('desc', str),
            'length': ('length', 'float'),
            'dir': ('dir', 'angle'),
            'staStart': ('staStart', 'float')
        }
    },
    'Curve': {
        'point_tags': ['Start', 'Center', 'End', 'PI'],
        'attr_map': {
            'name': ('name', str),
            'desc': ('desc', str),
            'length': ('length', 'float'),
            'radius': ('radius', 'float'),
            'chord': ('chord', 'float'),
            'crvType': ('crvType', str),
            'delta': ('delta', 'angle'),
            'dirStart': ('dirStart', 'angle'),
            'dirEnd': ('dirEnd', 'angle'),
            'tangent': ('tangent', 'float'),
            'midOrd': ('midOrd', 'float'),
            'external': ('external', 'float'),
            'staStart': ('staStart', 'float'),
            'rot': ('rot', str)
        }
    },
    'Spiral': {
        'point_tags': ['Start', 'PI', 'End'],
        'attr_map': {
            'name': ('name', str),
            'desc': ('desc', str),
            'length': ('length', 'float'),
            'radiusEnd': ('radiusEnd', 'radius'),
            'radiusStart': ('radiusStart', 'radius'),
            'rot': ('rot', str),
            'spiType': ('spiType', str),
            'theta': ('theta', 'angle'),
            'constant': ('constant', 'float'),
            'dirStart': ('dirStart', 'angle'),
            'dirEnd': ('dirEnd', 'angle'),
            'chord': ('chord', 'float'),
            'totalX': ('totalX', 'float'),
            'totalY': ('totalY', 'float'),
            'tanLong': ('tanLong', 'float'),
            'tanShort': ('tanShort', 'float'),
            'staStart': ('staStart', 'float')
        }
    }
}

# Alignment configuration
ALIGNMENT_CONFIG = {
    'attr_map': {
        'name': ('name', str),
        'desc': ('desc', str),
        'length': ('length', 'float'),
        'staStart': ('staStart', 'float')
    }
}

# Alignment PI configuration
ALIGN_PI_CONFIG = {
    'attr_map': {
        'station': ('station', 'float'),
        'desc': ('desc', str)
    }
}

# Station equation configuration
STATION_EQUATION_CONFIG = {
    'attr_map': {
        'staAhead': ('staAhead', 'float'),
        'staBack': ('staBack', 'float'),
        'staInternal': ('staInternal', 'float'),
        'desc': ('desc', str)
    },
    'required_fields': ['staAhead', 'staBack']
}

# CgPoint configuration
CGPOINT_CONFIG = {
    'attr_map': {
        'name': ('name', str),
        'desc': ('desc', str),
        'code': ('code', str),
        'state': ('state', str),
        'pntRef': ('pntRef', str),
        'featureRef': ('featureRef', str),
        'pointGeometry': ('pointGeometry', str),
        'DTMAttribute': ('DTMAttribute', str),
        'timeStamp': ('timeStamp', str)
    },
    'required_fields': ['name']
}

# Surface configuration
SURFACE_CONFIG = {
    'attr_map': {
        'name': ('name', str),
        'desc': ('desc', str),
        'state': ('state', str),
        'surfType': ('surfType', str),
        'area2DSurf': ('area2DSurf', 'float'),
        'area3DSurf': ('area3DSurf', 'float'),
        'elevMin': ('elevMin', 'float'),
        'elevMax': ('elevMax', 'float')
    },
    'required_fields': ['name']
}

# Face configuration (for TIN surfaces)
FACE_CONFIG = {
    'required_fields': []
}