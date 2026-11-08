import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "firmware" / "lib"))

from bmp280 import compensate

DATASHEET_CAL = (27504, 26435, -1000, 36477, -10685, 3024, 2855, 140, -7, 15500, -14600, 6000)


def test_datasheet_example():
    temp, pa = compensate(DATASHEET_CAL, adc_t=519888, adc_p=415148)
    assert temp == 25.08
    assert abs(pa - 100653.27) < 0.05
