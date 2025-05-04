# -*- coding: utf-8 -*-
__title__   = "Floor to Room"
__doc__     = """Version = 1.0
Date    = 15.06.2024
________________________________________________________________
Description:


________________________________________________________________
Author: Zwe"""

from pyrevit import revit, DB, forms
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter

doc = revit.doc
uidoc = revit.uidoc

# ------------------------------
# Room Selection Filter
# ------------------------------
class RoomSelectionFilter(ISelectionFilter):
    def AllowElement(self, element):
        return isinstance(element, DB.Architecture.Room)
    def AllowReference(self, ref, point):
        return True

# ------------------------------
# Select Room
# ------------------------------
room_ref = uidoc.Selection.PickObject(ObjectType.Element, RoomSelectionFilter(), "Select a room")
room = doc.GetElement(room_ref.ElementId)

if not room or not room.Location:
    forms.alert("Selected room is not valid or not placed.")
    raise Exception("Invalid room")

# ------------------------------
# Get Room Boundaries
# ------------------------------
options = DB.SpatialElementBoundaryOptions()
boundaries = room.GetBoundarySegments(options)

if not boundaries:
    forms.alert("Room has no boundary segments.")
    raise Exception("No boundaries")

curves = []
for loop in boundaries:
    for seg in loop:
        curves.append(seg.GetCurve())

# ------------------------------
# Ask for Offset (IronPython safe)
# ------------------------------
offset_input = forms.ask_for_string(default="0", prompt="Offset from level (in mm):")
try:
    offset_mm = float(offset_input)
except:
    forms.alert("Invalid number. Using 0 mm offset.")
    offset_mm = 0.0

offset = offset_mm / 304.8  # mm to feet

# ------------------------------
# Select Floor Type (Safe for IronPython)
# ------------------------------
floor_types = DB.FilteredElementCollector(doc).OfClass(DB.FloorType).ToElements()
floor_type_map = {
    ft.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString(): ft
    for ft in floor_types
}
floor_type_name = forms.SelectFromList.show(
    sorted(floor_type_map.keys()),
    button_name="Select Floor Type"
)
floor_type = floor_type_map.get(floor_type_name)

if not floor_type:
    forms.alert("No floor type selected.")
    raise Exception("No floor type")

# ------------------------------
# Select Level (Safe for IronPython)
# ------------------------------
levels = DB.FilteredElementCollector(doc).OfClass(DB.Level).ToElements()
level_map = { lvl.Name: lvl for lvl in levels }

level_name = forms.SelectFromList.show(
    sorted(level_map.keys()),
    button_name="Select Level"
)
level = level_map.get(level_name)

if not level:
    raise Exception("No level selected")

# ------------------------------
# Create Floor using DB.Floor.Create()
# ------------------------------
curve_loops = DB.CurveLoop.Create(curves)

with revit.Transaction("Create Floor from Room Boundary"):
    floor = DB.Floor.Create(doc, [curve_loops], floor_type.Id, level.Id)
    offset_param = floor.get_Parameter(DB.BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM)
    if offset_param and offset != 0:
        offset_param.Set(offset)

forms.alert("Floor created successfully!", title="Done")







