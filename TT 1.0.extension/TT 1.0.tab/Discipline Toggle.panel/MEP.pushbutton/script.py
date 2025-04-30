# -*- coding: utf-8 -*-
__title__   = "MEP / Links"
__doc__     = """Version = 1.0
Date    = 25.04.2025
________________________________________________________________
Description:

MEP On/Off

"""

# import

from pyrevit import revit, script
from Autodesk.Revit.DB import *
import clr
from pyrevit import revit, DB, forms, script



# Start transaction
with revit.Transaction("Toggle Linked Revit Models"):
    # Collect all Revit Link Instances
    collector = DB.FilteredElementCollector(revit.doc).OfCategory(DB.BuiltInCategory.OST_RvtLinks).WhereElementIsNotElementType()
    links = collector.ToElements()

    if not links:
        forms.alert("No Revit Links found in the model.")
    else:
        # Check visibility by Category, safer way
        hidden_count = 0
        for link in links:
            if not revit.active_view.CanCategoryBeHidden(link.Category.Id):
                continue
            if revit.active_view.GetCategoryHidden(link.Category.Id):
                hidden_count += 1

        toggle_to_hide = hidden_count <= len(links) / 2

        for link in links:
            try:
                if revit.active_view.CanCategoryBeHidden(link.Category.Id):
                    revit.active_view.SetCategoryHidden(link.Category.Id, toggle_to_hide)
            except Exception as e:
                print("Failed on link '{}': {}".format(link.Name, e))
        
        status = "Hidden" if toggle_to_hide else "Visible"
        forms.alert("All Revit Links are now: {}".format(status))









