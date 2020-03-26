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
import redis
import json
import gevent
import logging

from enum import Enum, unique

from HardwareRepository.BaseHardwareObjects import HardwareObject


@unique
class PlotType(Enum):
    SCATTER = "scatter"


class PlotDim(Enum):
    ONE_D = 1
    TWO_D = 2


class DataType(Enum):
    FLOAT = "float"


class FrameType(Enum):
    DATA = "data"
    START = "start"
    STOP = "stop"


def one_d_data(x, y):
    return {"x": x, "y": y}


class DataPublisherRegistry(HardwareObject):
    """
    DataPublisher handles data publishing
    """

    def __init__(self, name):
        super(DataPublisherRegistry, self).__init__(name)
        self._r = None
        self._subsribe_task = None

    def init(self):
        """
        FWK2 Init method
        """
        super(DataPublisherRegistry, self).init()

        rhost = self.getProperty("host", "localhost")
        rport = self.getProperty("port", 6379)
        rdb = self.getProperty("db", 11)

        self._r = redis.Redis(
            host=rhost, port=rport, db=rdb, charset="utf-8", decode_responses=True
        )

        if not self._subsribe_task:
            self._subsribe_task = gevent.spawn(self._subscribe_task)

    def _subscribe_task(self):
        pubsub = self._r.pubsub(ignore_subscribe_messages=True)
        pubsub.psubscribe("HWR_DP_NEW_DATA_POINT_*")

        _data = {}

        # The descriptions of active publishers for fast access
        # while publishing data
        active_publisher_desc = {}

        for message in pubsub.listen():
            if message:
                try:
                    redis_channel = message["channel"]
                    _id = redis_channel.split("_")[-1]

                    data = json.loads(message["data"])

                    if data["type"] == FrameType.START.value:
                        _data[redis_channel] = {"x": [], "y": []}

                        self._update_description(_id, {"running": True})
                        self._clear_data(_id)
                        self.emit(
                            "start", self.get_description(_id, include_data=True)[0]
                        )
                        active_publisher_desc[redis_channel] = self._get_description(
                            _id
                        )

                    elif data["type"] == FrameType.STOP.value:
                        self._update_description(_id, {"running": False})
                        self.emit(
                            "end", self.get_description(_id, include_data=True)[0]
                        )
                        active_publisher_desc.pop(redis_channel)
                    elif data["type"] == FrameType.DATA.value:
                        _data[redis_channel] = {
                            "x": _data[redis_channel]["x"] + [data["data"]["x"]],
                            "y": _data[redis_channel]["y"] + [data["data"]["y"]],
                        }

                        self.emit(
                            "data", {"id": _id, "data": _data[redis_channel]},
                        )

                        self._append_data(
                            _id, data["data"], active_publisher_desc[redis_channel]
                        )
                    else:
                        msg = "Unknown frame type %s" % message
                        logging.getLogger("HWR").error(msg)
                except:
                    msg = "Could not parse data in %s" % message
                    logging.getLogger("HWR").exception(msg)

    def _subscribe(self, _id):
        self._add_avilable(_id)

    def _unsubscribe(self, _id):
        self._remove_available(_id)

    def _remove_available(self, _id):
        publishers = self._get_available()
        publishers = {} if not publishers else publishers
        publishers.pop(_id)

        self._r.set("HWR_DP_PUBLISHERS", json.dumps(publishers))

    def _add_avilable(self, _id):
        publishers = self._get_available()
        publishers = {} if not publishers else publishers
        publishers[_id] = "HWR_DP_NEW_DATA_POINT_%s" % _id

        self._r.set("HWR_DP_PUBLISHERS", json.dumps(publishers))

    def _get_available(self):
        publishers = self._r.get("HWR_DP_PUBLISHERS")
        publishers = json.loads(publishers) if publishers else {}

        return publishers

    def _set_description(self, _id, desc):
        self._r.set("HWR_DP_%s_DESCRIPTION" % _id, json.dumps(desc))

    def _get_description(self, _id):
        return json.loads(self._r.get("HWR_DP_%s_DESCRIPTION" % _id))

    def _update_description(self, _id, data):
        desc = self._get_description(_id)
        desc.update(data)
        self._set_description(_id, desc)

    def _append_data(self, _id, data, desc):
        self._r.rpush("HWR_DP_%s_DATA_X" % _id, data.get("x", float("nan")))
        self._r.rpush("HWR_DP_%s_DATA_Y" % _id, data.get("y", float("nan")))

        if desc["data_dim"] > 1:
            self._r.rpush("HWR_DP_%s_DATA_Z" % _id, data.get("z", float("nan")))

    def _clear_data(self, _id):
        desc = self._get_description(_id)

        self._r.delete("HWR_DP_%s_DATA_X" % _id)
        self._r.delete("HWR_DP_%s_DATA_Y" % _id)

        if desc["data_dim"] > 1:
            self._r.delete("HWR_DP_%s_DATA_Z" % _id)

    def _publish(self, _id, data):
        self._r.publish("HWR_DP_NEW_DATA_POINT_%s" % _id, json.dumps(data))

    def register(
        self,
        _id,
        channel,
        name,
        data_type,
        data_dim,
        plot_type,
        content_type,
        sample_rate=0.5,
        _range=(None, None),
        meta={},
    ):

        plot_description = {
            "id": _id,
            "channel": channel,
            "name": name,
            "data_type": data_type.value,
            "data_dim": data_dim.value,
            "plot_type": plot_type.value,
            "sample_rate": sample_rate,
            "content_type": content_type,
            "range": _range,
            "meta": meta,
            "running": False,
        }

        self._set_description(_id, plot_description)
        self._subscribe(_id)

        return _id

    def pub(self, _id, data):
        self._publish(_id, {"type": FrameType.DATA.value, "data": data})

    def start(self, _id):
        self._publish(_id, {"type": FrameType.START.value, "data": {}})

    def stop(self, _id):
        self._update_description(_id, {"running": False})
        self._publish(_id, {"type": FrameType.STOP.value, "data": {}})

    def get_description(self, _id=None, include_data=False):
        desc = []

        if _id:
            _d = self._get_description(_id)

            if include_data:
                _d.update({"values": self.get_data(_id)})

            desc = [_d]

        else:
            available = self._get_available()

            for _id in available.keys():
                _d = self._get_description(_id)

            if include_data:
                _d.update({"values": self.get_data(_id)})

            desc.append(_d)

        return desc

    def get_data(self, _id):
        desc = self._get_description(_id)
        data = {
            "x": self._r.lrange("HWR_DP_%s_DATA_X" % _id, 0, -1),
            "y": self._r.lrange("HWR_DP_%s_DATA_Y" % _id, 0, -1),
        }

        if desc["data_dim"] > 1:
            data.update(
                {"z": self._r.lrange("HWR_DP_%s_DATA_Z" % _id, 0, -1),}
            )

        return data
