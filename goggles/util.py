# talk to model, get data in JSON form

from .models import Projects, Experiments, Batches, MeasurementTypes, Measurements, GrowthAnalyses, \
    TemperatureMeasurements, Protocol, Medias

from django.core import serializers


import json
from pathlib import Path
from django.conf import settings
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timezone
import logging
import time
# Limits for temperature plotting
TEMPERATURE_MIN = 10
TEMPERATURE_MAX = 100

# Map UI keys → curveball model strings found in JSON
CURVEBALL_MAP = {
    "gr_curveball_BaranyiRoberts": "Model(BaranyiRoberts)",
    "gr_curveball_Logistic": "Model(Logistic)",
    "gr_curveball_LogisticLag1": "Model(LogisticLag1)",
    "gr_curveball_LogisticLag2": "Model(LogisticLag2)",
    "gr_curveball_Richards": "Model(Richards)",
    "gr_curveball_RichardsLag1": "Model(RichardsLag1)",
}

logger = logging.getLogger(__name__)

CONFIG_FILE = Path(settings.GOGGLES_MACHINE_CONFIG)


def json_serialize(qs):
    qs_json = serializers.serialize('json', qs)
    return qs_json


def get_ale_machines():
    """Load machine metadata from config file"""
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)  # list of dicts

def _select_gr_value(gf: dict, gr_type: Optional[str]) -> Optional[float]:
    """Return the requested growth-rate value from a growth_fits dict.
    Accept 0.0 as valid; only None/-1 are considered missing.
    """
    def valid(v) -> bool:
        return v is not None and v != -1

    # No explicit model requested → keep current fallback order
    if not gr_type:
        for key in ("gr_bestfit", "gr_original", "gr_awf", "gr_croissance"):
            v = gf.get(key)
            if valid(v):
                return float(v)
        return None  # (no curveball fallback in legacy behavior)

    # Curveball variants
    if gr_type.startswith("gr_curveball_"):
        target = CURVEBALL_MAP.get(gr_type)
        if not target:
            return None
        cb = gf.get("gr_curveball") or []
        for item in cb:
            if isinstance(item, dict) and item.get("model") == target:
                v = item.get("growth_rate")
                if valid(v):
                    return float(v)
        return None

    # Plain keys
    v = gf.get(gr_type)
    return float(v) if valid(v) else None
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
            exp_data_new = {
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

            exp_legacy = (
                meta["experiment_ale_ids"][idx],                  # 1: ALE ID
                meta["experiment_descriptions"][idx],             # 2: Description
                meta["experiment_active_protocols"][idx],         # 3: Protocol
                None,                                              # 4: placeholder
                None,                                              # 5: placeholder
                f"{meta['experiment_descriptions'][idx]},#{exp_dbid}",  # 6: Unique string
                exp_dbid                                           # 7: DB ID
            )
            experiments_list.append(exp_legacy)

        projects[project_id] = {
            "name": f"Controller {project_id}",
            "experiments": experiments_list,
        }

    return projects
def _norm_wl(wl: Optional[str]) -> Optional[str]:
    return wl.strip().lower() if isinstance(wl, str) else None

def _resolve_wl_key(container: dict, wl: str) -> Optional[str]:
    """Find the exact dict key for a wavelength, case-insensitive."""
    if wl in container:
        return wl
    lw = wl.lower()
    for k in container.keys():
        if str(k).lower() == lw:
            return k
    return None

def _default_wl(exp: dict) -> Optional[str]:
    """Prefer 620A; else primary; else first measurement_types."""
    mts = [str(x).lower() for x in (exp.get("measurement_types") or [])]
    if "620a" in mts:
        return "620a"
    pm = _norm_wl(exp.get("primary_measurement_type"))
    if pm:
        return pm
    return mts[0] if mts else None

def _iso_to_epoch_ms(ts_iso: str) -> int:
    # Convert ISO datetime string to milliseconds since epoch (UTC)
    dt = datetime.fromisoformat(ts_iso)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)
def get_experiment_data(ale_machine: str,experiment_id: int,gr_type: Optional[str] = None,wavelength: Optional[str] = None):
    start_time = time.time()
    logger.info(f"get_experiment_data() called for machine={ale_machine}, experiment_id={experiment_id}")

    machines = get_ale_machines()
    machine_entry = next((m for m in machines if str(m["id"]) == str(ale_machine)), None)
    if not machine_entry:
        logger.warning(f"No machine found with id={ale_machine}")
        return [[], [], [], {"last_modified": None}]

    machine_dir = Path(machine_entry["data_dir"])
    logger.debug(f"Machine directory resolved to {machine_dir}")

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
        logger.warning(f"Experiment file not found for experiment_id={experiment_id}")
        return [[], [], [], {"last_modified": None}]

    logger.info(f"Found experiment file: {exp_file}")

    with open(exp_file, "r", encoding="utf-8") as f:
        exp = json.load(f)
    logger.debug("Experiment JSON loaded successfully")

    requested_wl = _norm_wl(wavelength)
    wl = requested_wl or _default_wl(exp)
    logger.debug(f"Selected wavelength (requested={requested_wl}) -> wl={wl}")

    if not wl:
        logger.warning(f"No wavelength found for experiment_id={experiment_id}")
        return [[], [], [], {
            "last_modified": exp.get("last_updated"),
            "selected_wavelength": None,
            "available_wavelengths": exp.get("measurement_types") or []
        }]

    measurement_list: List[List[Any]] = []
    growth_rate_list: List[List[Any]] = []
    temperature_measurements_list: List[List[Any]] = []

    last_modified = exp.get("last_updated")

    batch_count = 0
    for batch in exp.get("batches", []):
        batch_count += 1
        batch_id = batch.get("batch_id")
        media_desc = (batch.get("media") or {}).get("description", "N/A")
        meas_all = (batch.get("measurements") or {})
        wl_key_meas = _resolve_wl_key(meas_all, wl)
        measurements = meas_all.get(wl_key_meas) if wl_key_meas else None
        has_cryo = batch.get("cryostock")
        has_cryo = bool(has_cryo) if has_cryo is not None else False

        if not measurements:
            logger.debug(f"Batch {batch_id}: No measurements found for wl={wl}")
            continue

        times  = measurements.get("times", [])
        ods    = measurements.get("OD", [])
        temps  = measurements.get("temp", [])
        rel_s  = measurements.get("time_since_start", [])

        logger.debug(f"Batch {batch_id}: {len(times)} timepoints, {len(ods)} OD values, {len(temps)} temps")

        for t_iso, od, temp_c, _ in zip(times, ods, temps, rel_s):
            ts_ms = _iso_to_epoch_ms(t_iso)
            # OD values
            od_val = max(round(float(od), 3), 0.01)
            measurement_list.append([ts_ms, od_val, batch_id, media_desc,has_cryo])
            # Temperature values
            if temp_c is not None and TEMPERATURE_MIN < float(temp_c) < TEMPERATURE_MAX:
                temperature_measurements_list.append([ts_ms, float(temp_c), batch_id, media_desc])

        # Growth rate: explicit selection or fallback
        gf_all = (batch.get("growth_fits") or {})
        gf_by_wl = gf_all.get(_resolve_wl_key(gf_all, wl), {})
        gr_val = _select_gr_value(gf_by_wl, gr_type)
        logger.debug(f"Batch {batch_id}: selected GR model={gr_type or 'fallback'} value={gr_val}")
        if gr_val is not None and times:
            growth_rate_list.append([_iso_to_epoch_ms(times[-1]), float(gr_val), batch_id, media_desc, has_cryo])

    logger.info(
        f"Processed {batch_count} batches for experiment_id={experiment_id} in {time.time() - start_time:.2f}s "
        f"(OD={len(measurement_list)}, GR={len(growth_rate_list)}, Temp={len(temperature_measurements_list)})"
    )

    media_components_by_batch = {}
    for batch in exp.get("batches", []):
        bid = batch.get("batch_id")
        comps_out = []

        comps_raw = (batch.get("media") or {}).get("components")
        # Accept both dict and list formats; cap at 5
        if isinstance(comps_raw, dict):
            items = list(comps_raw.items())[:5]  # [(name, volume), ...]
            for name, vol in items:
                try:
                    vol = float(vol) if vol is not None else None
                except Exception:
                    vol = None
                comps_out.append({"name": str(name) if name is not None else "Unnamed", "volume": vol})
        elif isinstance(comps_raw, list):
            for comp in comps_raw[:5]:
                name = (comp.get("name") or comp.get("component") or "Unnamed") if isinstance(comp, dict) else "Unnamed"
                vol = comp.get("volume") if isinstance(comp, dict) else None
                try:
                    vol = float(vol) if vol is not None else None
                except Exception:
                    vol = None
                comps_out.append({"name": name, "volume": vol})
        else:
            comps_out = []

        media_components_by_batch[bid] = comps_out

    available = exp.get("measurement_types") or []
    meta = {
        "last_modified": last_modified,
        "selected_wavelength": wl,
        "available_wavelengths": available,
        "primary_measurement_type": exp.get("primary_measurement_type"),
        "media_components_by_batch": media_components_by_batch,  # <-- NEW
    }

    return [measurement_list, growth_rate_list, temperature_measurements_list, meta]

