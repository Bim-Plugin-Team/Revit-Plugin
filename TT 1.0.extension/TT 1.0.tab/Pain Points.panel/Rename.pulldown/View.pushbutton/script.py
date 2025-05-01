# -*- coding: utf-8 -*-
__title__   = "View"
__doc__     = """Version = 1.0
Date    = 22.04.2025
________________________________________________________________
Description:

To rename views
________________________________________________________________
How-To:

1. Click on the button
2. Select views
3. Define Renaming Rules
4. Rename Views
________________________________________________________________
Last Updates:
- [22.04.2025] v1.0 Release
________________________________________________________________
Author: Zwe"""

#Import

from Autodesk.Revit.DB import *
#pyrevit
from pyrevit import revit, forms

from rpw.ui.forms import (FlexForm, Label, TextBox, Separator, Button)

#.NET Imports
import clr
clr.AddReference('System')
from System.Collections.Generic import List


# Variable

app    = __revit__.Application
uidoc  = __revit__.ActiveUIDocument
doc    = __revit__.ActiveUIDocument.Document #type:Document


# Main


# Select Views

sel_ele_ids = uidoc.Selection.GetElementIds()
sel_elem = [doc.GetElement(e_id) for e_id in sel_ele_ids ]
sel_views = [el for el in sel_elem if issubclass(type(el), View)]

# If none selected - Select views from pyrevit forms

if not sel_views:
    sel_views = forms.select_views()

# Ensure Views Selected

if not sel_views:
    forms.alert('No Views Selected. Please Try Again', exitscript=True)

# Define renaming rule
components = [Label('Prefix:'),     TextBox('prefix'),
              Label('Find:'),       TextBox('find'),
              Label('Replace:'),    TextBox('replace'),
              Label('Suffix:'),     TextBox('suffix'),
              Separator(),          Button('Rename Views')           
              
              ]


form = FlexForm('Title', components)
form.show()

user_inputs = form.values


prefix  = user_inputs['prefix']
find    = user_inputs['find']
replace = user_inputs['replace']
suffix  = user_inputs['suffix']



t = Transaction (doc, 'Z_Rename Views')

t.Start()

for view in sel_views:

    #create new view name

    old_name  = view.Name
    new_name  = prefix + old_name.replace(find, replace) + suffix

    #rename views (Unique name)

    for i in range(20):
        try:

            view.Name = new_name
            print('{} -> {}' .format(old_name, new_name))

            break
        except:
            new_name += '*'


t.Commit()