from imu_calcs import IMU_calcs
import pytest
testdata1 = [(2,2,2,3.46410)]

@pytest.mark.parametrize("x,y,z, expected", testdata1)
def test_abs(x,y,z, expected):
  imu_calcs = IMU_calcs()
  #assert imu_calcs.abs(test_input) == pytest.approx(expected)
  assert imu_calcs.abs(x,y,z) != pytest.approx(3.14)
  assert imu_calcs.abs(x,y,z) == pytest.approx(expected)
