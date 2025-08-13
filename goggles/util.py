# talk to model, get data in JSON form

from .models import Projects, Experiments, Batches, MeasurementTypes, Measurements, GrowthAnalyses, \
    TemperatureMeasurements, Protocol, Medias

from django.core import serializers


import json
from pathlib import Path
from django.conf import settings
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timezone

# Limits for temperature plotting
TEMPERATURE_MIN = 10
TEMPERATURE_MAX = 100

CONFIG_FILE = Path(settings.GOGGLES_MACHINE_CONFIG)


def json_serialize(qs):
    qs_json = serializers.serialize('json', qs)
    return qs_json


def get_ale_machines():
    """Load machine metadata from config file"""
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)  # list of dicts


def get_initial_data():

    """
    Build overview for all machines by reading controller metadata JSON files.
    """
    data = {}
    for machine in get_ale_machines():
        machine_id = machine["id"]
        machine_name = machine["display_name"]
        codename = machine["codename"]
        data_dir = Path(machine["data_dir"])


        try:
            projects = compile_projects_with_experiments(data_dir)
            data[machine_id] = {
                "name": machine_name,
                "codename": codename,
                "id": machine_id,
                "projects": projects,
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            continue
    return data

def compile_projects_with_experiments(machine_dir: Path):
    """
    Parse controller metadata + experiment files from each controller db_id directory.
    For now, project_id == controller db_id.
    """
    projects = {}

    # Loop over every subdirectory in the machine folder
    for controller_dir in sorted(machine_dir.iterdir()):
        if not controller_dir.is_dir():
            continue

        project_id = controller_dir.name  # Use directory name (db_id) as project_id
        meta_file = controller_dir / f"controller_{project_id}_metadata.json"
        if not meta_file.exists():
            # Skip directories without a metadata file
            continue

        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)

        num_exps = len(meta["experiment_db_ids"])
        experiments_list = []

        for idx in range(num_exps):
            exp_dbid = meta["experiment_db_ids"][idx]
            exp_file = controller_dir / f"experiment_{exp_dbid}.json"

            # Basic experiment dict with metadata
            exp_data = {
                "ale_id": meta["experiment_ale_ids"][idx],
                "description": meta["experiment_descriptions"][idx],
                "protocol": meta["experiment_active_protocols"][idx],
                "filter_toggle": None,  # placeholder
                "media": None,  # placeholder
                "unique_str": f"{meta['experiment_descriptions'][idx]},#{exp_dbid}",
                "db_id": exp_dbid,
                "status": meta["experiment_statuses"][idx],
                "num_batches": meta["experiment_number_batches"][idx],
                "measurement_wavelengths": meta["experiment_measurement_wavelengths"][idx],
                "timeseries_file": str(exp_file) if exp_file.exists() else None,
            }

            experiments_list.append(exp_data)

        projects[project_id] = {
            "name": f"Project {project_id}",
            "experiments": experiments_list,
        }

    return projects

def _iso_to_epoch_ms(ts_iso: str) -> int:
    # Convert ISO datetime string to milliseconds since epoch (UTC)
    dt = datetime.fromisoformat(ts_iso)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)
def get_experiment_data(ale_machine: str, experiment_id: int):
    """
    Drop-in JSON replacement for MySQL-based get_experiment_data().
    Matches the original output format:
      - measurement_list: [timestamp_ms, od_value, batch_id, media]
      - growth_rate_list: [timestamp_ms, growth_rate, batch_id, media]
      - temperature_list: [timestamp_ms, temperature, batch_id, media]
    """
    machines = get_ale_machines()
    machine_entry = next((m for m in machines if str(m["id"]) == str(ale_machine)), None)
    if not machine_entry:
        return [[], [], []]

    machine_dir = Path(machine_entry["data_dir"])

    # Locate experiment file
    exp_file = None
    for controller_dir in machine_dir.iterdir():
        if not controller_dir.is_dir():
            continue
        candidate = controller_dir / f"experiment_{experiment_id}.json"
        if candidate.exists():
            exp_file = candidate
            break
    if not exp_file:
        return [[], [], []]

    with open(exp_file, "r", encoding="utf-8") as f:
        exp = json.load(f)

    wl = exp.get("primary_measurement_type") or (exp.get("measurement_types") or [None])[0]

    if not wl:
        return ([], [], [])

    measurement_list: List[List[Any]] = []
    growth_rate_list: List[List[Any]] = []
    temperature_measurements_list: List[List[Any]] = []

    for batch in exp.get("batches", []):
        batch_id = batch.get("batch_id")
        media_desc = (batch.get("media") or {}).get("description", "N/A")

        measurements = (batch.get("measurements") or {}).get(wl)
        if not measurements:
            continue

        times  = measurements.get("times", [])
        ods    = measurements.get("OD", [])
        temps  = measurements.get("temp", [])
        rel_s  = measurements.get("time_since_start", [])

        for t_iso, od, temp_c, _ in zip(times, ods, temps, rel_s):
            ts_ms = _iso_to_epoch_ms(t_iso)
            # OD values
            od_val = max(round(float(od), 3), 0.01)
            measurement_list.append([ts_ms, od_val, batch_id, media_desc])
            # Temperature values (filtered like old version)
            if temp_c is not None and TEMPERATURE_MIN < float(temp_c) < TEMPERATURE_MAX:
                temperature_measurements_list.append([ts_ms, float(temp_c), batch_id, media_desc])

        # Growth rate from 'best_fit' or fallback
        gf = (batch.get("growth_fits") or {}).get(wl, {})
        gr_val = (
            gf.get("gr_bestfit") if gf.get("gr_bestfit") not in (None, -1)
            else gf.get("gr_original") if gf.get("gr_original") not in (None, -1)
            else gf.get("gr_awf") if gf.get("gr_awf") not in (None, -1)
            else gf.get("gr_croissance")
        )
        if gr_val not in (None, -1) and times:
            growth_rate_list.append([_iso_to_epoch_ms(times[-1]), float(gr_val), batch_id, media_desc])

    return [measurement_list, growth_rate_list, temperature_measurements_list]
