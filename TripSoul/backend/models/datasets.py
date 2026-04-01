"""
Preloaded city datasets for NYC, Tokyo, and Paris.
Each city has 15+ attractions with real coordinates, cost ranges,
categories, popularity weights, and weather sensitivity flags.
"""

CITY_DATA = {
    "nyc": {
        "name": "New York City",
        "country": "USA",
        "timezone": "America/New_York",
        "center": {"lat": 40.7128, "lng": -74.0060},
        "currency": "USD",
        "attractions": [
            {"id": "nyc_01", "name": "Statue of Liberty", "category": "history", "lat": 40.6892, "lng": -74.0445, "cost": 24.0, "duration_hours": 3.0, "popularity": 0.98, "description": "Iconic symbol of freedom on Liberty Island. Ferry includes Ellis Island Immigration Museum.", "weather_sensitive": True, "opening_hour": 9, "closing_hour": 17},
            {"id": "nyc_02", "name": "Central Park", "category": "nature", "lat": 40.7829, "lng": -73.9654, "cost": 0.0, "duration_hours": 2.5, "popularity": 0.97, "description": "843-acre urban oasis with lakes, trails, Bethesda Fountain, and Strawberry Fields.", "weather_sensitive": True, "opening_hour": 6, "closing_hour": 22},
            {"id": "nyc_03", "name": "Metropolitan Museum of Art", "category": "culture", "lat": 40.7794, "lng": -73.9632, "cost": 30.0, "duration_hours": 3.0, "popularity": 0.96, "description": "World's largest art museum with 2M+ works spanning 5,000 years of civilization.", "weather_sensitive": False, "opening_hour": 10, "closing_hour": 17},
            {"id": "nyc_04", "name": "Times Square", "category": "shopping", "lat": 40.7580, "lng": -73.9855, "cost": 0.0, "duration_hours": 1.5, "popularity": 0.94, "description": "The Crossroads of the World — neon billboards, Broadway theaters, and urban energy.", "weather_sensitive": False, "opening_hour": 0, "closing_hour": 23},
            {"id": "nyc_05", "name": "Brooklyn Bridge Walk", "category": "adventure", "lat": 40.7061, "lng": -73.9969, "cost": 0.0, "duration_hours": 1.5, "popularity": 0.92, "description": "Walk the 1.1-mile Gothic Revival bridge with panoramic skyline views.", "weather_sensitive": True, "opening_hour": 6, "closing_hour": 22},
            {"id": "nyc_06", "name": "9/11 Memorial & Museum", "category": "history", "lat": 40.7115, "lng": -74.0134, "cost": 28.0, "duration_hours": 2.5, "popularity": 0.93, "description": "Somber memorial at Ground Zero with reflecting pools and underground museum.", "weather_sensitive": False, "opening_hour": 9, "closing_hour": 20},
            {"id": "nyc_07", "name": "Chelsea Market", "category": "food", "lat": 40.7424, "lng": -74.0061, "cost": 25.0, "duration_hours": 1.5, "popularity": 0.88, "description": "Industrial food hall in a former Nabisco factory. Lobster, tacos, artisan gelato.", "weather_sensitive": False, "opening_hour": 7, "closing_hour": 21},
            {"id": "nyc_08", "name": "Top of the Rock", "category": "culture", "lat": 40.7587, "lng": -73.9787, "cost": 43.0, "duration_hours": 1.5, "popularity": 0.91, "description": "70th-floor observation deck at Rockefeller Center with unobstructed Central Park/skyline views.", "weather_sensitive": True, "opening_hour": 9, "closing_hour": 23},
            {"id": "nyc_09", "name": "Broadway Show", "category": "nightlife", "lat": 40.7590, "lng": -73.9845, "cost": 120.0, "duration_hours": 2.5, "popularity": 0.95, "description": "World-class theater — musicals ranging from Hamilton to Wicked.", "weather_sensitive": False, "opening_hour": 19, "closing_hour": 22},
            {"id": "nyc_10", "name": "Smorgasburg", "category": "food", "lat": 40.7215, "lng": -73.9612, "cost": 20.0, "duration_hours": 2.0, "popularity": 0.85, "description": "Brooklyn's legendary open-air food market with 100+ local vendors.", "weather_sensitive": True, "opening_hour": 11, "closing_hour": 18},
            {"id": "nyc_11", "name": "The High Line", "category": "nature", "lat": 40.7480, "lng": -74.0048, "cost": 0.0, "duration_hours": 1.5, "popularity": 0.90, "description": "Elevated park on a former railway with art installations and Hudson River views.", "weather_sensitive": True, "opening_hour": 7, "closing_hour": 22},
            {"id": "nyc_12", "name": "MoMA", "category": "culture", "lat": 40.7614, "lng": -73.9776, "cost": 25.0, "duration_hours": 2.5, "popularity": 0.89, "description": "Museum of Modern Art — Starry Night, Campbell's Soup Cans, and contemporary masterworks.", "weather_sensitive": False, "opening_hour": 10, "closing_hour": 17},
            {"id": "nyc_13", "name": "Chinatown Food Tour", "category": "food", "lat": 40.7158, "lng": -73.9970, "cost": 15.0, "duration_hours": 2.0, "popularity": 0.82, "description": "Dim sum, hand-pulled noodles, and bubble tea in Manhattan's vibrant Chinatown.", "weather_sensitive": False, "opening_hour": 10, "closing_hour": 21},
            {"id": "nyc_14", "name": "One World Observatory", "category": "culture", "lat": 40.7127, "lng": -74.0134, "cost": 44.0, "duration_hours": 1.5, "popularity": 0.87, "description": "360° views from the 102nd floor of the Western Hemisphere's tallest building.", "weather_sensitive": True, "opening_hour": 10, "closing_hour": 21},
            {"id": "nyc_15", "name": "Greenwich Village Jazz Club", "category": "nightlife", "lat": 40.7336, "lng": -74.0027, "cost": 30.0, "duration_hours": 2.0, "popularity": 0.80, "description": "Live jazz at legendary Village Vanguard or Blue Note — NYC's beating musical heart.", "weather_sensitive": False, "opening_hour": 20, "closing_hour": 23},
            {"id": "nyc_16", "name": "DUMBO Photo Walk", "category": "adventure", "lat": 40.7033, "lng": -73.9894, "cost": 0.0, "duration_hours": 1.5, "popularity": 0.83, "description": "Brooklyn's most photogenic neighborhood — Manhattan Bridge frame, cobblestone streets.", "weather_sensitive": True, "opening_hour": 7, "closing_hour": 21},
        ],
    },
    "tokyo": {
        "name": "Tokyo",
        "country": "Japan",
        "timezone": "Asia/Tokyo",
        "center": {"lat": 35.6762, "lng": 139.6503},
        "currency": "JPY",
        "attractions": [
            {"id": "tyo_01", "name": "Senso-ji Temple", "category": "culture", "lat": 35.7148, "lng": 139.7967, "cost": 0.0, "duration_hours": 1.5, "popularity": 0.97, "description": "Tokyo's oldest temple (628 AD) in Asakusa with Thunder Gate and Nakamise shopping street.", "weather_sensitive": True, "opening_hour": 6, "closing_hour": 17},
            {"id": "tyo_02", "name": "Tsukiji Outer Market", "category": "food", "lat": 35.6654, "lng": 139.7707, "cost": 20.0, "duration_hours": 2.0, "popularity": 0.94, "description": "Fresh sushi, tamagoyaki, and street food at the world's most famous fish market district.", "weather_sensitive": False, "opening_hour": 5, "closing_hour": 14},
            {"id": "tyo_03", "name": "Shibuya Crossing", "category": "culture", "lat": 35.6595, "lng": 139.7004, "cost": 0.0, "duration_hours": 1.0, "popularity": 0.96, "description": "World's busiest pedestrian crossing — pure urban spectacle. Best viewed from Starbucks above.", "weather_sensitive": False, "opening_hour": 0, "closing_hour": 23},
            {"id": "tyo_04", "name": "Meiji Shrine", "category": "culture", "lat": 35.6764, "lng": 139.6993, "cost": 0.0, "duration_hours": 1.5, "popularity": 0.92, "description": "Serene Shinto shrine in a 170-acre forest dedicated to Emperor Meiji.", "weather_sensitive": True, "opening_hour": 5, "closing_hour": 18},
            {"id": "tyo_05", "name": "TeamLab Borderless", "category": "culture", "lat": 35.6267, "lng": 139.7842, "cost": 35.0, "duration_hours": 2.5, "popularity": 0.95, "description": "Immersive digital art museum — rooms of flowing light, responsive projections, infinite wonder.", "weather_sensitive": False, "opening_hour": 10, "closing_hour": 19},
            {"id": "tyo_06", "name": "Akihabara", "category": "shopping", "lat": 35.7023, "lng": 139.7745, "cost": 30.0, "duration_hours": 2.5, "popularity": 0.88, "description": "Electric Town — anime shops, maid cafes, retro arcades, and electronic gadget heaven.", "weather_sensitive": False, "opening_hour": 10, "closing_hour": 21},
            {"id": "tyo_07", "name": "Shinjuku Gyoen", "category": "nature", "lat": 35.6852, "lng": 139.7100, "cost": 5.0, "duration_hours": 2.0, "popularity": 0.89, "description": "Vast urban garden blending Japanese, English, and French landscape design.", "weather_sensitive": True, "opening_hour": 9, "closing_hour": 16},
            {"id": "tyo_08", "name": "Ramen Street (Tokyo Station)", "category": "food", "lat": 35.6812, "lng": 139.7671, "cost": 12.0, "duration_hours": 1.0, "popularity": 0.86, "description": "Eight top-tier ramen shops in a basement corridor. Each serves a different regional style.", "weather_sensitive": False, "opening_hour": 11, "closing_hour": 22},
            {"id": "tyo_09", "name": "Tokyo Skytree", "category": "adventure", "lat": 35.7101, "lng": 139.8107, "cost": 25.0, "duration_hours": 1.5, "popularity": 0.91, "description": "634m broadcasting tower with two observation decks and panoramic views of the Kanto plain.", "weather_sensitive": True, "opening_hour": 10, "closing_hour": 21},
            {"id": "tyo_10", "name": "Harajuku & Takeshita Street", "category": "shopping", "lat": 35.6702, "lng": 139.7026, "cost": 15.0, "duration_hours": 2.0, "popularity": 0.90, "description": "Kawaii culture epicenter — crepe stalls, vintage shops, cosplay, and street fashion.", "weather_sensitive": False, "opening_hour": 10, "closing_hour": 20},
            {"id": "tyo_11", "name": "Robot Restaurant Shinjuku", "category": "nightlife", "lat": 35.6938, "lng": 139.7034, "cost": 55.0, "duration_hours": 1.5, "popularity": 0.83, "description": "Neon-drenched performance show with giant robots and dancers — pure sensory overload.", "weather_sensitive": False, "opening_hour": 16, "closing_hour": 23},
            {"id": "tyo_12", "name": "Ueno Park & Museums", "category": "history", "lat": 35.7146, "lng": 139.7732, "cost": 10.0, "duration_hours": 3.0, "popularity": 0.87, "description": "Park with Tokyo National Museum, zoo, and temples. Cherry blossom hotspot in spring.", "weather_sensitive": True, "opening_hour": 9, "closing_hour": 17},
            {"id": "tyo_13", "name": "Golden Gai Bar Hop", "category": "nightlife", "lat": 35.6942, "lng": 139.7046, "cost": 25.0, "duration_hours": 2.0, "popularity": 0.85, "description": "Six narrow alleys packed with 200+ tiny bars seating 5-10 people each. Post-war atmosphere.", "weather_sensitive": False, "opening_hour": 19, "closing_hour": 23},
            {"id": "tyo_14", "name": "Yanaka Old Town Walk", "category": "history", "lat": 35.7275, "lng": 139.7636, "cost": 0.0, "duration_hours": 2.0, "popularity": 0.78, "description": "Pre-war neighborhood that survived the bombings — temples, cat statues, craft shops.", "weather_sensitive": True, "opening_hour": 8, "closing_hour": 18},
            {"id": "tyo_15", "name": "Odaiba Gundam & Beach", "category": "adventure", "lat": 35.6267, "lng": 139.7755, "cost": 0.0, "duration_hours": 2.5, "popularity": 0.81, "description": "Futuristic island with life-size Unicorn Gundam statue and Tokyo Bay beach.", "weather_sensitive": True, "opening_hour": 9, "closing_hour": 21},
        ],
    },
    "paris": {
        "name": "Paris",
        "country": "France",
        "timezone": "Europe/Paris",
        "center": {"lat": 48.8566, "lng": 2.3522},
        "currency": "EUR",
        "attractions": [
            {"id": "par_01", "name": "Eiffel Tower", "category": "culture", "lat": 48.8584, "lng": 2.2945, "cost": 29.0, "duration_hours": 2.5, "popularity": 0.99, "description": "The Iron Lady — 330m icon of Paris. Summit elevator for 360° views over the entire city.", "weather_sensitive": True, "opening_hour": 9, "closing_hour": 23},
            {"id": "par_02", "name": "Louvre Museum", "category": "culture", "lat": 48.8606, "lng": 2.3376, "cost": 22.0, "duration_hours": 3.5, "popularity": 0.98, "description": "World's largest art museum — Mona Lisa, Venus de Milo, Winged Victory across 72,735m².", "weather_sensitive": False, "opening_hour": 9, "closing_hour": 18},
            {"id": "par_03", "name": "Notre-Dame Cathedral", "category": "history", "lat": 48.8530, "lng": 2.3499, "cost": 0.0, "duration_hours": 1.5, "popularity": 0.95, "description": "Gothic masterpiece on Île de la Cité, rebuilt after 2019 fire. Exterior and square accessible.", "weather_sensitive": True, "opening_hour": 8, "closing_hour": 18},
            {"id": "par_04", "name": "Montmartre & Sacré-Cœur", "category": "culture", "lat": 48.8867, "lng": 2.3431, "cost": 0.0, "duration_hours": 2.5, "popularity": 0.93, "description": "Hilltop artists' quarter with white basilica, Place du Tertre painters, and sweeping views.", "weather_sensitive": True, "opening_hour": 6, "closing_hour": 22},
            {"id": "par_05", "name": "Musée d'Orsay", "category": "culture", "lat": 48.8600, "lng": 2.3266, "cost": 16.0, "duration_hours": 2.5, "popularity": 0.92, "description": "Impressionist paradise in a former railway station — Monet, Renoir, Van Gogh, Degas.", "weather_sensitive": False, "opening_hour": 9, "closing_hour": 18},
            {"id": "par_06", "name": "Le Marais Food Walk", "category": "food", "lat": 48.8566, "lng": 2.3622, "cost": 20.0, "duration_hours": 2.0, "popularity": 0.88, "description": "Falafel at L'As du Fallafel, pastries at Jacques Genin, cheese at Fromagerie Beaufils.", "weather_sensitive": False, "opening_hour": 10, "closing_hour": 20},
            {"id": "par_07", "name": "Seine River Cruise", "category": "adventure", "lat": 48.8583, "lng": 2.2945, "cost": 18.0, "duration_hours": 1.5, "popularity": 0.91, "description": "Glide past illuminated monuments at golden hour. Bateaux Mouches or Vedettes du Pont Neuf.", "weather_sensitive": True, "opening_hour": 10, "closing_hour": 22},
            {"id": "par_08", "name": "Sainte-Chapelle", "category": "history", "lat": 48.8554, "lng": 2.3451, "cost": 11.5, "duration_hours": 1.0, "popularity": 0.86, "description": "13th-century Gothic chapel with 1,113 stained glass panels — purest medieval light show.", "weather_sensitive": False, "opening_hour": 9, "closing_hour": 17},
            {"id": "par_09", "name": "Rue Cler Market Street", "category": "food", "lat": 48.8558, "lng": 2.3049, "cost": 15.0, "duration_hours": 1.5, "popularity": 0.84, "description": "Pedestrian market street near the Eiffel Tower — fromage, charcuterie, crêpes, macarons.", "weather_sensitive": True, "opening_hour": 8, "closing_hour": 19},
            {"id": "par_10", "name": "Versailles Palace", "category": "history", "lat": 48.8049, "lng": 2.1204, "cost": 21.0, "duration_hours": 4.0, "popularity": 0.94, "description": "Louis XIV's extravagant palace — Hall of Mirrors, Marie Antoinette's estate, formal gardens.", "weather_sensitive": True, "opening_hour": 9, "closing_hour": 18},
            {"id": "par_11", "name": "Shakespeare & Company + Latin Quarter", "category": "culture", "lat": 48.8526, "lng": 2.3471, "cost": 0.0, "duration_hours": 1.5, "popularity": 0.82, "description": "Legendary English bookshop across from Notre-Dame. Browse, read, explore the Latin Quarter.", "weather_sensitive": False, "opening_hour": 10, "closing_hour": 22},
            {"id": "par_12", "name": "Moulin Rouge Show", "category": "nightlife", "lat": 48.8841, "lng": 2.3323, "cost": 100.0, "duration_hours": 2.0, "popularity": 0.87, "description": "Iconic cabaret since 1889 — can-can dancers, champagne, feathers, and spectacle.", "weather_sensitive": False, "opening_hour": 21, "closing_hour": 23},
            {"id": "par_13", "name": "Luxembourg Gardens", "category": "nature", "lat": 48.8462, "lng": 2.3372, "cost": 0.0, "duration_hours": 1.5, "popularity": 0.85, "description": "Elegant 23-hectare garden with Medici fountain, puppet theater, and model boat sailing.", "weather_sensitive": True, "opening_hour": 7, "closing_hour": 21},
            {"id": "par_14", "name": "Catacombs of Paris", "category": "history", "lat": 48.8338, "lng": 2.3324, "cost": 15.0, "duration_hours": 1.5, "popularity": 0.83, "description": "Underground ossuary holding remains of 6 million Parisians beneath Montparnasse.", "weather_sensitive": False, "opening_hour": 10, "closing_hour": 20},
            {"id": "par_15", "name": "Canal Saint-Martin Stroll", "category": "nature", "lat": 48.8714, "lng": 2.3651, "cost": 0.0, "duration_hours": 1.5, "popularity": 0.79, "description": "Iron footbridges, tree-lined canal, where Amélie skipped stones. Bring wine and cheese.", "weather_sensitive": True, "opening_hour": 7, "closing_hour": 22},
            {"id": "par_16", "name": "Le Comptoir Wine Bar", "category": "nightlife", "lat": 48.8512, "lng": 2.3390, "cost": 35.0, "duration_hours": 2.0, "popularity": 0.80, "description": "Natural wine and small plates in Saint-Germain. Authentic Parisian evening culture.", "weather_sensitive": False, "opening_hour": 18, "closing_hour": 23},
        ],
    },
}


def get_city_data(city: str) -> dict:
    """Get city data by key (case-insensitive, stripped)."""
    key = city.lower().strip()
    return CITY_DATA.get(key, CITY_DATA.get("nyc"))


def get_available_cities() -> list:
    """Return list of available city keys."""
    return list(CITY_DATA.keys())
