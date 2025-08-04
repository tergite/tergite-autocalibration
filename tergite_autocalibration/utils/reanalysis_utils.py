# This code is part of Tergite
#
# (C) Copyright Axel Erik Andersson 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import typer
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple, Dict  # , Iterator
import re
from datetime import datetime, time, date

from tergite_autocalibration.utils.logging import logger

# Regex to extract the 'YYYYMMDD-HHMMSS' at the start of folder names
REGEX_MSMT_FOLDER = re.compile(r"^(\d{8}-\d{6})-\d{3}-[0-9a-f]{6}-[\w]+$")
REGEX_RUN_FOLDER = re.compile(r"^(\d{2}-\d{2}-\d{2})_[\w]+-[\w]+$")
REGEX_DAY_FOLDER = re.compile(r"^(\d{4}-\d{2}-\d{2})$")


def is_day_folder(path_to_something: Path | str):
    f = Path(path_to_something).resolve()
    return f.exists() and f.is_dir() and REGEX_DAY_FOLDER.match(f.name)


def is_run_folder(path_to_something: Path | str):
    f = Path(path_to_something).resolve()
    return f.exists() and f.is_dir() and REGEX_RUN_FOLDER.match(f.name)


def is_measurement_folder(path_to_something: Path | str):
    f = Path(path_to_something).resolve()
    return f.exists() and f.is_dir() and REGEX_MSMT_FOLDER.match(f.name)


@dataclass(frozen=True)
class MeasurementInfo:

    timestamp: datetime
    tuid: str
    msmt_idx: int
    node_name: str
    measurement_folder_path: Path
    run_folder_path: Path
    dataset_path: Path | None = None


@dataclass(frozen=True)
class RunInfo:
    timestamp: time
    run_idx: int
    measurements: list[MeasurementInfo]


@dataclass(frozen=True)
class DayInfo:
    timestamp: date
    day_idx: int
    runs: list[RunInfo]


def _classify_subfolders_by_hdf5(
    root_dir: Path | str,
) -> Tuple[Dict[int, MeasurementInfo], Dict[int, MeasurementInfo]]:
    root_dir = Path(root_dir)
    subfolders = sorted(
        filter(is_measurement_folder, root_dir.iterdir()), key=lambda d: d.name
    )

    with_hdf5: Dict[int, str] = {}
    without_hdf5: Dict[int, str] = {}

    for idx, folder in enumerate(subfolders, start=1):
        ts_match = REGEX_MSMT_FOLDER.match(folder.name)
        ts_str = ts_match.group(1)
        timestamp_val = datetime.strptime(ts_str, "%Y%m%d-%H%M%S")

        dataset_files = [
            file
            for file in folder.iterdir()
            if file.is_file() and file.suffix == ".hdf5"
        ]
        hdf5_exists = any(dataset_files)

        # NOTE: Assumes only one dataset file in folder
        dataset_fp = None if not hdf5_exists else dataset_files[0].resolve()

        tuid = folder.name.rsplit("-", maxsplit=1)[0]
        node_name = folder.name.rsplit("-", maxsplit=1)[1]
        measurement_folder_path = folder.resolve()
        run_folder_path = root_dir.resolve()

        info = MeasurementInfo(
            timestamp=timestamp_val,
            tuid=tuid,
            msmt_idx=idx,
            node_name=node_name,
            measurement_folder_path=measurement_folder_path,
            run_folder_path=run_folder_path,
            dataset_path=dataset_fp,
        )

        if hdf5_exists:
            assert dataset_fp.exists()
            with_hdf5[idx] = info
        else:
            without_hdf5[idx] = info

    return with_hdf5, without_hdf5


def select_measurement_for_analysis(
    path_to_run_folder: Path | str, node_name: str | None = None
) -> MeasurementInfo:
    path_to_run_folder = Path(path_to_run_folder)

    if not is_run_folder(path_to_run_folder):
        raise FileNotFoundError(f"'{path_to_run_folder}' is not a run folder.")

    with_data, without_data = _classify_subfolders_by_hdf5(path_to_run_folder)

    if len(with_data) == 0:
        raise FileNotFoundError(
            f"The folder '{path_to_run_folder}' contains no measurement data."
        )

    if len(without_data) > 0:
        _dataless_folders = [
            info.measurement_folder_path.name for info in without_data.values()
        ]
        logger.info(
            f"Filtering away: {_dataless_folders} since these folders do not contain measurement data."
        )

    existing_measurements_str = (
        "\n".join(
            [
                f"{idx}: {info.node_name} (measured: {info.timestamp})"
                for idx, info in sorted(with_data.items(), key=lambda t: t[1].timestamp)
            ]
        )
        + "\n"
    )

    if node_name:
        try:
            # NOTE: Assumes that a node is only visited once during a run
            #       since it returns as soon as it finds the node_name
            return next(
                filter(lambda info: info.node_name == node_name, with_data.values())
            )

        # StopIteration can happen during e.g. node_name misspelling
        except StopIteration:
            raise FileNotFoundError(
                f"The node name '{node_name}' was specified, but the run folder does not "
                + "contain a measurement with this node name. Existing measurements:\n"
                + existing_measurements_str
            ) from None

    # If the user did not specify which node to analyse, then prompt them
    num_folders_with_data = len(with_data)
    typer.echo(
        "Detected the following measurements in the specified folder:\n"
        + existing_measurements_str
    )
    while True:
        number = typer.prompt(
            "Which would you like to reanalyse? "
            f"Please enter a number between 1 and {num_folders_with_data} to re-analyse. Enter 0 to cancel",
            type=int,
        )
        if number == 0:
            raise typer.Abort()
        if 1 <= number <= len(with_data):
            break
        typer.echo(
            f"Number must be between 1 and {num_folders_with_data} to re-analyse. Enter 0 to cancel"
        )

    return with_data[number]


def get_run_infos(path_to_day_folder: Path | str) -> list[RunInfo]:
    path_to_day_folder = Path(path_to_day_folder)
    if not is_day_folder(path_to_day_folder):
        raise FileNotFoundError(f"'{path_to_day_folder}' is not a day folder.")

    subfolders = sorted(
        filter(is_run_folder, path_to_day_folder.iterdir()), key=lambda d: d.name
    )

    run_infos = []

    for idx, run_folder in enumerate(subfolders, start=1):
        run_match = REGEX_RUN_FOLDER.match(run_folder.name)

        run_timestamp_str = run_match.group(1)
        run_ts_val = datetime.strptime(run_timestamp_str, "%H-%M-%S").time()

        msmt_infos_with_data, _ = _classify_subfolders_by_hdf5(run_folder)

        run_info = RunInfo(
            timestamp=run_ts_val,
            run_idx=idx,
            measurements=msmt_infos_with_data.values(),
        )
        run_infos.append(run_info)

    return sorted(run_infos, key=lambda r_i: r_i.timestamp)


def get_day_infos(path_to_tergite_data_out_folder: Path | str) -> list[DayInfo]:
    path_to_tergite_data_out_folder = Path(path_to_tergite_data_out_folder).resolve()
    if (
        not path_to_tergite_data_out_folder.exists()
        and path_to_tergite_data_out_folder.name == "out"
    ):
        raise FileNotFoundError(
            f"'{path_to_tergite_data_out_folder}' should be the Tergite 'out' folder."
        )

    subfolders = sorted(
        filter(is_day_folder, path_to_tergite_data_out_folder.iterdir()),
        key=lambda d: d.name,
    )

    day_infos = []
    for idx, day_folder in enumerate(subfolders, start=1):
        day_match = REGEX_DAY_FOLDER.match(day_folder.name)

        date_str = day_match.group(1)
        date_val = datetime.strptime(date_str, "%Y-%m-%d").date()

        day_infos.append(
            DayInfo(timestamp=date_val, day_idx=idx, runs=get_run_infos(day_folder))
        )

    return sorted(day_infos, key=lambda d_i: d_i.timestamp)


def search_all_runs_for_measurement(
    path_to_tergite_data_out_folder: Path | str, data_identifier: str
) -> MeasurementInfo | None:
    path_to_tergite_data_out_folder = Path(path_to_tergite_data_out_folder)
    day_infos = get_day_infos(path_to_tergite_data_out_folder)
    data_identifier_as_path = Path(data_identifier).resolve()

    for d_i in day_infos:
        for r_i in d_i.runs:
            for m_i in r_i.measurements:
                if (
                    m_i.measurement_folder_path.name == data_identifier
                    or m_i.measurement_folder_path == data_identifier_as_path
                ):
                    return m_i

    return None
