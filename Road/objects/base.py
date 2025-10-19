# SPDX-License-Identifier: LGPL-2.1-or-later

"""Provides the object code for Base objects."""

class Base:

    def __init__(self, obj):
        """Default constructor"""

        self.Type = "Workbench::Base"

        obj.Proxy = self

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

        """
        obj.addProperty("App::PropertyString", "MyCustomProperty", "Title", "Description", 8, True, True, [Option, Option1, Option2]).MyCustomProperty = "MyCustomProperty"
        obj.addProperty(type: string, name: string, group="", doc="", attr=0, read_only=False, hidden=False, enum_vals=[])
        type: Property type.
        name: Property name.
        group: Property subsection (used in the Property editor).
        doc: Tooltip (idem).
        attr: Attribute.
            0 -- Prop_None, No special property attribute
            1 -- Prop_ReadOnly, Property is read-only in the editor
            2 -- Prop_Transient, Property won't be saved to file
            4 -- Prop_Hidden, Property won't appear in the editor
            8 -- Prop_Output, Modified property doesn't touch its parent container
            16 -- Prop_NoRecompute, Modified property doesn't touch its container for recompute
            32 -- Prop_NoPersist, Property won't be saved to file at all
        
        read_only: See above.
        hidden: See above.
        enum_vals: Enumeration values (list of string), only relevant if type is "App::PropertyEnumeration".attr
        """

        """
        obj.setEditorMode("MyPropertyName", mode)
        mode: Editor mode.
            0 -- default mode, read and write
            1 -- read-only
            2 -- hidden
            3 -- read-only and hidden
        """

    def execute(self, obj):
        """Called during document recomputes"""
        pass
        
    def onBeforeChange(self, obj, prop):
        """Called before a property value is changed"""
        pass
        
    def onChanged(self, obj, prop):
        """Called after a property is changed"""
        pass

    def onDocumentRestored(self, obj):
        """Called after a document is restored or a FeaturePython object is copied"""
        pass