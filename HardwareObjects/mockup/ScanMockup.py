#
#  Project: MXCuBE
#  https://github.com/mxcube.
#
#  This file is part of MXCuBE software.
#
#  MXCuBE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  MXCuBE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with MXCuBE.  If not, see <http://www.gnu.org/licenses/>.

import gevent
import random
import ast

from HardwareRepository.BaseHardwareObjects import HardwareObject
from HardwareRepository.HardwareObjects.DataPublisherRegistry import (
    PlotType,
    PlotDim,
    DataType,
    one_d_data,
)
from HardwareRepository import HardwareRepository as HWR


class ScanMockup(HardwareObject):
    """
    ScanMockup generates random data points to simulate an arbitrary scan
    """

    def __init__(self, name):
        super(ScanMockup, self).__init__(name)
        self._npoints = 100
        self._min = 0
        self._max = 10
        self._sample_rate = 0.5
        self._current_value = 0
        self._task = None
        self._dp_id = None

    def init(self):
        """
        FWK2 Init method
        """
        super(ScanMockup, self).init()

        self._npoints = self.getProperty("number_of_points", 100)
        self._min, self._max = ast.literal_eval(self.getProperty("min_max", (0, 10)))
        self._sample_rate = self.getProperty("sample_rate", 0.5)

        HWR.beamline.data_publisher_registry.register(
            "mockupscan",
            "diode",
            "MOCK SCAN",
            DataType.FLOAT,
            PlotDim.ONE_D,
            PlotType.SCATTER,
            "MOCK SCAN",
            sample_rate=self._sample_rate,
            _range=(self._min, self._max),
            meta={},
        )

        # self.start()

    def _generate_points(self):
        points = 0

        HWR.beamline.data_publisher_registry.start("mockupscan")

        while points < self._npoints:
            self._current_value = random.uniform(self._min, self._max)

            HWR.beamline.data_publisher_registry.pub(
                "mockupscan",
                one_d_data(points * self._sample_rate, self._current_value),
            )

            gevent.sleep(self._sample_rate)
            points += 1

        HWR.beamline.data_publisher_registry.stop("mockupscan")

    def start(self):
        """
        Start scan
        """
        if not self._task:
            self._task = gevent.spawn(self._generate_points)

    def stop(self):
        """
        Stop scan
        """
        self._task.kill()
        self._task = None
