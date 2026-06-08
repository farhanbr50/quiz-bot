import os
import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# messages.py se sirf welcome text load hoga
from messages import WELCOME_TEXT

TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 📚 MEGA QUIZ DATABASE (Poore 200 Mix Questions)
QUIZ_DATA = [
    # --- MATHS CATEGORY (100 Questions) ---
    {"q": "2 + 2 = ?", "o": ["3", "4", "5", "6"], "a": 1},
    {"q": "5 + 7 = ?", "o": ["10", "11", "12", "13"], "a": 2},
    {"q": "10 - 3 = ?", "o": ["6", "7", "8", "9"], "a": 1},
    {"q": "4 x 2 = ?", "o": ["6", "8", "10", "12"], "a": 1},
    {"q": "20 ÷ 2 = ?", "o": ["5", "10", "15", "20"], "a": 1},
    {"q": "15 + 15 = ?", "o": ["25", "30", "35", "40"], "a": 1},
    {"q": "9 x 9 = ?", "o": ["72", "81", "90", "99"], "a": 1},
    {"q": "50 - 25 = ?", "o": ["20", "25", "30", "35"], "a": 1},
    {"q": "12 ÷ 3 = ?", "o": ["3", "4", "5", "6"], "a": 1},
    {"q": "100 + 200 = ?", "o": ["250", "300", "350", "400"], "a": 1},
    {"q": "7 x 6 = ?", "o": ["40", "42", "44", "46"], "a": 1},
    {"q": "30 + 45 = ?", "o": ["65", "70", "75", "80"], "a": 2},
    {"q": "80 - 40 = ?", "o": ["30", "40", "50", "60"], "a": 1},
    {"q": "9 ÷ 3 = ?", "o": ["2", "3", "4", "5"], "a": 1},
    {"q": "11 x 11 = ?", "o": ["111", "121", "131", "141"], "a": 1},
    {"q": "60 + 60 = ?", "o": ["110", "120", "130", "140"], "a": 1},
    {"q": "75 - 25 = ?", "o": ["40", "50", "60", "70"], "a": 1},
    {"q": "8 x 5 = ?", "o": ["35", "40", "45", "50"], "a": 1},
    {"q": "36 ÷ 6 = ?", "o": ["5", "6", "7", "8"], "a": 1},
    {"q": "500 - 100 = ?", "o": ["300", "400", "500", "600"], "a": 1},
    {"q": "13 + 17 = ?", "o": ["28", "29", "30", "31"], "a": 2},
    {"q": "6 x 4 = ?", "o": ["20", "22", "24", "26"], "a": 2},
    {"q": "90 - 45 = ?", "o": ["35", "40", "45", "50"], "a": 2},
    {"q": "40 ÷ 5 = ?", "o": ["6", "7", "8", "9"], "a": 2},
    {"q": "15 x 2 = ?", "o": ["25", "30", "35", "40"], "a": 1},
    {"q": "25 + 25 = ?", "o": ["45", "50", "55", "60"], "a": 1},
    {"q": "70 - 35 = ?", "o": ["30", "35", "40", "45"], "a": 1},
    {"q": "3 x 9 = ?", "o": ["24", "27", "30", "33"], "a": 1},
    {"q": "100 ÷ 4 = ?", "o": ["20", "25", "30", "35"], "a": 1},
    {"q": "8 + 9 = ?", "o": ["15", "16", "17", "18"], "a": 2},
    {"q": "14 - 6 = ?", "o": ["6", "7", "8", "9"], "a": 2},
    {"q": "12 x 5 = ?", "o": ["50", "55", "60", "65"], "a": 2},
    {"q": "81 ÷ 9 = ?", "o": ["7", "8", "9", "10"], "a": 2},
    {"q": "45 + 45 = ?", "o": ["80", "85", "90", "95"], "a": 2},
    {"q": "200 - 50 = ?", "o": ["130", "140", "150", "160"], "a": 2},
    {"q": "7 x 7 = ?", "o": ["47", "48", "49", "50"], "a": 2},
    {"q": "64 ÷ 8 = ?", "o": ["6", "7", "8", "9"], "a": 2},
    {"q": "18 + 12 = ?", "o": ["28", "30", "32", "34"], "a": 1},
    {"q": "55 - 22 = ?", "o": ["31", "33", "35", "37"], "a": 1},
    {"q": "4 x 8 = ?", "o": ["30", "32", "34", "36"], "a": 1},
    {"q": "50 ÷ 2 = ?", "o": ["20", "25", "30", "35"], "a": 1},
    {"q": "9 + 14 = ?", "o": ["21", "22", "23", "24"], "a": 2},
    {"q": "33 - 11 = ?", "o": ["20", "22", "24", "26"], "a": 1},
    {"q": "6 x 7 = ?", "o": ["40", "42", "44", "46"], "a": 1},
    {"q": "120 ÷ 10 = ?", "o": ["10", "12", "14", "16"], "a": 1},
    {"q": "65 + 35 = ?", "o": ["90", "95", "100", "105"], "a": 2},
    {"q": "150 - 75 = ?", "o": ["65", "70", "75", "80"], "a": 2},
    {"q": "12 x 3 = ?", "o": ["32", "34", "36", "38"], "a": 2},
    {"q": "48 ÷ 6 = ?", "o": ["6", "7", "8", "9"], "a": 2},
    {"q": "7 + 16 = ?", "o": ["21", "22", "23", "24"], "a": 2},
    {"q": "40 - 19 = ?", "o": ["19", "20", "21", "22"], "a": 2},
    {"q": "5 x 12 = ?", "o": ["50", "55", "60", "65"], "a": 2},
    {"q": "90 ÷ 9 = ?", "o": ["8", "9", "10", "11"], "a": 2},
    {"q": "22 + 28 = ?", "o": ["48", "50", "52", "54"], "a": 1},
    {"q": "85 - 45 = ?", "o": ["35", "40", "45", "50"], "a": 1},
    {"q": "9 x 4 = ?", "o": ["32", "36", "40", "44"], "a": 1},
    {"q": "30 ÷ 3 = ?", "o": ["8", "10", "12", "14"], "a": 1},
    {"q": "14 + 16 = ?", "o": ["28", "30", "32", "34"], "a": 1},
    {"q": "72 - 12 = ?", "o": ["50", "60", "70", "80"], "a": 1},
    {"q": "8 x 8 = ?", "o": ["60", "64", "68", "72"], "a": 1},
    {"q": "150 ÷ 3 = ?", "o": ["40", "50", "60", "70"], "a": 1},
    {"q": "19 + 11 = ?", "o": ["28", "30", "32", "34"], "a": 1},
    {"q": "95 - 15 = ?", "o": ["70", "80", "90", "100"], "a": 1},
    {"q": "6 x 9 = ?", "o": ["50", "54", "58", "62"], "a": 1},
    {"q": "200 ÷ 2 = ?", "o": ["80", "100", "120", "140"], "a": 1},
    {"q": "45 + 15 = ?", "o": ["55", "60", "65", "70"], "a": 1},
    {"q": "110 - 20 = ?", "o": ["80", "90", "100", "110"], "a": 1},
    {"q": "7 x 8 = ?", "o": ["52", "56", "60", "64"], "a": 1},
    {"q": "70 ÷ 7 = ?", "o": ["8", "10", "12", "14"], "a": 1},
    {"q": "32 + 18 = ?", "o": ["48", "50", "52", "54"], "a": 1},
    {"q": "130 - 40 = ?", "o": ["80", "90", "100", "110"], "a": 1},
    {"q": "4 x 9 = ?", "o": ["32", "36", "40", "44"], "a": 1},
    {"q": "400 ÷ 4 = ?", "o": ["80", "100", "120", "140"], "a": 1},
    {"q": "27 + 13 = ?", "o": ["37", "40", "43", "46"], "a": 1},
    {"q": "160 - 80 = ?", "o": ["70", "80", "90", "100"], "a": 1},
    {"q": "8 x 3 = ?", "o": ["21", "24", "27", "30"], "a": 1},
    {"q": "45 ÷ 5 = ?", "o": ["7", "8", "9", "10"], "a": 2},
    {"q": "16 + 24 = ?", "o": ["38", "40", "42", "44"], "a": 1},
    {"q": "140 - 60 = ?", "o": ["70", "80", "90", "100"], "a": 1},
    {"q": "6 x 6 = ?", "o": ["32", "36", "40", "44"], "a": 1},
    {"q": "500 ÷ 5 = ?", "o": ["80", "100", "120", "140"], "a": 1},
    {"q": "35 + 25 = ?", "o": ["55", "60", "65", "70"], "a": 1},
    {"q": "180 - 90 = ?", "o": ["80", "90", "100", "110"], "a": 1},
    {"q": "9 x 3 = ?", "o": ["24", "27", "30", "33"], "a": 1},
    {"q": "300 ÷ 3 = ?", "o": ["80", "100", "120", "140"], "a": 1},
    {"q": "48 + 12 = ?", "o": ["58", "60", "62", "64"], "a": 1},
    {"q": "220 - 20 = ?", "o": ["180", "200", "220", "240"], "a": 1},
    {"q": "7 x 4 = ?", "o": ["24", "28", "32", "36"], "a": 1},
    {"q": "24 ÷ 4 = ?", "o": ["4", "5", "6", "7"], "a": 2},
    {"q": "19 + 21 = ?", "o": ["38", "40", "42", "44"], "a": 1},
    {"q": "170 - 70 = ?", "o": ["90", "100", "110", "120"], "a": 1},
    {"q": "5 x 8 = ?", "o": ["35", "40", "45", "50"], "a": 1},
    {"q": "80 ÷ 8 = ?", "o": ["8", "10", "12", "14"], "a": 1},
    {"q": "50 + 50 = ?", "o": ["90", "100", "110", "120"], "a": 1},
    {"q": "300 - 150 = ?", "o": ["140", "150", "160", "170"], "a": 1},
    {"q": "6 x 8 = ?", "o": ["44", "48", "52", "56"], "a": 1},
    {"q": "90 ÷ 10 = ?", "o": ["7", "8", "9", "10"], "a": 2},
    {"q": "15 + 45 = ?", "o": ["55", "60", "65", "70"], "a": 1},
    {"q": "250 - 50 = ?", "o": ["180", "200", "220", "240"], "a": 1},
    {"q": "7 x 3 = ?", "o": ["18", "21", "24", "27"], "a": 1},
    {"q": "21 ÷ 3 = ?", "o": ["5", "6", "7", "8"], "a": 2},

    # --- ENGLISH CATEGORY (100 Questions) ---
    {"q": "Sahi spelling chuno (Apple):", "o": ["Apel", "Apple", "Appel", "Aple"], "a": 1},
    {"q": "Sahi spelling chuno (Moon):", "o": ["Mon", "Mone", "Moon", "Moun"], "a": 2},
    {"q": "Sahi spelling chuno (Light):", "o": ["Lite", "Light", "Litgh", "Laight"], "a": 1},
    {"q": "Sahi spelling chuno (Ball):", "o": ["Bal", "Baal", "Boll", "Ball"], "a": 3},
    {"q": "Opposite of 'Day' kya hota hai?", "o": ["Night", "Morning", "Evening", "Noon"], "a": 0},
    {"q": "Opposite of 'Hot' kya hota hai?", "o": ["Warm", "Cold", "Spicy", "Ice"], "a": 1},
    {"q": "Opposite of 'Big' kya hota hai?", "o": ["Large", "Huge", "Small", "Tall"], "a": 2},
    {"q": "Opposite of 'Fast' kya hota hai?", "o": ["Quick", "Slow", "Run", "Stop"], "a": 1},
    {"q": "Plural chuno: 1 Boy, 2 ____?", "o": ["Boyes", "Boys", "Boies", "Boyen"], "a": 1},
    {"q": "Plural chuno: 1 Cat, 3 ____?", "o": ["Cats", "Cates", "Catz", "Kittens"], "a": 0},
    {"q": "Sahi spelling chuno (Water):", "o": ["Watar", "Water", "Woter", "Watir"], "a": 1},
    {"q": "Sahi spelling chuno (School):", "o": ["Scol", "Shul", "School", "Schoole"], "a": 2},
    {"q": "Sahi spelling chuno (Book):", "o": ["Bok", "Book", "Boke", "Bouk"], "a": 1},
    {"q": "Sahi spelling chuno (Friend):", "o": ["Frend", "Freind", "Friend", "Frind"], "a": 2},
    {"q": "Opposite of 'Happy' kya hai?", "o": ["Sad", "Angry", "Joy", "Cry"], "a": 0},
    {"q": "Opposite of 'Up' kya hota hai?", "o": ["High", "Down", "Left", "Right"], "a": 1},
    {"q": "Opposite of 'Good' kya hota hai?", "o": ["Best", "Nice", "Bad", "Fine"], "a": 2},
    {"q": "Opposite of 'Yes' kya hota hai?", "o": ["Never", "No", "Ok", "Sure"], "a": 1},
    {"q": "Plural chuno: 1 Dog, 5 ____?", "o": ["Doges", "Dogs", "Dogz", "Puppies"], "a": 1},
    {"q": "Plural chuno: 1 Tree, 4 ____?", "o": ["Trees", "Treeses", "Treez", "Treess"], "a": 0},
    {"q": "Sahi spelling chuno (Sun):", "o": ["Son", "Sun", "Sonn", "Sune"], "a": 1},
    {"q": "Sahi spelling chuno (Star):", "o": ["Star", "Starr", "Ster", "Stare"], "a": 0},
    {"q": "Sahi spelling chuno (King):", "o": ["Keng", "King", "Kyng", "Kengs"], "a": 1},
    {"q": "Sahi spelling chuno (Queen):", "o": ["Quen", "Quean", "Queen", "Queene"], "a": 2},
    {"q": "Opposite of 'Black' kya hota hai?", "o": ["Dark", "White", "Grey", "Blue"], "a": 1},
    {"q": "Opposite of 'Love' kya hota hai?", "o": ["Like", "Hate", "Angry", "Sad"], "a": 1},
    {"q": "Opposite of 'Open' kya hota hai?", "o": ["Close", "Lock", "Shut", "Hide"], "a": 0},
    {"q": "Opposite of 'Rich' kya hota hai?", "o": ["Poor", "Money", "Gold", "Cheap"], "a": 0},
    {"q": "Plural chuno: 1 Car, 2 ____?", "o": ["Cares", "Cars", "Carz", "Careses"], "a": 1},
    {"q": "Plural chuno: 1 Pen, 10 ____?", "o": ["Penes", "Penz", "Pens", "Pins"], "a": 2},
    {"q": "Sahi spelling chuno (House):", "o": ["Hous", "House", "Howse", "Huse"], "a": 1},
    {"q": "Sahi spelling chuno (Computer):", "o": ["Computar", "Computer", "Computor", "Comptur"], "a": 1},
    {"q": "Sahi spelling chuno (Mobile):", "o": ["Mobil", "Mobile", "Mobeil", "Mobail"], "a": 1},
    {"q": "Sahi spelling chuno (Clock):", "o": ["Clok", "Clock", "Cloke", "Clook"], "a": 1},
    {"q": "Opposite of 'Left' kya hota hai?", "o": ["Right", "Down", "Straight", "Back"], "a": 0},
    {"q": "Opposite of 'Soft' kya hota hai?", "o": ["Hard", "Tough", "Solid", "Smooth"], "a": 0},
    {"q": "Opposite of 'New' kya hota hai?", "o": ["Fresh", "Young", "Old", "Ancient"], "a": 2},
    {"q": "Opposite of 'Clean' kya hota hai?", "o": ["Dirty", "Dust", "Mess", "Wash"], "a": 0},
    {"q": "Plural chuno: 1 Chair, 3 ____?", "o": ["Chairs", "Chaires", "Chairz", "Cher"], "a": 0},
    {"q": "Plural chuno: 1 Table, 2 ____?", "o": ["Tables", "Tabels", "Tablez", "Tabless"], "a": 0},
    {"q": "Sahi spelling chuno (Time):", "o": ["Taim", "Time", "Tyme", "Tiime"], "a": 1},
    {"q": "Sahi spelling chuno (Game):", "o": ["Gaim", "Game", "Gaym", "Geim"], "a": 1},
    {"q": "Sahi spelling chuno (Music):", "o": ["Musik", "Musyc", "Music", "Muzic"], "a": 2},
    {"q": "Sahi spelling chuno (Movie):", "o": ["Movi", "Movie", "Movy", "Muvi"], "a": 1},
    {"q": "Opposite of 'True' kya hota hai?", "o": ["False", "Wrong", "Lie", "Correct"], "a": 0},
    {"q": "Opposite of 'First' kya hota hai?", "o": ["Second", "Last", "End", "Final"], "a": 1},
    {"q": "Opposite of 'Heavy' kya hota hai?", "o": ["Light", "Soft", "Thin", "Small"], "a": 0},
    {"q": "Opposite of 'Beautiful' kya hota hai?", "o": ["Ugly", "Bad", "Dirty", "Cute"], "a": 0},
    {"q": "Plural chuno: 1 Cup, 4 ____?", "o": ["Cupes", "Cups", "Cupz", "Cupless"], "a": 1},
    {"q": "Plural chuno: 1 Key, 2 ____?", "o": ["Keyes", "Keys", "Keies", "Keyz"], "a": 1},
    {"q": "Sahi spelling chuno (Fruit):", "o": ["Frut", "Fruit", "Froat", "Frute"], "a": 1},
    {"q": "Sahi spelling chuno (Banana):", "o": ["Banana", "Banan", "Bananna", "Benana"], "a": 0},
    {"q": "Sahi spelling chuno (Mango):", "o": ["Mengo", "Mango", "Mangoe", "Manngo"], "a": 1},
    {"q": "Sahi spelling chuno (Orange):", "o": ["Oreng", "Orange", "Orang", "Arange"], "a": 1},
    {"q": "Opposite of 'In' kya hota hai?", "o": ["Out", "On", "Up", "Under"], "a": 0},
    {"q": "Opposite of 'Far' kya hota hai?", "o": ["Near", "Close", "Distance", "Away"], "a": 0},
    {"q": "Opposite of 'Tall' kya hota hai?", "o": ["Short", "Small", "Low", "Little"], "a": 0},
    {"q": "Opposite of 'Smart' kya hota hai?", "o": ["Stupid", "Dumb", "Fool", "Silly"], "a": 0},
    {"q": "Plural chuno: 1 Bird, 5 ____?", "o": ["Birdes", "Birdz", "Birds", "Birdss"], "a": 2},
    {"q": "Plural chuno: 1 Ring, 2 ____?", "o": ["Rings", "Ringes", "Ringz", "Rengs"], "a": 0},
    {"q": "Sahi spelling chuno (Animal):", "o": ["Animel", "Animal", "Anemul", "Animale"], "a": 1},
    {"q": "Sahi spelling chuno (Tiger):", "o": ["Tegor", "Tiger", "Tigar", "Tygre"], "a": 1},
    {"q": "Sahi spelling chuno (Lion):", "o": ["Leon", "Lion", "Lyne", "Lione"], "a": 1},
    {"q": "Sahi spelling chuno (Elephant):", "o": ["Elefant", "Elephant", "Eliphant", "Elephante"], "a": 1},
    {"q": "Opposite of 'Sweet' kya hota hai?", "o": ["Sour", "Bitter", "Salty", "All of these"], "a": 3},
    {"q": "Opposite of 'Dry' kya hota hai?", "o": ["Wet", "Water", "Cold", "Rain"], "a": 0},
    {"q": "Opposite of 'Strong' kya hota hai?", "o": ["Weak", "Soft", "Low", "Thin"], "a": 0},
    {"q": "Opposite of 'Young' kya hota hai?", "o": ["Old", "Child", "Man", "Baby"], "a": 0},
    {"q": "Plural chuno: 1 Room, 3 ____?", "o": ["Rooms", "Roomes", "Roomz", "Rum"], "a": 0},
    {"q": "Plural chuno: 1 Door, 2 ____?", "o": ["Doores", "Doors", "Doorz", "Dors"], "a": 1},
    {"q": "Sahi spelling chuno (Sky):", "o": ["Skai", "Sky", "Skay", "Skie"], "a": 1},
    {"q": "Sahi spelling chuno (Cloud):", "o": ["Claud", "Cloud", "Clod", "Clowd"], "a": 1},
    {"q": "Sahi spelling chuno (Rain):", "o": ["Rane", "Rain", "Rayn", "Rane"], "a": 1},
    {"q": "Sahi spelling chuno (Wind):", "o": ["Wind", "Wend", "Wynd", "Winde"], "a": 0},
    {"q": "Opposite of 'High' kya hota hai?", "o": ["Low", "Down", "Short", "Small"], "a": 0},
    {"q": "Opposite of 'Deep' kya hota hai?", "o": ["Shallow", "Low", "High", "Flat"], "a": 0},
    {"q": "Opposite of 'Wide' kya hota hai?", "o": ["Narrow", "Small", "Short", "Thin"], "a": 0},
    {"q": "Opposite of 'Thick' kya hota hai?", "o": ["Thin", "Soft", "Light", "Small"], "a": 0},
    {"q": "Plural chuno: 1 Shoe, 2 ____?", "o": ["Shoes", "Shoese", "Shoez", "Shoen"], "a": 0},
    {"q": "Plural chuno: 1 Sock, 2 ____?", "o": ["Sockes", "Socks", "Sockz", "Sokes"], "a": 1},
    {"q": "Sahi spelling chuno (Fire):", "o": ["Fyre", "Fire", "Fier", "Fiire"], "a": 1},
    {"q": "Sahi spelling chuno (Earth):", "o": ["Erth", "Earth", "Earthe", "Urth"], "a": 1},
    {"q": "Sahi spelling chuno (River):", "o": ["Rivar", "River", "Rever", "Rivir"], "a": 1},
    {"q": "Sahi spelling chuno (Sea):", "o": ["See", "Sea", "Se", "Si"], "a": 1},
    {"q": "Opposite of 'Live' kya hota hai?", "o": ["Die", "Dead", "Sleep", "End"], "a": 0},
    {"q": "Opposite of 'Buy' kya hota hai?", "o": ["Sell", "Give", "Take", "Shop"], "a": 0},
    {"q": "Opposite of 'Win' kya hota hai?", "o": ["Lose", "Fail", "Drop", "Beat"], "a": 0},
    {"q": "Opposite of 'Give' kya hota hai?", "o": ["Take", "Get", "Receive", "All of these"], "a": 3},
    {"q": "Plural chuno: 1 Boat, 4 ____?", "o": ["Boates", "Boats", "Boatz", "Botes"], "a": 1},
    {"q": "Plural chuno: 1 Ship, 2 ____?", "o": ["Shipes", "Shipz", "Ships", "Sheps"], "a": 2},
    {"q": "Sahi spelling chuno (Gold):", "o": ["Gole", "Gold", "Golde", "Gould"], "a": 1},
    {"q": "Sahi spelling chuno (Silver):", "o": ["Silvar", "Silver", "Selver", "Sylver"], "a": 1},
    {"q": "Sahi spelling chuno (Diamond):", "o": ["Dimond", "Diamond", "Diamund", "Deamond"], "a": 1},
    {"q": "Sahi spelling chuno (Iron):", "o": ["Iron", "Ironn", "Iren", "Yron"], "a": 0},
    {"q": "Opposite of 'Sharp' kya hota hai?", "o": ["Blunt", "Soft", "Low", "Smooth"], "a": 0},
    {"q": "Opposite of 'Smooth' kya hota hai?", "o": ["Rough", "Hard", "Tough", "Sharp"], "a": 0},
    {"q": "Opposite of 'Polite' kya hota hai?", "o": ["Rude", "Angry", "Bad", "Hard"], "a": 0},
    {"q": "Plural chuno: 1 Window, 5 ____?", "o": ["Windows", "Windowes", "Windowz", "Windos"], "a": 0},
    {"q": "Plural chuno: 1 Clock, 2 ____?", "o": ["Clocks", "Clockes", "Clockz", "Cloks"], "a": 0}
]

GROUP_GAMES = {}

# 1️⃣ /start karne par SIRF stylish welcome profile message aayega
@dp.message(Command("start"))
async def send_welcome_profile(message: types.Message):
    user_name = message.from_user.first_name if message.from_user.first_name else "PLAYER"
    user_name = user_name.upper()
    text = WELCOME_TEXT.format(user_name=user_name)
    await message.answer(text)

# ⚙️ Speed Changer Command (/sc 10, /sc 20 etc.)
@dp.message(Command("sc"))
async def change_quiz_speed(message: types.Message):
    chat_id = message.chat.id
    args = message.text.split()
    
    if len(args) < 2:
        await message.answer("⚠️ **Sahi tareeqa:** `/sc 10` ya `/sc 20` likhein!")
        return
        
    try:
        new_time = int(args[1])
        if new_time < 5 or new_time > 300:
            await message.answer("⚠️ **Error:** Speed limit 5s se 300s tak hi ho sakti hai!")
            return
            
        if chat_id not in GROUP_GAMES:
            GROUP_GAMES[chat_id] = {"active": False, "speed": 15}
            
        GROUP_GAMES[chat_id]["speed"] = new_time
        await message.answer(f"⚡ **Speed Changed Successfully!**\nAb se har sawaal **{new_time} Seconds** tak chalega.")
        
    except ValueError:
        await message.answer("⚠️ **Error:** `/sc` ke aage ek sahi number dalein!")

# 2️⃣ Quiz Shuru Karne Ka Command: /quiz/on
@dp.message(lambda message: message.text and message.text.lower().startswith('/quiz/on'))
async def start_native_quiz(message: types.Message):
    chat_id = message.chat.id
    
    if chat_id not in GROUP_GAMES:
        GROUP_GAMES[chat_id] = {"active": False, "speed": 15}
        
    if GROUP_GAMES[chat_id]["active"]:
        await message.answer("⚠️ **Group mein pehle se ek quiz chal raha hai!**")
        return

    GROUP_GAMES[chat_id]["active"] = True
    current_speed = GROUP_GAMES[chat_id]["speed"]
    
    # Pure database (200 sawaal) se har round mein randomly 15 mix sawaal nikalega
    round_questions = random.sample(QUIZ_DATA, min(len(QUIZ_DATA), 15))
    total_q = len(round_questions)

    await message.answer(f"🚀 **MIX (MATHS + ENGLISH) QUIZ BATTLE STARTING IN 3 SECONDS...**\n⏱️ *Speed:* **{current_speed}s** | 📝 *Total Sawaal:* **{total_q}**")
    await asyncio.sleep(3)

    for idx, q_item in enumerate(round_questions):
        if chat_id not in GROUP_GAMES or not GROUP_GAMES[chat_id]["active"]:
            break
            
        await bot.send_poll(
            chat_id=chat_id,
            question=f"📝 SAWAAL {idx + 1}/{total_q}:\n👉 {q_item['q']}",
            options=q_item["o"],
            type="quiz",
            correct_option_id=q_item["a"],
            is_anonymous=False,
            open_period=current_speed
        )
        
        await asyncio.sleep(current_speed + 1)

    if chat_id in GROUP_GAMES and GROUP_GAMES[chat_id]["active"]:
        await bot.send_message(chat_id, "🏁 **Quiz Khatam! Khelne ke liye sabhi ka shukriya. ✨**")
        GROUP_GAMES[chat_id]["active"] = False

# 3️⃣ Quiz Rokne Ka Command: /quiz/off
@dp.message(lambda message: message.text and message.text.lower().startswith('/quiz/off'))
async def stop_native_quiz(message: types.Message):
    chat_id = message.chat.id
    if chat_id in GROUP_GAMES and GROUP_GAMES[chat_id]["active"]:
        GROUP_GAMES[chat_id]["active"] = False
        await message.answer("🛑 **Quiz ko beech mein hi rok diya gaya hai!**\n\nNaya game shuru karne ke liye `/quiz/on` likhein.")
    else:
        await message.answer("⚠️ **Abhi g
