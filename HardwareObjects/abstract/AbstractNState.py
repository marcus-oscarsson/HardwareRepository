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

"""
Defines the interface for N state devices
"""

import abc
from enum import Enum, unique
from HardwareRepository.HardwareObjects.abstract.AbstractActuator import (
    AbstractActuator,
)


__copyright__ = """ Copyright 2020 by the MXCuBE collaboration """
__license__ = "LGPLv3+"


@unique
class BaseValueEnum(Enum):
    """defines only the compulsory unknown."""

    UNKNOWN = "UNKNOWN"


class AbstractNState(AbstractActuator):
    """
    Abstract base class for N state objects.
    """

    __metaclass__ = abc.ABCMeta
    VALUES = BaseValueEnum

    def __init__(self, name):
        AbstractActuator.__init__(self, name)

    def validate_value(self, value):
        """Check if the value is within predefined values.
        Args:
            value(Enum): value to check
        Returns:
            (bool): True if within the values.
        """
        return value.name in self.VALUES.__members__

    def set_limits(self, limits):
        """Set actuator low and high limits.
        Args:
            limits (tuple): two floats tuple (low limit, high limit).
        """
        raise NotImplementedError

    def update_limits(self, limits=None):
        """Check if the limits have changed. Emits signal limitsChanged.
        Args:
            limits (tuple): two floats tuple (low limit, high limit).
        """
        raise NotImplementedError

    def get_values(self):
        """Get he predefined valies
        Returns:
            (Enum): predefined values Enum
        """
        return self.VALUES

    def value_to_enum(self, value):
        """Tranform a value to Enum
        Args:
           value (str, int, float, tuple): value
        Returns:
            (Enum): Enum member, corresponding to the value or UNKNOWN.
        """
        for enum_var in self.VALUES.__members__.values():
            if isinstance(value, tuple):
                if value == enum_var.value:
                    return enum_var
            try:
                if value == enum_var.value[0]:
                    return enum_var
            except TypeError:
                if value == enum_var.value:
                    return enum_var

        return self.VALUES.UNKNOWN
