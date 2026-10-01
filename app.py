from __future__ import annotations

import os
import re
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DIST_DIR = BASE_DIR / "dist"
DB_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "bookings.db")))
LOCK = threading.Lock()

BOOKING_FIELDS = (
    "booking_id",
    "name",
    "designation",
    "department",
    "lab",
    "component",
    "from_datetime",
    "to_datetime",
    "booked_at",
)

DESIGNATIONS = [
    "Student",
    "Faculty",
    "Research Scholar",
    "Lab In-charge",
    "Head of Department",
    "External Researcher",
]

DEPARTMENTS = [
    "Computer Science and Engineering",
    "Artificial Intelligence and Data Science",
    "Information Technology",
    "Electronics and Communication Engineering",
    "Electrical and Electronics Engineering",
    "Mechanical Engineering",
    "Civil Engineering",
    "Computer Science and Business Systems",
    "Electronics and Instrumentation Engineering",
]

LAB_CATALOG = {
    "Advanced Computing & AI Lab": [
        "GPU Workstation — NVIDIA A100",
        "High-Performance Compute Node",
        "Deep Learning Training Server",
        "Data Annotation Workstation",
    ],
    "IoT & Embedded Systems Lab": [
        "IoT Gateway Test Bench",
        "ARM Cortex Development Kit",
        "Sensor Fusion Rig",
        "PCB Prototyping Station",
    ],
    "VLSI & Electronics Lab": [
        "FPGA Development Board",
        "Mixed-Signal Oscilloscope",
        "Logic Analyzer",
        "Spectrum Analyzer",
    ],
    "Materials Characterization Lab": [
        "Universal Testing Machine",
        "Optical Microscope",
        "Hardness Tester",
        "Thermal Analysis Station",
    ],
    "CAD / CAM & Prototyping Lab": [
        "3D Printer — FDM",
        "CNC Milling Station",
        "CAD Workstation",
        "Coordinate Measuring Arm",
    ],
    "Renewable Energy Lab": [
        "Solar PV Test Bench",
        "Wind Energy Trainer",
        "Power Quality Analyzer",
        "Battery Characterization Unit",
    ],
    "Communication & Signal Processing Lab": [
        "Software-Defined Radio Kit",
        "Vector Network Analyzer",
        "DSP Development Board",
        "Antenna Measurement Setup",
    ],
}

NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,78}$")

app = Flask(__name__, static_folder=None)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")
CORS(app, resources={r"/api/*": {"origins": "*"}})


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                designation TEXT NOT NULL,
                department TEXT NOT NULL,
                lab TEXT NOT NULL,
                component TEXT NOT NULL,
                from_datetime TEXT NOT NULL,
                to_datetime TEXT NOT NULL,
                booked_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_bookings_lab_component
            ON bookings (lab, component, from_datetime, to_datetime)
            """
        )
        conn.commit()


def row_to_dict(row: sqlite3.Row) -> dict[str, str]:
    return {field: str(row[field]) for field in BOOKING_FIELDS}


def read_bookings() -> list[dict[str, str]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT booking_id, name, designation, department, lab, component,
                   from_datetime, to_datetime, booked_at
            FROM bookings
            ORDER BY from_datetime DESC
            """
        ).fetchall()
    return [row_to_dict(row) for row in rows]


def write_booking(row: dict[str, str]) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO bookings (
                booking_id, name, designation, department, lab, component,
                from_datetime, to_datetime, booked_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(row[field] for field in BOOKING_FIELDS),
        )
        conn.commit()


def parse_slot(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def format_slot(value: str) -> str:
    parsed = parse_slot(value)
    if not parsed:
        return value
    return parsed.strftime("%d %b %Y, %I:%M %p")


def slots_overlap(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    return start_a < end_b and start_b < end_a


def find_conflict(lab: str, component: str, start: datetime, end: datetime) -> dict[str, str] | None:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT booking_id, name, designation, department, lab, component,
                   from_datetime, to_datetime, booked_at
            FROM bookings
            WHERE lab = ? AND component = ?
            """,
            (lab, component),
        ).fetchall()

    for row in rows:
        existing = row_to_dict(row)
        existing_start = parse_slot(existing["from_datetime"])
        existing_end = parse_slot(existing["to_datetime"])
        if existing_start and existing_end and slots_overlap(start, end, existing_start, existing_end):
            return existing
    return None


def new_booking_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d")
    suffix = uuid4().hex[:4].upper()
    return f"RD-{stamp}-{suffix}"


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok"})


@app.route("/api/bookings", methods=["GET"])
def api_get_bookings():
    return jsonify(read_bookings())


@app.route("/api/bookings", methods=["POST"])
def api_create_booking():
    data = request.get_json(silent=True) or {}

    values = {
        "name": (data.get("name") or "").strip(),
        "designation": (data.get("designation") or "").strip(),
        "department": (data.get("department") or "").strip(),
        "lab": (data.get("lab") or "").strip(),
        "component": (data.get("component") or "").strip(),
        "from_datetime": (data.get("from_datetime") or "").strip(),
        "to_datetime": (data.get("to_datetime") or "").strip(),
    }

    errors = []
    if not NAME_PATTERN.match(values["name"]):
        errors.append("Enter a valid name using letters only.")
    if values["designation"] not in DESIGNATIONS:
        errors.append("Select a designation from the list.")
    if values["department"] not in DEPARTMENTS:
        errors.append("Select a department from the list.")
    if values["lab"] not in LAB_CATALOG:
        errors.append("Select a research lab from the list.")
    elif values["component"] not in LAB_CATALOG[values["lab"]]:
        errors.append("Select a component that belongs to the chosen lab.")

    start = parse_slot(values["from_datetime"])
    end = parse_slot(values["to_datetime"])
    if not start or not end:
        errors.append("Choose both a From and To date & time.")
    elif end <= start:
        errors.append("The To time must be later than the From time.")
    elif (end - start).total_seconds() > 8 * 60 * 60:
        errors.append("A single booking cannot exceed 8 hours.")

    if start and end and not errors:
        conflict = find_conflict(values["lab"], values["component"], start, end)
        if conflict:
            errors.append(
                f"{values['component']} in {values['lab']} is already booked "
                f"from {format_slot(conflict['from_datetime'])} to "
                f"{format_slot(conflict['to_datetime'])}."
            )

    if errors:
        return jsonify({"errors": errors}), 400

    booking = {
        **values,
        "booking_id": new_booking_id(),
        "booked_at": datetime.now().isoformat(timespec="minutes"),
    }

    with LOCK:
        write_booking(booking)

    return jsonify(booking), 201


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def spa(path: str):
    if path.startswith("api/"):
        return jsonify({"error": "Not found"}), 404

    if DIST_DIR.exists():
        candidate = DIST_DIR / path
        if path and candidate.is_file():
            return send_from_directory(DIST_DIR, path)
        return send_from_directory(DIST_DIR, "index.html")

    return (
        jsonify(
            {
                "message": "Frontend build not found. Run npm run build, or use Vite for local UI.",
                "api": "/api/bookings",
            }
        ),
        200,
    )


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
