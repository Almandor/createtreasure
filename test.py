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
        if etype == "random":
            typelist = []
            for item in self.datafiles:
                typelist.append(path.splitext(item)[0])
            etype = typelist[random.randint(0, len(typelist) -1)]

        selected = random.randint(0, len(self.datastore[etype])-1 )
        return self.datastore[etype][selected][0]

        # pprint.pprint(self.datastore)


a = DeliverItemFromFile()
print(a.output("random"))
