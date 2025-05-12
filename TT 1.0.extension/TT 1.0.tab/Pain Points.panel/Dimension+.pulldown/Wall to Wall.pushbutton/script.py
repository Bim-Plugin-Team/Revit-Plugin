# -*- coding: utf-8 -*-
__title__   = "Wall To Wall"
__doc__     = """Version = 1.0
Date    = 15.06.2024
________________________________________________________________
Description:


________________________________________________________________
Author: Zwe"""

from pyrevit import revit, forms, script
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog
import traceback

doc = revit.doc
uidoc = revit.uidoc
view = uidoc.ActiveView

def get_wall_direction(wall):
    loc = wall.Location
    if hasattr(loc, 'Curve'):
        return loc.Curve.Direction.Normalize()
    return None

# --- Step 1: Require pre-selected walls
selected_ids = uidoc.Selection.GetElementIds()
if not selected_ids:
    TaskDialog.Show("AutoDim", "Please select wall(s) in the model first.")
    script.exit()

walls = [doc.GetElement(eid) for eid in selected_ids if isinstance(doc.GetElement(eid), Wall)]
if len(walls) < 1:
    TaskDialog.Show("AutoDim", "No valid walls selected.")
    script.exit()

# --- Step 2: Build filter lists (type + level only)
type_map = {}
level_map = {}

for wall in walls:
    try:
        wtype = wall.WallType
        if not wtype:
            continue
        try:
            tname = wtype.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
            if not tname:
                tname = wtype.Name
        except:
            tname = wtype.Name

        level = wall.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT).AsValueString()

        if tname:
            type_map[tname] = wtype.Id
        if level:
            level_map[level] = level
    except:
        continue

if not type_map:
    TaskDialog.Show("AutoDim", "No wall types could be read from selection.")
    script.exit()

# --- Step 3: Show filter UI (only type + level)
type_names = sorted(type_map.keys())
level_names = sorted(level_map.keys())

picked_types = forms.SelectFromList.show(type_names, multiselect=True, title="Filter: Wall Type")
if not picked_types: script.exit()
picked_levels = forms.SelectFromList.show(level_names, multiselect=True, title="Filter: Base Level")
if not picked_levels: script.exit()

selected_type_ids = [type_map[name] for name in picked_types]
selected_levels = picked_levels

# --- Step 4: Apply filters
filtered_walls = []
for wall in walls:
    try:
        if wall.WallType.Id not in selected_type_ids:
            continue
        level = wall.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT).AsValueString()
        if level not in selected_levels:
            continue
        filtered_walls.append(wall)
    except:
        continue

if len(filtered_walls) < 1:
    TaskDialog.Show("AutoDim", "No walls match the selected filters.")
    script.exit()

# --- Step 5: Determine wall direction
dirs = [get_wall_direction(w) for w in filtered_walls if get_wall_direction(w)]
x_count = sum(1 for d in dirs if abs(d.X) > abs(d.Y))
y_count = sum(1 for d in dirs if abs(d.Y) > abs(d.X))
wall_direction = "X" if x_count >= y_count else "Y"
face_normal_dir = XYZ.BasisY if wall_direction == "X" else XYZ.BasisX
neg_face_normal_dir = XYZ(-face_normal_dir.X, -face_normal_dir.Y, -face_normal_dir.Z)

# --- Step 6: Use most recent dimension type
dim_type = None
last_dims = FilteredElementCollector(doc).OfClass(Dimension).ToElements()
if last_dims:
    recent_dim = sorted(last_dims, key=lambda d: d.Id.IntegerValue, reverse=True)[0]
    dim_type = doc.GetElement(recent_dim.GetTypeId())

if not dim_type or not isinstance(dim_type, DimensionType):
    dim_types = FilteredElementCollector(doc).OfClass(DimensionType).ToElements()
    linear_types = [dt for dt in dim_types if getattr(dt, "StyleType", None) == DimensionStyleType.Linear]
    if not linear_types:
        TaskDialog.Show("AutoDim", "No linear dimension types found.")
        script.exit()
    dim_type = linear_types[0]

# --- Step 7: Collect wall face references
options = Options()
options.ComputeReferences = True
options.DetailLevel = ViewDetailLevel.Fine

ref_data = []

for wall in filtered_walls:
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
                if norm.IsAlmostEqualTo(face_normal_dir) or norm.IsAlmostEqualTo(neg_face_normal_dir):
                    pt = face.Evaluate(UV(0.5, 0.5))
                    coord = pt.X if wall_direction == "Y" else pt.Y
                    ref_data.append((coord, face.Reference, pt))
            except:
                continue

if len(ref_data) < 2:
    TaskDialog.Show("AutoDim", "Not enough wall faces found for dimensioning.")
    script.exit()

# --- Step 8: Build sorted reference array
ref_data.sort(key=lambda x: x[0])
ref_array = ReferenceArray()
for _, ref, _ in ref_data:
    ref_array.Append(ref)

mid_pt = ref_data[len(ref_data)//2][2]
z = mid_pt.Z
min_val = min([v[0] for v in ref_data]) - 2
max_val = max([v[0] for v in ref_data]) + 2

if wall_direction == "Y":
    pt1 = XYZ(min_val, mid_pt.Y, z)
    pt2 = XYZ(max_val, mid_pt.Y, z)
else:
    pt1 = XYZ(mid_pt.X, min_val, z)
    pt2 = XYZ(mid_pt.X, max_val, z)

dim_line = Line.CreateBound(pt1, pt2)

# --- Step 9: Create the dimension
with revit.Transaction("Create Wall Dimension"):
    try:
        plane = Plane.CreateByNormalAndOrigin(XYZ.BasisZ, pt1)
        sketch_plane = SketchPlane.Create(doc, plane)
        view.SketchPlane = sketch_plane
        doc.Create.NewDimension(view, dim_line, ref_array, dim_type)
        
    except Exception as e:
        print("❌ ERROR during dimension:")
        print(traceback.format_exc())
        TaskDialog.Show("AutoDim", "❌ Failed to create dimension:\n{}".format(str(e)))
        script.exit()















































