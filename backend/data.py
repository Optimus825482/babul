BRAND_MODELS = {
    "BMW": ["320i", "520i", "X3", "X5", "116i", "330i", "520d", "X1", "X6", "3 Serisi", "5 Serisi", "4 Serisi", "118i", "320d"],
    "Mercedes": ["C180", "C200", "E200", "GLC", "A180", "CLA", "GLA", "E300", "S Class", "AMG GT", "C220", "A200", "GLB"],
    "Audi": ["A3", "A4", "A5", "A6", "Q5", "Q7", "A1", "Q3", "Q2", "S4", "RS6", "A7", "Q8"],
    "Volkswagen": ["Golf", "Passat", "Tiguan", "Polo", "Jetta", "Touareg", "T-Roc", "ID.4", "Golf GTI", "Golf R"],
    "Toyota": ["Corolla", "Camry", "RAV4", "Yaris", "C-HR", "Hilux", "Land Cruiser", "Supra", "Prius"],
    "Honda": ["Civic", "Accord", "CR-V", "HR-V", "City", "Jazz", "Civic Type R"],
    "Hyundai": ["Tucson", "i20", "i30", "Kona", "Elantra", "Santa Fe", "Bayon", "i10"],
    "Ford": ["Focus", "Kuga", "Puma", "Fiesta", "Ranger", "Mustang", "EcoSport", "Tourneo"],
    "Renault": ["Megane", "Clio", "Captur", "Duster", "Kadjar", "Symbol", "Fluence", "Arkana"],
    "Fiat": ["Egea", "500X", "Panda", "Tipo", "Doblo", "500", "Ducato", "Pulse"],
    "Peugeot": ["3008", "2008", "308", "508", "208", "5008", "Rifter"],
    "Volvo": ["XC60", "XC90", "S60", "V60", "V90", "XC40", "S90"],
    "Nissan": ["Qashqai", "Juke", "X-Trail", "Micra", "Leaf", "Patrol", "Kicks"],
    "Kia": ["Sportage", "Ceed", "Cerato", "Seltos", "Sorento", "Picanto", "Stonic", "EV6"],
    "Mazda": ["CX-5", "3", "CX-3", "6", "MX-5", "CX-30", "CX-9", "CX-60"],
    "Škoda": ["Octavia", "Superb", "Kodiaq", "Kamiq", "Karoq", "Fabia", "Scala"],
    "Seat": ["Leon", "Ibiza", "Ateca", "Tarraco", "Arona", "Toledo"],
    "Opel": ["Astra", "Corsa", "Mokka", "Crossland", "Grandland", "Insignia", "Zafira"],
    "Tesla": ["Model 3", "Model Y", "Model S", "Model X"],
    "Togg": ["T10X"],
}

YEARS = [str(y) for y in range(2026, 1999, -1)]

FILTER_OPTIONS = {
    "fuelTypes": ["Benzin", "Dizel", "LPG", "Hybrid", "Elektrik"],
    "transmissions": ["Otomatik", "Manuel", "Yarı Otomatik"],
    "bodyTypes": ["Sedan", "Hatchback", "SUV", "Station Wagon", "Coupe", "Cabrio", "MPV", "Pickup"],
    "sources": ["arabam.com", "sahibinden.com"],
    "sortOptions": [
        {"value": "price_asc", "label": "En düşük fiyat"},
        {"value": "price_desc", "label": "En yüksek fiyat"},
        {"value": "km_asc", "label": "En düşük km"},
        {"value": "year_desc", "label": "En yeni model"},
        {"value": "date_desc", "label": "En yeni ilan"},
    ],
}
