import random  # makes random numbers and random choices
import sqlite3  # built-in Python tool for SQLite databases
from datetime import datetime, timedelta  # for dates and time differences

# --- The facts of our made-up delivery world ---

# Each restaurant is (name, cuisine, city)
RESTAURANTS = [
    ("Spice Route", "Indian", "Middlesbrough"),
    ("Tandoori Nights", "Indian", "Leeds"),
    ("Burger Yard", "Burgers", "Middlesbrough"),
    ("Green Bowl", "Healthy", "Manchester"),
    ("Dragon Wok", "Chinese", "Leeds"),
    ("Pizza Forno", "Italian", "Manchester"),
    ("Kebab Corner", "Turkish", "Middlesbrough"),
    ("Sushi Lane", "Japanese", "London"),
]

# Each driver is (name, vehicle)
DRIVERS = [
    ("Ali", "bike"),
    ("Sara", "car"),
    ("John", "scooter"),
    ("Emma", "bike"),
    ("Omar", "car"),
    ("Lucy", "scooter"),
]

# --- The rules that decide how long a delivery takes ---
MINUTES_PER_KM = {
    "bike": 4.5,
    "scooter": 3.2,
    "car": 3.8,
}  # slower vehicle = more minutes per km
CITY_DELAY = {
    "London": 6,
    "Manchester": 3,
    "Leeds": 2,
    "Middlesbrough": 0,
}  # extra minutes per city
HOURS = list(range(11, 23))  # orders happen between 11:00 and 22:59
HOUR_WEIGHTS = [
    2,
    5,
    5,
    2,
    1,
    1,
    2,
    5,
    6,
    5,
    3,
    1,
]  # how likely each hour is (lunch and dinner peaks)
RUSH_HOURS = {12, 13, 18, 19, 20}  # busy hours that slow deliveries down
ORDER_COUNT = 3000  # how many orders to generate


def main() -> None:
    random.seed(42)  # fixes the "random" numbers so every run gives the same data
    con = sqlite3.connect("delivery.db")  # opens (or creates) the database file

    # Delete old tables if they exist, then create fresh empty ones.
    # A table is like a spreadsheet: columns are fields, rows are records.
    con.executescript("""
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS drivers;
    DROP TABLE IF EXISTS restaurants;
    CREATE TABLE restaurants (id INTEGER PRIMARY KEY, name TEXT, cuisine TEXT, city TEXT);
    CREATE TABLE drivers (id INTEGER PRIMARY KEY, name TEXT, vehicle TEXT);
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        restaurant_id INTEGER,
        driver_id INTEGER,
        order_time TEXT,
        distance_km REAL,
        order_value REAL,
        delivery_fee REAL,
        tip REAL,
        delivery_minutes INTEGER,
        status TEXT
    );
    """)

    # Insert all restaurants and drivers. The ? marks are placeholders that get
    # filled from the lists, which is the safe way to put values into SQL.
    con.executemany(
        "INSERT INTO restaurants (name, cuisine, city) VALUES (?,?,?)", RESTAURANTS
    )
    con.executemany("INSERT INTO drivers (name, vehicle) VALUES (?,?)", DRIVERS)

    # Midnight today. We count backwards from here to spread orders over 60 days.
    day_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    for _ in range(ORDER_COUNT):  # repeat 3000 times: one order per loop
        # Pick a random restaurant and driver (ids start at 1)
        restaurant_id = random.randint(1, len(RESTAURANTS))
        driver_id = random.randint(1, len(DRIVERS))
        city = RESTAURANTS[restaurant_id - 1][2]  # look up that restaurant's city
        vehicle = DRIVERS[driver_id - 1][1]  # look up that driver's vehicle

        # Pick an hour, with lunch and dinner more likely, then build the order time
        hour = random.choices(HOURS, weights=HOUR_WEIGHTS)[0]
        when = (
            day_start
            - timedelta(days=random.randint(0, 60))
            + timedelta(hours=hour, minutes=random.randint(0, 59))
        )
        distance = round(random.uniform(0.5, 9.0), 1)  # distance in km
        value = round(random.uniform(8, 60), 2)  # basket value in pounds

        # The delivery-time rule: base time + travel time + city delay
        # + rush-hour penalty + a little random noise (gauss = bell-curve randomness)
        minutes = (
            8
            + distance * MINUTES_PER_KM[vehicle]
            + CITY_DELAY[city]
            + (random.uniform(4, 10) if hour in RUSH_HOURS else 0)
            + random.gauss(0, 3)
        )
        minutes = max(8, round(minutes))  # whole minutes, never below 8

        # Long deliveries are cancelled more often: 3% base chance,
        # plus 0.4% for every minute over 35
        cancelled = random.random() < 0.03 + 0.004 * max(0, minutes - 35)

        # Tips: none if cancelled, better for fast deliveries, worse for slow ones
        if cancelled:
            tip = 0
        elif minutes < 30:
            tip = random.choice([0, 1, 2, 3, 5])
        else:
            tip = random.choice([0, 0, 0, 1, 2])

        # Save this order as one row in the orders table
        con.execute(
            "INSERT INTO orders (restaurant_id, driver_id, order_time, distance_km, "
            "order_value, delivery_fee, tip, delivery_minutes, status) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                restaurant_id,
                driver_id,
                when.strftime(
                    "%Y-%m-%d %H:%M"
                ),  # turn the date into text like 2026-10-07 18:30
                distance,
                value,
                random.choice([1.99, 2.49, 2.99, 3.49]),  # delivery fee
                tip,
                minutes,
                "cancelled" if cancelled else "delivered",
            ),
        )

    con.commit()  # save all changes to the file (without this they'd be lost)
    con.close()  # close the database
    print("delivery.db created")


if __name__ == "__main__":  # run main() only when this file is started directly
    main()
