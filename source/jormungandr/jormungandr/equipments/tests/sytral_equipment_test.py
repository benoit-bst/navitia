# encoding: utf-8
# Copyright (c) 2001-2019, Canal TP and/or its affiliates. All rights reserved.
#
# This file is part of Navitia,
#     the software to build cool stuff with public transport.
#
# Hope you'll enjoy and contribute to this project,
#     powered by Canal TP (www.canaltp.fr).
# Help us simplify mobility and open public transport:
#     a non ending quest to the responsive locomotion way of traveling!
#
# LICENCE: This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Stay tuned using
# twitter @navitia
# IRC #navitia on freenode
# https://groups.google.com/d/forum/navitia
# www.navitia.io

from __future__ import absolute_import, print_function, unicode_literals, division

from mock import MagicMock
from jormungandr.equipments.sytral import SytralProvider
from navitiacommon.type_pb2 import StopPoint

mock_data = {
    "equipments_details": [
        {
            "id": "261",
            "name": "sortie Place Basse niveau Parc Relais",
            "embedded_type": "escalator",
            "current_availaibity": {
                "status": "available",
                "cause": {"label": "Probleme technique"},
                "effect": {"label": "."},
                "periods": [{"begin": "2018-09-14T00:00:00+02:00", "end": "2018-09-15T23:30:00+02:00"}],
                "updated_at": "2018-09-15T12:01:31+02:00",
            },
        }
    ]
}


def create_stop_point(code_type, code_value):
    st = StopPoint()
    code = st.codes.add()
    code.type = code_type
    code.value = code_value
    return st


def equipments_get_information_test():
    """
    Test that 'equipment_details' structure is added to StopPoint proto when conditions are met
    """
    provider = SytralProvider(url="sytral.url")
    provider._call_webservice = MagicMock(return_value=mock_data)

    # stop point has code with correct type and value present in webservice response
    # equipment_details is added
    st = create_stop_point("TCL_ASCENCEUR", "261")
    provider.get_informations([st])
    assert st.equipment_details

    # stop point has code with correct type but value not present in webservice response
    # equipment_details is not added
    st = create_stop_point("TCL_ASCENCEUR", "262")
    provider.get_informations([st])
    assert not st.equipment_details

    # stop point has code with incorrect type but value present in webservice response
    # equipment_details is not added
    st = create_stop_point("ASCENCEUR", "261")
    provider.get_informations([st])
    assert not st.equipment_details

