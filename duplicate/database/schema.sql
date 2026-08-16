-- SQLite schema. Safe to execute repeatedly; it never deletes or replaces data.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS iucr_codes (
    iucr_code TEXT PRIMARY KEY CHECK(length(iucr_code) = 4), primary_type TEXT NOT NULL,
    description TEXT NOT NULL, index_code TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS beat (beat_num INTEGER PRIMARY KEY, district_code INTEGER NOT NULL,
sector INTEGER NOT NULL, beat INTEGER NOT NULL, FOREIGN KEY(district_code) REFERENCES district(district_code));

CREATE TABLE IF NOT EXISTS district (district_code INTEGER PRIMARY KEY, district_name TEXT NOT NULL, address TEXT NOT NULL, city TEXT NOT NULL, state TEXT NOT NULL, zip TEXT NOT NULL, website TEXT NOT NULL, phone TEXT NOT NULL, fax TEXT NOT NULL, tty TEXT NOT NULL, x_coordinate REAL NOT NULL, y_coordinate REAL NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL, location TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS community (community_code INTEGER PRIMARY KEY, community_name TEXT NOT NULL, population INTEGER NOT NULL, area_sqmile REAL NOT NULL, area_sqkm REAL NOT NULL, density_per_sqmi REAL NOT NULL, density_per_sqkm REAL NOT NULL);

CREATE TABLE IF NOT EXISTS ward (ward_no INTEGER PRIMARY KEY, alderman TEXT NOT NULL, address TEXT NOT NULL, city TEXT NOT NULL, state TEXT NOT NULL, zipcode TEXT NOT NULL, ward_phone TEXT NOT NULL, ward_fax TEXT NOT NULL, email TEXT NOT NULL, website TEXT NOT NULL, location TEXT NOT NULL, city_hall_address TEXT NOT NULL, city_hall_city TEXT NOT NULL, city_hall_state TEXT NOT NULL, city_hall_zipcode TEXT NOT NULL, city_hall_phone TEXT NOT NULL, source_provenance TEXT NOT NULL CHECK(source_provenance IN ('MAIN','SUPPLEMENTAL')));

CREATE TABLE IF NOT EXISTS crime (id INTEGER PRIMARY KEY, case_number TEXT NOT NULL UNIQUE, date TEXT NOT NULL, block TEXT NOT NULL, iucr_code TEXT NOT NULL, primary_type TEXT NOT NULL, description TEXT NOT NULL, location_desc TEXT, arrest INTEGER NOT NULL CHECK(arrest IN (0,1)), domestic INTEGER NOT NULL CHECK(domestic IN (0,1)), beat_num INTEGER NOT NULL, district_code INTEGER NOT NULL, ward_no INTEGER, community_code INTEGER, fbi_code TEXT NOT NULL, x_coordinate REAL, y_coordinate REAL, year INTEGER NOT NULL, date_of_update TEXT NOT NULL, latitude REAL, longitude REAL, location TEXT, FOREIGN KEY(iucr_code) REFERENCES iucr_codes(iucr_code), FOREIGN KEY(beat_num) REFERENCES beat(beat_num), FOREIGN KEY(district_code) REFERENCES district(district_code), FOREIGN KEY(ward_no) REFERENCES ward(ward_no), FOREIGN KEY(community_code) REFERENCES community(community_code));
CREATE INDEX IF NOT EXISTS idx_crime_date ON crime(date);
CREATE INDEX IF NOT EXISTS idx_crime_primary_type ON crime(primary_type);
