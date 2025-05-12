# -*- coding: utf-8 -*-
__title__   = "Sheets to CAD"
__doc__     = """Version = 1.0
Date    = 15.06.2024
________________________________________________________________
Description:


________________________________________________________________
Author: Zwe"""

import os
import clr
clr.AddReference('RevitServices')
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('Microsoft.VisualBasic')

from Autodesk.Revit.DB import *
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager
from System import Type, Activator
from System.Collections.Generic import List
from pyrevit import forms
from pyrevit import revit, script
from Autodesk.Revit.UI.Selection import ObjectType
from Autodesk.Revit.UI import TaskDialog
import traceback

# Collect document and UI
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument
doc = uidoc.Document

# 1. Ask user to select sheets
sheets = forms.select_sheets(title='Select Sheets to Export to DWG', multiple=True)
if not sheets:
    forms.alert("No sheets selected. Operation cancelled.", title="Cancelled")
    script.exit()

# 2. Ask user to select an existing DWG export setup
export_setup_name = forms.ask_for_string("Enter DWG export setup name (from Export Setup dialog)")
if not export_setup_name:
    forms.alert("No export setup provided.", title="Cancelled")
    script.exit()

# 3. Ask for folder to save final merged DWG
output_folder = forms.pick_folder(title="Select folder to save merged DWG")
if not output_folder:
    forms.alert("No output folder selected.", title="Cancelled")
    script.exit()

# 4. Export selected sheets to temporary folder
temp_folder = os.path.join(output_folder, "_temp_export")
os.makedirs(temp_folder)

collector = FilteredElementCollector(doc).OfClass(ExportDWGSettings)
dwg_setup = None
for s in collector:
    if s.Name == export_setup_name:
        dwg_setup = s
        break

if not dwg_setup:
    forms.alert("DWG export setup not found.", title="Error")
    script.exit()

view_ids = List[ElementId]([s.Id for s in sheets])
result = doc.Export(temp_folder, "", view_ids, dwg_setup)
if not result:
    forms.alert("DWG Export failed.", title="Error")
    script.exit()

# 5. Launch AutoCAD and merge DWGs
from System.Runtime.InteropServices import Marshal

dwg_files = [f for f in os.listdir(temp_folder) if f.lower().endswith('.dwg')]
if not dwg_files:
    forms.alert("No DWG files exported.", title="Error")
    script.exit()

try:
    acad_type = Type.GetTypeFromProgID("AutoCAD.Application")
    acad = Activator.CreateInstance(acad_type)
    acad.Visible = True
except Exception as e:
    forms.alert("Failed to launch AutoCAD: {}".format(e), title="Error")
    script.exit()

acad_doc = acad.Documents.Add()
offset_y = 0
for dwg_file in dwg_files:
    dwg_path = os.path.join(temp_folder, dwg_file)
    cmd = '_.-INSERT "{}" 0,{} 1 1 0 \n'.format(dwg_path.replace("\\", "\\\\"), offset_y)
    acad_doc.SendCommand(cmd)
    offset_y -= 420

# Save merged DWG
merged_path = os.path.join(output_folder, "MergedSheets.dwg")
try:
    acad_doc.SaveAs(merged_path)
    forms.alert("Merged DWG saved as:\n{}".format(merged_path), title="Success")
except Exception as e:
    forms.alert("Failed to save merged DWG: {}".format(e), title="Error")





