# -*- coding: utf-8 -*-
__title__   = "Sheet"
__doc__     = """Version = 1.0
Date    = 29.04.2025
________________________________________________________________
Description:


________________________________________________________________
Author: Zwe"""

from pyrevit import forms
from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet
from pyrevit import revit, DB

# Collect all sheets
sheets = FilteredElementCollector(revit.doc).OfCategory(DB.BuiltInCategory.OST_Sheets).WhereElementIsNotElementType().ToElements()

sheet_options = {sheet.SheetNumber + " - " + sheet.Name: sheet for sheet in sheets}

selected_sheets = forms.SelectFromList.show(
    sheet_options.keys(),
    multiselect=True,
    title='Select Sheet(s) to Rename'
)

if selected_sheets:
    # Ask whether to rename Sheet Name or Sheet Number
    rename_target = forms.SelectFromList.show(
        ["Sheet Name", "Sheet Number"],
        multiselect=False,
        title='What do you want to rename?'
    )

    if rename_target:
        # Ask for Find, Replace, Prefix, Suffix
        find_text = forms.ask_for_string(
            default='',
            prompt='Find text (leave blank if none):'
        )

        replace_text = forms.ask_for_string(
            default='',
            prompt='Replace with (leave blank if none):'
        )

        prefix_text = forms.ask_for_string(
            default='',
            prompt='Prefix to add (leave blank if none):'
        )

        suffix_text = forms.ask_for_string(
            default='',
            prompt='Suffix to add (leave blank if none):'
        )

        with revit.Transaction("Rename Sheets"):
            for selected in selected_sheets:
                sheet = sheet_options[selected]

                if rename_target == "Sheet Name":
                    current_value = sheet.Name
                else:
                    current_value = sheet.SheetNumber

                # Apply find and replace
                if find_text:
                    new_value = current_value.replace(find_text, replace_text)
                else:
                    new_value = current_value

                # Apply prefix and suffix
                new_value = prefix_text + new_value + suffix_text

                # Update the sheet property
                if rename_target == "Sheet Name":
                    sheet.Name = new_value
                else:
                    sheet.SheetNumber = new_value

        forms.alert("Sheets renamed successfully!", title="Done")

