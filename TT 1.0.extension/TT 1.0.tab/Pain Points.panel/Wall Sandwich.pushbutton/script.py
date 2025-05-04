# -*- coding: utf-8 -*-
__title__   = "Wall Sandwich"
__doc__     = """Version = 1.0
Date    = 15.06.2024
________________________________________________________________
Description:


________________________________________________________________
Author: Zwe"""

from pyrevit import forms
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
import os
import math

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

# Conversion factor
MM_TO_FEET = 1 / 304.8

# Fallback storage file for defaults
DEFAULTS_FILE = os.path.join(os.environ["APPDATA"], "pyRevit", "wall_sandwich_defaults.txt")

# Selection filter to allow only walls
class WallSelectionFilter(ISelectionFilter):
    def AllowElement(self, elem):
        return isinstance(elem, Wall)
    def AllowReference(self, ref, point):
        return True

# Prompt user to select a structural wall
sel = uidoc.Selection
try:
    ref = sel.PickObject(ObjectType.Element, WallSelectionFilter(), "Select a structural wall")
except:
    forms.alert("No wall selected.", exitscript=True)

wall = doc.GetElement(ref.ElementId)
location_curve = wall.Location.Curve
level = doc.GetElement(wall.LevelId)

# Read structural wall offsets
struct_base_offset = wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).AsDouble()
struct_top_offset = wall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET).AsDouble()
struct_wall_thickness = wall.WallType.Width

# Read previous defaults from file
def read_defaults():
    if os.path.exists(DEFAULTS_FILE):
        with open(DEFAULTS_FILE, "r") as f:
            lines = f.read().splitlines()
            if len(lines) >= 3:
                return {"offsets": lines[0], "left_walltype": lines[1], "right_walltype": lines[2]}
    return None

# Save defaults to file
def save_defaults(offsets, left_type, right_type):
    with open(DEFAULTS_FILE, "w") as f:
        f.write(offsets + "\n")
        f.write((left_type or "") + "\n")
        f.write((right_type or "") + "\n")

# Retrieve direction vector
point1 = location_curve.GetEndPoint(0)
point2 = location_curve.GetEndPoint(1)
direction = point2 - point1
perp = XYZ(-direction.Y, direction.X, 0).Normalize()

# Get wall types and names
wall_types = [wt for wt in FilteredElementCollector(doc).OfClass(WallType) if wt.Kind == WallKind.Basic]
wt_names = [wt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() for wt in wall_types]

# Load defaults and ask if reuse
defaults = read_defaults()
if defaults:
    reuse = forms.alert("Use previous wall types and offsets?", options=["Yes", "No"])
else:
    reuse = "No"

if reuse == "Yes":
    values = defaults["offsets"]
    left_choice = defaults["left_walltype"]
    right_choice = defaults["right_walltype"]
else:
    def_str = defaults["offsets"] if defaults else "0,0,0,0"
    values = forms.ask_for_string(
        default=def_str,
        prompt="Enter offsets in mm as: Left Base, Left Top, Right Base, Right Top",
        title="Wall Offsets in mm"
    )
    try:
        _ = [float(x) for x in values.split(",")]
    except:
        forms.alert("Invalid input. Enter 4 numbers in mm, separated by commas.", exitscript=True)

    left_choice = forms.SelectFromList.show(wt_names, title="Select Left Finish Wall Type", default=(defaults.get("left_walltype") if defaults else None), button_name="Use This Type")
    if not left_choice:
        forms.alert("No left wall type selected.", exitscript=True)

    right_choice = forms.SelectFromList.show(wt_names, title="Select Right Finish Wall Type", default=(defaults.get("right_walltype") if defaults else None), button_name="Use This Type")
    if not right_choice:
        forms.alert("No right wall type selected.", exitscript=True)

    # Save current values
    save_defaults(values, left_choice, right_choice)

# Convert values to feet
l_base, l_top, r_base, r_top = [float(x) * MM_TO_FEET for x in values.split(",")]

# Get selected wall types
left_wall_type = next(wt for wt in wall_types if wt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == left_choice)
right_wall_type = next(wt for wt in wall_types if wt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == right_choice)

# Start transaction
transaction = Transaction(doc, "Create Wall Sandwich")
transaction.Start()

for offset_sign, base_offset_delta, top_offset_delta, wall_type in [
    (+1, l_base, l_top, left_wall_type),
    (-1, r_base, r_top, right_wall_type)
]:
    total_offset = (struct_wall_thickness / 2.0) + (wall_type.Width / 2.0)
    offset = perp * total_offset * offset_sign
    transform = Transform.CreateTranslation(offset)
    new_curve = location_curve.CreateTransformed(transform)

    new_wall = Wall.Create(
        doc,
        new_curve,
        wall_type.Id,
        level.Id,
        10.0,
        struct_base_offset + base_offset_delta,
        False,
        False
    )

    new_wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE).Set(
        wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE).AsElementId()
    )
    new_wall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET).Set(
        struct_top_offset + top_offset_delta
    )

transaction.Commit()

TaskDialog.Show("Wall Sandwich", "Finish walls created!")










