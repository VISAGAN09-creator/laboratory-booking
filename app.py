from __future__ import annotations

import csv
import os
import re
import threading
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

CSV_PATH = BASE_DIR / "data" / "bookings.csv"
LOCK = threading.Lock()

CSV_FIELDS = [
    "booking_id",
    "name",
    "designation",
    "department",
    "lab",
    "component",
    "from_datetime",
    "to_datetime",
    "booked_at",
]

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

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")
CORS(app)


def ensure_csv() -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists() or CSV_PATH.stat().st_size == 0:
        with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
            csv.DictWriter(handle, fieldnames=CSV_FIELDS).writeheader()


def read_bookings() -> list[dict[str, str]]:
    ensure_csv()
    with CSV_PATH.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows.sort(key=lambda row: row.get("from_datetime", ""), reverse=True)
    return rows


def write_booking(row: dict[str, str]) -> None:
    ensure_csv()
    with CSV_PATH.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writerow(row)


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
    for row in read_bookings():
        if row.get("lab") != lab or row.get("component") != component:
            continue
        existing_start = parse_slot(row.get("from_datetime", ""))
        existing_end = parse_slot(row.get("to_datetime", ""))
        if existing_start and existing_end and slots_overlap(start, end, existing_start, existing_end):
            return row
    return None


def new_booking_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d")
    suffix = uuid4().hex[:4].upper()
    return f"RD-{stamp}-{suffix}"


# ─── JSON API ────────────────────────────────────────────────────────────────

@app.route("/api/bookings", methods=["GET"])
def api_get_bookings():
    return jsonify(read_bookings())


@app.route("/api/bookings", methods=["POST"])
def api_create_booking():
    data = request.get_json(force=True)

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


# ─── HTML routes (kept for legacy/template usage) ────────────────────────────

def form_context(values: dict[str, str] | None = None) -> dict:
    return {
        "designations": DESIGNATIONS,
        "departments": DEPARTMENTS,
        "catalog": LAB_CATALOG,
        "values": values or {},
    }


@app.context_processor
def inject_helpers() -> dict:
    return {"format_slot": format_slot}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/book-now", methods=["GET", "POST"])
def book_now():
    if request.method == "GET":
        return render_template("book.html", **form_context())

    values = {
        "name": request.form.get("name", "").strip(),
        "designation": request.form.get("designation", "").strip(),
        "department": request.form.get("department", "").strip(),
        "lab": request.form.get("lab", "").strip(),
        "component": request.form.get("component", "").strip(),
        "from_datetime": request.form.get("from_datetime", "").strip(),
        "to_datetime": request.form.get("to_datetime", "").strip(),
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
        for message in errors:
            flash(message, "error")
        return render_template("book.html", **form_context(values)), 400

    booking = {
        **values,
        "booking_id": new_booking_id(),
        "booked_at": datetime.now().isoformat(timespec="minutes"),
    }

    with LOCK:
        write_booking(booking)

    flash(f"Slot reserved. Booking ID {booking['booking_id']}.", "success")
    return redirect(url_for("booked_details"))


@app.route("/booked-details")
def booked_details():
    return render_template("bookings.html", bookings=read_bookings())


if __name__ == "__main__":
    ensure_csv()
    app.run(debug=True)
