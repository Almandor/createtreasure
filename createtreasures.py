#!/usr/bin/python3

'''
Programname: createtrasures.py
Description: Rolemaster-Support tool to generate Treasure
'''

import argparse
import csv
import random
from sys import exit
import pprint
from os import path
import re


def getnumberofrolls():
    '''
    Randomizes number of roles from Wealth Treasure Size Chart.
    Returns Result
    :return:
    '''
    numberofrolls = (((1, 30), 1),
                     ((31, 55), 2),
                     ((56, 75), 3),
                     ((76, 90), 4),
                     ((91, 97), 5),
                     ((98, 99), 6),
                     ((100, 100), 7))

    x = random.randrange(1, 100)

    for i in numberofrolls:
        if i[0][0] <= x <= i[0][1]:
            return i[1]


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
    print("Roll: " + str(x))
    for select in richnesstable:
        if select[0][0] <= x <= select[0][1]:
            item = select[1]
    return (item)


def getcomposition(richness, richnesstable):
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
    treasurecomposition = []
    for element in range(len(richness)):
        if richness[element] > 0:
            print(str(richness[element]) + "x " + richnesstable[element])
            for i in range(richness[element]):
                x = random.randrange(1, 100)
                print("Roll: " + str(x))
                for select in treasurecompositiontable:
                    if select[0][0] <= x <= select[0][1]:
                        treasurecomposition.append(select[1][element])
    return treasurecomposition


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
        ((26, 30), ["70%", "+ 10", "+ 1 Ment", "Staff", "Weapon", "Bow & Thrown"]),
        ((31, 35), ["70%", "+ 10", "+1 Hybrid", "Rod", "Weapon", "Special"]),
        ((36, 44), ["70%", "+ 10", "+2 Ess", "Rod", "Shield"]),
        ((45, 50), ["60%", "+15", "+2 Chan", "Rod", "Rigid Leather Armor"]),
        ((51, 53), ["60%", "+15", "+2 Ment", "Rod", "Soft Leather Armor"]),
        ((54, 56), ["60%", "+ 15", "+2 Hybrid", "Rod", "Helmet"]),
        ((57, 62), ["60%", "+20", "+3 Ess", "Wand", "Chain Armor"]),
        ((63, 68), ["50%", "+5(M)", "x2 Ess", "Wand", "Plate Armor"]),
        ((69, 72), ["50%", "+5(M)", "+3 Chan", "Wand", "Lockpick Kit"]),
        ((73, 76), ["50%", "+5(M)", "x2 Chan", "Wand", "Disarm Trap Kit"]),
        ((77, 78), ["50%", "+10(M)", "+3 Ment", "Robes", "Gloves (Martial Arts)"]),
        ((79, 80), ["50%", "+10(M)", "x2 Ment", "Robes", "Glasses (Perception)"]),
        ((81, 82), ["40%", "+10(M)", "+3 Hybrid", "Robes", "Cloak (Hiding)"]),
        ((83, 84), ["40%", "+ 10(M)", "x2 Hybrid", "Robes", "Boots (Stalking)"]),
        ((85, 85), ["40%", "+ 10(M)", "+4 Ess", "Robes", "Bridle (Riding)"]),
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
    print(item)


def getitemandspelllevel(type="random"):
    '''
    Provides, if requested, type and level of magical Item based on "Item and Spell Level Chart"
    :param type: Possible values: random, Runepaper, Potion, Singleuse, Daily1 - 4, Wand, Rod, Staff, Constant and Tome
    :return: type, itemdetails as string
    '''
    if type == "random":
        x = random.randint(1, 100)
        if 1 <= x <= 30:
            type = "Runepaper"
        elif 31 <= x <= 50:
            type = "Potion"
        elif 51 <= x <= 65:
            type = "Singleuse"
        elif 66 <= x <= 70:
            type = "Daily1"
        elif 71 <= x <= 75:
            type = "Daily2"
        elif 76 <= x <= 80:
            type = "Daily3"
        elif 81 <= x <= 85:
            type = "Daily4"
        elif 86 <= x <= 94:
            type = "Wand"
        elif 95 <= x <= 98:
            type = "Rod"
        elif  x == 99:
            type = "Staff"
        else:
            type = "Constant"

    listposition = ["filler", "Runepaper", "Potion", "Singleuse", "Daily1", "Daily2", "Daily3", "Daily4", "Wand",
                    "Rod", "Staff", "Constant", "Tome"]
    if type not in listposition[1:]:
        print("received unexpected value in getitemandspelllevel. Got: " + str(type))
        raise

    matchlist = (
        ((1, 20), 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, "1-5"),
        ((21, 25), 2, 1, 2, 1, 1, 1, 1, 1, 1, 2, 2, "1-5"),
        ((26, 30), 2, 1, 2, 1, 1, 1, 1, 1, 1, 3, 2, "6-10"),
        ((31, 35), 2, 2, 3, 1, 1, 1, 1, 1, 2, 3, 3, "6-10"),
        ((36, 40), 2, 2, 3, 2, 1, 1, 1, 1, 2, 4, 3, "6-10"),
        ((41, 45), 3, 2, 4, 2, 2, 1, 1, 1, 2, 4, 4, "6-10"),
        ((46, 50), 3, 2, 4, 2, 2, 2, 1, 1, 2, 5, 4, "1-10"),
        ((51, 55), 3, 2, 5, 3, 2, 2, 1, 1, 2, 5, 5, "1-10"),
        ((56, 60), 4, 3, 5, 3, 2, 2, 2, 2, 3, 6, 5, "1-10"),
        ((61, 65), 4, 3, 6, 4, 3, 2, 2, 2, 3, 6, 6, "1-10"),
        ((66, 70), 5, 4, 6, 4, 3, 2, 2, 2, 3, 7, 6, "1-10"),
        ((71, 75), 5, 4, 7, 5, 3, 3, 2, 2, 3, 7, 7, "11-20"),
        ((76, 80), 6, 5, 7, 5, 4, 3, 2, 2, 4, 8, 7, "11-20"),
        ((81, 85), 7, 6, 8, 6, 4, 3, 2, 2, 4, 8, 8, "11-20"),
        ((86, 90), 8, 7, 9, 7, 5, 4, 3, 2, 4, 9, 8, "1-20"),
        ((91, 94), 9, 8, 10, 8, 5, 4, 3, 2, 5, 9, 9, "1-20"),
        ((95, 97), 10, 9, "HL", 9, 6, 5, 3, 2, 5, 10, 10, "1-25"),
        ((98, 99), "HL", 10, "HL", 10, 7, 5, 3, 2, 5, 10, 10, "1-30"),
        ((100, 100), "HL", "HL", "HL", "HL", "HL", "HL", "HL", 2, 5, "HL", "HL", "l-50")
    )
    x = random.randint(1, 100)
    print("Debug x: " + str(x))
    for item in matchlist:
        if item[0][0] <= x <= item[0][1]:
            return type, str(item[listposition.index(type)])
    print("Error. getitemandspelllevel failure. Item location not found. Aborting")
    exit()

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


def retrievespell(type):
    spelllist = getspelllist()


def retrieveartifact(type):
    pass


def itemresult():
    richnesstable = ["Poor", "Very Poor", "Normal", "Rich", "Very Rich"]
    richness = getrichness()
    itemcompositionlist = getcomposition(richness, richnesstable)
    print(itemcompositionlist)
    itemlist = []
    for i in itemcompositionlist:
        if i in ["Normal", "Light", "Bonus", "Sp. Bonus"]:
            itemlist.append(retrieveitem(i))
        elif i == "Spell":
            itemlist.append(retrievespell(i))
        elif i == "Tome":
            a = [getitemorspelllevel("tome")[0], getitemorspelllevel("tome")[1]] + getspelllist()
        elif i == "Artifact":
            itemlist.append(retrieveartifact(i))
        else:
            print("Error! Type " + str(i) + " not found. Aborting!")
            exit()

def translatespelllisttofile(listname):
    '''
    also evil magician --> evil essence,
    Evil cleric --> evil channeling,
    Evil mentalist --> evil mentalism
    ach ja und für seer kannst du die dabbler nehmenNachricht eingeben
    :param listname:
    :return:
    '''


    listtofile = {
        "Evil Magician Base Lists": "Essence_Evil",
        "Evil Cleric Base Lists": "Channeling_Evil",
        "Evil Mentalist Base Lists": "Mentalism_Evil",
        "Essence_Magican_Base": "Base_List_Magican"
    }

def getspelllist():
    spelllist = (
        ((1, 3), "Spell Defense", "Open Lists", "Spell Wall", "Open Lists", "Delving", "Open Lists",
         "Physical Erosion", "Evil Magician Base Lists"),
        ((4, 6), "Barrier Law", "Open Lists", "Essence's Perception", "Open Lists", "Cloaking", "Open Lists",
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
            spell["Listcategory"] = select[spelltype + 1]
    spell["Category"] = spellcat
    return spell


def getitemorspelllevel(type):
    '''
    :param type: possible parameters random, runepaper, singleuse, daily1, daily2, daily3, daily4, wand, rod, staff, constant, tome
    :return:
    '''
    if type == "random":
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
                type = select[1]

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
        "runepaper": ["1st", "2nd", "2nd", "2nd", "2nd", "3rd", "3rd", "3rd", "4th", "4th", "5th", "5th", "6th", "7th",
                      "8th", "9th", "10th", "HL", "HL"],
        "potion": ["1st", "1st", "1st", "2nd", "2nd", "2nd", "2nd", "2nd", "3rd", "3rd", "4th", "4th", "5th", "6th",
                   "7th", "8th", "9th", "10th", "HL"],
        "singleuse": ["1st", "2nd", "2nd", "3rd", "3rd", "4th", "4th", "5th", "5th", "6th", "6th", "7th", "7th", "8th",
                      "9th", "10th", "HL", "HL", "HL"],
        "daily1": ["1st", "1st", "1st", "1st", "2nd", "2nd", "2nd", "3rd", "3rd", "4rd", "4th", "5th", "5th", "6th",
                   "7th", "8th", "9th", "10th", "HL"],
        "daily2": ["1st", "1st", "1st", "1st", "1st", "2nd", "2nd", "2nd", "2nd", "3rd", "3rd", "3rd", "4th", "4th",
                   "5th", "5th", "6th", "7th", "HL"],
        "daily3": ["1st", "1st", "1st", "1st", "1st", "1st", "2nd", "2nd", "2nd", "2nd", "2nd", "3rd", "3rd", "3rd",
                   "4th", "4th", "5th", "5th", "HL"],
        "daily4": ["1st", "1st", "1st", "1st", "1st", "1st", "1st", "1st", "2nd", "2nd", "2nd", "2nd", "2nd", "2nd",
                   "3rd", "3rd", "3rd", "3rd", "HL"],
        "wand": ["1st", "1st", "1st", "1st", "1st", "1st", "1st", "1st", "2nd", "2nd", "2nd", "2nd", "2nd", "2nd",
                 "2nd", "2nd", "2nd", "2nd", "2nd"],
        "rod": ["1st", "1st", "1st", "2nd", "2nd", "2nd", "2nd", "2nd", "3rd", "3rd", "3rd", "3rd", "4th", "4th", "4th",
                "5th", "5th", "5th", "5th"],
        "staff": ["1st", "2nd", "3rd", "3rd", "4th", "4th", "5th", "5th", "6th", "6th", "7th", "7th", "8th", "8th",
                  "9th", "9th", "10th", "10th", "HL"],
        "constant": ["1st", "2nd", "2nd", "3rd", "3rd", "4th", "4th", "5th", "5th", "6th", "6th", "7th", "7th", "8th",
                     "8th", "9th", "10th", "10th", "HL"],
        "tome": ["lst-5th", "lst-5th", "6th- 10th", "6th- 10th", "6th- 10th", "6th- 10th", "1st- 10th", "1st- 10th",
                 "1st- 10th", "1st- 10th", "1st- 10th", "llth-20th", "llth- 20th", "llth-20th", "lst-20th", "lst-20th",
                 "lst-25th", "lst-30th", "lst-50th"]
    }

    return type, result[type][selected]

def getmoney(rolls, treasurequality):
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
    result = {}
    if type(treasurequality) != int:
        print("Treasuretype not configured. Please use Int between 1 and 5")
        exit()
    print("Rolling Treasure...")

    for i in range(1, rolls + 1):
        x = random.randrange(1, 100)
        for select in money:
            if select[0][0] <= x <= select[0][1]:
                item = select[treasurequality]
                if item[1] not in result:
                    result[item[1]] = item[0]
                else:
                    result[item[1]] += item[0]

    return result


def getspellfromfile(spell):
    if spell["Listcategory"].find("List") != -1:
        buffer = spell["Listcategory"][:-6]
        print("Debug Buffer: " + buffer)
    elif spell["Listcategory"].find("Evil") != -1:
        buffer = "Evil"
    else:
        print("getspellfromfile failed!")
        pprint.pprint(spell)
        exit()
    buildfilepath = "./data/magic/" + spell["Category"] + "_" + buffer + "/" + spell["Spelllist"] + ".csv"
    buildfilepath = buildfilepath.replace("'", "").replace(" ", "_")
    filepath = translatespelllisttofile(buildfilepath)
    if not path.exists(filepath):
        print("File not found:")
        print(filepath)
    return spell

# Main

parser = argparse.ArgumentParser(description="Generate Treasure")
parser.add_argument('treasuretype', choices=["money", "magic", "both", "debug"], type=str)
parser.add_argument('treasurequality', choices=range(1, 6), type=int, nargs="?")
args = parser.parse_args()

random.seed()

if args.treasuretype in ["money", "both"]:

    rolls = getnumberofrolls()
    moneyresult = getmoney(rolls, args.treasurequality)

    print("Geldwerte:")
    if "Sch" in moneyresult:
        print("Schmuckstücke: " + str(moneyresult["Sch"]))
    if "Ed" in moneyresult:
        print("Edelsteine: " + str(moneyresult["Ed"]))
    if "MS" in moneyresult:
        print("Mithril: " + str(moneyresult["MS"]))
    if "GS" in moneyresult:
        print("Gold: " + str(moneyresult["GS"]))
    if "SS" in moneyresult:
        print("Silber: " + str(moneyresult["SS"]))
    if "BS" in moneyresult:
        print("Bronze: " + str(moneyresult["BS"]))
    if "KS" in moneyresult:
        print("Kupfer: " + str(moneyresult["KS"]))
    if "ZS" in moneyresult:
        print("Zinn: " + str(moneyresult["ZS"]))

if args.treasuretype in ["magic", "both"]:
    itemresult()

if args.treasuretype == "debug":
    a, b = getitemandspelllevel()
    print("Type: " + a)
    spell = getspelllist()

    if spell["Listcategory"].find("Animist") != -1:
        spell["Listcategory"] = "Base List Animist"
    elif spell["Listcategory"].find("Alchemist") != -1:
        spell["Listcategory"] = "Base List Alchemist"
    elif spell["Listcategory"].find("Bard") != -1:
        spell["Listcategory"] = "Base List Bard"
    elif spell["Listcategory"].find("Cleric") != -1:
        spell["Listcategory"] = "Base List Cleric"
    elif spell["Listcategory"].find("Dabbler") != -1:
        spell["Listcategory"] = "Base List Dabbler"
    elif spell["Listcategory"].find("Healer") != -1:
        spell["Listcategory"] = "Base List Healer"
    elif spell["Listcategory"].find("Illusionist") != -1:
        spell["Listcategory"] = "Base List Illusionist" # fortsetzen

    spell["Level"] = b
    pprint.pprint(spell)
    if spell["Listcategory"].lower() == "special":
        print("Special!")
    elif spell["Listcategory"].lower() == "cursed":
        print("Cursed!")
    else:
        spell = getspellfromfile(spell)