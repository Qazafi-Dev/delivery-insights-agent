import random
import sqlite3
from datetime import datetime, timedelta

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
DRIVERS = [
    ("Ali", "bike"),
    ("Sara", "car"),
    ("John", "scooter"),
    ("Emma", "bike"),
    ("Omar", "car"),
    ("Lucy", "scooter"),
]


def main() -> None:
    random.seed(42)
    con = sqlite3.connect("delivery.db")
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
        order_value REAL,
        delivery_fee REAL,
        tip REAL,
        delivery_minutes INTEGER,
        status TEXT
    );
    """)
    con.executemany(
        "INSERT INTO restaurants (name, cuisine, city) VALUES (?,?,?)", RESTAURANTS
    )
    con.executemany("INSERT INTO drivers (name, vehicle) VALUES (?,?)", DRIVERS)

    now = datetime.now()
    for _ in range(600):
        when = now - timedelta(days=random.randint(0, 60), hours=random.randint(0, 12))
        cancelled = random.random() < 0.07
        con.execute(
            "INSERT INTO orders (restaurant_id, driver_id, order_time, order_value, "
            "delivery_fee, tip, delivery_minutes, status) VALUES (?,?,?,?,?,?,?,?)",
            (
                random.randint(1, len(RESTAURANTS)),
                random.randint(1, len(DRIVERS)),
                when.strftime("%Y-%m-%d %H:%M"),
                round(random.uniform(8, 60), 2),
                random.choice([1.99, 2.49, 2.99, 3.49]),
                0 if cancelled else random.choice([0, 0, 1, 2, 3, 5]),
                random.randint(12, 55),
                "cancelled" if cancelled else "delivered",
            ),
        )
    con.commit()
    con.close()
    print("delivery.db created")


if __name__ == "__main__":
    main()
