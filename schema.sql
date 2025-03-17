DROP TABLE IF EXISTS login_accounts;

CREATE TABLE login_accounts
(
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    account_type NOT NULL,
    account_status TEXT
);

INSERT INTO login_accounts
VALUES 
    ("admin","12341","ADMIN",NULL)
;

DROP TABLE IF EXISTS services;

CREATE TABLE services
(
    service_code INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL,
    description TEXT NOT NULL,
    seller_code TEXT REFERENCES seller_details(seller_code),
    promo_code TEXT,
    promo_discount DECIMAL DEFAULT 0.15,
    max_booking_hrs INTEGER DEFAULT 2,
    price_per_hour DECIMAL NOT NULL
);

INSERT INTO services
VALUES 
    (1,"Yarn Winding","I will untangle and/or re-wind your yarn for crochet or knit projects. I have six years of professional experience as a knitter and four as a detangler.Can work with any type of yarn.",1,NULL,0.15,4,12.50),
    (2,"Bottle Emptier","Have loads of almost empty bottles of condiments that you always seem to waste? I will empty all you bottles using industry-level employing tools (no mess!).Cleaning and recycling is extra. Terms and conditions apply.",2,NULL,0.15,3,16.00),
    (3,"Budget Personal Chef","I am an amateur cook with decades of experience preparing meals for a family of 5. I will prepare meals using only what is in your refrigerator and pantry. I can also provide meal planning services at an extra cost.",3,NULL,0.15,6,17.45)
;
DROP TABLE IF EXISTS seller_details;

CREATE TABLE seller_details
(
    seller_code TEXT PRIMARY KEY,
    seller_name TEXT NOT NULL,
    phone_number TEXT NOT NULL CHECK(LENGTH(phone_number) = 10)
);

INSERT INTO seller_details
VALUES 
    (1,"Donna Stringer","0823732835"),
    (2,"Sam Ketchupe","0834563483"),
    (3,"Momma Sue","0813464993")    
;

DROP TABLE IF EXISTS booking_details;

CREATE TABLE booking_details
(
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_code INTEGER REFERENCES services(service_code),
    customer_username TEXT NOT NULL,
    address TEXT NOT NULL,
    seller_code TEXT REFERENCES seller_details(seller_code),
    date DATE NOT NULL,
    from_when TIME NOT NULL,
    till_when TIME NOT NULL,
    price DECIMAL NOT NULL
);

-- INSERT INTO booking_details
-- VALUES ();

DROP TABLE IF EXISTS cancelled_bookings;

CREATE TABLE cancelled_bookings
(
    booking_id INTEGER NOT NULL,
    cancelled_by_whom TEXT NOT NULL,
    reason TEXT NOT NULL
);

-- INSERT INTO cancelled_bookings
-- VALUES ();

DROP TABLE IF EXISTS messages_table;

CREATE TABLE messages_table
(
    message_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    message TEXT NOT NULL,
    sent_to TEXT NOT NULL,
    sent_from TEXT NOT NULL,
    viewed TEXT DEFAULT "no"
);

-- INSERT INTO messages_table
-- VALUES ();

DROP TABLE IF EXISTS seller_availability;

CREATE TABLE seller_availability
(
    seller_code TEXT NOT NULL,
    date DATE NOT NULL,
    from_when TIME NOT NULL,
    till_when TIME NOT NULL
);

-- INSERT INTO seller_availability
-- VALUES ();

DROP TABLE IF EXISTS reviews_table;

CREATE TABLE reviews_table
(
    review_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    review TEXT NOT NULL,
    rating INTEGER NOT NULL,
    customer_username TEXT NOT NULL,
    seller_username TEXT NOT NULL,
    date DATE NOT NULL
);

-- INSERT INTO reviews_table
-- VALUES ();

DROP TABLE IF EXISTS reports_table;

CREATE TABLE reports_table
(
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    reported_service_code INTEGER,
    report_reason TEXT NOT NULL,
    reported_by TEXT NOT NULL,
    got_reported TEXT NOT NULL,
    date DATE NOT NULL
);

-- INSERT INTO reports_table
-- VALUES ();

DROP TABLE IF EXISTS monthly_subscription;

-- should ii just do month with a check(in [1,2,3...,12]) instead of date?
CREATE TABLE monthly_subscription
(
    seller_username TEXT NOT NULL,
    date DATE NOT NULL,     
    PRIMARY KEY (seller_username,date)
);

SELECT round((julianday("2000-10-0210:00:00") - julianday("2000-10-0109:00:00"))*24);