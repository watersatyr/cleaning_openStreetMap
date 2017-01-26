#!usr/bin/env python
# -*- coding: utf-8 -*-
# Title: p3_clean_value_class.py
# author: sle7in
# class: Udacity SQL Project 3
# date: 1/25/2016

import re

class CleanValue(object):
    """CleanValue returns a corrected value (determined by audit).
    It requires the value's key to determine cleaning route."""

    def __init__(self):
        """will later add class variables as instantiateable """
        pass

    expected_street_types = ["Street", "Avenue", "Boulevard", "Drive", "Court",
        "Place", "Square", "Lane", "Road", "Trail", "Parkway", "Commons", "Way",
        "Circle", "East", "West", "North", "South", "Southwest", "Alley", "Square"]

    mapping = { "st" : "Street",
                "St" : "Street",
                "St." : "Street",
                "Aventue" : "Avenue",
                "Rd" : "Road",
                "Dr" : "Drive",
                "Ct" : "Court" }

    foco_manual_updates = { "S Summit View #11" : "S Summit View Drive",
                            "Old Town Square #238" : "Old Town Square",
                            "S Timberline" : "S Timberline Road",
                            "West Oak" : "West Oak Street",
                            "Seventh-Day Adventist Church" : "E Pitkin Street" }

    expected_postal_codes = ["80521", "80522", "80523", "80524", "80525", "80526",
                             "80527", "80528", "80553", "80547", "80538", "80535" ]


    street_type_re = re.compile(r"\b\S+\.?$", re.IGNORECASE)

    def correct_post(self, postal_code):
        """Correct postal code if not expected."""
        if postal_code[:5] not in self.expected_postal_codes:

            re_state_prefix = re.compile(r"\D*\s+", re.IGNORECASE)
            if re_state_prefix.match(postal_code):
                postal_code = re.sub(re_state_prefix, '', postal_code)   # remove any letters/spaces from 'CO 80525'
            elif postal_code == "80701":
                postal_code = "80525"     # specific to correct weigh station postal_code typo

        return postal_code

    def correct_street(self, street_name):
        """Replaces street_type with its mapping if not expected."""
        street_name = street_name.strip()
        street_type = self.street_type_re.search(street_name).group()

        if street_type not in self.expected_street_types:

            if street_type in self.mapping:
                street_name = street_name.replace(street_type, self.mapping[street_type])
            elif street_name in self.foco_manual_updates:
                street_name = self.foco_manual_updates[street_name]

        return street_name

    # zip and streets in one function accepting any value
    def process(self, key, value):
        """Accepts key and value. Calls the correct value cleaner based on key."""

        if "post" in key:
            return self.correct_post(value)
        elif key == "addr:street":
            return self.correct_street(value)
        else:
            return value
