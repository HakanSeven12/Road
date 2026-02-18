# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the viewprovider code for Base objects."""

class ViewProviderBase:
    def __init__(self, vobj):
        """Default constructor"""

        vobj.Proxy = self

        property_list =[
            'App::PropertyBool', 'App::PropertyBoolList', 'App::PropertyFloat', 'App::PropertyFloatList', 
            'App::PropertyFloatConstraint', 'App::PropertyPrecision', 'App::PropertyQuantity', 
            'App::PropertyQuantityConstraint', 'App::PropertyInteger', 'App::PropertyIntegerConstraint', 
            'App::PropertyPercent', 'App::PropertyEnumeration', 'App::PropertyIntegerList', 'App::PropertyIntegerSet', 
            'App::PropertyMap', 'App::PropertyString', 'App::PropertyPersistentObject', 'App::PropertyUUID', 
            'App::PropertyFont', 'App::PropertyStringList', 'App::PropertyLink', 'App::PropertyLinkChild', 
            'App::PropertyLinkGlobal', 'App::PropertyLinkHidden', 'App::PropertyLinkSub', 'App::PropertyLinkSubChild', 
            'App::PropertyLinkSubGlobal', 'App::PropertyLinkSubHidden', 'App::PropertyLinkList', 'App::PropertyLinkListChild', 
            'App::PropertyLinkListGlobal', 'App::PropertyLinkListHidden', 'App::PropertyLinkSubList', 
            'App::PropertyLinkSubListChild', 'App::PropertyLinkSubListGlobal', 'App::PropertyLinkSubListHidden', 
            'App::PropertyXLink', 'App::PropertyXLinkSub', 'App::PropertyXLinkSubHidden', 'App::PropertyXLinkSubList', 
            'App::PropertyXLinkList', 'App::PropertyMatrix', 'App::PropertyVector', 'App::PropertyVectorDistance', 
            'App::PropertyPosition', 'App::PropertyDirection', 'App::PropertyVectorList', 'App::PropertyPlacement', 
            'App::PropertyPlacementList', 'App::PropertyPlacementLink', 'App::PropertyRotation', 'App::PropertyColor', 
            'App::PropertyColorList', 'App::PropertyMaterial', 'App::PropertyMaterialList', 'App::PropertyPath', 
            'App::PropertyFile', 'App::PropertyFileIncluded', 'App::PropertyPythonObject', 'App::PropertyExpressionEngine', 
            'App::PropertyAcceleration', 'App::PropertyAmountOfSubstance', 'App::PropertyAngle', 'App::PropertyArea', 
            'App::PropertyCompressiveStrength', 'App::PropertyCurrentDensity', 'App::PropertyDensity', 'App::PropertyDissipationRate', 
            'App::PropertyDistance', 'App::PropertyDynamicViscosity', 'App::PropertyElectricalCapacitance', 
            'App::PropertyElectricalConductance', 'App::PropertyElectricalConductivity', 'App::PropertyElectricalInductance', 
            'App::PropertyElectricalResistance', 'App::PropertyElectricCharge', 'App::PropertyElectricCurrent', 
            'App::PropertyElectricPotential', 'App::PropertyFrequency', 'App::PropertyForce', 'App::PropertyHeatFlux', 
            'App::PropertyInverseArea', 'App::PropertyInverseLength', 'App::PropertyInverseVolume', 'App::PropertyKinematicViscosity', 
            'App::PropertyLength', 'App::PropertyLuminousIntensity', 'App::PropertyMagneticFieldStrength', 'App::PropertyMagneticFlux', 
            'App::PropertyMagneticFluxDensity', 'App::PropertyMagnetization', 'App::PropertyMass', 'App::PropertyMoment', 
            'App::PropertyPressure', 'App::PropertyPower', 'App::PropertyShearModulus', 'App::PropertySpecificEnergy', 
            'App::PropertySpecificHeat', 'App::PropertySpeed', 'App::PropertyStiffness', 'App::PropertyStiffnessDensity', 
            'App::PropertyStress', 'App::PropertyTemperature', 'App::PropertyThermalConductivity', 'App::PropertyThermalExpansionCoefficient', 
            'App::PropertyThermalTransferCoefficient', 'App::PropertyTime', 'App::PropertyUltimateTensileStrength', 'App::PropertyVacuumPermittivity', 
            'App::PropertyVelocity', 'App::PropertyVolume', 'App::PropertyVolumeFlowRate', 'App::PropertyVolumetricThermalExpansionCoefficient', 
            'App::PropertyWork', 'App::PropertyYieldStrength', 'App::PropertyYoungsModulus', 'Materials::PropertyMaterial', 
            'Part::PropertyPartShape', 'Part::PropertyGeometryList', 'Part::PropertyShapeHistory', 'Part::PropertyFilletEdges', 
            'Part::PropertyShapeCache', 'Part::PropertyTopoShapeList', 'Sketcher::PropertyConstraintList']

        vobj.addProperty("App::PropertyString", "Test", "Base", "Test property").Test = "Test"

    def attach(self, vobj):
        """Setup the scene sub-graph of the view provider, this method is mandatory"""
        self.Object = vobj.Object

    def onChanged(self, vobj, prop):
        """Called after a view property is changed"""
        pass

    def updateData(self, vobj, prop):
        """Called after a data (model) property is changed"""
        pass

    def getDisplayModes(self, vobj):
        """Return a list of display modes."""
        modes = ["Base", "Base1", "Base2"]
        return modes

    def getDefaultDisplayMode(self):
        """Return the name of the default display mode."""
        return "Base"

    def setDisplayMode(self, mode):
        """Map the display mode defined in attach with those defined in getDisplayModes.
        Since they have the same names nothing needs to be done. (optional)"""
        return mode

    def getIcon(self):
        """Return the icon in XMP format which will appear in the tree view. 
        If not defined a default icon is shown."""

        return "/Icon/path/to/the/file"

    def claimChildren(self):
        """Provides object grouping"""
        return self.Object.Group

    def setEdit(self, vobj, mode=0):
        """Enable edit"""
        return True

    def unsetEdit(self, vobj, mode=0):
        """Disable edit"""
        return False

    def doubleClicked(self, vobj):
        """Detect double click"""
        pass

    def setupContextMenu(self, obj, menu):
        """Context menu construction"""
        pass

    def edit(self):
        """Edit callback"""
        pass
    def dumps(self):
        """Called during document saving."""
        return None

    def loads(self, state):
        """Called during document restore."""
        return None