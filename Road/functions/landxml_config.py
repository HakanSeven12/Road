# SPDX-License-Identifier: LGPL-2.1-or-later

"""
LandXML Parser Configuration
Contains all mapping configurations for parsing LandXML elements.
"""

# Geometry element configurations
GEOMETRY_CONFIG = {
    'Line': {
        'point_tags': ['Start', 'End'],
        'attr_map': {
            'name': ('name', str),
            'desc': ('desc', str),
            'length': ('length', 'float'),
            'dir': ('dir', 'float'),
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
            'delta': ('delta', 'float'),
            'dirStart': ('dirStart', 'float'),
            'dirEnd': ('dirEnd', 'float'),
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
            'theta': ('theta', 'float'),
            'constant': ('constant', 'float'),
            'dirStart': ('dirStart', 'float'),
            'dirEnd': ('dirEnd', 'float'),
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

# LandXML namespaces
LANDXML_NAMESPACES = {
    'landxml': 'http://www.landxml.org/schema/LandXML-1.2',
    '': 'http://www.landxml.org/schema/LandXML-1.2'
}

# Converter function types
CONVERTER_TYPES = {
    'float': 'float',
    'int': 'int',
    'str': str,
    'rotation': 'rotation',  # Converts 'cw'/'ccw' to 1/-1
    'radius': 'radius'       # Converts 'INF' to float('inf')
}