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
selected_sheets = forms.select_sheets(title="Select up to 12 Sheets to pull Drawing Info")
if not selected_sheets:
    forms.alert("No sheets selected. Cancelling.", exitscript=True)

# Step 4: Collect info for each sheet
sheet_infos = []
for sheet in selected_sheets[:12]:
    number = sheet.LookupParameter("Sheet Number").AsString()
    title = sheet.LookupParameter("Sheet Name").AsString()

    # Get title block instance
    titleblocks = FilteredElementCollector(doc, sheet.Id).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsNotElementType().ToElements()
    if titleblocks:
        titleblock_inst = titleblocks[0]
        tb_type = doc.GetElement(titleblock_inst.GetTypeId())
        tb_name = tb_type.LookupParameter("Type Name").AsString() if tb_type.LookupParameter("Type Name") else "Unknown"
        size = "A1" if "A1" in tb_name else ("A3" if "A3" in tb_name else "?")

        # Use custom Revision parameter from title block instance
        try:
            rev = titleblock_inst.LookupParameter("Revision").AsString()
            if not rev:
                rev = "-"
        except:
            rev = "-"
    else:
        rev = "-"
        size = "?"

    sheet_infos.append((number, title, rev, size))

# Step 5: Start transaction
transaction = Transaction(doc, "Update RFA Form")
transaction.Start()

# Set parameters for each drawing slot
for i, info in enumerate(sheet_infos):
    index = i + 1
    no_param = form_instance.LookupParameter("Drawing_{}_No".format(index))
    title_param = form_instance.LookupParameter("Drawing_{}_Title".format(index))
    rev_param = form_instance.LookupParameter("Drawing_{}_Rev".format(index))
    size_param = form_instance.LookupParameter("Drawing_{}_Size".format(index))
    serial_param = form_instance.LookupParameter("Si.No_{}".format(index))

    if no_param:
        try:
            no_param.Set(info[0])
        except:
            pass
    if title_param:
        try:
            title_param.Set(info[1])
        except:
            pass
    if rev_param:
        try:
            rev_param.Set(info[2])
        except:
            pass
    if size_param:
        try:
            size_param.Set(info[3])
        except:
            pass
    if serial_param:
        try:
            serial_param.Set(str(index))
        except:
            pass

# Finalize
doc.Regenerate()
transaction.Commit()










