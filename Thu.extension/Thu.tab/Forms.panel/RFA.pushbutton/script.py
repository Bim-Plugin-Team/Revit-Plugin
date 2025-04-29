# -*- coding: utf-8 -*-
__title__   = "RFA"
__doc__     = """Version = 1.0
Date    = 15.06.2024
________________________________________________________________
Description:


________________________________________________________________
Author: Zwe"""

from pyrevit import forms
from Autodesk.Revit.DB import *

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document

# Step 1: Collect all placed RFA Form instances in the model
form_instances = []
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_GenericAnnotation).WhereElementIsNotElementType()
for el in collector:
    if el.Symbol.FamilyName == "rfa_form_template":
        form_instances.append(el)

if not form_instances:
    forms.alert("No placed RFA Form instances found in the model.", exitscript=True)

# Step 2: Show dropdown list to select one
options = ["{} | Sheet: {}".format(el.Id.IntegerValue, doc.GetElement(el.OwnerViewId).Name) for el in form_instances]
selected = forms.SelectFromList.show(options, title="Select an RFA Form instance to update")

if not selected:
    forms.alert("No form selected. Exiting.", exitscript=True)

# Match selected string to element
selected_id = int(selected.split(" | ")[0])
form_instance = doc.GetElement(ElementId(selected_id))

# Step 3: Pick sheets to extract info
selected_sheets = forms.select_sheets(title="Select up to 2 Sheets to pull Drawing Info")
if not selected_sheets:
    forms.alert("No sheets selected. Cancelling.", exitscript=True)

sheet_infos = []
for sheet in selected_sheets[:2]:
    number = sheet.LookupParameter("Sheet Number").AsString()
    title = sheet.LookupParameter("Sheet Name").AsString()
    sheet_infos.append((number, title))

# Step 4: Start transaction
transaction = Transaction(doc, "Update RFA Form")
transaction.Start()

param_map = {
    "Drawing_1_No": sheet_infos[0][0] if len(sheet_infos) > 0 else None,
    "Drawing_1_Title": sheet_infos[0][1] if len(sheet_infos) > 0 else None,
    "Si.No_1": "1" if len(sheet_infos) > 0 else None,
    "Drawing_2_No": sheet_infos[1][0] if len(sheet_infos) > 1 else None,
    "Drawing_2_Title": sheet_infos[1][1] if len(sheet_infos) > 1 else None,
    "Si.No_2": "2" if len(sheet_infos) > 1 else None
}

for pname, pvalue in param_map.items():
    if pvalue is None:
        continue
    param = form_instance.LookupParameter(pname)
    if param:
        try:
            param.Set(pvalue)
        except Exception as e:
            forms.alert("Failed to set '{}': {}".format(pname, e))
    else:
        forms.alert("Parameter '{}' not found on the instance.".format(pname))

# Finalize and commit
doc.Regenerate()
transaction.Commit()







