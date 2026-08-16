"""Transactional, idempotent loader for the locked Stage 6.5 CSV package."""

from __future__ import annotations

import csv
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Callable, Iterable

from init_mysql import initialize_mysql
from mysql_connection import get_connection


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
DATE_FORMAT = "%m/%d/%Y %H:%M"
LOGGER = logging.getLogger("mysql_loader")


def _configure_logging() -> None:
    """Persist loader failures outside the source-data directory."""
    if LOGGER.handlers:
        return
    OUTPUT_DIR.mkdir(exist_ok=True)
    handler = logging.FileHandler(OUTPUT_DIR / "mysql_load_errors.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)


def _text(value: str) -> str | None:
    return value.strip() if value is not None and value.strip() != "" else None


def _integer(value: str) -> int | None:
    value = _text(value)
    return int(value) if value is not None else None


def _decimal(value: str) -> Decimal | None:
    value = _text(value)
    return Decimal(value) if value is not None else None


def _date(value: str) -> datetime:
    value = _text(value)
    if value is None:
        raise ValueError("required datetime is blank")
    return datetime.strptime(value, DATE_FORMAT)


def _boolean(value: str) -> bool:
    value = _text(value)
    if value not in {"True", "False"}:
        raise ValueError(f"expected True or False, received {value!r}")
    return value == "True"


def _iucr(value: str) -> str:
    value = _text(value)
    if value is None or not value.isdigit() or len(value) > 4:
        raise ValueError(f"invalid IUCR code: {value!r}")
    return value.zfill(4)


def _read_csv(filename: str) -> list[dict[str, str]]:
    with (DATA_DIR / filename).open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def _records(filename: str, transform: Callable[[dict[str, str]], tuple]) -> list[tuple]:
    output: list[tuple] = []
    for number, row in enumerate(_read_csv(filename), start=2):
        try:
            output.append(transform(row))
        except Exception as error:
            raise ValueError(f"{filename} row {number}: {error}") from error
    return output


def _upsert(connection, table: str, columns: list[str], key: str, records: Iterable[tuple]) -> dict[str, int]:
    records = list(records)
    cursor = connection.cursor()
    try:
        cursor.execute(f"SELECT `{key}` FROM `{table}`")
        existing = {row[0] for row in cursor.fetchall()}
        placeholders = ", ".join(["%s"] * len(columns))
        update_columns = [column for column in columns if column != key]
        updates = ", ".join(f"`{column}` = VALUES(`{column}`)" for column in update_columns)
        statement = (
            f"INSERT INTO `{table}` ({', '.join(f'`{column}`' for column in columns)}) "
            f"VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {updates}"
        )
        cursor.executemany(statement, records)
        inserted = sum(1 for record in records if record[0] not in existing)
        return {"inserted": inserted, "updated": len(records) - inserted, "skipped": 0}
    finally:
        cursor.close()


def load_all() -> dict[str, dict[str, int]]:
    """Load all dimensions then crimes in one transaction; rollback entirely on failure."""
    _configure_logging()
    initialize_mysql()
    connection = get_connection()
    try:
        iucr = _records("iucr_codes.csv", lambda r: (_iucr(r["IUCR_CODE"]), _text(r["PRIMARY_TYPE"]), _text(r["DESCRIPTION"]), _text(r["INDEX_CODE"])))
        beats = _records("chicago_police_beat_info.csv", lambda r: (_integer(r["BEAT_NUM"]), _integer(r["DISTRICT"]), _integer(r["SECTOR"]), _integer(r["BEAT"])))
        districts = _records("chicago_district_ps_info.csv", lambda r: (_integer(r["DISTRICT_CODE"]), _text(r["DISTRICT_NAME"]), _text(r["ADDRESS"]), _text(r["CITY"]), _text(r["STATE"]), _text(r["ZIP"]), _text(r["WEBSITE"]), _text(r["PHONE"]), _text(r["FAX"]), _text(r["TTY"]), _decimal(r["X_COORDINATE"]), _decimal(r["Y_COORDINATE"]), _decimal(r["LATITUDE"]), _decimal(r["LONGITUDE"]), _text(r["LOCATION"])))
        communities = _records("chicago_city_community.csv", lambda r: (_integer(r["community_code"]), _text(r["community_name"]), _integer(r["population"]), _decimal(r["area_sqmile"]), _decimal(r["area_sqkm"]), _decimal(r["density_per_sqmi"]), _decimal(r["density_per_sqkm"])))

        ward_columns = ["ward_no", "alderman", "address", "city", "state", "zipcode", "ward_phone", "ward_fax", "email", "website", "location", "city_hall_address", "city_hall_city", "city_hall_state", "city_hall_zipcode", "city_hall_phone", "source_provenance"]
        def ward_transform(source: str):
            return lambda r: (_integer(r["WARD_NO"]), _text(r["ALDERMAN"]), _text(r["ADDRESS"]), _text(r["CITY"]), _text(r["STATE"]), _text(r["ZIPCODE"]), _text(r["WARD_PHONE"]), _text(r["WARD_FAX"]), _text(r["EMAIL"]), _text(r["WEBSITE"]), _text(r["LOCATION"]), _text(r["CITY_HALL_ADDRESS"]), _text(r["CITY_HALL_CITY"]), _text(r["CITY_HALL_STATE"]), _text(r["CITY_HALL_ZIPCODE"]), _text(r["CITY_HALL_PHONE"]), source)
        wards = _records("chicago_ward_offices.csv", ward_transform("MAIN")) + _records("chicago_ward_offices_dummy.csv", ward_transform("SUPPLEMENTAL"))
        ward_keys = [record[0] for record in wards]
        if len(ward_keys) != len(set(ward_keys)):
            raise ValueError("ward source files contain duplicate ward numbers; refusing ambiguous load")

        crimes = _records("chicago_crime_dataset.csv", lambda r: (_integer(r["id"]), _text(r["case_number"]), _date(r["date"]), _text(r["block"]), _iucr(r["iucr_code"]), _text(r["primary_type"]), _text(r["description"]), _text(r["location_desc"]), _boolean(r["arrest"]), _boolean(r["domestic"]), _integer(r["beat_num"]), _integer(r["district_code"]), _integer(r["ward_no"]), _integer(r["community_code"]), _text(r["fbi_code"]), _integer(r["x_coordinate"]), _integer(r["y_coordinate"]), _integer(r["year"]), _date(r["date_of_update"]), _decimal(r["latitude"]), _decimal(r["longitude"]), _text(r["location"])))

        result = {
            "iucr_codes": _upsert(connection, "iucr_codes", ["iucr_code", "primary_type", "description", "index_code"], "iucr_code", iucr),
            "beat": _upsert(connection, "beat", ["beat_num", "district_code", "sector", "beat"], "beat_num", beats),
            "district": _upsert(connection, "district", ["district_code", "district_name", "address", "city", "state", "zip", "website", "phone", "fax", "tty", "x_coordinate", "y_coordinate", "latitude", "longitude", "location"], "district_code", districts),
            "community": _upsert(connection, "community", ["community_code", "community_name", "population", "area_sqmile", "area_sqkm", "density_per_sqmi", "density_per_sqkm"], "community_code", communities),
            "ward": _upsert(connection, "ward", ward_columns, "ward_no", wards),
            "crime": _upsert(connection, "crime", ["id", "case_number", "date", "block", "iucr_code", "primary_type", "description", "location_desc", "arrest", "domestic", "beat_num", "district_code", "ward_no", "community_code", "fbi_code", "x_coordinate", "y_coordinate", "year", "date_of_update", "latitude", "longitude", "location"], "id", crimes),
        }
        connection.commit()
        return result
    except Exception:
        connection.rollback()
        LOGGER.exception("MySQL load failed; transaction rolled back and no records were skipped silently.")
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    import json
    print(json.dumps(load_all(), indent=2))
