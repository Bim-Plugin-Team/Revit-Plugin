# -*- coding: utf-8 -*-
__title__   = "Wall Length"
__doc__     = """Version = 1.0
Date    = 15.06.2024
________________________________________________________________
Description:


________________________________________________________________
Author: Zwe"""

from pyrevit import revit, script
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType
from Autodesk.Revit.UI import TaskDialog
import traceback


doc = revit.doc
uidoc = revit.uidoc
view = uidoc.ActiveView

# --- Step 1: Select a wall
try:
    ref = uidoc.Selection.PickObject(ObjectType.Element, "Select one wall")
    wall = doc.GetElement(ref)
    if not isinstance(wall, Wall):
        TaskDialog.Show("AutoDim", "Selected element is not a wall.")
        script.exit()
except:
    script.exit()

# --- Step 2: Get wall direction and reference faces
loc = wall.Location
if not hasattr(loc, 'Curve'):
    TaskDialog.Show("AutoDim", "Wall does not have a linear location curve.")
    script.exit()

curve = loc.Curve
start = curve.GetEndPoint(0)
end = curve.GetEndPoint(1)
vec = (end - start).Normalize()

is_vertical = abs(vec.X) < abs(vec.Y)
ref_dir = XYZ.BasisY if is_vertical else XYZ.BasisX

# --- Step 3: Gather face references from wall and inserts
options = Options()
options.ComputeReferences = True
options.IncludeNonVisibleObjects = False
options.DetailLevel = ViewDetailLevel.Fine

ref_data = []

# --- Collect face references from wall geometry
def collect_wall_face_refs(w):
    geo = w.get_Geometry(options)
    for obj in geo:
        solid = obj if isinstance(obj, Solid) else None
        if not solid: continue
        for face in solid.Faces:
            try:
                normal = face.ComputeNormal(UV(0.5, 0.5))
                if normal.IsAlmostEqualTo(ref_dir) or normal.IsAlmostEqualTo(-ref_dir):
                    ref = face.Reference
                    origin = face.Origin
                    offset = origin.X if is_vertical else origin.Y
                    if ref is not None and ref.ElementId.IntegerValue > 0:
                        ref_data.append((offset, ref))
            except:
                continue

collect_wall_face_refs(wall)

# --- Collect references from inserts (doors, windows, etc.)
inserts = wall.FindInserts(True, False, False, False)
for insert_id in inserts:
    insert = doc.GetElement(insert_id)
    if not insert:
        continue
    collect_wall_face_refs(insert)

# --- Collect references from joined walls
collector = FilteredElementCollector(doc, view.Id).OfClass(Wall).WhereElementIsNotElementType()
for other_wall in collector:
    if other_wall.Id == wall.Id:
        continue
    other_curve = other_wall.Location.Curve if hasattr(other_wall.Location, 'Curve') else None
    if not other_curve:
        continue
    if curve.Distance(other_curve.GetEndPoint(0)) < 0.01 or curve.Distance(other_curve.GetEndPoint(1)) < 0.01:
        collect_wall_face_refs(other_wall)

# --- Step 4: Sort and prepare reference array
if len(ref_data) < 2:
    TaskDialog.Show("AutoDim", "Could not find enough referenceable faces.")
    script.exit()

ref_data.sort(key=lambda x: x[0])
ref_array = ReferenceArray()
for _, ref in ref_data:
    ref_array.Append(ref)

# --- Step 5: Build dimension line
mid = curve.Evaluate(0.5, True)
z = mid.Z
min_offset = min(x[0] for x in ref_data) - 2
max_offset = max(x[0] for x in ref_data) + 2

if is_vertical:
    pt1 = XYZ(mid.X, min_offset, z)
    pt2 = XYZ(mid.X, max_offset, z)
else:
    pt1 = XYZ(min_offset, mid.Y, z)
    pt2 = XYZ(max_offset, mid.Y, z)

dim_line = Line.CreateBound(pt1, pt2)

# --- Step 6: Get recent dimension type
dim_type = None
last_dims = FilteredElementCollector(doc).OfClass(Dimension).ToElements()
if last_dims:
    recent = sorted(last_dims, key=lambda d: d.Id.IntegerValue, reverse=True)[0]
    dim_type = doc.GetElement(recent.GetTypeId())
if not dim_type:
    dim_types = FilteredElementCollector(doc).OfClass(DimensionType).ToElements()
    linear_types = [dt for dt in dim_types if getattr(dt, "StyleType", None) == DimensionStyleType.Linear]
    dim_type = linear_types[0] if linear_types else None
if not dim_type:
    TaskDialog.Show("AutoDim", "No dimension type found.")
    script.exit()

# --- Step 7: Create dimension
with revit.Transaction("Create Wall Length Dimension"):
    try:
        plane = Plane.CreateByNormalAndOrigin(XYZ.BasisZ, pt1)
        sketch_plane = SketchPlane.Create(doc, plane)
        view.SketchPlane = sketch_plane
        doc.Create.NewDimension(view, dim_line, ref_array, dim_type)
        print("✅ Dimension created successfully.")
    except Exception as e:
        print("❌ ERROR DURING DIMENSION CREATION:")
        print(traceback.format_exc())
        TaskDialog.Show("AutoDim", "❌ Failed to create dimension:\n{}".format(str(e)))
        script.exit()























































