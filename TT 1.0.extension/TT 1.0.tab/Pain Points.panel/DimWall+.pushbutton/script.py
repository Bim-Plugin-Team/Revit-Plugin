# -*- coding: utf-8 -*-
__title__   = "DimWall+"
__doc__     = """Version = 1.0
Date    = 15.06.2024
________________________________________________________________
Description:


________________________________________________________________
Author: Zwe"""

from pyrevit import revit, forms, script
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog
from Autodesk.Revit.UI.Selection import ObjectType

doc = revit.doc
uidoc = revit.uidoc
view = uidoc.ActiveView

# --- Step 1: Select model or detail line
try:
    ref = uidoc.Selection.PickObject(ObjectType.Element, "Select a straight detail or model line")
    line_elem = doc.GetElement(ref)
    if not isinstance(line_elem, CurveElement):
        TaskDialog.Show("AutoDim", "Selected element is not a line.")
        script.exit()
    dim_line_3d = line_elem.GeometryCurve
except:
    script.exit()

# Flatten line to XY
def to2D(pt): return XYZ(pt.X, pt.Y, 0)
line_start = to2D(dim_line_3d.GetEndPoint(0))
line_end = to2D(dim_line_3d.GetEndPoint(1))
dim_line_2d = Line.CreateBound(line_start, line_end)
direction = (line_end - line_start).Normalize()

# --- Step 2: Filter linear dimension types
dim_types = FilteredElementCollector(doc).OfClass(DimensionType).ToElements()
linear_types = []
for dt in dim_types:
    try:
        if dt.StyleType == DimensionStyleType.Linear:
            linear_types.append(dt)
    except:
        continue

dim_names = [dt.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString() for dt in linear_types]
dim_choice = forms.SelectFromList.show(dim_names, title="Select Dimension Type", button_name="Use")
if not dim_choice:
    script.exit()
selected_dim_type = next(
    (dt for dt in linear_types if dt.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString() == dim_choice),
    None
)

# --- Step 3: Geometry setup
options = Options()
options.ComputeReferences = True
options.DetailLevel = ViewDetailLevel.Fine

tolerance_mm = 50
tolerance_ft = UnitUtils.ConvertToInternalUnits(tolerance_mm, UnitTypeId.Millimeters)

def point_to_line_distance(pt, a, b):
    v = pt - a
    d = b - a
    d_len = d.GetLength()
    if d_len < 1e-9:
        return v.GetLength()
    proj = v.DotProduct(d) / d_len
    closest = a + d.Normalize().Multiply(proj)
    return (pt - closest).GetLength()

# --- Step 4: Collect valid vertical edge references
seen_offsets = set()
ref_points = []

walls = FilteredElementCollector(doc, view.Id).OfClass(Wall).WhereElementIsNotElementType().ToElements()

for wall in walls:
    geo = wall.get_Geometry(options)
    if not geo:
        continue
    for obj in geo:
        solid = obj if isinstance(obj, Solid) else None
        if not solid:
            continue
        for edge in solid.Edges:
            try:
                curve = edge.AsCurve()
                p0 = curve.GetEndPoint(0)
                p1 = curve.GetEndPoint(1)
                dir = (p1 - p0).Normalize()

                # Vertical edge = mostly Z direction
                if abs(dir.Z) < 0.99:
                    continue

                # Get midpoint and flatten
                mid = (p0 + p1) / 2.0
                mid2d = to2D(mid)

                # Is edge close to line?
                dist = point_to_line_distance(mid2d, line_start, line_end)
                if dist > tolerance_ft:
                    continue

                # Project and sort
                vec = mid2d - line_start
                offset = round(vec.DotProduct(direction), 6)

                if offset not in seen_offsets:
                    ref_points.append((offset, edge.Reference))
                    seen_offsets.add(offset)

            except:
                continue

# --- Step 5: Build ReferenceArray
ref_points.sort(key=lambda x: x[0])
ref_array = ReferenceArray()
for d, ref in ref_points:
    ref_array.Append(ref)

print("Collected edge references:", ref_array.Size)

if ref_array.Size < 2:
    TaskDialog.Show("AutoDim", "Not enough valid edge references found.")
    script.exit()

# --- Step 6: Create Dimension
with revit.Transaction("Create Wall Chain Dimension (Edges)"):
    doc.Create.NewDimension(view, dim_line_3d, ref_array, selected_dim_type)





















