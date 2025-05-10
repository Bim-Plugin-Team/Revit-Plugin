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
import traceback

doc = revit.doc
uidoc = revit.uidoc
view = uidoc.ActiveView

def flatten(pt):
    return XYZ(pt.X, pt.Y, 0)

# --- Step 1: Select walls
try:
    wall_refs = uidoc.Selection.PickObjects(ObjectType.Element, "Select aligned walls (X or Y direction only)")
    walls = [doc.GetElement(r) for r in wall_refs if isinstance(doc.GetElement(r), Wall)]
    if len(walls) < 1:
        TaskDialog.Show("AutoDim", "Select at least one wall.")
        script.exit()
except:
    script.exit()

# --- Step 2: Check alignment direction
def get_wall_direction(wall):
    loc = wall.Location
    if hasattr(loc, 'Curve'):
        return loc.Curve.Direction.Normalize()
    return None

directions = [get_wall_direction(w) for w in walls if get_wall_direction(w) is not None]
if not directions:
    TaskDialog.Show("AutoDim", "Unable to read wall directions.")
    script.exit()

# Calculate average direction
x_count = sum(1 for d in directions if abs(d.X) > abs(d.Y))
y_count = sum(1 for d in directions if abs(d.Y) > abs(d.X))

if x_count > 0 and y_count > 0:
    TaskDialog.Show("AutoDim", "Please select walls aligned in the same direction (only X or only Y).")
    script.exit()

wall_direction = "X" if x_count > 0 else "Y"
face_normal_dir = XYZ.BasisY if wall_direction == "X" else XYZ.BasisX

# --- Step 3: Choose dimension type
dim_types = FilteredElementCollector(doc).OfClass(DimensionType).ToElements()
linear_types = [dt for dt in dim_types if getattr(dt, "StyleType", None) == DimensionStyleType.Linear]
dim_names = [dt.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString() for dt in linear_types]
dim_choice = forms.SelectFromList.show(dim_names, title="Select Dimension Type", button_name="Use")
if not dim_choice:
    script.exit()
dim_type = next(
    (dt for dt in linear_types if dt.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString() == dim_choice),
    None
)

# --- Step 4: Collect side faces
options = Options()
options.ComputeReferences = True
options.DetailLevel = ViewDetailLevel.Fine

ref_data = []

for wall in walls:
    geo = wall.get_Geometry(options)
    if not geo:
        continue
    for obj in geo:
        solid = obj if isinstance(obj, Solid) else None
        if not solid:
            continue
        for face in solid.Faces:
            try:
                norm = face.ComputeNormal(UV(0.5, 0.5)).Normalize()
                if norm.IsAlmostEqualTo(face_normal_dir) or norm.IsAlmostEqualTo(face_normal_dir.Negate()):
                    pt = face.Evaluate(UV(0.5, 0.5))
                    coord = pt.X if wall_direction == "Y" else pt.Y
                    ref_data.append((coord, face.Reference, pt))
            except:
                continue

if len(ref_data) < 2:
    TaskDialog.Show("AutoDim", "Could not find enough valid wall side faces.")
    script.exit()

# --- Step 5: Sort by coordinate
ref_data.sort(key=lambda x: x[0])
ref_array = ReferenceArray()
for c, ref, pt in ref_data:
    ref_array.Append(ref)

# --- Step 6: Build dimension line
mid_coord = sum([pt.Y if wall_direction == "Y" else pt.X for _, _, pt in ref_data]) / len(ref_data)
z = ref_data[0][2].Z
min_coord = min([c for c, _, _ in ref_data]) - 2
max_coord = max([c for c, _, _ in ref_data]) + 2

if wall_direction == "Y":
    pt1 = XYZ(min_coord, mid_coord, z)
    pt2 = XYZ(max_coord, mid_coord, z)
else:
    pt1 = XYZ(mid_coord, min_coord, z)
    pt2 = XYZ(mid_coord, max_coord, z)

dim_line = Line.CreateBound(pt1, pt2)

# --- Step 7: Create dimension
with revit.Transaction("Create Wall Dimension (X/Y Smart)"):
    try:
        plane = Plane.CreateByNormalAndOrigin(XYZ.BasisZ, pt1)
        sketch_plane = SketchPlane.Create(doc, plane)
        view.SketchPlane = sketch_plane
        doc.Create.NewDimension(view, dim_line, ref_array, dim_type)
        
    except Exception as e:
        print("❌ ERROR DURING DIMENSION CREATION:")
        print(traceback.format_exc())
        TaskDialog.Show("AutoDim", "❌ Failed to create dimension:\n{}".format(str(e)))
        script.exit()

































