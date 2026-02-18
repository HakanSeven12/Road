# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import Dict, List, Tuple, Optional, Union
from .arc import Arc
from .tangent import Tangent
from .parabola import Parabola


class Profile:
    """
    LandXML 1.2 vertical profile reader & geometry generator.
    Manages multiple vertical alignments (ProfAlign) and surface profiles (ProfSurf).
    Each uses geometry elements (Tangent, Parabola, Arc).
    """

    def __init__(self, name: str=None, desc: str=None, data: Dict=None):
        """
        Initialize profile from LandXML data dictionary.
        
        Args:
            data: Dictionary containing profile data
            parent_alignment: Reference to parent Alignment object (optional)
        """
        
        # Profile metadata
        self.name = name
        self.data = data
        self.description = desc
        self.elements: List[Union[Tangent, Arc, Parabola]] = []

        self.update(data)

    def update(self, data: Dict) -> None:
        """
        Update profile geometry from LandXML data dictionary.
        
        Args:
            data: Dictionary containing profile data
        """
        self.data = data
        self._create_geometry(data)

    def _create_geometry(self, data: List[Dict]) -> List:
        """Create geometry elements (Tangent, Parabola, Arc) from geometry data"""
        self.elements.clear()
        # Extract PVI points and curve data
        last_end = data[0]['pvi'].copy()
        for i in range(1, len(data) - 1):
            pvi_prev = data[i - 1]['pvi']
            pvi_curr = data[i]['pvi']
            pvi_next = data[i + 1]['pvi']

            # Calculate grade in
            sta_diff_in = pvi_curr['station'] - pvi_prev['station']
            elev_diff_in = pvi_curr['elevation'] - pvi_prev['elevation']
            grade_in = elev_diff_in / sta_diff_in if sta_diff_in != 0 else 0.0

            # Calculate grade out
            sta_diff_out = pvi_next['station'] - pvi_curr['station']
            elev_diff_out = pvi_next['elevation'] - pvi_curr['elevation']
            grade_out = elev_diff_out / sta_diff_out if sta_diff_out != 0 else 0.0

            geom_type = data[i].get('type')
            if geom_type is None:
                tangent = Tangent(
                    sta_start=last_end['station'],
                    elev_start=last_end['elevation'],
                    sta_end=pvi_curr['station'],
                    elev_end=pvi_curr['elevation']
                )
                self.elements.append(tangent)
                last_end = pvi_curr
                
            if geom_type in ['ParaCurve', 'UnsymParaCurve']:
                parabola = Parabola(data[i], grade_in, grade_out)
                parabola_sta_start = parabola.get_station_range()[0]
                parabola_elev_start = parabola.get_elevation_at_station(parabola_sta_start)
                tangent = Tangent(
                    sta_start=last_end['station'],
                    elev_start=last_end['elevation'],
                    sta_end=parabola_sta_start,
                    elev_end=parabola_elev_start
                )
                self.elements.extend([tangent, parabola])
                last_end['station'] = parabola.get_station_range()[1]
                last_end['elevation'] = parabola.get_elevation_at_station(last_end['station'])

            if geom_type == 'CircCurve':
                arc = Arc(data[i], grade_in, grade_out)
                arc_sta_start = arc.get_station_range()[0]
                arc_elev_start = arc.get_elevation_at_station(arc_sta_start)
                tangent = Tangent(
                    sta_start=last_end['station'],
                    elev_start=last_end['elevation'],
                    sta_end=arc_sta_start,
                    elev_end=arc_elev_start
                )
                self.elements.extend([tangent, arc])
                last_end['station'] = arc.get_station_range()[1]
                last_end['elevation'] = arc.get_elevation_at_station(last_end['station'])

        # Final tangent to last PVI
        final_pvi = data[-1]['pvi']
        tangent = Tangent(
            sta_start=last_end['station'],
            elev_start=last_end['elevation'],
            sta_end=final_pvi['station'],
            elev_end=final_pvi['elevation']
        )
        self.elements.append(tangent)
    
    def get_elevation_at_station(self, station: float) -> Optional[float]:
        """
        Get design elevation at station from a specific ProfAlign.
        
        Args:
            station: Station to query
        """
        
        for elem in self.elements:
            sta_start, sta_end = elem.get_station_range()
            if sta_start <= station <= sta_end:
                return elem.get_elevation_at_station(station)
        return None
    
    def get_grade_at_station(self, station: float) -> Optional[float]:
        """
        Get design grade at station from a specific ProfAlign.
        
        Args:
            station: Station to query
        """
        for elem in self.elements:
            sta_start, sta_end = elem.get_station_range()
            if sta_start <= station <= sta_end:
                return elem.get_grade_at_station(station)
        return None
    
    def get_pvi_points(self) -> List[Tuple[float, float]]:
        """Return PVI points for a specific ProfAlign"""
        return [i.get('pvi') for i in self.data]
    
    def get_elements(self) -> Union[Tangent, Arc, Parabola]:
        """Return geometry elements for a specific ProfAlign"""
        return self.elements.copy()
    
    @property
    def start_station(self) -> Optional[float]:
        """Return profile start station"""
        return self.elements[0].get_station_range()[0] if self.elements else None

    @property
    def end_station(self) -> Optional[float]:
        """Return profile end station"""
        return self.elements[-1].get_station_range()[1] if self.elements else None
    
    def to_dict(self) -> Dict:
        """Export profile properties"""
        return {
            'name': self.name,
            'desc': self.description,
            'geometry': self.data
        }

    def __repr__(self) -> str:
        return (
            f"Profile(name='{self.name}', "
            f"elements={len(self.elements)}, "
            f"sta_range=[{self.start_station}, {self.end_station}]),"
            f"data={self.data})"
        )
    
    def __str__(self) -> str:
        return f"Profile '{self.name}': {len(self.elements)} elements, {self.start_station} to {self.end_station} station"