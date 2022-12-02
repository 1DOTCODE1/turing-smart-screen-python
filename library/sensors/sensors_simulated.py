import math
from typing import Tuple
import random

import library.sensors.sensors as sensors
from library.log import logger

class CPU(sensors.CPU):
    @staticmethod
    def percentage(interval: float) -> float:
        return random.uniform(0, 100)

    @staticmethod
    def frequency() -> float:
        return random.uniform(800, 3400)

    @staticmethod
    def load() -> Tuple[float, float, float]:  # 1 / 5 / 15min avg:
        return random.uniform(0, 100), random.uniform(0, 100), random.uniform(0, 100)

    @staticmethod
    def is_temperature_available() -> bool:
        return True

    @staticmethod
    def temperature() -> float:
        return random.uniform(30, 90)


class Gpu(sensors.GPU):
    @staticmethod
    def stats() -> Tuple[float, float, float, float]:  # load (%) / used mem (%) / used mem (Mb) / temp (°C)
        return random.uniform(0, 100), random.uniform(0, 100), random.uniform(300, 16000), random.uniform(30, 90)

    @staticmethod
    def is_available() -> bool:
        return True


class Memory(sensors.Memory):
    @staticmethod
    def swap_percent() -> float:
        return random.uniform(0, 100)

    @staticmethod
    def virtual_percent() -> float:
        return random.uniform(0, 100)

    @staticmethod
    def virtual_used() -> int:
        return random.randint(300, 16000)

    @staticmethod
    def virtual_free() -> int:
        return random.randint(300, 16000)


class Disk(sensors.Disk):
    @staticmethod
    def disk_usage_percent() -> float:
        return psutil.disk_usage("/").percent

    @staticmethod
    def disk_used() -> int:
        return psutil.disk_usage("/").used

    @staticmethod
    def disk_total() -> int:
        return psutil.disk_usage("/").total

    @staticmethod
    def disk_free() -> int:
        return psutil.disk_usage("/").free


class Net(sensors.Net):
    @staticmethod
    def stats(if_name, interval) -> Tuple[int, int, int, int]:
        global PNIC_BEFORE
        # Get current counters
        pnic_after = psutil.net_io_counters(pernic=True)

        upload_rate = math.nan
        uploaded = math.nan
        download_rate = math.nan
        downloaded = math.nan

        try:
            if if_name in pnic_after:
                upload_rate = (pnic_after[if_name].bytes_sent - PNIC_BEFORE[if_name].bytes_sent) / interval
                uploaded = pnic_after[if_name].bytes_sent
                download_rate = (pnic_after[if_name].bytes_recv - PNIC_BEFORE[if_name].bytes_recv) / interval
                downloaded = pnic_after[if_name].bytes_recv
        except:
            # Interface might not be in PNIC_BEFORE for now
            pass

        PNIC_BEFORE.update({if_name: pnic_after[if_name]})

        return upload_rate, uploaded, download_rate, downloaded
