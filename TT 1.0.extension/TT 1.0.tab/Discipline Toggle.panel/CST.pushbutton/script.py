# -*- coding: utf-8 -*-
__title__   = "CST"
__doc__     = """Version = 1.0
Date    = 25.04.2025
________________________________________________________________
Description:

CST On/Off

"""

# import
from pyrevit import revit, script
from Autodesk.Revit.DB import *

# variable

doc = revit.doc
view = revit.active_view


# main

# set filter name

filter_name = "CST on off"

# Start transaction
t = Transaction(doc, "Toggle Filter Visibility")
t.Start()

try:
    filters = view.GetFilters()
    for f_id in filters:
        f = doc.GetElement(f_id)
        if f.Name == filter_name:
            current_state = view.GetFilterVisibility(f_id)
            view.SetFilterVisibility(f_id, not current_state)
            
            break
    else:
        print("Filter not found in active view.")
except Exception as e:
    print("Error: {}".format(e))
finally:
    t.Commit()







