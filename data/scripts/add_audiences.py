#!/usr/bin/env python3
"""
Fold the target-audience analysis into the dashboard aggregate.

Source of truth is data/bq/pdi_unique_products.csv, labelled by
classify_target_consumers.py. That file is licensed PDI data and stays out of
the repo, so the reduced aggregate is embedded here as a literal — same pattern
as add_segments.py.

Carries three views of the same nine audiences:
  auds            what convenience-store sell-through looks like (PDI, measured)
  demand.now      total US demand 2025, PDI blended with Mintel MULO on Mintel
                  channel weights (convenience 59.9% / everything else 40.1%)
  demand.future   2030 projection against Mintel's $38.6B central forecast

Writes data["audiences"] into public/data/dashboard.json. Idempotent.
"""
import json
import os

AUD = json.loads(r'''
{
 "total": 7123579032.89,
 "skus": 2309,
 "brands": 232,
 "window": "lifetime PDI convenience-channel sales, Jan 2016 \u2013 2026-07-01",
 "auds": [
  {
   "name": "Young adults",
   "age": "18-34",
   "gender": "Male-skewing",
   "note": "25-34s are about twice as likely as the average adult to drink it - the youngest-skewing large brand in the category.",
   "skus": 726,
   "rev": 5070972624.84,
   "share": 71.2,
   "brandN": 99,
   "top": [
    {
     "b": "Red Bull",
     "r": 2655781943.86
    },
    {
     "b": "Monster",
     "r": 2147329534.74
    },
    {
     "b": "Rockstar",
     "r": 213794904.07
    },
    {
     "b": "AMP",
     "r": 19842987.98
    },
    {
     "b": "Mtn Dew (energy)",
     "r": 19115761.18
    },
    {
     "b": "Clean Cause",
     "r": 1221701.24
    },
    {
     "b": "Bar Stool\u00c2",
     "r": 1192905.28
    },
    {
     "b": "Hoist",
     "r": 1085879.3
    }
   ],
   "prod": [
    {
     "d": "RED BULL ORIGINAL ENERGY DRINK 12 OZ CAN",
     "b": "Red Bull",
     "fl": "Original",
     "sz": "12 OZ",
     "st": 35167,
     "r": 564460135.29,
     "last": "2026-07-01"
    },
    {
     "d": "MONSTER",
     "b": "Monster",
     "fl": "",
     "sz": "",
     "st": 35203,
     "r": 527655261.92,
     "last": "2026-07-01"
    },
    {
     "d": "RED BULL",
     "b": "Red Bull",
     "fl": "",
     "sz": "",
     "st": 35148,
     "r": 285997428.3,
     "last": "2026-07-01"
    },
    {
     "d": "MONSTER",
     "b": "Monster",
     "fl": "",
     "sz": "",
     "st": 34843,
     "r": 243287784.98,
     "last": "2026-07-01"
    },
    {
     "d": "RED BULL",
     "b": "Red Bull",
     "fl": "",
     "sz": "",
     "st": 34649,
     "r": 232117749.47,
     "last": "2026-07-01"
    },
    {
     "d": "RED BULL ORIGINAL ENERGY DRINK 20 OZ CAN",
     "b": "Red Bull",
     "fl": "Original",
     "sz": "20 OZ",
     "st": 33848,
     "r": 203092729.48,
     "last": "2026-07-01"
    },
    {
     "d": "RED BULL",
     "b": "Red Bull",
     "fl": "",
     "sz": "",
     "st": 34222,
     "r": 151754390.85,
     "last": "2026-07-01"
    },
    {
     "d": "MONSTER",
     "b": "Monster",
     "fl": "",
     "sz": "",
     "st": 32762,
     "r": 136050333.29,
     "last": "2026-07-01"
    },
    {
     "d": "RED BULL WATERMELON ENERGY DRINK 12 OZ CAN 12 PK",
     "b": "Red Bull",
     "fl": "Watermelon",
     "sz": "12 OZ",
     "st": 32782,
     "r": 114829417.94,
     "last": "2026-07-01"
    },
    {
     "d": "RED BULL",
     "b": "Red Bull",
     "fl": "",
     "sz": "",
     "st": 34069,
     "r": 103718842.48,
     "last": "2026-07-01"
    },
    {
     "d": "RED BULL",
     "b": "Red Bull",
     "fl": "",
     "sz": "",
     "st": 33488,
     "r": 99413036.84,
     "last": "2026-07-01"
    },
    {
     "d": "RED BULL BLUEBERRY ENERGY DRINK 12 OZ CAN",
     "b": "Red Bull",
     "fl": "Blueberry",
     "sz": "12 OZ",
     "st": 32352,
     "r": 95220104.93,
     "last": "2026-07-01"
    }
   ]
  },
  {
   "name": "Gym & fitness",
   "age": "18-34",
   "gender": "Male-skewing (~70/30)",
   "note": "The youngest audience measured in the category: 18-24s are nearly twice as likely as the average adult to drink it.",
   "skus": 526,
   "rev": 803291237.32,
   "share": 11.3,
   "brandN": 24,
   "top": [
    {
     "b": "Bang",
     "r": 326663958.57
    },
    {
     "b": "C4",
     "r": 164321363.13
    },
    {
     "b": "Ghost",
     "r": 160842127.23
    },
    {
     "b": "Reign",
     "r": 83632449.34
    },
    {
     "b": "Bucked Up",
     "r": 16017470.26
    },
    {
     "b": "Xyience",
     "r": 9890835.73
    },
    {
     "b": "Ryse",
     "r": 9272082.61
    },
    {
     "b": "Adrenaline Shoc",
     "r": 8531528.09
    }
   ],
   "prod": [
    {
     "d": "BANG BLUE RAZZ ENERGY DRINK 16 OZ CAN",
     "b": "Bang",
     "fl": "Blue Razz",
     "sz": "16 OZ",
     "st": 30910,
     "r": 28142556.1,
     "last": "2026-07-01"
    },
    {
     "d": "BANG MANGO PEACH ENERGY DRINK 16 OZ CAN",
     "b": "Bang",
     "fl": "Mango Peach",
     "sz": "16 OZ",
     "st": 30418,
     "r": 27918538.76,
     "last": "2026-07-01"
    },
    {
     "d": "BANG GRAPE ENERGY DRINK 16 OZ CAN",
     "b": "Bang",
     "fl": "Grape",
     "sz": "16 OZ",
     "st": 29999,
     "r": 24070087.79,
     "last": "2026-07-01"
    },
    {
     "d": "C4 ENERGY",
     "b": "C4",
     "fl": "",
     "sz": "",
     "st": 22628,
     "r": 22909123.57,
     "last": "2026-07-01"
    },
    {
     "d": "BANG COTTON-CANDY ENERGY DRINK 16 OZ CAN",
     "b": "Bang",
     "fl": "Cotton-Candy",
     "sz": "16 OZ",
     "st": 28994,
     "r": 22890970.04,
     "last": "2026-07-01"
    },
    {
     "d": "BANG STAR BLAST ENERGY DRINK 16 OZ CAN",
     "b": "Bang",
     "fl": "Star Blast",
     "sz": "16 OZ",
     "st": 28102,
     "r": 22259745.45,
     "last": "2026-07-01"
    },
    {
     "d": "BANG CHERRY VANILLA ENERGY DRINK 16 OZ CAN",
     "b": "Bang",
     "fl": "Cherry Vanilla",
     "sz": "16 OZ",
     "st": 28090,
     "r": 22228703.9,
     "last": "2026-07-01"
    },
    {
     "d": "C4 ENERGY BOMBSICLE ENERGY DRINK 16 OZ CAN",
     "b": "C4",
     "fl": "Bombsicle",
     "sz": "16 OZ",
     "st": 23854,
     "r": 20423733.75,
     "last": "2026-07-01"
    },
    {
     "d": "REIGN",
     "b": "Reign",
     "fl": "",
     "sz": "",
     "st": 23413,
     "r": 19783243.31,
     "last": "2026-07-01"
    },
    {
     "d": "GHOST ENERGY SOUR PATCH KIDS BLUE RASPBERRY ENERGY DRINK 16 ",
     "b": "Ghost",
     "fl": "Sour Patch Kids Blue Raspberry",
     "sz": "16 OZ",
     "st": 22645,
     "r": 18767255.4,
     "last": "2026-07-01"
    },
    {
     "d": "GHOST ENERGY ORANGE CREAM ENERGY DRINK 16 OZ CAN",
     "b": "Ghost",
     "fl": "Orange Cream",
     "sz": "16 OZ",
     "st": 22325,
     "r": 18151563.1,
     "last": "2026-07-01"
    },
    {
     "d": "BANG SOUR HEADS ENERGY DRINK 16 OZ CAN",
     "b": "Bang",
     "fl": "Sour Heads",
     "sz": "16 OZ",
     "st": 24415,
     "r": 15746394.9,
     "last": "2026-07-01"
    }
   ]
  },
  {
   "name": "Women (fitness & wellness)",
   "age": "18-34",
   "gender": "Female-skewing",
   "note": "Read as a women's brand, but consumption is close to an even 50/50 split between men and women.",
   "skus": 211,
   "rev": 485476686.24,
   "share": 6.8,
   "brandN": 3,
   "top": [
    {
     "b": "Celsius",
     "r": 332782688.95
    },
    {
     "b": "Alani Nu",
     "r": 150330679.3
    },
    {
     "b": "Bloom",
     "r": 2363317.99
    }
   ],
   "prod": [
    {
     "d": "CELSIUS ORANGE ENERGY DRINK 12 OZ CAN",
     "b": "Celsius",
     "fl": "Orange",
     "sz": "12 OZ",
     "st": 27393,
     "r": 25310439.98,
     "last": "2026-07-01"
    },
    {
     "d": "CELSIUS PEACH PEAR ENERGY DRINK 12 OZ CAN",
     "b": "Celsius",
     "fl": "Peach Pear",
     "sz": "12 OZ",
     "st": 26954,
     "r": 24292637.94,
     "last": "2026-07-01"
    },
    {
     "d": "CELSIUS TROPICAL VIBE ENERGY DRINK 12 OZ CAN",
     "b": "Celsius",
     "fl": "Tropical Vibe",
     "sz": "12 OZ",
     "st": 26246,
     "r": 21636608.07,
     "last": "2026-07-01"
    },
    {
     "d": "CELSIUS ARCTIC VIBE ENERGY DRINK 12 OZ CAN",
     "b": "Celsius",
     "fl": "Arctic Vibe",
     "sz": "12 OZ",
     "st": 25026,
     "r": 19781316.39,
     "last": "2026-07-01"
    },
    {
     "d": "CELSIUS WATERMELON ENERGY DRINK 12 OZ CAN",
     "b": "Celsius",
     "fl": "Watermelon",
     "sz": "12 OZ",
     "st": 26358,
     "r": 19326501.87,
     "last": "2026-07-01"
    },
    {
     "d": "CELSIUS MANGO PEACH GREEN TEA ENERGY DRINK 12 OZ CAN",
     "b": "Celsius",
     "fl": "Mango Peach Green Tea",
     "sz": "12 OZ",
     "st": 23055,
     "r": 16922213.11,
     "last": "2026-07-01"
    },
    {
     "d": "CELSIUS SPARKLING KIWI GUAVA ENERGY DRINK 12 OZ CAN",
     "b": "Celsius",
     "fl": "Sparkling Kiwi Guava",
     "sz": "12 OZ",
     "st": 25663,
     "r": 16783281.19,
     "last": "2026-07-01"
    },
    {
     "d": "CELSIUS SPARKLING GRAPE ENERGY DRINK 12 OZ CAN",
     "b": "Celsius",
     "fl": "Sparkling Grape",
     "sz": "12 OZ",
     "st": 23458,
     "r": 16773677.49,
     "last": "2026-07-01"
    },
    {
     "d": "ALANI NU CHERRY SLUSH ENERGY DRINK 12 OZ CAN",
     "b": "Alani Nu",
     "fl": "Cherry Slush",
     "sz": "12 OZ",
     "st": 21329,
     "r": 16099035.6,
     "last": "2026-07-01"
    },
    {
     "d": "CELSIUS WILD BERRY ENERGY DRINK 12 OZ CAN",
     "b": "Celsius",
     "fl": "Wild Berry",
     "sz": "12 OZ",
     "st": 23757,
     "r": 15974679.38,
     "last": "2026-07-01"
    },
    {
     "d": "ALANI NU ENERGY DRINK 20 OZ",
     "b": "Alani Nu",
     "fl": "",
     "sz": "20 OZ",
     "st": 19614,
     "r": 14683165.72,
     "last": "2026-07-01"
    },
    {
     "d": "CELSIUS APPLE PEAR ENERGY DRINK 12 OZ CAN 2 PK",
     "b": "Celsius",
     "fl": "Apple Pear",
     "sz": "12 OZ",
     "st": 22060,
     "r": 12445547.19,
     "last": "2026-07-01"
    }
   ]
  },
  {
   "name": "Shift workers & military",
   "age": "25-44",
   "gender": "Male-skewing",
   "note": "Skews distinctly male - about three quarters of drinkers are in male-headed households - and concentrates in the 25-34 band.",
   "skus": 145,
   "rev": 401790440.07,
   "share": 5.6,
   "brandN": 10,
   "top": [
    {
     "b": "NOS",
     "r": 227561390.86
    },
    {
     "b": "Full Throttle",
     "r": 67936845.74
    },
    {
     "b": "Venom",
     "r": 46815509.13
    },
    {
     "b": "Rip It",
     "r": 32032563.64
    },
    {
     "b": "Arizona Energy",
     "r": 19327642.5
    },
    {
     "b": "Liquid Ice",
     "r": 2664854.68
    },
    {
     "b": "Raptor",
     "r": 1794176.35
    },
    {
     "b": "Ol' Glory",
     "r": 1571373.69
    }
   ],
   "prod": [
    {
     "d": "NOS ORIGINAL ENERGY DRINK 16 OZ CAN",
     "b": "NOS",
     "fl": "Original",
     "sz": "16 OZ",
     "st": 33446,
     "r": 116477728.95,
     "last": "2026-07-01"
    },
    {
     "d": "NOS ORIGINAL ENERGY DRINK 24 OZ CAN",
     "b": "NOS",
     "fl": "Original",
     "sz": "24 OZ",
     "st": 29322,
     "r": 51139728.02,
     "last": "2026-07-01"
    },
    {
     "d": "FULL THROTTLE CITRUS ENERGY DRINK 16 OZ CAN",
     "b": "Full Throttle",
     "fl": "Citrus",
     "sz": "16 OZ",
     "st": 29704,
     "r": 50672814.73,
     "last": "2026-07-01"
    },
    {
     "d": "NOS GRAPE ENERGY DRINK 16 OZ CAN",
     "b": "NOS",
     "fl": "Grape",
     "sz": "16 OZ",
     "st": 27734,
     "r": 30851043.89,
     "last": "2026-07-01"
    },
    {
     "d": "FULL THROTTLE BLUE-AGAVE ENERGY DRINK 16 OZ CAN",
     "b": "Full Throttle",
     "fl": "Blue-Agave",
     "sz": "16 OZ",
     "st": 21350,
     "r": 16947888.57,
     "last": "2026-07-01"
    },
    {
     "d": "VENOM ENERGY BLACK-MAMBA ENERGY DRINK 16 OZ CAN",
     "b": "Venom",
     "fl": "Black-Mamba",
     "sz": "16 OZ",
     "st": 15084,
     "r": 13544072.95,
     "last": "2026-07-01"
    },
    {
     "d": "NOS SOUR ENERGY DRINK 16 OZ CAN",
     "b": "NOS",
     "fl": "Sour",
     "sz": "16 OZ",
     "st": 22568,
     "r": 12914059.11,
     "last": "2026-07-01"
    },
    {
     "d": "ARIZONA ORIGINAL ENERGY DRINK 23 OZ CAN",
     "b": "Arizona Energy",
     "fl": "Original",
     "sz": "23 OZ",
     "st": 18302,
     "r": 12758058.76,
     "last": "2026-07-01"
    },
    {
     "d": "VENOM ENERGY TAIPAN ENERGY DRINK 16 OZ CAN",
     "b": "Venom",
     "fl": "Taipan",
     "sz": "16 OZ",
     "st": 14747,
     "r": 12232510.55,
     "last": "2026-07-01"
    },
    {
     "d": "VENOM ENERGY ORANGE FRUIT PUNCH ENERGY DRINK 16 OZ CAN",
     "b": "Venom",
     "fl": "Orange Fruit Punch",
     "sz": "16 OZ",
     "st": 14259,
     "r": 8309058.99,
     "last": "2026-07-01"
    },
    {
     "d": "NOS ENERGY DRINK 16 OZ",
     "b": "NOS",
     "fl": "",
     "sz": "16 OZ",
     "st": 16480,
     "r": 5933849.14,
     "last": "2026-07-01"
    },
    {
     "d": "VENOM ENERGY BLACK CHERRY KIWI ENERGY DRINK 16 OZ CAN",
     "b": "Venom",
     "fl": "Black Cherry Kiwi",
     "sz": "16 OZ",
     "st": 11999,
     "r": 5600392.28,
     "last": "2026-07-01"
    }
   ]
  },
  {
   "name": "Calorie-cutters",
   "age": "25-44",
   "gender": "Mixed",
   "note": "The same mainstream drinker cutting sugar, not chasing fitness. The zero-sugar lines reach older and more female buyers than the sugared ones.",
   "skus": 445,
   "rev": 255962680.28,
   "share": 3.6,
   "brandN": 89,
   "top": [
    {
     "b": "Red Bull",
     "r": 133122897.09
    },
    {
     "b": "Rockstar",
     "r": 74975287.26
    },
    {
     "b": "Monster",
     "r": 37230344.38
    },
    {
     "b": "Bum Energy",
     "r": 1274568.94
    },
    {
     "b": "Rip It",
     "r": 1144896.56
    },
    {
     "b": "Mtn Dew (energy)",
     "r": 819006.29
    },
    {
     "b": "Lucky Beverage",
     "r": 786582.39
    },
    {
     "b": "ON",
     "r": 751952.34
    }
   ],
   "prod": [
    {
     "d": "RED BULL ORIGINAL ENERGY DRINK 8.4 OZ CAN",
     "b": "Red Bull",
     "fl": "Original",
     "sz": "8.4 OZ",
     "st": 34211,
     "r": 76070154.4,
     "last": "2026-07-01"
    },
    {
     "d": "RED BULL ORIGINAL ENERGY DRINK 20 OZ CAN",
     "b": "Red Bull",
     "fl": "Original",
     "sz": "20 OZ",
     "st": 28013,
     "r": 45691634.34,
     "last": "2026-07-01"
    },
    {
     "d": "ROCKSTAR SUGAR FREE DIET 16.0 OZ CAN",
     "b": "Rockstar",
     "fl": "Original",
     "sz": "16 OZ",
     "st": 23284,
     "r": 15397983.64,
     "last": "2026-07-01"
    },
    {
     "d": "ROCKSTAR PURE ZERO SILVER ICE 16.0 OZ CAN",
     "b": "Rockstar",
     "fl": "Silver Ice",
     "sz": "16 OZ",
     "st": 21345,
     "r": 12988230.08,
     "last": "2026-07-01"
    },
    {
     "d": "ROCKSTAR PURE ZERO PUNCHED 16.0 OZ CAN",
     "b": "Rockstar",
     "fl": "Punched",
     "sz": "16 OZ",
     "st": 20423,
     "r": 11390468.04,
     "last": "2026-07-01"
    },
    {
     "d": "MONSTER REGULAR ENERGY DRINK 19.2 OZ ALUMINUM CAN",
     "b": "Monster",
     "fl": "Regular",
     "sz": "19.2 OZ",
     "st": 16966,
     "r": 10586077.07,
     "last": "2026-07-01"
    },
    {
     "d": "MONSTER ZERO ULTRA ENERGY DRINK 12 OZ ALUMINUM CAN",
     "b": "Monster",
     "fl": "Zero Ultra",
     "sz": "12 OZ",
     "st": 17912,
     "r": 10001765.09,
     "last": "2026-07-01"
    },
    {
     "d": "MONSTER ULTRA GOLD ENERGY DRINK 16 OZ ALUMINUM CAN",
     "b": "Monster",
     "fl": "Ultra Gold",
     "sz": "16 OZ",
     "st": 19044,
     "r": 7926891.66,
     "last": "2026-07-01"
    },
    {
     "d": "RED BULL ZERO TOTAL ENERGY DRINK 8.4 OZ CAN",
     "b": "Red Bull",
     "fl": "Zero Total",
     "sz": "8.4 OZ",
     "st": 24108,
     "r": 5526765.79,
     "last": "2026-07-01"
    },
    {
     "d": "ROCKSTAR ORIGINAL 16OZ CAN",
     "b": "Rockstar",
     "fl": "Original",
     "sz": "16 OZ",
     "st": 14116,
     "r": 5320614.97,
     "last": "2026-06-30"
    },
    {
     "d": "RED BULL ORIGINAL ENERGY DRINK 8.4 OZ CAN 4 PK",
     "b": "Red Bull",
     "fl": "Original",
     "sz": "8.4 OZ",
     "st": 13167,
     "r": 5318925.95,
     "last": "2026-07-01"
    },
    {
     "d": "ROCKSTAR PURE ZERO TMGS 16.0 OZ CAN",
     "b": "Rockstar",
     "fl": "Tmgs",
     "sz": "16 OZ",
     "st": 13033,
     "r": 4388354.41,
     "last": "2026-07-01"
    }
   ]
  },
  {
   "name": "Health-conscious adults",
   "age": "30-55",
   "gender": "Mixed",
   "note": "Rejects the stimulant framing entirely. Wants organic, yerba mate or plant caffeine, and skews older and better-off than the category.",
   "skus": 118,
   "rev": 66097024.27,
   "share": 0.9,
   "brandN": 21,
   "top": [
    {
     "b": "Guayaki",
     "r": 24301657.17
    },
    {
     "b": "Uptime",
     "r": 17823678.7
    },
    {
     "b": "Mtn Dew Rise",
     "r": 15284672.59
    },
    {
     "b": "Yachak",
     "r": 5330577.82
    },
    {
     "b": "Starbucks Baya",
     "r": 1620539.79
    },
    {
     "b": "Lotus Plant Power Drink",
     "r": 786274.62
    },
    {
     "b": "LOTUS PLANT POWER",
     "r": 447974.82
    },
    {
     "b": "Hiball Energy",
     "r": 283053.59
    }
   ],
   "prod": [
    {
     "d": "GUAYAKI MINT YERBA MATE 15.5 OZ CAN",
     "b": "Guayaki",
     "fl": "Mint",
     "sz": "15.5 OZ",
     "st": 4369,
     "r": 8269585.84,
     "last": "2026-07-01"
    },
    {
     "d": "GUAYAKI BERRY YERBA MATE ICED TEA 15.5 OZ CAN",
     "b": "Guayaki",
     "fl": "Berry Yerba Mate",
     "sz": "15.5 OZ",
     "st": 4153,
     "r": 6263604.01,
     "last": "2026-07-01"
    },
    {
     "d": "GUAYAKI BLUEPHORIA YERBA MATE YERBA MATE 15.5 OZ CAN",
     "b": "Guayaki",
     "fl": "Bluephoria Yerba Mate",
     "sz": "15.5 OZ",
     "st": 4302,
     "r": 6154936.43,
     "last": "2026-07-01"
    },
    {
     "d": "MOUNTAIN DEW RISE POMEGRANATE BLUE BURST ENERGY DRINK 16 OZ ",
     "b": "Mtn Dew Rise",
     "fl": "Pomegranate Blue Burst",
     "sz": "16 OZ",
     "st": 16361,
     "r": 3873387.19,
     "last": "2026-06-05"
    },
    {
     "d": "MOUNTAIN DEW RISE STRAWBERRY MELON SPARK ENERGY DRINK 16 OZ ",
     "b": "Mtn Dew Rise",
     "fl": "Strawberry Melon Spark",
     "sz": "16 OZ",
     "st": 15843,
     "r": 3343418.24,
     "last": "2026-06-28"
    },
    {
     "d": "MOUNTAIN DEW RISE ORANGE BREEZE ENERGY DRINK 16 OZ CAN",
     "b": "Mtn Dew Rise",
     "fl": "Orange Breeze",
     "sz": "16 OZ",
     "st": 14455,
     "r": 2948954.83,
     "last": "2026-06-11"
    },
    {
     "d": "GUAYAKI ORANGE YERBA MATE YERBA MATE 15.5 OZ CAN",
     "b": "Guayaki",
     "fl": "Orange Yerba Mate",
     "sz": "15.5 OZ",
     "st": 2477,
     "r": 2877314.34,
     "last": "2026-07-01"
    },
    {
     "d": "UPTIME BLUEBERRY POMEGRANATE ENERGY DRINK 12 OZ BOTTLE",
     "b": "Uptime",
     "fl": "Blueberry Pomegranate",
     "sz": "12 OZ",
     "st": 5427,
     "r": 2507647.65,
     "last": "2026-07-01"
    },
    {
     "d": "UPTIME CITRUS ENERGY DRINK 12 OZ BOTTLE",
     "b": "Uptime",
     "fl": "Citrus",
     "sz": "12 OZ",
     "st": 5471,
     "r": 2409185.3,
     "last": "2026-07-01"
    },
    {
     "d": "MOUNTAIN DEW RISE TROPICAL SUNRISE ENERGY DRINK 16 OZ CAN",
     "b": "Mtn Dew Rise",
     "fl": "Tropical Sunrise",
     "sz": "16 OZ",
     "st": 13497,
     "r": 2338011.37,
     "last": "2026-04-07"
    },
    {
     "d": "UPTIME MANGO PINEAPPLE ENERGY DRINK 12 OZ BOTTLE",
     "b": "Uptime",
     "fl": "Mango Pineapple",
     "sz": "12 OZ",
     "st": 5390,
     "r": 2214526.97,
     "last": "2026-07-01"
    },
    {
     "d": "UPTIME BLOOD ORANGE ENERGY DRINK 12 OZ BOTTLE",
     "b": "Uptime",
     "fl": "Blood Orange",
     "sz": "12 OZ",
     "st": 5502,
     "r": 2080708.49,
     "last": "2026-07-01"
    }
   ]
  },
  {
   "name": "Gamers & creators",
   "age": "16-27",
   "gender": "Male-skewing",
   "note": "Buys the influencer and the flavour drop as much as the caffeine. Mostly reached online, so convenience stores understate this group.",
   "skus": 92,
   "rev": 31419629.72,
   "share": 0.4,
   "brandN": 3,
   "top": [
    {
     "b": "Prime",
     "r": 23300493.11
    },
    {
     "b": "G.O.A.T. Fuel",
     "r": 4382676.9
    },
    {
     "b": "G FUEL",
     "r": 3736459.71
    }
   ],
   "prod": [
    {
     "d": "PRIME CHERRY SPORTS DRINKS 16.9 OZ",
     "b": "Prime",
     "fl": "Cherry",
     "sz": "16.9 OZ",
     "st": 13584,
     "r": 3404653.87,
     "last": "2026-07-01"
    },
    {
     "d": "PRIME GLOWBERRY SPORTS DRINKS 16.9 OZ",
     "b": "Prime",
     "fl": "Glowberry",
     "sz": "16.9 OZ",
     "st": 12152,
     "r": 3149210.45,
     "last": "2026-07-01"
    },
    {
     "d": "PRIME BLUE RASPBERRY ENERGY DRINKS 12 OZ CAN",
     "b": "Prime",
     "fl": "Blue Raspberry",
     "sz": "12 OZ",
     "st": 9111,
     "r": 2416264.87,
     "last": "2026-07-01"
    },
    {
     "d": "PRIME STRAWBERRY WATERMELON ENERGY DRINKS 12 OZ CAN",
     "b": "Prime",
     "fl": "Strawberry Watermelon",
     "sz": "12 OZ",
     "st": 9237,
     "r": 2178078.88,
     "last": "2026-06-30"
    },
    {
     "d": "PRIME SPORTS DRINKS 16 OZ",
     "b": "Prime",
     "fl": "",
     "sz": "16 OZ",
     "st": 11126,
     "r": 1876718.05,
     "last": "2026-07-01"
    },
    {
     "d": "PRIME TROPICAL PUNCH ENERGY DRINKS 12 OZ CAN",
     "b": "Prime",
     "fl": "Tropical Punch",
     "sz": "12 OZ",
     "st": 8136,
     "r": 1689422.65,
     "last": "2026-07-01"
    },
    {
     "d": "PRIME ENERGY DRINKS 12 OZ",
     "b": "Prime",
     "fl": "",
     "sz": "12 OZ",
     "st": 7415,
     "r": 1317485.03,
     "last": "2026-06-29"
    },
    {
     "d": "PRIME LEMON LIME ENERGY DRINKS 12 OZ CAN",
     "b": "Prime",
     "fl": "Lemon Lime",
     "sz": "12 OZ",
     "st": 7016,
     "r": 1258006.19,
     "last": "2026-07-01"
    },
    {
     "d": "PRIME ORANGE MANGO ENERGY DRINKS 12 OZ CAN",
     "b": "Prime",
     "fl": "Orange Mango",
     "sz": "12 OZ",
     "st": 7472,
     "r": 1253902.41,
     "last": "2026-06-30"
    },
    {
     "d": "PRIME SPORTS DRINKS 16.9 OZ",
     "b": "Prime",
     "fl": "",
     "sz": "16.9 OZ",
     "st": 8369,
     "r": 1243436.67,
     "last": "2026-07-01"
    },
    {
     "d": "G FUEL 16 OZ",
     "b": "G FUEL",
     "fl": "",
     "sz": "16 OZ",
     "st": 4329,
     "r": 1005231.14,
     "last": "2026-07-01"
    },
    {
     "d": "G.O.A.T. FUEL 16 OZ",
     "b": "G.O.A.T. Fuel",
     "fl": "",
     "sz": "16 OZ",
     "st": 3431,
     "r": 658876.06,
     "last": "2026-07-01"
    }
   ]
  },
  {
   "name": "Coffee drinkers",
   "age": "30-55",
   "gender": "Mixed",
   "note": "Wants the caffeine without identifying as an energy-drink drinker. Comes in through cold brew and canned coffee rather than the energy aisle.",
   "skus": 28,
   "rev": 6557397.11,
   "share": 0.1,
   "brandN": 8,
   "top": [
    {
     "b": "Blue Bottle Coffee",
     "r": 4171469.18
    },
    {
     "b": "Black Rifle Coffee Company",
     "r": 1394990.89
    },
    {
     "b": "Black Rifle Coffee",
     "r": 556949.37
    },
    {
     "b": "Super Coffee",
     "r": 314358.44
    },
    {
     "b": "Stok",
     "r": 71555.17
    },
    {
     "b": "STOK",
     "r": 35977.11
    },
    {
     "b": "SUPER COFFEE",
     "r": 7339.68
    },
    {
     "b": "KeHE Distributors",
     "r": 4757.27
    }
   ],
   "prod": [
    {
     "d": "Blue Bottle Coffee",
     "b": "Blue Bottle Coffee",
     "fl": "",
     "sz": "",
     "st": 65,
     "r": 2189139.49,
     "last": "2025-12-31"
    },
    {
     "d": "Blue Bottle Coffee",
     "b": "Blue Bottle Coffee",
     "fl": "",
     "sz": "",
     "st": 65,
     "r": 1982326.7,
     "last": "2025-09-03"
    },
    {
     "d": "BLACK RIFLE WILD FROST 16 OZ  CAN SINGLE",
     "b": "Black Rifle Coffee Company",
     "fl": "Wild Frost",
     "sz": "16 OZ",
     "st": 3180,
     "r": 425591.42,
     "last": "2025-12-31"
    },
    {
     "d": "BLACK RIFLE RANGER BERRY 16 OZ  CAN SINGLE",
     "b": "Black Rifle Coffee Company",
     "fl": "Ranger Berry",
     "sz": "16 OZ",
     "st": 2771,
     "r": 379999.88,
     "last": "2025-12-31"
    },
    {
     "d": "BLACK RIFLE FREEDOM PUNCH 16 OZ  CAN SINGLE",
     "b": "Black Rifle Coffee Company",
     "fl": "Freedom Punch",
     "sz": "16 OZ",
     "st": 3145,
     "r": 328895.45,
     "last": "2025-12-31"
    },
    {
     "d": "BLACK RIFLE PROJECT MANGO 16 OZ  CAN SINGLE",
     "b": "Black Rifle Coffee Company",
     "fl": "Project Mango",
     "sz": "16 OZ",
     "st": 2281,
     "r": 260504.14,
     "last": "2025-12-31"
    },
    {
     "d": "SUPER COFFEE 12 OZ",
     "b": "Super Coffee",
     "fl": "",
     "sz": "12 OZ",
     "st": 1656,
     "r": 187256.04,
     "last": "2026-07-01"
    },
    {
     "d": "BLACK RIFLE WILD FROST 16 OZ  CAN SINGLE",
     "b": "Black Rifle Coffee",
     "fl": "Wild Frost",
     "sz": "16 OZ",
     "st": 2706,
     "r": 186210.14,
     "last": "2026-07-01"
    },
    {
     "d": "BLACK RIFLE RANGER BERRY 16 OZ  CAN SINGLE",
     "b": "Black Rifle Coffee",
     "fl": "Ranger Berry",
     "sz": "16 OZ",
     "st": 2349,
     "r": 157168.0,
     "last": "2026-07-01"
    },
    {
     "d": "BLACK RIFLE FREEDOM PUNCH 16 OZ  CAN SINGLE",
     "b": "Black Rifle Coffee",
     "fl": "Freedom Punch",
     "sz": "16 OZ",
     "st": 2600,
     "r": 136843.77,
     "last": "2026-07-01"
    },
    {
     "d": "BLACK RIFLE PROJECT MANGO 16 OZ  CAN SINGLE",
     "b": "Black Rifle Coffee",
     "fl": "Project Mango",
     "sz": "16 OZ",
     "st": 1746,
     "r": 76727.46,
     "last": "2026-07-01"
    },
    {
     "d": "SUPER COFFEE 12 OZ",
     "b": "Super Coffee",
     "fl": "",
     "sz": "12 OZ",
     "st": 802,
     "r": 42413.5,
     "last": "2026-05-07"
    }
   ]
  },
  {
   "name": "Older functional users",
   "age": "35-54",
   "gender": "Male-skewing",
   "note": "Takes it as a dose, not a drink. Heavily skewed toward avid sports fans, who are more than twice as likely as average to buy it.",
   "skus": 18,
   "rev": 2011313.04,
   "share": 0.0,
   "brandN": 8,
   "top": [
    {
     "b": "5-Hour Energy",
     "r": 1298192.9
    },
    {
     "b": "Tweaker",
     "r": 444018.63
    },
    {
     "b": "Essentia Water",
     "r": 107762.18
    },
    {
     "b": "Lucky Beverage",
     "r": 80984.61
    },
    {
     "b": "Uptime Energy",
     "r": 45028.5
    },
    {
     "b": "G Fuel",
     "r": 33637.42
    },
    {
     "b": "LUCKY F*CK",
     "r": 1028.94
    },
    {
     "b": "Lucky Energy",
     "r": 659.86
    }
   ],
   "prod": [
    {
     "d": "TWEAKER BERRY ENERGY SHOT 2 OZ BOX 12 PK",
     "b": "Tweaker",
     "fl": "Berry",
     "sz": "2 OZ",
     "st": 601,
     "r": 428138.92,
     "last": "2026-07-01"
    },
    {
     "d": "5-HOUR ENERGY BERRY ENERGY DRINK 16 OZ CAN",
     "b": "5-Hour Energy",
     "fl": "Berry",
     "sz": "16 OZ",
     "st": 3936,
     "r": 380538.44,
     "last": "2026-06-30"
    },
    {
     "d": "5-HOUR ENERGY GRAPE ENERGY DRINK 16 OZ CAN",
     "b": "5-Hour Energy",
     "fl": "Grape",
     "sz": "16 OZ",
     "st": 3594,
     "r": 346909.38,
     "last": "2026-06-30"
    },
    {
     "d": "5-HOUR ENERGY WATERMELON ENERGY DRINK 16 OZ CAN",
     "b": "5-Hour Energy",
     "fl": "Watermelon",
     "sz": "16 OZ",
     "st": 3496,
     "r": 319523.65,
     "last": "2026-06-29"
    },
    {
     "d": "5-HOUR ENERGY TROPICAL BURST ENERGY DRINK 16 OZ CAN",
     "b": "5-Hour Energy",
     "fl": "Tropical Burst",
     "sz": "16 OZ",
     "st": 1657,
     "r": 130986.66,
     "last": "2026-07-01"
    },
    {
     "d": "5-HOUR ENERGY ORANGE SICLE ENERGY DRINK 16 OZ CAN",
     "b": "5-Hour Energy",
     "fl": "Orange Sicle",
     "sz": "16 OZ",
     "st": 1719,
     "r": 120234.77,
     "last": "2026-06-29"
    },
    {
     "d": "ESSENTIA WATER RASPBERRY POMEGRANATE WATER 15.2 OZ BOTTLE",
     "b": "Essentia Water",
     "fl": "Raspberry Pomegranate",
     "sz": "15.2 OZ",
     "st": 1944,
     "r": 107762.18,
     "last": "2026-07-01"
    },
    {
     "d": "UPTIME ENERGY ORIGINAL ENERGY SHOT 2 OZ BOTTLE 24 PK",
     "b": "Uptime Energy",
     "fl": "Original",
     "sz": "2 OZ",
     "st": 423,
     "r": 45028.5,
     "last": "2026-06-02"
    },
    {
     "d": "G FUEL ENERGY ONE SHOT GURL STRAWBERRY SLUSHIE CAN 16 OZ 12 ",
     "b": "G Fuel",
     "fl": "One Shot Gurl Strawberry Slushie",
     "sz": "16 OZ",
     "st": 403,
     "r": 33637.42,
     "last": "2026-06-21"
    },
    {
     "d": "LUCKY ENERGY BODACIOUS BERRY 19.2 OZ CAN SINGLE",
     "b": "Lucky Beverage",
     "fl": "Bodacious Berry",
     "sz": "19.2 OZ",
     "st": 253,
     "r": 22901.38,
     "last": "2025-12-31"
    },
    {
     "d": "LUCKY F*CK TROPICAL THRILL 19.2 OZ CAN SINGLE",
     "b": "Lucky Beverage",
     "fl": "Tropical Thrill",
     "sz": "19.2 OZ",
     "st": 256,
     "r": 21509.92,
     "last": "2025-12-30"
    },
    {
     "d": "LUCKY F*CK RED RYDER PUNCH 19.2 OZ CAN SINGLE",
     "b": "Lucky Beverage",
     "fl": "Red Ryder Punch",
     "sz": "19.2 OZ",
     "st": 246,
     "r": 20128.1,
     "last": "2025-12-23"
    }
   ]
  }
 ],
 "demand": {
  "now": {
   "label": "US demand today (2025)",
   "sub": "All channels. Convenience shares measured from PDI, multi-outlet from Mintel MULO brand sales, blended on Mintel channel weights.",
   "market": 26948.0,
   "auds": [
    {
     "name": "Young adults",
     "share": 64.9,
     "usd": 17497.3,
     "age": "18-34",
     "gender": "Male-skewing"
    },
    {
     "name": "Women (fitness & wellness)",
     "share": 18.4,
     "usd": 4947.7,
     "age": "18-34",
     "gender": "Female-skewing"
    },
    {
     "name": "Gym & fitness",
     "share": 9.5,
     "usd": 2549.3,
     "age": "18-34",
     "gender": "Male-skewing (~70/30)"
    },
    {
     "name": "Shift workers & military",
     "share": 4.2,
     "usd": 1129.1,
     "age": "25-44",
     "gender": "Male-skewing"
    },
    {
     "name": "Calorie-cutters",
     "share": 2.2,
     "usd": 598.2,
     "age": "25-44",
     "gender": "Mixed"
    },
    {
     "name": "Health-conscious adults",
     "share": 0.5,
     "usd": 121.3,
     "age": "30-55",
     "gender": "Mixed"
    },
    {
     "name": "Gamers & creators",
     "share": 0.2,
     "usd": 59.3,
     "age": "16-27",
     "gender": "Male-skewing"
    },
    {
     "name": "Coffee drinkers",
     "share": 0.2,
     "usd": 45.8,
     "age": "30-55",
     "gender": "Mixed"
    },
    {
     "name": "Older functional users",
     "share": 0.0,
     "usd": 2.7,
     "age": "35-54",
     "gender": "Male-skewing"
    }
   ]
  },
  "future": {
   "label": "Projected US demand (2030)",
   "sub": "Mintel's central forecast of $38.6B, split by extrapolating each audience's measured share drift and damping it for saturation.",
   "market": 38600.52,
   "auds": [
    {
     "name": "Young adults",
     "share": 56.5,
     "usd": 21809.3,
     "age": "18-34",
     "gender": "Male-skewing"
    },
    {
     "name": "Women (fitness & wellness)",
     "share": 28.3,
     "usd": 10923.9,
     "age": "18-34",
     "gender": "Female-skewing"
    },
    {
     "name": "Gym & fitness",
     "share": 8.1,
     "usd": 3126.6,
     "age": "18-34",
     "gender": "Male-skewing (~70/30)"
    },
    {
     "name": "Shift workers & military",
     "share": 3.3,
     "usd": 1273.8,
     "age": "25-44",
     "gender": "Male-skewing"
    },
    {
     "name": "Gamers & creators",
     "share": 1.6,
     "usd": 617.6,
     "age": "16-27",
     "gender": "Male-skewing"
    },
    {
     "name": "Health-conscious adults",
     "share": 0.9,
     "usd": 347.4,
     "age": "30-55",
     "gender": "Mixed"
    },
    {
     "name": "Calorie-cutters",
     "share": 0.8,
     "usd": 308.8,
     "age": "25-44",
     "gender": "Mixed"
    },
    {
     "name": "Coffee drinkers",
     "share": 0.4,
     "usd": 154.4,
     "age": "30-55",
     "gender": "Mixed"
    },
    {
     "name": "Older functional users",
     "share": 0.1,
     "usd": 38.6,
     "age": "35-54",
     "gender": "Male-skewing"
    }
   ]
  },
  "channels": {
   "convenience": 16131,
   "supermarket": 3632,
   "other": 7185
  },
  "band": {
   "low90": 30026.56,
   "high90": 47174.48
  },
  "why": {
   "Young adults": "Still the biggest audience by far, and still growing in dollars \u2014 but its share erodes about 2-3 points a year in both channels as the category widens beyond it. Red Bull and Monster are each growing 15% in multi-outlet; they are not shrinking, they are being diluted.",
   "Women (fitness & wellness)": "The clearest trend in the data. Went from 0.2% to 11.8% of convenience sales in six years, and is already 24% of multi-outlet sales where Celsius and Alani Nu concentrate. Alani Nu alone grew 84% year on year. Mintel's survey backs it: 39% of consumers want naturally-sweetened energy.",
   "Gym & fitness": "Flat in convenience for four years, and losing multi-outlet share as Bang (-8%) and Reign (-22%) decline. The RTD pre-workout idea is mature; the growth has migrated to the wellness framing rather than the performance one.",
   "Shift workers & military": "Slow structural decline. Value brands lose share whenever the category premiumises, and c-store traffic is the channel most exposed to that.",
   "Calorie-cutters": "The sharpest faller, and it is a definitional shift rather than a real collapse: sugar-free stopped being a distinct proposition. 72% of 2024-26 launches claim it, so it is now table stakes folded into every other audience.",
   "Health-conscious adults": "Small but compounding. Yerba mate and plant-caffeine brands sell mainly through natural grocery, which convenience data barely sees, so the true base is larger than 0.5%.",
   "Gamers & creators": "Understated everywhere in this data \u2014 G FUEL and Prime sell primarily through e-commerce and mass, and the 'other' channel that carries them grew 28% in 2025. Held at a floor of 1.6% for 2030 rather than trended, because both measured channels are blind to it.",
   "Coffee drinkers": "Early but real. Coffee-energy hybrids convert adults who reject the energy-drink identity, and the entry point is cold brew rather than the energy aisle.",
   "Older functional users": "Shots remain a niche in this dataset, though trade reporting suggests 2oz formats are outgrowing large cans in channels PDI does not cover."
  },
  "cagr": {
   "Young adults": 4.5,
   "Gym & fitness": 4.2,
   "Women (fitness & wellness)": 17.2,
   "Shift workers & military": 2.4,
   "Calorie-cutters": -12.4,
   "Health-conscious adults": 23.4,
   "Gamers & creators": 59.8,
   "Coffee drinkers": 27.5,
   "Older functional users": 70.3
  },
  "pdi_vs_mulo": [
   {
    "name": "Young adults",
    "pdi": 67.6,
    "mulo": 61.0
   },
   {
    "name": "Women (fitness & wellness)",
    "pdi": 11.8,
    "mulo": 28.2
   },
   {
    "name": "Gym & fitness",
    "pdi": 11.7,
    "mulo": 6.2
   },
   {
    "name": "Shift workers & military",
    "pdi": 4.9,
    "mulo": 3.1
   },
   {
    "name": "Calorie-cutters",
    "pdi": 3.0,
    "mulo": 1.1
   },
   {
    "name": "Health-conscious adults",
    "pdi": 0.6,
    "mulo": 0.2
   },
   {
    "name": "Gamers & creators",
    "pdi": 0.3,
    "mulo": 0.1
   },
   {
    "name": "Coffee drinkers",
    "pdi": 0.2,
    "mulo": 0.1
   },
   {
    "name": "Older functional users",
    "pdi": 0.0,
    "mulo": 0.0
   }
  ]
 }
}
''')

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "public", "data", "dashboard.json")


def main():
    path = os.path.normpath(OUT)
    with open(path) as fh:
        data = json.load(fh)
    data["audiences"] = AUD
    with open(path, "w") as fh:
        json.dump(data, fh, separators=(",", ":"))
    print(f"wrote {len(AUD['auds'])} audiences + demand views -> {path}")


if __name__ == "__main__":
    main()
