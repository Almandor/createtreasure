#!/usr/bin/python3
# -*- coding: UTF8 -*-


'''
Programname: createtrasures.py
Description: Rolemaster-Support tool to generate Treasure

ToDo: Find Error UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d in position 325: character maps to <undefined> -> FIXED (hopefully, with encoding='utf8', errors='ignore')
ToDo: Add Sp. Bonusitems -> FIXED
# Todo: if key == "Spells": Spells ausgeben -> Partially addressed via ItemAndMoneyStore restructuring
'''

import argparse
import csv
import random
from sys import exit
import pprint
from os import path, remove, walk
import logging
import json

# --- Helper function for CSV cleaning ---
def clean_csv_string(text):
    """Removes specified template artifacts and strips whitespace."""
    if not isinstance(text, str): # Ensure input is a string
        text = str(text)
    artifacts = ["\\textdaggerdbl", "\\ddagger", "\\textasteriskcentered"]
    cleaned_text = text
    for artifact in artifacts:
        cleaned_text = cleaned_text.replace(artifact, "")
    # Remove potential multiple spaces left after replacement
    cleaned_text = ' '.join(cleaned_text.split())
    return cleaned_text.strip()
# -----------------------------------------


class DeliverItemFromFile:
    '''
    Läd das equipment und liefert einen Gegenstand basierend auf übergebener Parameter zurück.
    Parameter betreffen Typ (armor, weapon...) und / oder Gewichtkategorie (rod, staff, wand...)
    Für jeden Parameter kann RANDOM übergeben werden und die Klasse sucht sich per Zufall einen Gegenstand aus.
    '''
    def __init__(self, logger): # Added logger
        self.filepath = './data/equipment/'
        self.datafiles = []
        self.datastore = {}
        self.logger = logger
        self.lookupfiles()
        self.readdata()
        self.sampleweights = [("rod", 2), ("wand", 0.5), ("staff", 5)] # Currently unused?

    def lookupfiles(self):
        self.logger.info(f"Looking for equipment CSVs in: {self.filepath}")
        try:
            for root, dirs, files in walk(self.filepath):
                # print(dirs) # Debug
                # print(files) # Debug
                for file in files:
                    if file.endswith(".csv"):
                        self.logger.debug(f"Found equipment file: {file}")
                        self.datafiles.append(file)
        except FileNotFoundError:
            self.logger.error(f"Equipment directory not found: {self.filepath}")
            print(f"ERROR: Equipment directory not found: {self.filepath}")
            exit(1)


    def readdata(self):
        if not self.datafiles:
            self.logger.warning("No equipment data files found to load.")
            return

        for file in self.datafiles:
            self.temp = []
            self.counter = 0
            full_path = path.join(self.filepath, file)
            self.logger.info(f"Reading equipment data from: {full_path}")
            try:
                # Use utf8 encoding for broader compatibility
                with open(full_path, "r", encoding='utf8', errors='ignore') as f:
                    for row in f:
                        self.counter += 1
                        if self.counter == 1: # Skip header row
                            continue
                        # Clean the raw row and split
                        self.shorttemp = row.strip("\n").strip(" lbs.") # Original cleaning
                        # Apply artifact cleaning to each element after splitting
                        try:
                            cleaned_tuple = tuple(clean_csv_string(item) for item in self.shorttemp.split(","))
                            self.temp.append(cleaned_tuple)
                        except Exception as e:
                             self.logger.error(f"Error processing row {self.counter} in {file}: '{row.strip()}' - {e}")

            except FileNotFoundError:
                 self.logger.error(f"Could not open equipment file: {full_path}")
                 continue # Skip to next file if one is missing
            except Exception as e:
                 self.logger.error(f"Error reading file {full_path}: {e}")
                 continue

            # Store data using filename without extension as key
            data_key = path.splitext(file)[0]
            self.datastore[data_key] = self.temp
            self.logger.info(f"Loaded {len(self.temp)} items into datastore key '{data_key}'")

    def output(self, etype):
        original_etype = etype
        if not self.datastore:
            self.logger.error("Cannot provide item, equipment datastore is empty.")
            return "Error: No equipment data loaded"

        if etype == "weapon":
            etype = "weapons" # Normalize to expected key name

        if etype == "random":
            # Use keys from the loaded datastore, not just potential filenames
            typelist = list(self.datastore.keys())
            if not typelist:
                 self.logger.error("Cannot select random type, equipment datastore is empty.")
                 return "Error: No equipment types loaded"
            etype = random.choice(typelist)
            self.logger.info(f"Randomly selected equipment type: {etype}")

        # Check if the selected type (or the original) exists in the datastore
        if etype not in self.datastore:
            self.logger.error(f"Equipment type '{etype}' (requested: '{original_etype}') not found in loaded data.")
            # Fallback: try to return a random item from *any* loaded list
            if self.datastore:
                etype = random.choice(list(self.datastore.keys()))
                self.logger.warning(f"Falling back to random type: {etype}")
            else:
                return f"Error: Type '{etype}' not loaded"


        if not self.datastore[etype]: # Check if the list for the type is empty
             self.logger.error(f"No items available for equipment type '{etype}'.")
             return f"Error: No items for type '{etype}'"

        selected_index = random.randint(0, len(self.datastore[etype]) - 1)
        selected_item_tuple = self.datastore[etype][selected_index]

        # Assuming the item name is the first element in the tuple
        if selected_item_tuple:
            item_name = selected_item_tuple[0]
            self.logger.debug(f"Selected item: '{item_name}' from type '{etype}'")
            return item_name
        else:
            self.logger.error(f"Selected empty tuple at index {selected_index} for type '{etype}'")
            return "Error: Selected empty item data"


class Filewriter:
    def __init__(self):
        self.items = [] # Initialize as list
        self.money = {}
        self.final = [] # This will hold the final dicts { "items": [...] } and { "money": {...} }

    def add(self, element, value):
        if element == "items":
            # Expecting value to be the list of item dicts
            if isinstance(value, list):
                 self.items = value
            else:
                 # Log error or handle unexpected type
                 print(f"Error: Expected list for items, got {type(value)}")
        elif element == "money":
             # Expecting value to be the money dict
            if isinstance(value, dict):
                 self.money = value
            else:
                 # Log error
                 print(f"Error: Expected dict for money, got {type(value)}")


    def finalize(self):
        # Only add sections if they have content
        if self.items: # Check if the list is not empty
            self.final.append({"items": self.items})
        if self.money: # Check if the dict is not empty
             # Ensure money dict itself is properly nested if needed by structure
            # Assuming self.money structure is {"mithril": X, "gold": Y,...}
            # and the desired output is {"money": {"mithril": X, ...}}
            if "money" not in self.money: # Check if it's already nested
                self.final.append({"money": self.money})
            else: # It was already nested by getmoney()
                self.final.append(self.money)

        if not self.final:
            print("Warning: No treasure generated to write.")
            return

        try:
            # Use "w" (write) mode since the file is deleted earlier
            with open("treasure.json", "w", encoding='utf8') as outfile:
                json.dump(self.final, outfile, indent=4, ensure_ascii=False) # ensure_ascii=False for non-latin chars
            print("Treasure data written to treasure.json")
        except Exception as e:
            print(f"Error writing treasure.json: {e}")


class ItemAndMoneyStore:
    def __init__(self):
        self.money = {
            "mithril": 0,
            "gold": 0,
            "silber": 0, # Keep original names for consistency
            "bronze": 0,
            "kupfer": 0,
            "zinn": 0,
            "edelsteine": 0, # Keep original names
            "schmuckstücke": 0 # Keep original names
        }
        self.conversion = {
            "MS": "mithril",
            "GS": "gold",
            "SS": "silber",
            "BS": "bronze",
            "KS": "kupfer",
            "ZS": "zinn",
            "Ed": "edelsteine",
            "Sch": "schmuckstücke"
        }
        self.itemlist = [] # List to store Item objects
        # Order for output JSON
        self.moneyorderlist = ["mithril", "gold", "silber", "bronze", "kupfer", "zinn", "edelsteine", "schmuckstücke"]

    def additem(self, item_obj): # Pass the actual Item object
        self.itemlist.append(item_obj)

    def addmoney(self, typ, amount):
        if typ in self.conversion:
            money_key = self.conversion[typ]
            if isinstance(amount, (int, float)):
                 self.money[money_key] += amount
            else:
                 # Log error - amount is not a number
                 print(f"Warning: Invalid amount '{amount}' for money type '{typ}'. Skipping.")
        else:
            # Log error - unknown type
            print(f"Warning: Unknown money type code '{typ}'. Skipping.")

    def getmoney(self):
        # Filter out zero amounts and maintain order
        mymoneydict = {}
        for key in self.moneyorderlist:
            if key in self.money and self.money[key] > 0:
                # Convert amounts to string for JSON consistency if desired, or keep as numbers
                mymoneydict[str(key)] = str(self.money[key]) # Converting to string as in original

        # Return the nested structure directly expected by Filewriter
        if mymoneydict:
             return {"money": mymoneydict}
        else:
             return {} # Return empty dict if no money


    def getitems(self):
        output_itemlist = []
        item_counter = 0
        for item_obj in self.itemlist:
            item_counter += 1
            item_data = item_obj.getitem() # Get the dictionary from the Item object

            # Create a dictionary for the current item
            current_item_dict = {}

            for key, value in item_data.items():
                if key == "spells" and isinstance(value, list):
                    # Process list of Spell objects
                    spell_output_list = [] # Store processed spell dicts
                    spell_counter = 0
                    for spell_obj in value:
                        spell_counter += 1
                        if hasattr(spell_obj, 'output') and callable(spell_obj.output):
                            spell_data = spell_obj.output()
                            # Clean spell data and convert values to strings
                            cleaned_spell_data = {str(k): str(v) for k, v in spell_data.items()}
                            # Add a unique key like spell_1, spell_2 within the item dict (alternative structure)
                            # current_item_dict[f"spell_{spell_counter}"] = cleaned_spell_data
                            # OR append to a list under the "spells" key (more standard structure)
                            spell_output_list.append(cleaned_spell_data)
                        else:
                             print(f"Warning: Item {item_counter} has a non-Spell object in its 'spells' list.")

                    if spell_output_list:
                         current_item_dict["spells"] = spell_output_list # Store list of spell dicts

                else:
                    # Convert other values to string for JSON consistency
                    current_item_dict[str(key)] = str(value)

            # Append the complete dictionary for the current item to the output list
            if current_item_dict: # Only append if item has data
                output_itemlist.append(current_item_dict)

        print(f"Processed {item_counter} items for output.")
        # Return just the list of item dictionaries
        return output_itemlist


class Item:

    class Spell:
        def __init__(self, itemtype, logger): # Added logger
            self.logger = logger
            self.data = {
                "Spelllist": "", "Listcategory": "", "Spellcategory": "",
                "Level": "", "Description": "", "Uses": "", # Uses needs to be set somewhere if applicable
                "Itemtype": itemtype, "Name": "", "AoE": "None",
                "Duration": "None", "Type": "None", "Range": "None"
            }

        def fill(self):
            # Ensure helper functions get the logger if they need it
            buffer = getspelllist(self.logger) # Pass logger
            self.data["Spelllist"] = buffer.get("Spelllist", "Error: Spelllist missing")
            self.data["Listcategory"] = buffer.get("listcategory", "Error: listcategory missing")
            self.data["Spellcategory"] = buffer.get("Category", "Error: Category missing")
            self.data["Level"] = getspelllevel(translatespellcapacity(self.data["Itemtype"]), self.logger) # Pass logger

            # retrievespell needs logger to pass to getspellfromfile
            self.buffer = retrievespell(self.data["Listcategory"], self.data["Spelllist"],
                                        self.data["Level"], self.data["Spellcategory"], self.logger)

            if isinstance(self.buffer, dict):
                # Use .get() for safer access, provide default/original values if key missing
                self.data["Level"] = self.buffer.get("Lvl", self.data["Level"]) # Prefer Lvl from file if present
                self.data["Duration"] = self.buffer.get("Duration", self.data["Duration"])
                self.data["Name"] = self.buffer.get("Spell", self.data["Name"])
                self.data["AoE"] = self.buffer.get("Area of Effect", self.data["AoE"])
                self.data["Range"] = self.buffer.get("Range", self.data["Range"])
                # Description might be multi-line or contain details, keep it
                self.data["Description"] = self.buffer.get("Description", "No description found.")
                # Also capture Type if present in CSV
                self.data["Type"] = self.buffer.get("Type", self.data["Type"])

            elif isinstance(self.buffer, str): # Handle error strings from retrievespell
                self.data["Description"] = self.buffer # Put the error message in Description
                self.data["Name"] = "Error retrieving spell"
                self.logger.error(f"Spell retrieval failed: {self.buffer}")
            else:
                self.data["Description"] = "Failed to retrieve spell details (Unknown error)"
                self.data["Name"] = "Error retrieving spell"
                self.logger.error(f"Spell retrieval failed with unexpected buffer type: {type(self.buffer)}")


        def output(self):
            # Return a copy to prevent modification of internal state if needed
            return self.data.copy()

    def __init__(self, itemtype, logger):
        # Get an instance of DeliverItemFromFile (requires logger)
        getnormalitem = DeliverItemFromFile(logger)
        self.logger = logger
        self.item = {
            "base_item_type_from_table": "None", # Helps track origin if needed
            "itemtype": itemtype # The initial type (Bonus, Spell, Normal, etc.)
        }
        self.logger.info(f"Creating Item, initial type: {itemtype}")

        # Determine base item type early if needed, store separately?
        base_item_set = False # Flag to track if a base item (weapon, armor etc.) is set

        # Determine additional capabilities
        if self.item["itemtype"].lower() in ["bonus", "light", "sp. bonus"]:
             # Pass logger to getadditionalmagicitemcapabilities if it needs it
            additional_caps = getadditionalmagicitemcapabilities(self.item["itemtype"])
            self.capabilities = [self.item["itemtype"]] + additional_caps
            self.logger.debug(f"Item capabilities: {self.capabilities}")
        else:
            self.capabilities = [self.item["itemtype"]]

        # Process capabilities
        for capability in self.capabilities:
            cap_lower = capability.lower()
            self.logger.debug(f"Processing capability: {capability}")

            # --- Set Base Item Type if not already set and required by capability ---
            if not base_item_set and cap_lower in ['bonus', 'light', 'sp. bonus', 'spell']:
                temp_base_type = "Error"
                if cap_lower in ['bonus', 'light']:
                    temp_base_type = getitemfrommagicitemscapabilitieschart("TYPE B", self.logger) # Corrected call
                elif cap_lower == 'sp. bonus':
                    temp_base_type = getitemfrommagicitemscapabilitieschart("TYPE A", self.logger) # Corrected call
                elif cap_lower == 'spell':
                     # Spell items get type from a different table
                    temp_base_type = getrandomitemtype(self.logger) # Pass logger

                # Check if a valid type was returned and it's not just a category like "Weapon"
                if temp_base_type and temp_base_type != "Special":
                    # Store this as the 'actual' item being enchanted
                    self.item["base_item"] = temp_base_type
                    self.item["base_item_type_from_table"] = temp_base_type # Track origin
                    base_item_set = True
                    self.logger.info(f"Base item type set to: {temp_base_type} based on {capability}")
                elif temp_base_type == "Special":
                     self.logger.warning(f"Got 'Special' base item type for capability {capability}. Needs manual handling.")
                     self.item["base_item"] = "Special (Requires Manual Definition)"
                     base_item_set = True # Mark as handled
                else:
                     self.logger.error(f"Failed to determine base item type for capability {capability}")

            # --- Apply Capability Effect ---
            if cap_lower == 'bonus':
                bonus_value = getitemfrommagicitemscapabilitieschart("Bonus", self.logger) # Corrected call
                self.item[self.getlastelement("bonus")] = bonus_value
                self.logger.debug(f"Added bonus: {bonus_value}")

            elif cap_lower == 'sp. bonus':
                # Fetch and add the actual special bonus effect
                sp_bonus_value = getitemfrommagicitemscapabilitieschart("Sp. Bonus", self.logger) # Corrected call
                self.item[self.getlastelement("sp_bonus")] = sp_bonus_value # FIXED
                self.logger.debug(f"Added special bonus: {sp_bonus_value}")

            elif cap_lower == 'light':
                 # Fetch and add the weight reduction
                reduction_value = getitemfrommagicitemscapabilitieschart("Light", self.logger) # Corrected call
                # Store it meaningfully
                self.item["weight_reduction"] = reduction_value
                self.logger.debug(f"Added weight reduction: {reduction_value}")

            elif cap_lower == 'spell':
                if 'spells' not in self.item:
                    self.item["spells"] = [] # Initialize list to hold Spell objects

                # Create and fill the Spell object
                # Pass logger to Spell constructor
                buffer = self.Spell(self.item.get("base_item", self.item["itemtype"]), self.logger)
                buffer.fill() # This determines the spell details
                self.item["spells"].append(buffer) # Add the filled Spell object
                self.logger.debug(f"Added spell: {buffer.data.get('Name', 'Unknown')}")

            elif cap_lower == 'normal':
                # If base wasn't set by magic, get a normal item
                if not base_item_set:
                    normal_item = getnormalitem.output("random")
                    self.item["base_item"] = normal_item
                    self.item["base_item_type_from_table"] = "Normal (Random)"
                    base_item_set = True
                    self.logger.info(f"Base item type set to normal random: {normal_item}")
                else:
                     self.logger.debug("Base item already set, ignoring 'Normal' capability.")

            # Special handling for weapon types from chart vs. normal items
            # The chart might return "Weapon" or "1-H Slashing", etc.
            # We need to resolve this to a specific weapon name if possible.
            if base_item_set and self.item.get("base_item") == "Weapon":
                specific_weapon = getnormalitem.output("weapon") # Get a random weapon name
                self.item["base_item"] = specific_weapon
                self.logger.info(f"Resolved 'Weapon' base type to specific: {specific_weapon}")
            # Could add more specific mappings here if needed (e.g., "1-H Slashing" -> fetch from a filtered list)

        # Final cleanup/check - Ensure there's a base item description
        if not base_item_set and "base_item" not in self.item:
             self.logger.warning(f"Item finished processing capabilities but no base item was set. Initial type: {self.item['itemtype']}. Assigning generic.")
             # Assign a default or handle as error?
             self.item["base_item"] = f"Undefined Item ({self.item['itemtype']})"


    def getitem(self):
        # Return a copy of the item dictionary
        return self.item.copy()

    def getlastelement(self, type_prefix):
        """ Finds the next available key like 'bonus_1', 'bonus_2' """
        # Check if the base key exists first
        if type_prefix not in self.item:
            return type_prefix
        # If base key exists, find the next numbered suffix
        counter = 1
        while True:
            key = f"{type_prefix}_{counter}"
            if key not in self.item:
                return key
            counter += 1
            if counter > 99: # Safety break
                 self.logger.error(f"Too many elements with prefix {type_prefix}, stopping.")
                 return f"{type_prefix}_error"


class Controller:
    def __init__(self, selection, quality, logger):
        self.selection = selection
        self.quality = quality
        self.mais = ItemAndMoneyStore()
        self.logger = logger
        self.logger.info(f"Controller started. Selection: '{selection}', Quality: {quality}")

        # Delete existing file before generation
        self.deletefile()

        self.filewriter = Filewriter()

        # Generate Magic Items
        if self.selection.lower() in ["magic", "both"]:
            self.logger.info("Starting magic item generation...")
            self.magicitems()
            # Add generated items to filewriter (getitems returns the list)
            items_data = self.mais.getitems()
            if items_data:
                self.filewriter.add("items", items_data)
            else:
                 self.logger.info("No magic items generated.")


        # Generate Money
        if self.selection.lower() in ["money", "both"]:
            self.logger.info("Starting money generation...")
            # Validate quality for money generation
            if not self.quality or not 1 <= int(self.quality) <= 5:
                self.logger.error(f"Invalid Treasure Quality '{self.quality}'. Must be 1-5 for money generation.")
                print("ERROR: Please provide Treasure Quality between 1 and 5 for money/both.")
                # Decide whether to exit or just skip money generation
                # exit(1) # Option: Exit program
                pass # Option: Skip money generation
            else:
                self.money()
                 # Add generated money to filewriter (getmoney returns the dict)
                money_data = self.mais.getmoney()
                if money_data:
                    self.filewriter.add("money", money_data) # Pass the {"money": {...}} dict
                else:
                    self.logger.info("No money generated.")

        # Finalize and write the JSON file
        self.logger.info("Finalizing treasure generation.")
        self.filewriter.finalize()
        self.logger.info("Treasure generation complete.")


    def deletefile(self):
        if path.exists("treasure.json"):
            try:
                remove("treasure.json")
                self.logger.info("Deleted existing treasure.json")
            except OSError as e:
                self.logger.error(f"Error deleting treasure.json: {e}")
                print(f"Warning: Could not delete existing treasure.json: {e}")


    def magicitems(self):
        # Pass logger to helper functions
        rollnumber = getrichness(self.logger) # List of counts per richness level
        total_items_generated = 0
        # The list index corresponds to richness level (0=lowest)
        for richness_level, count in enumerate(rollnumber):
            if count > 0:
                self.logger.info(f"Generating {count} item(s) at richness level {richness_level}")
                for _ in range(count): # Generate 'count' items for this level
                    # Pass logger to getcomposition and Item constructor
                    item_type = getcomposition(richness_level, self.logger)
                    if item_type: # Ensure a valid type was returned
                        new_item = Item(item_type, self.logger)
                        self.mais.additem(new_item) # Add the Item object
                        total_items_generated += 1
                    else:
                        self.logger.error(f"Failed to get composition for richness level {richness_level}")

        self.logger.info(f"Finished magic item generation. Total items created: {total_items_generated}")


    def money(self):
        # Pass logger to helper functions
        roll_count = getnumberofrolls(self.logger)
        total_parcels = 0
        self.logger.info(f"Generating {roll_count} parcel(s) of money/valuables.")

        for i in range(roll_count): # Corrected range
            amount, typ = getmoney(self.quality, self.logger)
            if amount > 0: # Only add if there's an amount
                self.mais.addmoney(typ, amount)
                total_parcels +=1
            else:
                 self.logger.debug(f"Generated zero amount for money type '{typ}' on roll {i+1}.")

        self.logger.info(f"Finished money generation. Total non-zero parcels added: {total_parcels}")


# --- Global Helper Functions ---

def getnumberofrolls(logger):
    '''
    Randomizes number of roles from Wealth Treasure Size Chart.
    Returns Result
    :return: Integer number of rolls
    '''
    logger.info("Determining number of wealth rolls...")
    numberofrolls_table = ( # Renamed for clarity
                     ((1, 30), 1),
                     ((31, 55), 2),
                     ((56, 75), 3),
                     ((76, 90), 4),
                     ((91, 97), 5),
                     ((98, 99), 6),
                     ((100, 100), 7))

    roll = random.randint(1, 100)
    logger.debug(f"Wealth size roll: {roll}")
    for i in numberofrolls_table:
        if i[0][0] <= roll <= i[0][1]:
            num_rolls = i[1]
            logger.info(f"Number of Rolls determined: {num_rolls}")
            return num_rolls
    logger.error("Failed to determine number of rolls (logic error in table?). Defaulting to 1.")
    return 1 # Should not happen with a 1-100 table


def translatespellcapacity(itemtype):
    """ Maps item type string to spell capacity category. """
    # Be more robust, check lower case
    itemtype_lower = str(itemtype).lower() if itemtype else ""

    wand = ["wand"]
    rod = ["rod"]
    staff = ["staff"]
    other = ["constant", "daily", "singleuse", "runepaper", "potion",
             "daily1", "daily2", "daily3", "daily4"] # Add daily variations

    # Check specific types first
    if any(s in itemtype_lower for s in wand): return "wand"
    if any(s in itemtype_lower for s in rod): return "rod"
    if any(s in itemtype_lower for s in staff): return "staff"
    # Check broader categories
    if any(s in itemtype_lower for s in other):
        # Find which specific 'other' type it is
        for s in other:
            if s in itemtype_lower:
                return s
    # If none match, log an error and return a default/error value
    # print(f"Warning: Unknown Itemtype for spell capacity: {itemtype}") # Replaced with logging if logger available
    # Consider logging this error instead of printing
    return "unknown" # Return a value indicating failure


def getrichness(logger):
    '''
    Returns random result from "Magic Item Treasure Size Chart"
    :return: List of integers representing counts for each richness level [lvl0, lvl1, ..., lvl4]
    '''
    logger.info("Determining magic item richness distribution...")
    richnesstable = (
        ((1, 20), [0, 0, 0, 0, 2]), # Corrected range from original code example
        ((21, 40), [0, 0, 0, 1, 2]),
        ((41, 55), [0, 0, 1, 2, 2]),
        ((56, 70), [0, 1, 1, 2, 3]),
        ((71, 80), [0, 1, 2, 2, 3]),
        ((81, 90), [1, 1, 2, 3, 4]),
        ((91, 94), [1, 2, 3, 3, 4]),
        ((95, 97), [2, 3, 4, 4, 6]),
        ((98, 99), [3, 4, 5, 6, 8]),
        ((100, 100), [4, 5, 6, 8, 10])
    )
    roll = random.randint(1, 100)
    logger.debug(f"Richness table roll: {roll}")
    for select in richnesstable:
        if select[0][0] <= roll <= select[0][1]:
            item_counts = select[1]
            logger.info(f"Richness distribution determined: {item_counts}")
            return item_counts
    logger.error("Failed to determine richness (logic error in table?). Defaulting to [0,0,0,0,0].")
    return [0, 0, 0, 0, 0] # Should not happen


def getcomposition(richness_level, logger):
    '''
    Returns Random Result from "Magic Item Treasure Composition Table" based on richness level.
    :param richness_level: Integer index (0-4) corresponding to the level from getrichness list.
    :return: String Magic item Type (e.g., "Bonus", "Spell", "Normal") or None on error.
    '''
    logger.info(f"Getting composition for richness level: {richness_level}")

    treasurecompositiontable = (
        # Roll Range, [Level 0, Level 1, Level 2, Level 3, Level 4] results
        ((1, 5), ["Normal", "Normal", "Normal", "Normal", "Normal"]),
        ((6, 10), ["Normal", "Normal", "Normal", "Light", "Light"]),
        ((11, 20), ["Normal", "Normal", "Light", "Light", "Light"]),
        ((21, 30), ["Normal", "Light", "Light", "Light", "Spell"]),
        ((31, 40), ["Light", "Light", "Light", "Bonus", "Spell"]),
        ((41, 50), ["Light", "Light", "Bonus", "Bonus", "Spell"]),
        ((51, 60), ["Light", "Bonus", "Bonus", "Bonus", "Bonus"]),
        ((61, 65), ["Bonus", "Bonus", "Bonus", "Bonus", "Bonus"]), # Original code typo Bonus/Bonus? Assume Bonus
        ((66, 75), ["Bonus", "Bonus", "Bonus", "Spell", "Bonus"]), # Original code typo? Bonus/Spell? Assume Bonus
        ((76, 85), ["Bonus", "Bonus", "Spell", "Spell", "Sp. Bonus"]),
        ((86, 90), ["Bonus", "Spell", "Spell", "Sp. Bonus", "Sp. Bonus"]),
        ((91, 94), ["Spell", "Spell", "Sp. Bonus", "Sp. Bonus", "Tome"]), # Tome needs implementation
        ((95, 97), ["Spell", "Sp. Bonus", "Sp. Bonus", "Tome", "Special"]), # Special/Tome need impl.
        ((98, 99), ["Sp. Bonus", "Sp. Bonus", "Tome", "Special", "Special"]), # Special/Tome need impl.
        ((100, 100), ["Special", "Special", "Special", "Special", "Artifact"]) # Special/Artifact need impl.
    )
    roll = random.randint(1, 100)
    logger.debug(f"Composition table roll: {roll}")

    if not 0 <= richness_level < 5:
         logger.error(f"Invalid richness_level '{richness_level}' passed to getcomposition.")
         return None

    composition = None
    for select in treasurecompositiontable:
        if select[0][0] <= roll <= select[0][1]:
            try:
                composition = select[1][richness_level]
                logger.info(f"Composition result: '{composition}' for level {richness_level}")
                # Handle unimplemented types explicitly if needed
                if composition in ["Tome", "Special", "Artifact"]:
                     logger.warning(f"Composition result '{composition}' is not fully implemented.")
                     # Decide: return it anyway, return None, return "Normal"?
                     # Returning it for now, Item class needs to handle it.
                return composition
            except IndexError:
                 logger.error(f"IndexError accessing composition table for roll {roll}, level {richness_level}.")
                 return None # Return None on error

    logger.error("Failed to determine composition (logic error in table?).")
    return None # Return None on error


def getadditionalmagicitemcapabilities(initial_type):
    """ Determines if an item gets extra capabilities. """
    # Logger could be passed here if needed for detailed debugging
    additionalcapabilities_lookup = ["Bonus", "Light", "Sp. Bonus"] # Use initial type to index cols
    compabilitiestable = (
        # Roll, [[Bonus item adds], [Light item adds], [Sp. Bonus item adds]]
        ((41, 50), [["Bonus"], ["Light"], ["Nothing"]]),
        ((51, 75), [["Bonus"], ["Light"], ["Light"]]),
        ((76, 88), [["Spell"], ["Spell"], ["Spell"]]),
        ((89, 91), [["Sp. Bonus"], ["Sp. Bonus"], ["Bonus"]]),
        ((92, 94), [["Bonus", "Spell"], ["Light", "Spell"], ["Light", "Spell"]]),
        ((95, 96), [["Sp. Bonus", "Spell"], ["Light", "Sp. Bonus"], ["Light", "Bonus"]]),
        ((97, 98), [["Bonus", "Sp. Bonus"], ["Sp. Bonus", "Spell"], ["Bonus", "Spell"]]),
        ((99, 99), [["Bonus", "Sp. Bonus", "Spell"], ["Light", "Sp. Bonus", "Spell"], ["Light", "Bonus", "Spell"]]),
        ((100, 100), [["Special"], ["Special"], ["Special"]]) # Needs implementation
    )
    roll = random.randint(1, 100)
    # print(f"Add. Capability Roll: {roll}") # Optional debug

    if roll < 41:
        return ["Nothing"] # Explicitly return ["Nothing"] for clarity

    try:
        initial_type_index = additionalcapabilities_lookup.index(initial_type)
    except ValueError:
        # print(f"Warning: Unknown initial_type '{initial_type}' for additional capabilities.")
        return ["Nothing"] # Default if type isn't in the lookup

    added_caps = ["Nothing"] # Default
    for select in compabilitiestable:
        if select[0][0] <= roll <= select[0][1]:
            try:
                added_caps = select[1][initial_type_index]
                # print(f"Added Capabilities: {added_caps}") # Optional debug
                # Handle "Special" case
                if "Special" in added_caps:
                     # print("Warning: 'Special' additional capability not implemented.")
                     pass # Keep "Special" for Item class to handle
                return added_caps
            except IndexError:
                 # print(f"Error: Index out of bounds for additional capabilities table (Roll: {roll}, Index: {initial_type_index}).")
                 return ["Nothing"] # Return default on error

    # Should only be reached if roll >= 41 but not found in table (error in table def)
    # print(f"Error: Logic error in additional capabilities table for roll {roll}.")
    return ["Nothing"]


def getitemfrommagicitemscapabilitieschart(type, logger): # Added logger parameter
    '''
    Provides an Random item / capability based on given type as stated in "Magic Items Cpabilities Chart"
    :param type: "Light", "Bonus", "Sp. Bonus", "TYPE A", "TYPE B"
    :param logger: Logger instance
    :return: String result from chart or "Error"
    '''
    logger.info(f"Getting item/capability from chart for type: {type}")
    magicitemstable = (
        # Roll, ["Light", "Bonus", "Sp. Bonus", "TYPE A", "TYPE B"]
        ((1, 7), ["80%", "+5", "+1 Ess", "Staff", "Weapon"]), # Removed "1-H Slashing" - handle specific later
        ((8, 11), ["80%", "+5", "+1 Ess", "Staff", "Weapon"]), # Removed "1-H Concussion"
        ((12, 15), ["80%", "+5", "+1 Ess", "Staff", "Weapon"]), # Removed "2-Handed"
        ((16, 19), ["80%", "+5", "+1 Chan", "Staff", "Weapon"]), # Removed "Pole Arm"
        ((20, 22), ["80%", "+5", "+1 Chan", "Staff", "10 Arrows"]),
        ((23, 25), ["80%", "+5", "+1 Chan", "Staff", "10 Quarrels"]),
        ((26, 30), ["70%", "+10", "+1 Ment", "Staff", "Weapon"]), # Removed "Bow & Thrown"
        ((31, 35), ["70%", "+10", "+1 Hybrid", "Rod", "Weapon"]), # Removed "Special"
        ((36, 44), ["70%", "+10", "+2 Ess", "Rod", "Shield"]),
        ((45, 50), ["60%", "+15", "+2 Chan", "Rod", "Rigid Leather Armor"]),
        ((51, 53), ["60%", "+15", "+2 Ment", "Rod", "Soft Leather Armor"]),
        ((54, 56), ["60%", "+15", "+2 Hybrid", "Rod", "Helmet"]),
        ((57, 62), ["60%", "+20", "+3 Ess", "Wand", "Chain Armor"]),
        ((63, 68), ["50%", "+5(M)", "x2 Ess", "Wand", "Plate Armor"]),
        ((69, 72), ["50%", "+5(M)", "+3 Chan", "Wand", "Lockpick Kit"]),
        ((73, 76), ["50%", "+5(M)", "x2 Chan", "Wand", "Disarm Trap Kit"]),
        ((77, 78), ["50%", "+10(M)", "+3 Ment", "Robes", "Gloves (Martial Arts)"]),
        ((79, 80), ["50%", "+10(M)", "x2 Ment", "Robes", "Glasses (Perception)"]),
        ((81, 82), ["40%", "+10(M)", "+3 Hybrid", "Robes", "Cloak (Hiding)"]),
        ((83, 84), ["40%", "+10(M)", "x2 Hybrid", "Robes", "Boots (Stalking)"]),
        ((85, 85), ["40%", "+10(M)", "+4 Ess", "Robes", "Bridle (Riding)"]),
        ((86, 87), ["40%", "+15(M)", "+4 Ess", "Robes", "Robes (DB if no armor)"]),
        ((88, 89), ["40%", "+15(M)", "x3 Ess", "Headband", "Bracers (Adrenal Def.)"]),
        # ((90, 90), ["40%", "+15(M)", "x3 Ess", "Headband", "Bracers (Adrenal Def.)"]), # Seems duplicate, check RM rules? Removed for now.
        ((90, 90), ["40%", "+15(M)", "x3 Ess", "Headband", "Bracers (Adrenal Def.)"]), # Kept one 90 entry
        ((91, 91), ["30%", "+20(M)", "+4 Chan", "Armband", "Belt (DB)"]),
        ((92, 92), ["30%", "+20(M)", "x3 Chan", "Armband", "Lockpick Kit"]), # Duplicate kit?
        ((93, 93), ["20%", "+25(M)", "+4 Ment", "Necklace", "Disarm Trap Kit"]), # Duplicate kit?
        ((94, 94), ["20%", "Special", "x3 Ment", "Necklace", "30 Pitons (Climbing)"]),
        ((95, 95), ["Special", "Special", "+4 Hybrid", "Ring", "Saddle (Riding)"]),
        ((96, 96), ["Special", "Special", "x3 Hybrid", "Ring", "Ring (DB)"]),
        ((97, 97), ["Special", "Special", "+5 Ess", "Ring", "Special"]), # Needs implementation
        ((98, 98), ["Special", "Special", "x4 Ess", "Special", "Special"]), # Needs implementation
        ((99, 99), ["Special", "Special", "Special", "Special", "Special"]), # Needs implementation
        ((100, 100), ["Special", "Special", "Special", "Special", "Special"]) # Needs implementation
    )
    roll = random.randint(1, 100)
    logger.debug(f"Magic items capabilities chart roll: {roll}")
    typetocolumnlist = ["Light", "Bonus", "Sp. Bonus", "TYPE A", "TYPE B"]

    try:
        col_index = typetocolumnlist.index(type)
    except ValueError:
        logger.error(f"Invalid type '{type}' requested from capabilities chart.")
        return "Error: Invalid Type"

    item = "Error: Roll not found" # Default error
    for select in magicitemstable:
        if select[0][0] <= roll <= select[0][1]:
            try:
                item = select[1][col_index]
                logger.info(f"Chart result for type '{type}': '{item}'")
                if item == "Special":
                    logger.warning("Chart result 'Special' requires manual handling.")
                # Remove specific weapon types if they are still present, handle later
                # weapon_subtypes = ["1-H Slashing", "1-H Concussion", "2-Handed", "Pole Arm", "Bow & Thrown"]
                # if item in weapon_subtypes:
                #     logger.debug(f"Chart returned weapon subtype '{item}', using 'Weapon' instead.")
                #     item = "Weapon"
                return item
            except IndexError:
                 logger.error(f"IndexError accessing capabilities chart for roll {roll}, type '{type}', index {col_index}.")
                 return "Error: Table Index"

    logger.error(f"Failed to find result in capabilities chart for roll {roll}, type '{type}'.")
    return item # Returns "Error: Roll not found"


# retrieveitem function seems incomplete/unused, commented out for now
# def retrieveitem(type):
#     if type == "Light":
#         item = getitemfrommagicitemscapabilitieschart("TYPE B")
#         if item == "Special":
#             item = "Special item!"
#         reduction = getitemfrommagicitemscapabilitieschart("Light")
#         if reduction == "Special":
#             reduction = "Light special!"
#         result = item + " - " + reduction + " weight"
#         return result
#     if type == "Bonus":
#         pass # Incomplete


def retrievespell(listcategory, spelllist, level, spellcategory, logger): # Added logger
    """ Fetches spell details based on category, list, level. """
    logger.info(f"Retrieving spell: Cat={listcategory}, List={spelllist}, Lvl={level}, Realm={spellcategory}")

    # Simplify list category mapping (crude examples, needs refinement based on actual filenames)
    # This mapping logic seems flawed/incomplete in original. Needs accurate mapping.
    list_prefix_map = {
        "Animist": "Base_List_Animist", "Alchemist": "Base_List_Alchemist",
        "Bard": "Base_List_Bard", "Cleric": "Base_List_Cleric",
        "Dabbler": "Base_List_Dabbler", # Seer might use this?
        "Healer": "Base_List_Healer", "Illusionist": "Base_List_Illusionist",
        "Lay-Healer": "Base_List_Lay-Healer", "Magent": "Base_List_Magent", # Typo? Magician?
        "Magician": "Base_List_Magician", "Mentalist": "Base_List_Mentalist",
        "Mystic": "Base_List_Mystic", "Paladin": "Base_List_Paladin",
        "Ranger": "Base_List_Ranger", "Sorcerer": "Base_List_Sorcerer",
        "Taoist-Monk": "Base_List_Taoist-Monk", "Zen-Monk": "Base_List_Zen-Monk",
        "Monk": "Base_List_Monk",
        "Evil Magician": "Essence_Evil", # Assuming filename structure
        "Evil Cleric": "Channeling_Evil",
        "Evil Mentalist": "Mentalism_Evil",
        # Add mappings for Open Lists, Closed Lists etc. if they have dedicated folders/files
        "Open Lists": "Open", # Example structure
        "Closed Lists": "Closed", # Example structure
    }

    # Determine the base path part based on simplified category
    base_path_part = "Unknown_Category"
    for key, value in list_prefix_map.items():
        if key in listcategory:
            base_path_part = value
            break
        # Handle cases like "Open Lists" which don't contain a profession name
        if key == listcategory:
             base_path_part = value
             break

    if base_path_part == "Unknown_Category" and listcategory.lower() not in ["special", "cursed"]:
         logger.warning(f"Could not map list category '{listcategory}' to a known path prefix.")
         # Decide fallback behavior - maybe try generic paths?

    # Handle Special/Cursed directly
    if listcategory.lower() == "special":
        logger.info("Spell category is 'special'.")
        return "Special Spell Effect (Requires Manual Definition)"
    elif listcategory.lower() == "cursed":
        logger.info("Spell category is 'cursed'.")
        return "Cursed Spell Effect (Requires Manual Definition)"
    else:
        # Pass logger to getspellfromfile
        spell_data = getspellfromfile(base_path_part, spelllist, level, spellcategory, logger)
        return spell_data


# retrieveartifact function is a placeholder
def retrieveartifact(type, logger): # Added logger
    '''
    todo: all
    :param type:
    :param logger:
    :return:
    '''
    logger.warning(f"Artifact retrieval for type '{type}' is not implemented.")
    return {"name": f"Unimplemented Artifact ({type})", "description": "Requires GM definition."}


# translatespelllisttofile seems overly complex if path constructed in retrievespell. Simplified.
# If filenames are complex, this might need to be more robust.
def translatespelllisttofile(filepath_guess, logger):
    """
    Validates or adjusts the guessed spell file path.
    (Currently just checks existence, could add complex mapping later).
    """
    # Example: Add specific known translations if needed
    translation_map = {
        # "./data/magic/Base_List_Magican/Fire_Law.csv": "./data/magic/Base_List_Magician/Fire_Law.csv", # Correct typo
    }
    if filepath_guess in translation_map:
        corrected_path = translation_map[filepath_guess]
        logger.debug(f"Translated spell path '{filepath_guess}' to '{corrected_path}'")
        return corrected_path

    # Basic check if guessed path exists
    if path.exists(filepath_guess):
        return filepath_guess
    else:
        # Attempt variations? e.g., underscores vs spaces? Case changes?
        # Simple check: try replacing underscores with spaces in list name part
        dir_name, file_name = path.split(filepath_guess)
        alt_file_name = file_name.replace("_", " ")
        alt_path = path.join(dir_name, alt_file_name)
        if path.exists(alt_path):
            logger.debug(f"Found spell file using space variation: {alt_path}")
            return alt_path

        logger.warning(f"Spell file path not found or translated: {filepath_guess}")
        return filepath_guess # Return the guess even if not found, let caller handle


def getspelllist(logger): # Added logger
    """ Determines a random spell list, category, and realm. """
    logger.info("Determining random spell list...")
    spelllist_table = ( # Renamed for clarity
        # Roll, SpellList(Ch), ListCat(Ch), SpellList(Ess), ListCat(Ess), SpellList(Ment), ListCat(Ment), SpellList(Evil/Semi), ListCat(Evil/Semi)
        ((1, 3), "Spell Defense", "Open Lists", "Spell Wall", "Open Lists", "Delving", "Open Lists", "Physical Erosion", "Evil Magician Base Lists"),
        ((4, 6), "Barrier Law", "Open Lists", "Essence's Perceptions", "Open Lists", "Cloaking", "Open Lists", "Matter Disruption", "Evil Magician Base Lists"),
        ((7, 9), "Detection Mastery", "Open Lists", "Rune Mastery", "Open Lists", "Damage Resistance", "Open Lists", "Dark Contacts", "Evil Magician Base Lists"),
        ((10, 12), "Lofty Movements", "Open Lists", "Essence Hand", "Open Lists", "Anticipations", "Open Lists", "Dark Summons", "Evil Magician Base Lists"),
        ((13, 15), "Weather Ways", "Open Lists", "Unbarring Ways", "Open Lists", "Attack Avoidance", "Open Lists", "Darkness", "Evil Magician Base Lists"),
        ((16, 18), "Sound's Way", "Open Lists", "Physical Enhancement", "Open Lists", "Brilliance", "Open Lists", "Monk's Bridge", "Monk Base Lists"),
        ((19, 21), "Light's Way", "Open Lists", "Lesser Illusions", "Open Lists", "Self Healing", "Open Lists", "Evasions", "Monk Base Lists"),
        ((22, 24), "Purifications", "Open Lists", "Detecting Ways", "Open Lists", "Detections", "Open Lists", "Body Reins", "Monk Base Lists"),
        ((25, 27), "Concussion's Ways", "Open Lists", "Elemental Shields", "Open Lists", "Illusions", "Open Lists", "Monk's Sense", "Monk Base Lists"),
        ((28, 30), "Nature's Law", "Open Lists", "Delving Ways", "Open Lists", "Spell Resistance", "Open Lists", "Body Renewal", "Monk Base Lists"),
        ((31, 33), "Blood Law", "Closed Lists", "Invisible Ways", "Closed Lists", "Sense Mastery", "Closed Lists", "Disease", "Evil Cleric Base Lists"),
        ((34, 36), "Bone Law", "Closed Lists", "Living Change", "Closed Lists", "Gas Manipulation", "Closed Lists", "Dark Channels", "Evil Cleric Base Lists"),
        ((37, 39), "Organ Law", "Closed Lists", "Spirit Mastery", "Closed Lists", "Shifting", "Closed Lists", "Dark Lore", "Evil Cleric Base Lists"), # Corrected range 35->37
        ((40, 42), "Muscle Law", "Closed Lists", "Spell Reins", "Closed Lists", "Liquid Manipulation", "Closed Lists", "Curses", "Evil Cleric Base Lists"),
        ((43, 45), "Nerve Law", "Closed Lists", "Lofty Bridge", "Closed Lists", "Speed", "Closed Lists", "Necromancy", "Evil Cleric Base Lists"),
        ((46, 48), "Locating Ways", "Closed Lists", "Spell Enhancement", "Closed Lists", "Mind Mastery", "Closed Lists", "Path Mastery", "Ranger Base Lists"),
        ((49, 51), "Calm Spirits", "Closed Lists", "Dispelling Ways", "Closed Lists", "Solid Manipulation", "Closed Lists", "Moving Ways", "Ranger Base Lists"),
        ((52, 54), "Creations", "Closed Lists", "Shield Mastery", "Closed Lists", "Telekinesis", "Closed Lists", "Nature's Guises", "Ranger Base Lists"),
        ((55, 57), "Symbolic Ways", "Closed Lists", "Rapid Ways", "Closed Lists", "Mind's Door", "Closed Lists", "Inner Walls", "Ranger Base Lists"),
        ((58, 60), "Lore", "Closed Lists", "Gate Mastery", "Closed Lists", "Movement", "Closed Lists", "Nature's Ways", "Ranger Base Lists"),
        ((61, 63), "Channels", "Cleric Base Lists", "Fire Law", "Magician Base Lists", "Presence", "Mentalist Base Lists", "Soul Destruction", "Sorcerer Base Lists"),
        ((64, 66), "Summons", "Cleric Base Lists", "Ice Law", "Magician Base Lists", "Mind Merge", "Mentalist Base Lists", "Gas Destruction", "Sorcerer Base Lists"),
        ((67, 69), "Communal Ways", "Cleric Base Lists", "Earth Law", "Magician Base Lists", "Mind Control", "Mentalist Base Lists", "Solid Destruction", "Sorcerer Base Lists"),
        ((70, 72), "Life Mastery", "Cleric Base Lists", "Light Law", "Magician Base Lists", "Sense Control", "Mentalist Base Lists", "Fluid Destruction", "Sorcerer Base Lists"),
        ((73, 75), "Protections", "Cleric Base Lists", "Wind Law", "Magician Base Lists", "Mind Attack", "Mentalist Base Lists", "Mind Destruction", "Sorcerer Base Lists"),
        ((76, 78), "Repulsions", "Cleric Base Lists", "Water Law", "Magician Base Lists", "Mind Speech", "Mentalist Base Lists", "Flesh Destruction", "Sorcerer Base Lists"),
        ((79, 79), "Surface Ways", "Healer Base Lists", "Illusion Mastery", "Illusionist Base Lists", "Past Visions", "Seer Base Lists", "Confusing Ways", "Mystic Base Lists"),
        ((80, 80), "Bone Ways", "Healer Base Lists", "Mind Sense Molding", "Illusionist Base Lists", "Mind Visions", "Seer Base Lists", "Hiding", "Mystic Base Lists"),
        ((81, 81), "Muscle Ways", "Healer Base Lists", "Guises", "Illusionist Base Lists", "True Perception", "Seer Base Lists", "Mystical Change", "Mystic Base Lists"),
        ((82, 82), "Organ Ways", "Healer Base Lists", "Sound Molding", "Illusionist Base Lists", "Future Visions", "Seer Base Lists", "Liquid Alteration", "Mystic Base Lists"),
        ((83, 83), "Blood Ways", "Healer Base Lists", "Light Molding", "Illusionist Base Lists", "Sense Through Others", "Seer Base Lists", "Solid Alteration", "Mystic Base Lists"),
        ((84, 84), "Transferring Ways", "Healer Base Lists", "Feel-Taste-Smell", "Illusionist Base Lists", "True Sight", "Seer Base Lists", "Gas Alteration", "Mystic Base Lists"), # Corrected typo Fcel
        ((85, 85), "Nature's Movement", "Animist Base Lists", "Enchanting Ways", "Alchemist Base Lists", "Muscle Mastery", "Lay Healer Base Lists", "Time's Bridge", "Astrologer Base Lists"),
        ((86, 86), "Plant Mastery", "Animist Base Lists", "Essence Imbedding", "Alchemist Base Lists", "Concussion Mastery", "Lay Healer Base Lists", "Way of the Voice", "Astrologer Base Lists"),
        ((87, 87), "Animal Mastery", "Animist Base Lists", "Ment.-Chan. Imbedding", "Alchemist Base Lists", "Bone Mastery", "Lay Healer Base Lists", "Holy Vision", "Astrologer Base Lists"),
        ((88, 88), "Herb Mastery", "Animist Base Lists", "Organic Skills", "Alchemist Base Lists", "Blood Mastery", "Lay Healer Base Lists", "Far Voice", "Astrologer Base Lists"),
        ((89, 89), "Nature's Lore", "Animist Base Lists", "Liquid-Gas Skills", "Alchemist Base Lists", "Prosthetics", "Lay Healer Base Lists", "Starlights", "Astrologer Base Lists"),
        ((90, 90), "Nature's Protection", "Animist Base Lists", "Inorganic Skills", "Alchemist Base Lists", "Nerve & Organ Mastery", "Lay Healer Base Lists", "Starsense", "Astrologer Base Lists"),
        ((91, 91), "special", "special", "special", "special", "special", "special", "Mind Erosion", "Evil Mentalist Base Lists"),
        ((92, 92), "special", "special", "special", "special", "special", "special", "Mind Subversion", "Evil Mentalist Base Lists"),
        ((93, 93), "special", "special", "special", "special", "special", "special", "Mind Death", "Evil Mentalist Base Lists"),
        ((94, 94), "special", "special", "special", "special", "special", "special", "Mind Disease", "Evil Mentalist Base Lists"),
        ((95, 95), "special", "special", "special", "special", "special", "special", "Mind Domination", "Evil Mentalist Base Lists"),
        ((96, 96), "cursed", "cursed", "cursed", "cursed", "cursed", "cursed", "Lore", "Bard Base Lists"),
        ((97, 97), "cursed", "cursed", "cursed", "cursed", "cursed", "cursed", "Contolling Songs", "Bard Base Lists"), # Controlling typo
        ((98, 98), "cursed", "cursed", "cursed", "cursed", "cursed", "cursed", "Sound Control", "Bard Base Lists"),
        ((99, 99), "cursed", "cursed", "cursed", "cursed", "cursed", "cursed", "Sound Projection", "Bard Base Lists"),
        ((100, 100), "cursed", "cursed", "cursed", "cursed", "cursed", "cursed", "Item Lore", "Bard Base Lists")
    )
    spelltypelist = ( # Determines which *column* pair to read from spelllist_table
        # Roll Range, Column Index (0=Ch, 2=Ess, 4=Ment, 6=Evil/Semi), Realm Name
        ((1, 25), 0, "Channeling"),
        ((26, 74), 2, "Essence"),
        ((75, 90), 4, "Mentalism"),
        ((91, 100), 6, "Evil/Semi/Hybrid") # Check realm name consistency
    )
    realm_roll = random.randint(1, 100)
    logger.debug(f"Spell Realm roll: {realm_roll}")
    col_index = 2 # Default to Essence?
    spell_realm = "Essence" # Default realm name
    for select in spelltypelist:
        if select[0][0] <= realm_roll <= select[0][1]:
            col_index = select[1]
            spell_realm = select[2]
            break
    logger.info(f"Selected Realm: {spell_realm} (Column Index: {col_index})")


    list_roll = random.randint(1, 100)
    logger.debug(f"Spell List roll: {list_roll}")
    spell_details = {}
    for select in spelllist_table:
        if select[0][0] <= list_roll <= select[0][1]:
            try:
                spell_details["Spelllist"] = select[col_index + 1] # Column pairs are (idx+1=List, idx+2=Category)
                spell_details["listcategory"] = select[col_index + 2]
                spell_details["Category"] = spell_realm # The overall realm category
                logger.info(f"Determined Spell List: '{spell_details['Spelllist']}', List Category: '{spell_details['listcategory']}'")

                # Handle special/cursed results immediately
                if spell_details["Spelllist"].lower() in ["special", "cursed"]:
                     logger.info(f"Directly returning '{spell_details['Spelllist']}' result.")
                     # Keep category info if needed?
                     spell_details["listcategory"] = spell_details["Spelllist"] # Overwrite category for clarity

                return spell_details
            except IndexError:
                 logger.error(f"IndexError accessing spelllist table for list roll {list_roll}, column index {col_index}.")
                 return {"Spelllist": "Error", "listcategory": "Error", "Category": "Error"}


    logger.error("Failed to determine spell list (logic error in table?).")
    return {"Spelllist": "Error", "listcategory": "Error", "Category": "Error"}


def getrandomitemtype(logger): # Added logger
    """ Gets a random item type suitable for embedding spells (wand, potion, etc.) """
    logger.info("Getting random spell item type...")
    itemtype = "Error" # Default
    items_table = (
        ((1, 30), "runepaper"),
        ((31, 50), "potion"),
        ((51, 65), "singleuse"),
        ((66, 70), "daily1"),
        ((71, 75), "daily2"),
        ((76, 80), "daily3"),
        ((81, 85), "daily4"),
        ((86, 94), "wand"),
        ((95, 98), "rod"),
        ((99, 99), "staff"),
        ((100, 100), "constant")
    )
    roll = random.randint(1, 100)
    logger.debug(f"Spell item type roll: {roll}")
    for select in items_table:
        if select[0][0] <= roll <= select[0][1]:
            itemtype = select[1]
            logger.info(f"Selected spell item type: {itemtype}")
            return itemtype
    logger.error("Failed to get random item type (table error?).")
    return itemtype # Returns "Error"


def getspelllevel(item_capacity_type, logger): # Added logger
    '''
    Determines spell level based on item's capacity type.
    :param item_capacity_type: String category from translatespellcapacity (wand, rod, potion, daily1 etc.)
    :param logger: Logger instance
    :return: String spell level (e.g., "1", "5", "10", "HL") or "1" on error.
    '''
    logger.info(f"Getting spell level for capacity type: {item_capacity_type}")

    # Check if type is valid first
    if item_capacity_type == "unknown" or not item_capacity_type:
         logger.error("Cannot get spell level for unknown item capacity type.")
         return "1" # Default to level 1 on error

    # Roll vs Level Bands
    level_bands = ( # Renamed for clarity
        (1, 20), (21, 25), (26, 30), (31, 35), (36, 40), (41, 45), (46, 50),
        (51, 55), (56, 60), (61, 65), (66, 70), (71, 75), (76, 80), (81, 85),
        (86, 90), (91, 94), (95, 97), (98, 99), (100, 100)
    )
    roll = random.randint(1, 100)
    logger.debug(f"Spell level band roll: {roll}")

    selected_band_index = -1
    for index, band in enumerate(level_bands):
        if band[0] <= roll <= band[1]:
            selected_band_index = index
            break

    if selected_band_index == -1:
        logger.error("Failed to determine level band (table error?). Defaulting to index 0.")
        selected_band_index = 0

    # Level results per capacity type for each band index
    level_results = {
        # type: [band 0 result, band 1 result, ..., band 18 result]
        "runepaper": ["1", "2", "2", "2", "2", "3", "3", "3", "4", "4", "5", "5", "6", "7", "8", "9", "10", "HL", "HL"],
        "potion":    ["1", "1", "1", "2", "2", "2", "2", "2", "3", "3", "4", "4", "5", "6", "7", "8", "9", "10", "HL"],
        "singleuse": ["1", "2", "2", "3", "3", "4", "4", "5", "5", "6", "6", "7", "7", "8", "9", "10", "HL", "HL", "HL"],
        "daily1":    ["1", "1", "1", "1", "2", "2", "2", "3", "3", "4", "4", "5", "5", "6", "7", "8", "9", "10", "HL"],
        "daily2":    ["1", "1", "1", "1", "1", "2", "2", "2", "2", "3", "3", "3", "4", "4", "5", "5", "6", "7", "HL"],
        "daily3":    ["1", "1", "1", "1", "1", "1", "2", "2", "2", "2", "2", "3", "3", "3", "4", "4", "5", "5", "HL"],
        "daily4":    ["1", "1", "1", "1", "1", "1", "1", "1", "2", "2", "2", "2", "2", "2", "3", "3", "3", "3", "HL"],
        "wand":      ["1", "1", "1", "1", "1", "1", "1", "1", "2", "2", "2", "2", "2", "2", "2", "2", "2", "2", "2"],
        "rod":       ["1", "1", "1", "2", "2", "2", "2", "2", "3", "3", "3", "3", "4", "4", "4", "5", "5", "5", "5"],
        "staff":     ["1", "2", "3", "3", "4", "4", "5", "5", "6", "6", "7", "7", "8", "8", "9", "9", "10", "10", "HL"],
        "constant":  ["1", "2", "2", "3", "3", "4", "4", "5", "5", "6", "6", "7", "7", "8", "8", "9", "10", "10", "HL"],
        "tome":      ["1-5", "1-5", "6-10", "6-10", "6-10", "6-10", "1-10", "1-10", "1-10", "1-10", "1-10", "11-20", "11-20", "11-20", "1-20", "1-20", "1-25", "1-30", "1-50"] # Tome levels need specific handling
        # Add other capacity types if necessary
    }

    if item_capacity_type not in level_results:
        logger.error(f"No level results defined for capacity type '{item_capacity_type}'. Defaulting to Level 1.")
        return "1"

    try:
        level = level_results[item_capacity_type][selected_band_index]
        logger.info(f"Determined spell level: {level}")
        # Handle "HL" - maybe resolve to a specific high level number here?
        if level == "HL":
            hl_level = random.randint(11, 20) # Example: Resolve HL to 11-20
            logger.info(f"Resolved 'HL' to Level {hl_level}")
            return str(hl_level) # Return as string
        # Handle Tome ranges - needs specific resolution logic elsewhere
        if "-" in level:
             logger.warning(f"Tome level range '{level}' requires specific handling.")
             # Return the range for now, caller must interpret
        return level
    except IndexError:
        logger.error(f"IndexError accessing level results for type '{item_capacity_type}', band index {selected_band_index}.")
        return "1" # Default to level 1 on error


def getmoney(treasurequality, logger): # Added logger
    """ Gets a random parcel of money/valuables based on quality level. """
    logger.info(f"Getting money parcel for quality: {treasurequality}")
    # Ensure quality is integer for indexing
    try:
        quality_index = int(treasurequality) # Index is quality (1-5)
        if not 1 <= quality_index <= 5:
            raise ValueError("Quality out of range 1-5")
    except (ValueError, TypeError):
         logger.error(f"Invalid treasure quality '{treasurequality}' passed to getmoney. Defaulting to 1.")
         quality_index = 1


    money_table = (
        # Roll Range, Quality 1 (Amt, Type), Q2, Q3, Q4, Q5
        ((1, 10), (50, "ZS"), (500, "ZS"), (1000, "ZS"), (5000, "ZS"), (10000, "ZS")),
        ((11, 20), (100, "ZS"), (1500, "ZS"), (3000, "ZS"), (7500, "ZS"), (5000, "KS")),
        ((21, 30), (500, "ZS"), (2500, "ZS"), (5000, "ZS"), (1000, "KS"), (10000, "KS")),
        ((31, 35), (1000, "ZS"), (500, "KS"), (1000, "KS"), (1750, "KS"), (1500, "BS")),
        ((36, 40), (2000, "ZS"), (750, "KS"), (1500, "KS"), (2500, "KS"), (2000, "BS")),
        ((41, 45), (300, "KS"), (1000, "KS"), (2000, "KS"), (400, "BS"), (250, "SS")),
        ((46, 50), (400, "KS"), (1250, "KS"), (250, "BS"), (500, "BS"), (300, "SS")),
        ((51, 55), (500, "KS"), (150, "BS"), (300, "BS"), (600, "BS"), (400, "SS")),
        ((56, 60), (600, "KS"), (200, "BS"), (350, "BS"), (70, "SS"), (60, "GS")),
        ((61, 65), (70, "BS"), (250, "BS"), (40, "SS"), (90, "SS"), (80, "GS")),
        ((66, 70), (80, "BS"), (30, "SS"), (50, "SS"), (110, "SS"), (100, "GS")),
        ((71, 75), (90, "BS"), (35, "SS"), (60, "SS"), (15, "GS"), (125, "GS")),
        ((76, 80), (100, "BS"), (40, "SS"), (70, "SS"), (25, "GS"), (150, "GS")),
        ((81, 85), (12, "SS"), (50, "SS"), (8, "GS"), (35, "GS"), (2, "MS")),
        ((86, 90), (15, "SS"), (60, "SS"), (10, "GS"), (45, "GS"), (250, "Ed")),
        ((91, 94), (20, "SS"), (7, "GS"), (15, "GS"), (60, "Ed"), (300, "Ed")),
        ((95, 97), (3, "GS"), (8, "GS"), (20, "Ed"), (80, "Ed"), (400, "Sch")),
        ((98, 99), (5, "GS"), (10, "Ed"), (50, "Ed"), (1, "MS"), (600, "Sch")),
        ((100, 100), (10, "Ed"), (25, "Sch"), (100, "Sch"), (500, "Sch"), (1000, "Sch"))
    )

    roll = random.randint(1, 100)
    logger.debug(f"Money table roll: {roll}")
    result = (0, "Error") # Default error value

    for select in money_table:
        if select[0][0] <= roll <= select[0][1]:
            try:
                # Index 1 = Q1, Index 2 = Q2, ..., Index 5 = Q5
                result = select[quality_index]
                # Add variability: +- 10% ? RM rules might specify this.
                # Example: amount = result[0]; variability = random.uniform(0.9, 1.1); amount = int(amount * variability)
                # For now, use exact amount from table.
                amount = int(result[0]) # Ensure amount is integer
                typ = result[1]
                logger.info(f"Money parcel result: {amount} {typ}")
                return amount, typ
            except IndexError:
                 logger.error(f"IndexError accessing money table for roll {roll}, quality {quality_index}.")
                 return 0, "Error" # Return error tuple

    logger.error(f"Failed to find result in money table for roll {roll}.")
    return 0, "Error" # Return error tuple


def getspellfromfile(listcategory_path_part, spelllist_name, level, spellcategory, logger): # Added logger
    """ Reads spell data from a CSV file. """
    logger.info(f"Attempting to load spell: PathPart='{listcategory_path_part}', List='{spelllist_name}', Level='{level}', Category='{spellcategory}'")

    # --- Construct the file path ---
    # Clean list name for filename (replace spaces, apostrophes etc.)
    safe_list_name = spelllist_name.replace("'", "").replace(" ", "_").replace("-", "_")
    # Base directory
    base_dir = "./data/magic/"
    # Construct path based on category/realm - THIS NEEDS ACCURATE MAPPING TO FOLDER STRUCTURE
    # Example structure assumption: ./data/magic/Realm_ListCategory/Spell_List.csv
    # Or: ./data/magic/ListCategory_Base/Spell_List.csv
    # The logic from retrievespell/translatespelllisttofile needs refining based on actual folders.
    # Using the 'base_path_part' from retrievespell for now:
    folder_name = listcategory_path_part # e.g., "Base_List_Magician", "Essence_Evil", "Open"
    if not folder_name:
         logger.error("Cannot construct spell file path: listcategory_path_part is empty.")
         return "Error: Invalid spell category for path"

    # Handle potential realm prefix needed for non-base lists (Open/Closed)
    if folder_name in ["Open", "Closed"]:
        folder_name = f"{spellcategory}_{folder_name}" # e.g., Essence_Open, Channeling_Closed

    buildfilepath = path.join(base_dir, folder_name, f"{safe_list_name}.csv")
    logger.debug(f"Constructed spell file path guess: {buildfilepath}")

    # Validate/Translate path (Optional, depends on complexity)
    filepath = translatespelllisttofile(buildfilepath, logger) # Pass logger

    # --- Check File Existence ---
    if not path.exists(filepath):
        logger.error(f"Spell file not found: {filepath}")
        return f"Error: Spell file not found - {filepath}"

    # --- Read the file ---
    data = None # Default if level not found
    save = None # To store spell just below target level

    # Check file size/readability first (using the fixed encoding)
    try:
        # Use encoding='utf8' and errors='ignore'/'replace' for robustness
        line_count = 0
        with open(filepath, 'r', encoding='utf8', errors='ignore') as f_check:
            for _ in f_check:
                 line_count += 1
        logger.debug(f"Spell file {filepath} has {line_count} lines.")
        if line_count <= 1: # Empty or header only
             logger.warning(f"Spell file is empty or contains only header: {filepath}")
             return f"Error: No spell data in file - {filepath}"
    except Exception as e:
        logger.error(f"Error checking/counting lines in spell file {filepath}: {e}")
        return f"Error: Cannot read spell file - {filepath}: {e}"

    # Process the CSV
    try:
        with open(filepath, encoding="utf8", errors='ignore') as csvfile:
            # Use DictReader for easier column access
            reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            # Check if 'Lvl' header exists
            if 'Lvl' not in reader.fieldnames:
                 logger.error(f"'Lvl' column not found in header of {filepath}")
                 return f"Error: Missing 'Lvl' column in {filepath}"

            target_level_str = str(level).replace("HL", "").strip() # Clean up level string
            if not target_level_str.isdigit():
                 logger.error(f"Invalid target spell level format: {level}")
                 # Decide fallback: use level 1? Or return error?
                 target_level_str = "1" # Default to 1 on format error
            target_lvl = int(target_level_str)

            logger.debug(f"Searching for spell level >= {target_lvl}")

            for row_raw in reader:
                # Clean the row data *immediately* after reading
                row = {key: clean_csv_string(str(value)) for key, value in row_raw.items()}

                # Check if 'Lvl' exists and is a digit in this specific row
                if row.get('Lvl') and row['Lvl'].isdigit():
                    current_lvl = int(row['Lvl'])

                    if current_lvl < target_lvl:
                        save = row # Store the cleaned row as potential fallback
                    elif current_lvl == target_lvl:
                        data = row # Found exact match
                        logger.info(f"Found exact spell level {target_lvl} in {filepath}")
                        break # Stop searching
                    else: # current_lvl > target_lvl
                        # Found a level higher than target. Use 'save' if it exists.
                        data = save if save else row # If no lower level saved, use the current (first > target)
                        if save:
                             logger.info(f"Target level {target_lvl} not found, using closest lower level {save.get('Lvl')} from {filepath}")
                        else:
                             logger.info(f"Target level {target_lvl} not found, using first higher level {current_lvl} from {filepath}")
                        break # Stop searching
                else:
                    # Log rows skipped due to missing/invalid Lvl
                    logger.warning(f"Skipping row in {filepath} due to missing/invalid 'Lvl': {row_raw}")
                    continue # Skip to next row

            # After loop: Handle cases where target level > max level in file
            if data is None and save:
                data = save # Use the highest level found that was less than target
                logger.info(f"Target level {target_lvl} is higher than max in file, using highest available level {save.get('Lvl')} from {filepath}")
            elif data is None: # No exact match, no lower match found, loop finished
                 logger.warning(f"Spell level {target_lvl} (or lower) not found in {filepath}. No spell data returned.")
                 data = f"Error: Level {target_lvl} (or lower) not found in {filepath}"

    except FileNotFoundError:
         # Should be caught earlier, but double-check
         logger.error(f"Spell file disappeared: {filepath}")
         return f"Error: Spell file disappeared - {filepath}"
    except Exception as e:
        logger.error(f"Error processing CSV spell file {filepath}: {e}")
        return f"Error: CSV processing failed - {filepath}: {e}"

    # Return the found spell data (dict) or an error string
    return data


def createtreasure(treasurtype, treasurequality):
    # Initiate logging
    # Use filemode="w" to overwrite log each time
    logging.basicConfig(filename="createtreasures.log", level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        filemode="w")
    # Create logger instance
    logger = logging.getLogger("createtreasures")
    logger.info("--- Starting Treasure Generation ---")
    logger.debug(f"Input - Type: {treasurtype}, Quality: {treasurequality}")


    random.seed() # Initialize random generator
    # Create the controller, passing the logger
    try:
        control = Controller(treasurtype, treasurequality, logger)
    except Exception as e:
        logger.exception("An unhandled exception occurred during Controller execution:")
        print(f"FATAL ERROR: {e}")

    logger.info("--- Treasure Generation Finished ---")

# Main Execution Block
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Rolemaster Treasure (Money and/or Magic Items)")
    parser.add_argument('treasuretype', choices=["money", "magic", "both"], # Removed debug choice? Add back if needed
                        help="Type of treasure to generate: 'money', 'magic', or 'both'.")
    parser.add_argument('treasurequality', type=int, nargs="?", # Optional quality
                        help="Treasure quality level (1-5). Required if type includes 'money'.")

    args = parser.parse_args()

    # Validate arguments
    if args.treasuretype in ["money", "both"] and args.treasurequality is None:
        parser.error("argument 'treasurequality' is required when 'treasuretype' is 'money' or 'both'")
    if args.treasurequality is not None and not 1 <= args.treasurequality <= 5:
         parser.error("argument 'treasurequality' must be between 1 and 5")

    # breakpoint() # Remove or comment out breakpoint()

    # Call the main generation function
    createtreasure(args.treasuretype, args.treasurequality)