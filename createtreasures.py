#!/usr/bin/python3
# -*- coding: UTF8 -*-


'''
Programname: createtrasures.py
Description: Rolemaster-Support tool to generate Treasure

ToDo: Find Error UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d in position 325: character maps to <undefined>
ToDo: Add Sp. Bonusitems,
# Todo: if key == "Spells": Spells ausgeben
'''

import argparse
import csv
import random
from sys import exit
import pprint
from os import path, remove, walk
import logging
import json


class DeliverItemFromFile:
    '''
    Läd das equipment und liefert einen Gegenstand basierend auf übergebener Parameter zurück.
    Parameter betreffen Typ (armor, weapon...) und / oder Gewichtkategorie (rod, staff, wand...)
    Für jeden Parameter kann RANDOM übergeben werden und die Klasse sucht sich per Zufall einen Gegenstand aus.
    '''
    def __init__(self):
        self.filepath = './data/equipment/'
        self.datafiles = []
        self.datastore = {}
        self.lookupfiles()
        self.readdata()
        self.sampleweights = [("rod", 2), ("wand", 0.5), ("staff", 5)]

    def lookupfiles(self):
        for root, dirs, files in walk(self.filepath):
            for file in files:
                if file.endswith(".csv"):
                    self.datafiles.append(file)

    def readdata(self):
        for file in self.datafiles:
            self.temp = []
            self.counter = 0
            f = open(self.filepath + file, "r")
            for row in f:
                # print(row)
                self.counter += 1
                if self.counter == 1:
                    continue
                self.shorttemp = row.strip("\n").strip(" lbs.")
                self.temp.append(tuple(self.shorttemp.split(",")))
            f.close()
            self.datastore[str(file)[:-4]] = self.temp

    def output(self, etype):
        if etype == "weapon":
            etype = "weapons"
        if etype == "random":
            typelist = []
            for item in self.datafiles:
                typelist.append(path.splitext(item)[0])
            etype = typelist[random.randint(0, len(typelist) - 1)]

        selected = random.randint(0, len(self.datastore[etype]) - 1)
        return self.datastore[etype][selected][0]


class Filewriter:
    def __init__(self):
        self.items = {}
        self.money = {}
        self.final = []

    def add(self,element, value):
        if element == "items":
            self.items = value
        elif element == "money":
            self.money = value

    def finalize(self):
        if len(self.items) > 0:
            self.final.append(self.items)
        if len(self.money) > 0:
            self.final.append(self.money)
        with open("treasure.json", "a") as outfile:
            json.dump(self.final, outfile, indent=4)


class ItemAndMoneyStore:
    def __init__(self):
        self.money = {
            "mithril": 0,
            "gold": 0,
            "silber": 0,
            "bronze": 0,
            "kupfer": 0,
            "zinn": 0,
            "edelsteine": 0,
            "schmuckstücke": 0
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
        self.itemlist = []
        self.itemcounter = 0
        self.moneyorderlist = ["mithril", "gold", "bronze", "kupfer", "zinn", "edelsteine", "schmuckstücke"]

    def additem(self, itemtype):
        self.itemcounter += 1
        self.itemlist.append(itemtype)

    def addmoney(self, typ, amount):
        self.money[self.conversion[typ]] += amount

    def getmoney(self):
        mymoneydict = {}
        for key in self.moneyorderlist:
            if key in self.money:
                mymoneydict[str(key)] = str(self.money[key])
        final = {"money": mymoneydict}
        return final

    def getitems(self):
        counter = 0
        itemlist = []
        for item in self.itemlist:
            counter += 1
            a = item.getitem()
            # itemname = "item_" + str(counter)
            dummydict = {}
            for key, values in a.items():
                if key == "spells":
                    spellcounter = 0
                    spelllist = {}
                    for value in values:
                        spellcounter += 1
                        spellname = "spell_" + str(spellcounter)
                        spelllist[spellname] = {}
                        data = value.output()
                        for element in data:
                            spelllist[spellname][str(element)] = str(data[element])
                        dummydict[spellname] = spelllist[spellname]
                else:
                    dummydict[str(key)] = str(values)
                itemlist.append(dummydict)
                dummydict = {}
        print("Generated " + str(counter) + " items")
        final = {"items": itemlist}
        return final


class Item:

    class Spell:
        def __init__(self, itemtype):
            self.data = {
                "Spelllist": "",
                "Listcategory": "",
                "Spellcategory": "",
                "Level": "",
                "Description": "",
                "Uses": "",
                "Itemtype": itemtype,
                "Name": "",
                "AoE": "None",
                "Duration": "None",
                "Type": "None",
                "Range": "None"
            }

        def fill(self):
            buffer = getspelllist()
            self.data["Spelllist"] = buffer["Spelllist"]
            self.data["Listcategory"] = buffer["listcategory"]
            self.data["Spellcategory"] = buffer["Category"]
            self.data["Level"] = getspelllevel(translatespellcapacity(self.data["Itemtype"]))
            self.buffer = retrievespell(self.data["Listcategory"], self.data["Spelllist"], self.data["Level"], self.data["Spellcategory"])
            if isinstance(self.buffer, dict):
                if "Lvl" in self.buffer:
                    self.data["Level"] = self.buffer["Lvl"]
                if "Duration" in self.buffer:
                    self.data["Duration"] = self.buffer["Duration"]
                if "Spell" in self.buffer:
                    self.data["Name"] = self.buffer["Spell"]
                if "Area of Effect" in self.buffer:
                    self.data["AoE"] = self.buffer["Area of Effect"]
                if "Range" in self.buffer:
                    self.data["Range"] = self.buffer["Range"]
                if "Description" in self.buffer:
                    self.data["Description"] = self.buffer["Description"]
            else:
                self.data["Description"] = self.buffer

        def output(self):
            return self.data

    def __init__(self, itemtype):

        getnormalitem = DeliverItemFromFile()

        self.item = {
            "itemtype": itemtype
        }
        if self.item["itemtype"].lower() in ["bonus", "light", "sp. bonus"]:
            self.counter = [self.item["itemtype"]] + getadditionalmagicitemcapabilities(self.item["itemtype"])
        else:
            self.counter = [self.item["itemtype"]]

        self.itemcounter = 0
        for item in self.counter:
            self.itemcounter += 1
            if item.lower() == 'bonus':
                if self.item["itemtype"].lower() in ["bonus", "light", "sp. bonus", "spell"]:
                    self.item["itemtype"] = getitemfrommagicitemscapabilitieschart("TYPE B")
                self.item[self.getlastelement("bonus")] = getitemfrommagicitemscapabilitieschart("Bonus")

            if item.lower() == 'sp. bonus':
                if self.item["itemtype"].lower() in ["bonus", "light", "sp. bonus", "spell"]:
                    self.item["itemtype"] = getitemfrommagicitemscapabilitieschart("TYPE A")

            if item.lower() == 'light':
                if self.item["itemtype"].lower() in ["bonus", "light", "sp. bonus", "spell"]:
                    self.item["itemtype"] = getitemfrommagicitemscapabilitieschart("TYPE B")
                if "weightreduction" not in self.item:
                    self.item["weightreduction"] = getitemfrommagicitemscapabilitieschart("Light")

            if item.lower() == 'spell':
                if 'spells' not in self.item:
                    self.item["spells"] = []

                if self.item["itemtype"].lower() in ["bonus", "light", "sp. bonus", "spell"]:
                    self.item["itemtype"] = getrandomitemtype()

                buffer = self.Spell(self.item["itemtype"])
                buffer.fill()
                self.item["spells"].append(buffer)

            if item.lower() == 'normal':
                self.item["itemtype"] = getnormalitem.output("random")

            if self.item["itemtype"].lower() == 'weapon':
                self.item["itemtype"] = getnormalitem.output("weapon")



    def getitem(self):
        return self.item

    def getlastelement(self, type):
        counter = 0
        if type in self.item:
            while True:
                counter += 1
                if type + "_" +str(counter) not in self.item:
                    return counter
        else:
            return type


class Controller:
    def __init__(self, selection, quality, logger):
        self.selection = selection
        self.quality = quality
        self.mais = ItemAndMoneyStore()
        self.logger = logger
        self.logger.info("controller started with selection: " + str(selection) + " and quality: " + str(quality))
        self.deletefile()
        self.filewriter = Filewriter()
        if self.selection.lower() in ["magic", "both"]:
            self.magicitems()
        if self.selection.lower() in ["money", "both"]:
            self.money()
        if self.selection.lower() in ["magic", "both"]:
            self.filewriter.add("items", self.mais.getitems())
        if self.selection.lower() in ["money", "both"]:
            self.filewriter.add("money", self.mais.getmoney())
        self.filewriter.finalize()

    def deletefile(self):
        if path.exists("treasure.json"):
            remove("treasure.json")

    def magicitems(self):
        rollnumber = getrichness()
        counter = 0
        for i in rollnumber:
            counter += 1
            if i > 0:
                for x in range(1, i):
                    self.mais.additem(Item(getcomposition(counter - 1)))

    def money(self):
        rollnumber = getnumberofrolls(self.logger)

        if not self.quality or not 1 <= int(self.quality) <= 5:
            print("Please make Treasurequality between 1 and 5")
            exit()

        for i in range(1, rollnumber):
            amount, typ = getmoney(self.quality, self.logger)
            self.mais.addmoney(typ, amount)


def getnumberofrolls(logger):
    '''
    Randomizes number of roles from Wealth Treasure Size Chart.
    Returns Result
    :return:
    '''
    logger.info("Getting number of rolls")
    numberofrolls = (((1, 30), 1),
                     ((31, 55), 2),
                     ((56, 75), 3),
                     ((76, 90), 4),
                     ((91, 97), 5),
                     ((98, 99), 6),
                     ((100, 100), 7))

    x = random.randrange(1, 100)
    logger.inof("Result of Random: " + str(x))
    for i in numberofrolls:
        if i[0][0] <= x <= i[0][1]:
            logger.info("Number of Rolls: " + str(i[1]))
            return i[1]


def translatespellcapacity(itemtype):
    wand = ["wand"]
    rod = ["rod"]
    staff = ["staff"]
    other = ["constant", "daily", "singleuse", "runepaper", "potion"]

    for item in wand:
        if item in itemtype:
            return "wand"
    for item in rod:
        if item in itemtype:
            return "rod"
    for item in staff:
        if item in itemtype:
            return "staff"
    for item in other:
        return item

    print("Unknown Itemtype " + str(itemtype))
    print("Aborting...")
    exit()


def getrichness():
    '''
    Returns random result from "Magic Item Treasure Size Chart"
    :return: List of integers
    '''
    richnesstable = (
        ((1, 30), [0, 0, 0, 0, 2]),
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
    x = random.randrange(1, 100)
    for select in richnesstable:
        if select[0][0] <= x <= select[0][1]:
            item = select[1]
    return (item)


def getcomposition(element):
    '''
    Returns Random Result from "Magic Item Treasure Composition Table" based on richness and richnesstable
    :param richness: List of Integers as stated in getrichness
    :param richnesstable: List of Strings
    :return: List of Magic item Types
    '''
    treasurecompositiontable = (
        ((1, 5), ["Normal", "Normal", "Normal", "Normal", "Normal"]),
        ((6, 10), ["Normal", "Normal", "Normal", "Light", "Light"]),
        ((11, 20), ["Normal", "Normal", "Light", "Light", "Light"]),
        ((21, 30), ["Normal", "Light", "Light", "Light", "Spell"]),
        ((31, 40), ["Light", "Light", "Light", "Bonus", "Spell"]),
        ((41, 50), ["Light", "Light", "Bonus", "Bonus", "Spell"]),
        ((51, 60), ["Light", "Bonus", "Bonus", "Bonus", "Bonus"]),
        ((61, 65), ["Bonus", "Bonus", "Bonus", "Bonus", "Bonus"]),
        ((66, 75), ["Bonus", "Bonus", "Bonus", "Spell", "Bonus"]),
        ((76, 85), ["Bonus", "Bonus", "Spell", "Spell", "Sp. Bonus"]),
        ((86, 90), ["Bonus", "Spell", "Spell", "Sp. Bonus", "Sp. Bonus"]),
        ((91, 94), ["Spell", "Spell", "Sp. Bonus", "Sp. Bonus", "Tome"]),
        ((95, 97), ["Spell", "Sp. Bonus", "Sp. Bonus", "Tome", "Special"]),
        ((98, 99), ["Sp. Bonus", "Sp. Bonus", "Tome", "Special", "Special"]),
        ((100, 100), ["Special", "Special", "Special", "Special", "Artifact"])
    )
    x = random.randrange(1, 100)
    treasurecomposition = ""
    for select in treasurecompositiontable:
        if select[0][0] <= x <= select[0][1]:
            treasurecomposition = select[1][element]
    return treasurecomposition


def getadditionalmagicitemcapabilities(oldtype):
    additionalcapabilities = ["Light", "Bonus", "Sp. Bonus"]
    compabilitiestable = (
        ((41, 50), [["Bonus"], ["Light"], ["Nothing"]]),
        ((51, 75), [["Bonus"], ["Light"], ["Light"]]),
        ((76, 88), [["Spell"], ["Spell"], ["Spell"]]),
        ((89, 91), [["Sp. Bonus"], ["Sp. Bonus"], ["Bonus"]]),
        ((92, 94), [["Bonus", "Spell"], ["Light", "Spell"], ["Light", "Spell"]]),
        ((95, 96), [["Sp. Bonus", "Spell"], ["Light", "Sp. Bonus"], ["Light", "Bonus"]]),
        ((97, 98), [["Bonus", "Sp. Bonus"], ["Sp. Bonus", "Spell"], ["Bonus", "Spell"]]),
        ((99, 99), [["Bonus", "Sp. Bonus", "Spell"], ["Light", "Sp. Bonus", "Spell"], ["Light", "Bonus", "Spell"]]),
        ((100, 100), [["Special"], ["Special"], ["Special"]])
    )
    x = random.randrange(1, 100)
    if x < 41:
        return ["Nothing"]
    else:
        buffer = ""
        for select in compabilitiestable:
            if select[0][0] <= x <= select[0][1]:
                buffer = select[1][additionalcapabilities.index(oldtype)]
        return buffer


def getitemfrommagicitemscapabilitieschart(type):
    '''
    Provides an Random item / capability based on given type as stated in "Magic Items Cpabilities Chart"
    :param type: "Light", "Bonus", "Sp. Bonus", "TYPE A", "TYPE B"
    :return: String
    '''
    magicitemstable = (
        ((1, 7), ["80%", "+5", "+ 1 Ess", "Staff", "Weapon", "1-H Slashing"]),
        ((8, 11), ["80%", "+5", "+1 Ess", "Staff", "Weapon", "1-H Concussion"]),
        ((12, 15), ["80%", "+5", "+ 1 Ess", "Staff", "Weapon", "2-Handed"]),
        ((16, 19), ["80%", "+5", "+1 Chan", "Staff", "Weapon", "Pole Arm"]),
        ((20, 22), ["80%", "+5", "+1 Chan", "Staff", "Weapon", "10 Arrows"]),
        ((23, 25), ["80%", "+5", "+1 Chan", "Staff", "Weapon", "10 Quarrels"]),
        ((26, 30), ["70%", "+10", "+ 1 Ment", "Staff", "Weapon", "Bow & Thrown"]),
        ((31, 35), ["70%", "+10", "+1 Hybrid", "Rod", "Weapon", "Special"]),
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
        ((90, 90), ["40%", "+15(M)", "x3 Ess", "Headband", "Bracers (Adrenal Def.)"]),
        ((91, 91), ["30%", "+20(M)", "+4 Chan", "Armband", "Belt (DB)"]),
        ((92, 92), ["30%", "+20(M)", "x3 Chan", "Armband", "Lockpick Kit"]),
        ((93, 93), ["20%", "+25(M)", "+4 Ment", "Necklace", "Disarm Trap Kit"]),
        ((94, 94), ["20%", "Special", "x3 Ment", "Necklace", "30 Pitons (Climbing)"]),
        ((95, 95), ["Special", "Special", "+4 Hybrid", "Ring", "Saddle (Riding)"]),
        ((96, 96), ["Special", "Special", "x3 Hybrid", "Ring", "Ring (DB)"]),
        ((97, 97), ["Special", "Special", "+5 Ess", "Ring", "Special"]),
        ((98, 98), ["Special", "Special", "x4 Ess", "Special", "Special"]),
        ((99, 99), ["Special", "Special", "Special", "Special", "Special"]),
        ((100, 100), ["Special", "Special", "Special", "Special", "Special"])
    )
    x = random.randrange(1, 100)
    typetocolumnlist = ["Light", "Bonus", "Sp. Bonus", "TYPE A", "TYPE B"]

    for select in magicitemstable:
        if select[0][0] <= x <= select[0][1]:
            item = select[1][typetocolumnlist.index(type)]
    return item


def retrieveitem(type):
    if type == "Light":
        item = getitemfrommagicitemscapabilitieschart("TYPE B")
        if item == "Special":
            item = "Special item!"
        reduction = getitemfrommagicitemscapabilitieschart("Light")
        if reduction == "Special":
            reduction = "Light special!"
        result = item + " - " + reduction + " weight"
        return result
    if type == "Bonus":
        pass


def retrievespell(listcategory, spelllist, level, spellcategory):
    if listcategory.find("Animist") != -1:
        listcategory = "Base List Animist"
    elif listcategory.find("Alchemist") != -1:
        listcategory = "Base List Alchemist"
    elif listcategory.find("Bard") != -1:
        listcategory = "Base List Bard"
    elif listcategory.find("Cleric") != -1:
        listcategory = "Base List Cleric"
    elif listcategory.find("Dabbler") != -1:
        listcategory = "Base List Dabbler"
    elif listcategory.find("Healer") != -1:
        listcategory = "Base List Healer"
    elif listcategory.find("Illusionist") != -1:
        listcategory = "Base List Illusionist"
    elif listcategory.find("Lay-Healer") != -1:
        listcategory = "Base List Lay-Healer"
    elif listcategory.find("Magent") != -1:
        listcategory = "Base List Magent"
    elif listcategory.find("Magician") != -1:
        listcategory = "Base List Magician"
    elif listcategory.find("Mentalist") != -1:
        listcategory = "Base List Mentalist"
    elif listcategory.find("Mystic") != -1:
        listcategory = "Base List Mystic"
    elif listcategory.find("Paladin") != -1:
        listcategory = "Base List Paladin"
    elif listcategory.find("Ranger") != -1:
        listcategory = "Base List Ranger"
    elif listcategory.find("Sorcerer") != -1:
        listcategory = "Base List Sorcerer"
    elif listcategory.find("Taoist-Monk") != -1:
        listcategory = "Base List Taoist-Monk"
    elif listcategory.find("Zen-Monk") != -1:
        listcategory = "Base List Zen-Monk"
    elif listcategory.find("Monk") != -1:
        listcategory = "Base List Monk"

    if listcategory.lower() == "special":
        spell = "special"
    elif listcategory.lower() == "cursed":
        spell = "cursed"
    else:
        spell = getspellfromfile(listcategory, spelllist, level, spellcategory)
    return spell


def retrieveartifact(type):
    '''
    todo: all
    :param type:
    :return:
    '''
    pass


def translatespelllisttofile(listname):
    '''
    also evil magician --> evil essence,
    Evil cleric --> evil channeling,
    Evil mentalist --> evil mentalism
    ach ja und für seer kannst du die dabbler nehmenNachricht eingeben
    :param listname:
    :return:
    '''
    # print(listname)

    listtofile = {
        "Evil Magician Base Lists": "Essence_Evil",
        "Evil Cleric Base Lists": "Channeling_Evil",
        "Evil Mentalist Base Lists": "Mentalism_Evil",
        "Essence_Magican_Base": "Base_List_Magican"
    }
    return listname


def getspelllist():
    spelllist = (
        ((1, 3), "Spell Defense", "Open Lists", "Spell Wall", "Open Lists", "Delving", "Open Lists",
         "Physical Erosion", "Evil Magician Base Lists"),
        ((4, 6), "Barrier Law", "Open Lists", "Essence's Perceptions", "Open Lists", "Cloaking", "Open Lists",
         "Matter Disruption", "Evil Magician Base Lists"),
        ((7, 9), "Detection Mastery", "Open Lists", "Rune Mastery", "Open Lists", "Damage Resistance", "Open Lists",
         "Dark Contacts", "Evil Magician Base Lists"),
        ((10, 12), "Lofty Movements", "Open Lists", "Essence Hand", "Open Lists", "Anticipations", "Open Lists",
         "Dark Summons", "Evil Magician Base Lists"),
        ((13, 15), "Weather Ways", "Open Lists", "Unbarring Ways", "Open Lists", "Attack Avoidance", "Open Lists",
         "Darkness", "Evil Magician Base Lists"),
        ((16, 18), "Sound's Way", "Open Lists", "Physical Enhancement", "Open Lists", "Brilliance", "Open Lists",
         "Monk's Bridge", "Monk Base Lists"),
        ((19, 21), "Light's Way", "Open Lists", "Lesser Illusions", "Open Lists", "Self Healing", "Open Lists",
         "Evasions", "Monk Base Lists"),
        ((22, 24), "Purifications", "Open Lists", "Detecting Ways", "Open Lists", "Detections", "Open Lists",
         "Body Reins", "Monk Base Lists"),
        ((25, 27), "Concussion's Ways", "Open Lists", "Elemental Shields", "Open Lists", "Illusions", "Open Lists",
         "Monk's Sense", "Monk Base Lists"),
        ((28, 30), "Nature's Law", "Open Lists", "Delving Ways", "Open Lists", "Spell Resistance", "Open Lists",
         "Body Renewal", "Monk Base Lists"),
        ((31, 33), "Blood Law", "Closed Lists", "Invisible Ways", "Closed Lists", "Sense Mastery", "Closed Lists",
         "Disease", "Evil Cleric Base Lists"),
        ((34, 36), "Bone Law", "Closed Lists", "Living Change", "Closed Lists", "Gas Manipulation", "Closed Lists",
         "Dark Channels", "Evil Cleric Base Lists"),
        ((35, 39), "Organ Law", "Closed Lists", "Spirit Mastery", "Closed Lists", "Shifting", "Closed Lists",
         "Dark Lore", "Evil Cleric Base Lists"),
        ((40, 42), "Muscle Law", "Closed Lists", "Spell Reins", "Closed Lists", "Liquid Manipulation", "Closed Lists",
         "Curses", "Evil Cleric Base Lists"),
        ((43, 45), "Nerve Law", "Closed Lists", "Lofty Bridge", "Closed Lists", "Speed", "Closed Lists", "Necromancy",
         "Evil Cleric Base Lists"),
        ((46, 48), "Locating Ways", "Closed Lists", "Spell Enhancement", "Closed Lists", "Mind Mastery", "Closed Lists",
         "Path Mastery", "Ranger Base Lists"),
        ((49, 51), "Calm Spirits", "Closed Lists", "Dispelling Ways", "Closed Lists", "Solid Manipulation",
         "Closed Lists", "Moving Ways", "Ranger Base Lists"),
        ((52, 54), "Creations", "Closed Lists", "Shield Mastery", "Closed Lists", "Telekinesis", "Closed Lists",
         "Nature's Guises", "Ranger Base Lists"),
        ((55, 57), "Symbolic Ways", "Closed Lists", "Rapid Ways", "Closed Lists", "Mind's Door", "Closed Lists",
         "Inner Walls", "Ranger Base Lists"),
        ((58, 60), "Lore", "Closed Lists", "Gate Mastery", "Closed Lists", "Movement", "Closed Lists", "Nature's Ways",
         "Ranger Base Lists"),
        ((61, 63), "Channels", "Cleric Base Lists", "Fire Law", "Magician Base Lists", "Presence",
         "Mentalist Base Lists", "Soul Destruction", "Sorcerer Base Lists"),
        ((64, 66), "Summons", "Cleric Base Lists", "Ice Law", "Magician Base Lists", "Mind Merge",
         "Mentalist Base Lists", "Gas Destruction", "Sorcerer Base Lists"),
        ((67, 69), "Communal Ways", "Cleric Base Lists", "Earth Law", "Magician Base Lists", "Mind Control",
         "Mentalist Base Lists", "Solid Destruction", "Sorcerer Base Lists"),
        ((70, 72), "Life Mastery", "Cleric Base Lists", "Light Law", "Magician Base Lists", "Sense Control",
         "Mentalist Base Lists", "Fluid Destruction", "Sorcerer Base Lists"),
        ((73, 75), "Protections", "Cleric Base Lists", "Wind Law", "Magician Base Lists", "Mind Attack",
         "Mentalist Base Lists", "Mind Destruction", "Sorcerer Base Lists"),
        ((76, 78), "Repulsions", "Cleric Base Lists", "Water Law", "Magician Base Lists", "Mind Speech",
         "Mentalist Base Lists", "Flesh Destruction", "Sorcerer Base Lists"),
        ((79, 79), "Surface Ways", "Healer Base Lists", "Illusion Mastery", "Illusionist Base Lists", "Past Visions",
         "Seer Base Lists", "Confusing Ways", "Mystic Base Lists"),
        ((80, 80), "Bone Ways", "Healer Base Lists", "Mind Sense Molding", "Illusionist Base Lists", "Mind Visions",
         "Seer Base Lists", "Hiding", "Mystic Base Lists"),
        ((81, 81), "Muscle Ways", "Healer Base Lists", "Guises", "Illusionist Base Lists", "True Perception",
         "Seer Base Lists", "Mystical Change", "Mystic Base Lists"),
        ((82, 82), "Organ Ways", "Healer Base Lists", "Sound Molding", "Illusionist Base Lists", "Future Visions",
         "Seer Base Lists", "Liquid Alteration", "Mystic Base Lists"),
        ((83, 83), "Blood Ways", "Healer Base Lists", "Light Molding", "Illusionist Base Lists", "Sense Through Others",
         "Seer Base Lists", "Solid Alteration", "Mystic Base Lists"),
        ((84, 84), "Transferring Ways", "Healer Base Lists", "Fcel-Taste-Smell", "Illusionist Base Lists", "True Sight",
         "Seer Base Lists", "Gas Alteration", "Mystic Base Lists"),
        ((85, 85), "Nature's Movement", "Animist Base Lists", "Enchanting Ways", "Alchemist Base Lists",
         "Muscle Mastery", "Lay Healer Base Lists", "Time's Bridge", "Astrologer Base Lists"),
        ((86, 86), "Plant Mastery", "Animist Base Lists", "Essence Imbedding", "Alchemist Base Lists",
         "Concussion Mastery", "Lay Healer Base Lists", "Way of the Voice", "Astrologer Base Lists"),
        ((87, 87), "Animal Mastery", "Animist Base Lists", "Ment.-Chan. Imbedding", "Alchemist Base Lists",
         "Bone Mastery", "Lay Healer Base Lists", "Holy Vision", "Astrologer Base Lists"),
        ((88, 88), "Herb Mastery", "Animist Base Lists", "Organic Skills", "Alchemist Base Lists", "Blood Mastery",
         "Lay Healer Base Lists", "Far Voice", "Astrologer Base Lists"),
        ((89, 89), "Nature's Lore", "Animist Base Lists", "Liquid-Gas Skills", "Alchemist Base Lists", "Prosthetics",
         "Lay Healer Base Lists", "Starlights", "Astrologer Base Lists"),
        ((90, 90), "Nature's Protection", "Animist Base Lists", "Inorganic Skills", "Alchemist Base Lists",
         "Nerve & Organ Mastery", "Lay Healer Base Lists", "Starsense", "Astrologer Base Lists"),
        ((91, 91), "special", "special", "special", "special", "special", "special", "Mind Erosion",
         "Evil Mentalist Base Lists"),
        ((92, 92), "special", "special", "special", "special", "special", "special", "Mind Subversion",
         "Evil Mentalist Base Lists"),
        ((93, 93), "special", "special", "special", "special", "special", "special", "Mind Death",
         "Evil Mentalist Base Lists"),
        ((94, 94), "special", "special", "special", "special", "special", "special", "Mind Disease",
         "Evil Mentalist Base Lists"),
        ((95, 95), "special", "special", "special", "special", "special", "special", "Mind Domination",
         "Evil Mentalist Base Lists"),
        ((96, 96), "cursed", "cursed", "cursed", "cursed", "cursed", "cursed", "Lore", "Bard Base Lists"),
        ((97, 97), "cursed", "cursed", "cursed", "cursed", "cursed", "cursed", "Contolling Songs", "Bard Base Lists"),
        ((98, 98), "cursed", "cursed", "cursed", "cursed", "cursed", "cursed", "Sound Control", "Bard Base Lists"),
        ((99, 99), "cursed", "cursed", "cursed", "cursed", "cursed", "cursed", "Sound Projection", "Bard Base Lists"),
        ((100, 100), "cursed", "cursed", "cursed", "cursed", "cursed", "cursed", "Item Lore", "Bard Base Lists")
    )
    spelltypelist = (
        ((1, 25), 1, "Channeling"),
        ((26, 74), 3, "Essence"),
        ((75, 90), 5, "Mentalism"),
        ((91, 100), 7, "Evil/Semi/Hybrid")
    )
    x = random.randrange(1, 100)
    for select in spelltypelist:
        if select[0][0] <= x <= select[0][1]:
            spelltype = select[1]
            spellcat = select[2]

    x = random.randrange(1, 100)
    spell = {}
    for select in spelllist:
        if select[0][0] <= x <= select[0][1]:
            spell["Spelllist"] = select[spelltype]
            spell["listcategory"] = select[spelltype + 1]
    spell["Category"] = spellcat
    return spell


def getrandomitemtype():
    itemtype = ""
    items = (
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
    x = random.randrange(1, 100)
    for select in items:
        if select[0][0] <= x <= select[0][1]:
            itemtype = select[1]
    return itemtype


def getspelllevel(type):
    '''
    :param type: possible parameters runepaper, singleuse, daily1, daily2, daily3, daily4, wand, rod, staff, constant, tome
    :return:
    '''


    matchmatrix = (
        (1, 20),
        (21, 25),
        (26, 30),
        (31, 35),
        (36, 40),
        (41, 45),
        (46, 50),
        (51, 55),
        (56, 60),
        (61, 65),
        (66, 70),
        (71, 75),
        (76, 80),
        (81, 85),
        (86, 90),
        (91, 94),
        (95, 97),
        (98, 99),
        (100, 100)
    )
    x = random.randrange(1, 100)
    selected = 0
    counter = -1
    for select in matchmatrix:
        counter += 1
        if select[0] <= x <= select[1]:
            selected = counter
            break


    result = {
        "runepaper": ["1", "2", "2", "2", "2", "3", "3", "3", "4", "4", "5", "5", "6", "7", "8", "9", "10", "HL", "HL"],
        "potion": ["1", "1", "1", "2", "2", "2", "2", "2", "3", "3", "4", "4", "5", "6", "7", "8", "9", "10", "HL"],
        "singleuse": ["1", "2", "2", "3", "3", "4", "4", "5", "5", "6", "6", "7", "7", "8", "9", "10", "HL", "HL", "HL"],
        "daily1": ["1", "1", "1", "1", "2", "2", "2", "3", "3", "4", "4", "5", "5", "6", "7", "8", "9", "10", "HL"],
        "daily2": ["1", "1", "1", "1", "1", "2", "2", "2", "2", "3", "3", "3", "4", "4", "5", "5", "6", "7", "HL"],
        "daily3": ["1", "1", "1", "1", "1", "1", "2", "2", "2", "2", "2", "3", "3", "3", "4", "4", "5", "5", "HL"],
        "daily4": ["1", "1", "1", "1", "1", "1", "1", "1", "2", "2", "2", "2", "2", "2", "3", "3", "3", "3", "HL"],
        "wand": ["1", "1", "1", "1", "1", "1", "1", "1", "2", "2", "2", "2", "2", "2", "2", "2", "2", "2", "2"],
        "rod": ["1", "1", "1", "2", "2", "2", "2", "2", "3", "3", "3", "3", "4", "4", "4", "5", "5", "5", "5"],
        "staff": ["1", "2", "3", "3", "4", "4", "5", "5", "6", "6", "7", "7", "8", "8", "9", "9", "10", "10", "HL"],
        "constant": ["1", "2", "2", "3", "3", "4", "4", "5", "5", "6", "6", "7", "7", "8", "8", "9", "10", "10", "HL"],
        "tome": ["1-5", "1-5", "6- 10", "6- 10", "6- 10", "6- 10", "1- 10", "1- 10",
                 "1-10", "1-10", "1-10", "11-20", "11- 20", "11-20", "1-20", "1-20",
                 "1-25", "1-30", "1-50"]
    }

    return result[type][selected]

def getmoney(treasurequality, logger):
    logger.info("getmoney - Quality: " + str(treasurequality))
    money = (((1, 10), (50, "ZS"), (500, "ZS"), (1000, "ZS"), (5000, "ZS"), (10000, "ZS")),
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
             ((100, 100), (10, "Ed"), (25, "Sch"), (100, "Sch"), (500, "Sch"), (1000, "Sch")))

    x = random.randrange(1, 100)
    logger.info("getmoney - Random: " + str(x))
    for select in money:
        if select[0][0] <= x <= select[0][1]:
            item = select[treasurequality]
    logger.info("getmoney - Money: " + str(item))
    return item


def getspellfromfile(listcategory, spelllist, level, spellcategory):
    if listcategory.find("Lists") != -1:
        buffer = listcategory[:-6]
    elif listcategory.find("Evil") != -1:
        buffer = "Evil"
    elif listcategory.find("List") != -1:
        buffer = listcategory
    else:
        print("getspellfromfile failed!")
        print(listcategory + "\n" + spelllist + "\n" + str(level))
        exit()
    if buffer.find("Base") != -1:
        buildfilepath = "./data/magic/" + buffer + "/" + spelllist + ".csv"
    else:
        buildfilepath = "./data/magic/" + spellcategory + "_" + buffer + "/" + spelllist + ".csv"
    buildfilepath = buildfilepath.replace("'", "").replace(" ", "_")
    filepath = translatespelllisttofile(buildfilepath)

    if not path.exists(filepath):
        data = "File not found: " + str(filepath)
    else:
        try:
            count = len(open(filepath).readlines()) # ToDo: Find Error UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d in position 325: character maps to <undefined>
        except Exception as e:
            print(filepath)
            print(e)
            count = 0

        if count > 1:
            with open(filepath, encoding="utf8") as csvfile:
                save = {}
                file = csv.DictReader(csvfile, delimiter=',', quotechar='"')
                if level.endswith("HL"):
                    level = random.randint(int(level[:-2]) + 1, 50) # Fix for HighLevel Spells. Random Level between last found spell level and level 50.
                for row in file:
                    if int(row["Lvl"]) < int(level):
                        save = row
                    elif int(row["Lvl"]) == int(level):
                        data = row
                        break
                    else:
                        data = save
        else:
            data = "No Data in File: " + str(filepath)

    if data:
        return data
    else:
        return ""

def createtreasure(treasurtype, treasurequality):
    #initiate logging
    logging.basicConfig(filename="createtreasures.log", level=logging.DEBUG, filemode="w")
    logging.debug("Start")
    logger = logging.getLogger("createtreasures")

    random.seed()
    control = Controller(treasurtype, treasurequality, logger)

# Main
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Treasure")
    parser.add_argument('treasuretype', choices=["money", "magic", "both", "debug"], type=str)
    parser.add_argument('treasurequality', choices=range(1, 6), type=int, nargs="?")
    args = parser.parse_args()

    createtreasure(args.treasuretype, args.treasurequality)