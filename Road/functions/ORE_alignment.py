import math
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from scipy.special import fresnel


class RoadGeometry(ABC):
    """
    RoadGeometry class is responsible for storing the basic chordline geometry properties
    """
    
    def __init__(self, s: float, x: float, y: float, hdg: float, length: float):
        """
        Constructor that initializes the base properties of the record
        """
        self.mS = s
        self.mX = x
        self.mY = y
        self.mHdg = hdg
        self.mLength = length
        self.mS2 = s + length
        self.mGeomType = 0  # 0-line, 1-arc, 2-spiral, 3-poly3
    
    def compute_vars(self):
        """
        Computes the required vars
        """
        pass
    
    @abstractmethod
    def clone(self) -> 'RoadGeometry':
        """
        Clones and returns the new geometry record
        """
        pass
    
    def set_geom_type(self, geom_type: int):
        """
        Sets the type of the geometry
        0: Line, 1: Arc, 2: Spiral, 3: Poly3
        """
        self.mGeomType = geom_type
    
    def set_base(self, s: float, x: float, y: float, hdg: float, length: float, recalculate: bool = True):
        """
        Setter for the base properties
        """
        self.mS = s
        self.mX = x
        self.mY = y
        self.mHdg = hdg
        self.mLength = length
        self.mS2 = self.mS + self.mLength
        if recalculate:
            self.compute_vars()
    
    def set_s(self, s: float):
        self.mS = s
        self.mS2 = self.mS + self.mLength
        self.compute_vars()
    
    def set_x(self, x: float):
        self.mX = x
    
    def set_y(self, y: float):
        self.mY = y
    
    def set_hdg(self, hdg: float):
        self.mHdg = hdg
        self.compute_vars()
    
    def set_length(self, length: float):
        self.mLength = length
        self.mS2 = self.mS + self.mLength
        self.compute_vars()
    
    # Getters
    def get_geom_type(self) -> int:
        return self.mGeomType
    
    def get_s(self) -> float:
        return self.mS
    
    def get_s2(self) -> float:
        return self.mS2
    
    def get_x(self) -> float:
        return self.mX
    
    def get_y(self) -> float:
        return self.mY
    
    def get_hdg(self) -> float:
        return self.mHdg
    
    def get_length(self) -> float:
        return self.mLength
    
    def check_interval(self, s_check: float) -> bool:
        """
        Checks if the sample S gets in the current block interval
        """
        return self.mS <= s_check <= self.mS2
    
    def get_coords(self, s_check: float) -> Tuple[float, float]:
        """
        Gets the coordinates at the sample S offset
        """
        x, y, _ = self.get_coords_with_hdg(s_check)
        return x, y
    
    @abstractmethod
    def get_coords_with_hdg(self, s_check: float) -> Tuple[float, float, float]:
        """
        Gets the coordinates and heading at the sample S offset
        """
        pass


class GeometryLine(RoadGeometry):
    """
    GeometryLine inherits the RoadGeometry class but adds no additional properties
    """
    
    def __init__(self, s: float, x: float, y: float, hdg: float, length: float):
        """
        Constructor that initializes the base properties of the record
        """
        super().__init__(s, x, y, hdg, length)
        self.set_geom_type(0)
    
    def clone(self) -> 'GeometryLine':
        """
        Clones and returns the new geometry record
        """
        return GeometryLine(self.mS, self.mX, self.mY, self.mHdg, self.mLength)
    
    def set_all(self, s: float, x: float, y: float, hdg: float, length: float):
        """
        Setter for the base properties
        """
        self.set_base(s, x, y, hdg, length, False)
        self.compute_vars()
    
    def get_coords_with_hdg(self, s_check: float) -> Tuple[float, float, float]:
        """
        Gets the coordinates at the sample S offset
        """
        new_length = s_check - self.mS
        # Find the end of the chord line
        ret_x = self.mX + math.cos(self.mHdg) * new_length
        ret_y = self.mY + math.sin(self.mHdg) * new_length
        ret_hdg = self.mHdg
        return ret_x, ret_y, ret_hdg


class GeometryArc(RoadGeometry):
    """
    GeometryArc inherits the RoadGeometry class and adds Curvature property
    """
    
    def __init__(self, s: float, x: float, y: float, hdg: float, length: float, curvature: float):
        """
        Constructor that initializes the base properties of the record
        """
        super().__init__(s, x, y, hdg, length)
        self.set_geom_type(1)
        self.mCurvature = curvature
        
        # Optimization related variables
        self.mCircleX = 0.0
        self.mCircleY = 0.0
        self.mStartAngle = 0.0
        
        self.compute_vars()
    
    def compute_vars(self):
        """
        Computes the required vars
        """
        radius = 0.0
        # If curvature is 0, radius is also 0, otherwise, radius is 1/curvature
        if abs(self.mCurvature) > 1.00e-15:
            radius = abs(1.0 / self.mCurvature)
        
        # Calculate the start angle for the arc plot
        if self.mCurvature <= 0:
            self.mStartAngle = self.mHdg + math.pi / 2
        else:
            self.mStartAngle = self.mHdg - math.pi / 2
        
        self.mCircleX = self.mX + math.cos(self.mStartAngle - math.pi) * radius
        self.mCircleY = self.mY + math.sin(self.mStartAngle - math.pi) * radius
    
    def clone(self) -> 'GeometryArc':
        """
        Clones and returns the new geometry record
        """
        return GeometryArc(self.mS, self.mX, self.mY, self.mHdg, self.mLength, self.mCurvature)
    
    def set_all(self, s: float, x: float, y: float, hdg: float, length: float, curvature: float):
        """
        Setter for the base properties
        """
        self.set_base(s, x, y, hdg, length, False)
        self.mCurvature = curvature
        self.compute_vars()
    
    def set_curvature(self, curvature: float):
        self.mCurvature = curvature
        self.compute_vars()
    
    def get_curvature(self) -> float:
        return self.mCurvature
    
    def get_coords_with_hdg(self, s_check: float) -> Tuple[float, float, float]:
        """
        Gets the coordinates at the sample S offset
        """
        # S from the beginning of the segment
        current_length = s_check - self.mS
        end_angle = self.mStartAngle
        radius = 0.0
        
        # If curvature is 0, radius is also 0, so don't add anything to the initial radius,
        # otherwise, radius is 1/curvature so the central angle can be calculated and added to the initial direction
        if abs(self.mCurvature) > 1.00e-15:
            end_angle += current_length / (1.0 / self.mCurvature)
            radius = abs(1.0 / self.mCurvature)
        
        # Coords on the arc for given s value
        ret_x = self.mCircleX + math.cos(end_angle) * radius
        ret_y = self.mCircleY + math.sin(end_angle) * radius
        
        # Heading at the given position
        if self.mCurvature <= 0:
            ret_hdg = end_angle - math.pi / 2
        else:
            ret_hdg = end_angle + math.pi / 2
        
        return ret_x, ret_y, ret_hdg


class GeometrySpiral(RoadGeometry):
    """
    GeometrySpiral inherits the RoadGeometry class and adds Curvature properties
    """
    
    SQRT_PI_O2 = math.sqrt(math.pi / 2)
    
    def __init__(self, s: float, x: float, y: float, hdg: float, length: float, 
                 curvature_start: float, curvature_end: float):
        """
        Constructor that initializes the base properties of the record
        """
        super().__init__(s, x, y, hdg, length)
        self.set_geom_type(2)
        self.mCurvatureStart = curvature_start
        self.mCurvatureEnd = curvature_end
        
        # Computation variables
        self.mA = 0.0
        self.mCurvature = 0.0
        self.mDenormalizeFactor = 0.0
        self.mEndX = 0.0
        self.mEndY = 0.0
        self.mNormalDir = True
        self.differenceAngle = 0.0
        self.mRotCos = 0.0
        self.mRotSin = 0.0
        
        self.compute_vars()
    
    def compute_vars(self):
        """
        Computes the required vars
        """
        self.mA = 0
        
        # If the curvatureEnd is the non-zero curvature, then the motion is in normal direction along the spiral
        if abs(self.mCurvatureEnd) > 1.00e-15 and abs(self.mCurvatureStart) <= 1.00e-15:
            self.mNormalDir = True
            self.mCurvature = self.mCurvatureEnd
            # Calculate the normalization term: a = 1.0/sqrt(2*End_Radius*Total_Curve_Length)
            self.mA = 1.0 / math.sqrt(2 * 1.0 / abs(self.mCurvature) * self.mLength)
            # Denormalization Factor
            self.mDenormalizeFactor = 1.0 / self.mA
            
            # Calculate the sine and cosine of the heading angle used to rotate the spiral according to the heading
            self.mRotCos = math.cos(self.mHdg)
            self.mRotSin = math.sin(self.mHdg)
        else:
            # Motion is in the inverse direction along the spiral
            self.mNormalDir = False
            self.mCurvature = self.mCurvatureStart
            # Calculate the normalization term: a = 1.0/sqrt(2*End_Radius*Total_Curve_Length)
            self.mA = 1.0 / math.sqrt(2 * 1.0 / abs(self.mCurvature) * self.mLength)
            
            # Because we move in the inverse direction, we need to rotate the curve according to the heading
            # around the last point of the normalized spiral
            # Calculate the total length, normalize it and divide by sqrtPiO2, then, calculate the position of the final point.
            L = (self.mS2 - self.mS) * self.mA / self.SQRT_PI_O2
            self.mEndY, self.mEndX = fresnel(L)
            
            # Invert the curve if the curvature is negative
            if self.mCurvature < 0:
                self.mEndY = -self.mEndY
            
            # Denormalization factor
            self.mDenormalizeFactor = 1.0 / self.mA
            # Find the x,y coords of the final point of the curve in local curve coordinates
            self.mEndX *= self.mDenormalizeFactor * self.SQRT_PI_O2
            self.mEndY *= self.mDenormalizeFactor * self.SQRT_PI_O2
            
            # Calculate the tangent angle
            self.differenceAngle = L * L * (self.SQRT_PI_O2 * self.SQRT_PI_O2)
            
            # Calculate the tangent and heading angle difference that will be used to rotate the spiral
            if self.mCurvature < 0:
                diff_angle = self.mHdg - self.differenceAngle - math.pi
            else:
                diff_angle = self.mHdg + self.differenceAngle - math.pi
            
            # Calculate the sine and cosine of the difference angle
            self.mRotCos = math.cos(diff_angle)
            self.mRotSin = math.sin(diff_angle)
    
    def clone(self) -> 'GeometrySpiral':
        """
        Clones and returns the new geometry record
        """
        return GeometrySpiral(self.mS, self.mX, self.mY, self.mHdg, self.mLength, 
                             self.mCurvatureStart, self.mCurvatureEnd)
    
    def set_all(self, s: float, x: float, y: float, hdg: float, length: float,
                curvature_start: float, curvature_end: float):
        """
        Setter for the base properties
        """
        self.set_base(s, x, y, hdg, length, False)
        self.mCurvatureStart = curvature_start
        self.mCurvatureEnd = curvature_end
        self.compute_vars()
    
    def set_curvature_start(self, curvature: float):
        self.mCurvatureStart = curvature
        self.compute_vars()
    
    def set_curvature_end(self, curvature: float):
        self.mCurvatureEnd = curvature
        self.compute_vars()
    
    def get_curvature_start(self) -> float:
        return self.mCurvatureStart
    
    def get_curvature_end(self) -> float:
        return self.mCurvatureEnd
    
    def get_coords_with_hdg(self, s_check: float) -> Tuple[float, float, float]:
        """
        Gets the coordinates at the sample S offset
        """
        # Depending on the moving direction, calculate the length of the curve from its beginning to the current point and normalize
        # it by multiplying with the "a" normalization term
        # Cephes lib for solving Fresnel Integrals, uses cos/sin (PI/2 * X^2) format in its function.
        # So, in order to use the function, transform the argument (which is just L) by dividing it by the sqrt(PI/2) factor and multiply the results by it.
        if self.mNormalDir:
            l = (s_check - self.mS) * self.mA / self.SQRT_PI_O2
        else:
            l = (self.mS2 - s_check) * self.mA / self.SQRT_PI_O2
        
        # Solve the Fresnel Integrals
        tmp_y, tmp_x = fresnel(l)
        
        # If the curvature is negative, invert the curve on the Y axis
        if self.mCurvature < 0:
            tmp_y = -tmp_y
        
        # Denormalize the results and multiply by the sqrt(PI/2) term
        tmp_x *= self.mDenormalizeFactor * self.SQRT_PI_O2
        tmp_y *= self.mDenormalizeFactor * self.SQRT_PI_O2
        
        # Calculate the heading at the found position. Kill the sqrt(PI/2) term that was added to the L
        l = (s_check - self.mS) * self.mA
        tangent_angle = l * l
        if self.mCurvature < 0:
            tangent_angle = -tangent_angle
        ret_hdg = self.mHdg + tangent_angle
        
        if not self.mNormalDir:
            # If we move in the inverse direction, translate the spiral in order to rotate around its final point
            tmp_x -= self.mEndX
            tmp_y -= self.mEndY
            # Also invert the spiral in the y axis
            tmp_y = -tmp_y
        
        # Translate the curve to the required position and rotate it according to the heading
        ret_x = self.mX + tmp_x * self.mRotCos - tmp_y * self.mRotSin
        ret_y = self.mY + tmp_y * self.mRotCos + tmp_x * self.mRotSin
        
        return ret_x, ret_y, ret_hdg


class GeometryPoly3(RoadGeometry):
    """
    GeometryPoly3 inherits the RoadGeometry class and adds polynomial properties
    """
    
    def __init__(self, s: float, x: float, y: float, hdg: float, length: float,
                 a: float, b: float, c: float, d: float):
        """
        Constructor that initializes the base properties of the record
        """
        super().__init__(s, x, y, hdg, length)
        self.set_geom_type(3)
        self.mA = a
        self.mB = b
        self.mC = c
        self.mD = d
    
    def clone(self) -> 'GeometryPoly3':
        """
        Clones and returns the new geometry record
        """
        return GeometryPoly3(self.mS, self.mX, self.mY, self.mHdg, self.mLength,
                            self.mA, self.mB, self.mC, self.mD)
    
    def set_all(self, s: float, x: float, y: float, hdg: float, length: float,
                a: float, b: float, c: float, d: float):
        """
        Setter for the base properties
        """
        self.set_base(s, x, y, hdg, length, False)
        self.mA = a
        self.mB = b
        self.mC = c
        self.mD = d
        self.compute_vars()
    
    def get_coords_with_hdg(self, s_check: float) -> Tuple[float, float, float]:
        """
        Gets the coordinates at the sample S offset
        Note: This method needs to be implemented based on polynomial geometry requirements
        """
        # This is a placeholder implementation - the actual polynomial coordinate calculation
        # was not implemented in the original C++ code
        return self.mX, self.mY, self.mHdg


class GeometryBlock:
    """
    GeometryBlock is a class used to combine multiple geometry records into blocks.
    The basic use for this is to combine spiral-arc-spiral sequence of records into 
    a single "Turn" block for an easier way to define turns, keeping close to the
    road building practice of curvature use for transitions between straight segments and arcs
    """
    
    def __init__(self):
        """
        Constructor
        """
        self.mGeometryBlockElement: List[RoadGeometry] = []
    
    def __deepcopy__(self, memo):
        """
        Deep copy implementation
        """
        new_block = GeometryBlock()
        for geometry in self.mGeometryBlockElement:
            new_block.mGeometryBlockElement.append(geometry.clone())
        return new_block
    
    def add_geometry_line(self, s: float, x: float, y: float, hdg: float, length: float):
        """
        Methods used to add geometry records to the geometry record vector
        """
        self.mGeometryBlockElement.append(GeometryLine(s, x, y, hdg, length))
    
    def add_geometry_arc(self, s: float, x: float, y: float, hdg: float, length: float, curvature: float):
        self.mGeometryBlockElement.append(GeometryArc(s, x, y, hdg, length, curvature))
    
    def add_geometry_spiral(self, s: float, x: float, y: float, hdg: float, length: float,
                           curvature_start: float, curvature_end: float):
        self.mGeometryBlockElement.append(GeometrySpiral(s, x, y, hdg, length, curvature_start, curvature_end))
    
    def add_geometry_poly3(self, s: float, x: float, y: float, hdg: float, length: float,
                          a: float, b: float, c: float, d: float):
        self.mGeometryBlockElement.append(GeometryPoly3(s, x, y, hdg, length, a, b, c, d))
    
    def get_geometry_at(self, index: int) -> Optional[RoadGeometry]:
        """
        Getter for the geometry record at a given index position of the vector
        """
        if 0 <= index < len(self.mGeometryBlockElement):
            return self.mGeometryBlockElement[index]
        return None
    
    def get_block_length(self) -> float:
        """
        Getter for the overall block length (sum of geometry record lengths)
        """
        total = 0.0
        for geometry in self.mGeometryBlockElement:
            total += geometry.get_length()
        return total
    
    def check_if_line(self) -> bool:
        """
        Checks if the block is a straight line block or a turn
        """
        return len(self.mGeometryBlockElement) <= 1
    
    def recalculate(self, s: float, x: float, y: float, hdg: float):
        """
        Recalculates the geometry blocks when one of the geometry records is modified
        Makes sure that every geometry record starts where the previous record ends
        """
        l_s = s
        l_x = x
        l_y = y
        l_hdg = hdg
        
        if len(self.mGeometryBlockElement) == 1:
            geometry_line = self.mGeometryBlockElement[0]
            if isinstance(geometry_line, GeometryLine):
                # Updates the line to reflect the changes of the previous block
                geometry_line.set_base(l_s, l_x, l_y, l_hdg, geometry_line.get_length())
        
        elif len(self.mGeometryBlockElement) == 3:
            geometry_spiral1 = self.mGeometryBlockElement[0]
            geometry_arc = self.mGeometryBlockElement[1]
            geometry_spiral2 = self.mGeometryBlockElement[2]
            
            if (isinstance(geometry_spiral1, GeometrySpiral) and 
                isinstance(geometry_arc, GeometryArc) and 
                isinstance(geometry_spiral2, GeometrySpiral)):
                
                # Updates the first spiral to reflect the changes of the previous block
                geometry_spiral1.set_base(l_s, l_x, l_y, l_hdg, geometry_spiral1.get_length())
                
                # Reads the new coords of the spiral
                l_s = geometry_spiral1.get_s2()
                l_x, l_y, l_hdg = geometry_spiral1.get_coords_with_hdg(l_s)
                
                # Updates the arc to reflect the changes to the first spiral
                geometry_arc.set_base(l_s, l_x, l_y, l_hdg, geometry_arc.get_length())
                
                # Reads the new coords of the arc
                l_s = geometry_arc.get_s2()
                l_x, l_y, l_hdg = geometry_arc.get_coords_with_hdg(l_s)
                
                # Updates the second spiral to reflect the changes to the arc
                geometry_spiral2.set_base(l_s, l_x, l_y, l_hdg, geometry_spiral2.get_length())
    
    def get_last_s2(self) -> float:
        """
        Gets the S at the end of the block
        """
        if self.mGeometryBlockElement:
            return self.mGeometryBlockElement[-1].get_s2()
        return 0.0
    
    def get_last_geometry(self) -> Optional[RoadGeometry]:
        """
        Gets the last geometry in the geometry vector
        """
        if self.mGeometryBlockElement:
            return self.mGeometryBlockElement[-1]
        return None
    
    def get_last_coords(self) -> Tuple[float, float, float, float]:
        """
        Gets the coordinates at the end of the last geometry
        Returns: (s, x, y, hdg)
        """
        if self.mGeometryBlockElement:
            geometry = self.mGeometryBlockElement[-1]
            s = geometry.get_s2()
            x, y, hdg = geometry.get_coords_with_hdg(s)
            return s, x, y, hdg
        return 0.0, 0.0, 0.0, 0.0
    
    def check_interval(self, s_check: float) -> bool:
        """
        Check if sample S belongs to this block
        """
        for geometry in self.mGeometryBlockElement:
            if geometry.check_interval(s_check):
                return True
        return False
    
    def get_coords(self, s_check: float) -> Tuple[float, float]:
        """
        Gets the coordinates at the sample S offset
        """
        x, y, _ = self.get_coords_with_hdg(s_check)
        return x, y
    
    def get_coords_with_hdg(self, s_check: float) -> Tuple[float, float, float, int]:
        """
        Gets the coordinates and heading at the sample S offset
        Returns: (x, y, hdg, geometry_type) or (0, 0, 0, -999) if not found
        """
        # Go through all the elements
        for geometry in self.mGeometryBlockElement:
            # If the s_check belongs to one of the geometries
            if geometry.check_interval(s_check):
                # Get the x,y coords and return the type of the geometry
                x, y, hdg = geometry.get_coords_with_hdg(s_check)
                return x, y, hdg, geometry.get_geom_type()
        
        # If nothing found, return -999
        return 0.0, 0.0, 0.0, -999