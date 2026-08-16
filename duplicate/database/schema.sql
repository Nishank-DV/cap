-- Stage 7 MySQL physical schema. Run through database/init_mysql.py.
-- The schema is idempotent and never drops, truncates, or replaces data.

CREATE TABLE IF NOT EXISTS iucr_codes (
    iucr_code CHAR(4) NOT NULL,
    primary_type VARCHAR(64) NOT NULL,
    description VARCHAR(128) NOT NULL,
    index_code CHAR(1) NOT NULL,
    PRIMARY KEY (iucr_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS beat (
    beat_num SMALLINT UNSIGNED NOT NULL,
    district_code TINYINT UNSIGNED NOT NULL,
    sector SMALLINT UNSIGNED NOT NULL,
    beat SMALLINT UNSIGNED NOT NULL,
    PRIMARY KEY (beat_num),
    KEY idx_beat_district_code (district_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS district (
    district_code TINYINT UNSIGNED NOT NULL,
    district_name VARCHAR(100) NOT NULL,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state CHAR(2) NOT NULL,
    zip VARCHAR(10) NOT NULL,
    website VARCHAR(255) NOT NULL,
    phone VARCHAR(32) NOT NULL,
    fax VARCHAR(32) NOT NULL,
    tty VARCHAR(32) NOT NULL,
    x_coordinate DECIMAL(12,2) NOT NULL,
    y_coordinate DECIMAL(12,2) NOT NULL,
    latitude DECIMAL(11,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    location VARCHAR(64) NOT NULL,
    PRIMARY KEY (district_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS community (
    community_code TINYINT UNSIGNED NOT NULL,
    community_name VARCHAR(100) NOT NULL,
    population INT UNSIGNED NOT NULL,
    area_sqmile DECIMAL(8,4) NOT NULL,
    area_sqkm DECIMAL(8,4) NOT NULL,
    density_per_sqmi DECIMAL(12,2) NOT NULL,
    density_per_sqkm DECIMAL(12,2) NOT NULL,
    PRIMARY KEY (community_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ward (
    ward_no TINYINT UNSIGNED NOT NULL,
    alderman VARCHAR(150) NOT NULL,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state CHAR(2) NOT NULL,
    zipcode VARCHAR(10) NOT NULL,
    ward_phone VARCHAR(32) NOT NULL,
    ward_fax VARCHAR(32) NOT NULL,
    email VARCHAR(255) NOT NULL,
    website VARCHAR(255) NOT NULL,
    location VARCHAR(64) NOT NULL,
    city_hall_address VARCHAR(255) NOT NULL,
    city_hall_city VARCHAR(100) NOT NULL,
    city_hall_state CHAR(2) NOT NULL,
    city_hall_zipcode VARCHAR(10) NOT NULL,
    city_hall_phone VARCHAR(32) NOT NULL,
    source_provenance ENUM('MAIN', 'SUPPLEMENTAL') NOT NULL,
    PRIMARY KEY (ward_no),
    KEY idx_ward_source_provenance (source_provenance)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS crime (
    id BIGINT UNSIGNED NOT NULL,
    case_number CHAR(8) NOT NULL,
    date DATETIME NOT NULL,
    block VARCHAR(64) NOT NULL,
    iucr_code CHAR(4) NOT NULL,
    primary_type VARCHAR(64) NOT NULL,
    description VARCHAR(128) NOT NULL,
    location_desc VARCHAR(128) NULL,
    arrest BOOLEAN NOT NULL,
    domestic BOOLEAN NOT NULL,
    beat_num SMALLINT UNSIGNED NOT NULL,
    district_code TINYINT UNSIGNED NOT NULL,
    ward_no TINYINT UNSIGNED NULL,
    community_code TINYINT UNSIGNED NULL,
    fbi_code CHAR(3) NOT NULL,
    x_coordinate INT UNSIGNED NULL,
    y_coordinate INT UNSIGNED NULL,
    year SMALLINT UNSIGNED NOT NULL,
    date_of_update DATETIME NOT NULL,
    latitude DECIMAL(11,8) NULL,
    longitude DECIMAL(11,8) NULL,
    location VARCHAR(64) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_crime_case_number (case_number),
    KEY idx_crime_date (date),
    KEY idx_crime_primary_type (primary_type),
    KEY idx_crime_arrest (arrest),
    KEY idx_crime_iucr_code (iucr_code),
    KEY idx_crime_beat_num (beat_num),
    KEY idx_crime_district_code (district_code),
    KEY idx_crime_ward_no (ward_no),
    KEY idx_crime_community_code (community_code),
    CONSTRAINT fk_crime_iucr_code FOREIGN KEY (iucr_code) REFERENCES iucr_codes (iucr_code),
    CONSTRAINT fk_crime_beat_num FOREIGN KEY (beat_num) REFERENCES beat (beat_num),
    CONSTRAINT fk_crime_district_code FOREIGN KEY (district_code) REFERENCES district (district_code),
    CONSTRAINT fk_crime_ward_no FOREIGN KEY (ward_no) REFERENCES ward (ward_no),
    CONSTRAINT fk_crime_community_code FOREIGN KEY (community_code) REFERENCES community (community_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
