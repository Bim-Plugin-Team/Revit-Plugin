# -*- coding: utf-8 -*-
__title__   = "Grouting"
__doc__     = """Version = 1.0
Date    = 15.06.2024
________________________________________________________________
Description:


________________________________________________________________
Author: Zwe"""

from pyrevit import revit, forms, script
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import InstanceVoidCutUtils
from Autodesk.Revit.DB.Structure import StructuralType
from Autodesk.Revit.UI.Selection import ObjectType

# --- Selection ---
doc = revit.doc
uidoc = revit.uidoc

# Select inserts (windows/doors)
insert_refs = uidoc.Selection.PickObjects(ObjectType.Element, "Select windows/doors")
inserts = [doc.GetElement(r) for r in insert_refs if isinstance(doc.GetElement(r), FamilyInstance)]

if not inserts:
    forms.alert("No valid family instances selected.")
    script.exit()

# Select wall
wall_ref = uidoc.Selection.PickObject(ObjectType.Element, "Select the host wall")
wall = doc.GetElement(wall_ref)
if not isinstance(wall, Wall):
    forms.alert("You must select a wall.")
    script.exit()

# Validate all inserts are hosted on selected wall
for inst in inserts:
    if inst.Host.Id != wall.Id:
        forms.alert("All selected inserts must be hosted on the selected wall.")
        script.exit()

# --- User Input ---
selected_sides = []
if forms.alert('Add grout on LEFT?', options=['Yes', 'No']) == 'Yes':
    selected_sides.append("left")
if forms.alert('Add grout on RIGHT?', options=['Yes', 'No']) == 'Yes':
    selected_sides.append("right")
if forms.alert('Add grout on TOP?', options=['Yes', 'No']) == 'Yes':
    selected_sides.append("top")
if forms.alert('Add grout on BOTTOM?', options=['Yes', 'No']) == 'Yes':
    selected_sides.append("bottom")

if not selected_sides:
    script.exit()

thickness_input = forms.ask_for_string(default="50", prompt="Grout thickness in mm:")
try:
    grout_thickness = float(thickness_input) / 304.8  # mm to feet
except:
    forms.alert("Invalid thickness value.")
    script.exit()

# --- Find loaded void family ---
family_name = "Void_Grout"
symbol = None
symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
for sym in symbols:
    if sym.Family.Name == family_name:
        symbol = sym
        break

if not symbol:
    forms.alert("Void family 'Void_Grout' not loaded.")
    script.exit()

# --- Place voids and cut wall ---
with revit.Transaction("Place Grout Voids"):
    if not symbol.IsActive:
        symbol.Activate()
        doc.Regenerate()

    for insert in inserts:
        bbox = insert.get_BoundingBox(doc.ActiveView)
        min_pt, max_pt = bbox.Min, bbox.Max
        center = (min_pt + max_pt) * 0.5
        width = max_pt.X - min_pt.X
        height = max_pt.Z - min_pt.Z

        # Expand width/height based on selected sides
        extra_width = grout_thickness if "left" in selected_sides else 0
        extra_width += grout_thickness if "right" in selected_sides else 0

        extra_height = grout_thickness if "top" in selected_sides else 0
        extra_height += grout_thickness if "bottom" in selected_sides else 0

        # Assume wall thickness is width of bounding box in Y (for simplicity)
        wall_thickness = max_pt.Y - min_pt.Y

        void_inst = doc.Create.NewFamilyInstance(center, symbol, wall, StructuralType.NonStructural)

        # Set parameters
        try:
            void_inst.LookupParameter("VoidWidth").Set(width + extra_width)
            void_inst.LookupParameter("VoidHeight").Set(height + extra_height)
            void_inst.LookupParameter("VoidDepth").Set(wall_thickness)
        except:
            forms.alert("Void instance missing expected parameters.")
            continue

        # Cut wall
        if InstanceVoidCutUtils.CanBeCutWithVoid(wall):
            InstanceVoidCutUtils.AddInstanceVoidCut(doc, wall, void_inst)

forms.alert("✅ Voids placed and wall cut successfully.")


















