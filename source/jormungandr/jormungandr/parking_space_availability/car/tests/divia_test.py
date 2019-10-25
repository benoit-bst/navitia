# encoding: utf-8
# Copyright (c) 2001-2018, Canal TP and/or its affiliates. All rights reserved.
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
# channel `#navitia` on riot https://riot.im/app/#/room/#navitia:matrix.org
# https://groups.google.com/d/forum/navitia
# www.navitia.io

from __future__ import absolute_import, print_function, unicode_literals, division

import pytest
from mock import MagicMock

from jormungandr.parking_space_availability.car.divia import SearchPattern, DiviaProvider, DiviaPRParkProvider

from jormungandr.parking_space_availability.car.parking_places import ParkingPlaces

poi = {
    'properties': {'operator': 'divia', 'ref': '42'},
    'poi_type': {'name': 'Parking', 'id': 'poi_type:public_parking'},
}

poi_tours_parking_with_coords = {
    'properties': {'operator': 'divia', 'ref': '42'},
    'poi_type': {'name': 'Parking', 'id': 'poi_type:public_parking'},
    'coord': {'lat': '47.3858089', 'lon': '0.7257019'},
}

poi_hector_malot_paris_parking_with_coords = {
    'properties': {'operator': 'divia', 'ref': '42'},
    'poi_type': {'name': 'Parking', 'id': 'poi_type:public_parking'},
    'coord': {'lat': '48.846808', 'lon': '2.377202'},
}

# 60 meters from the hector malot parking Poi
realtime_divia_hector_malot_paris_parking_coords = {'lat': 48.847267, 'lon': 2.377647}

DIVIA_TOLARANCE_FOR_POI_COORDS_MATCHING = 200


def car_park_space_availability_support_poi_test():
    """
    DIVIA car provider support
    """
    provider = DiviaProvider("fake.url", {'Divia'}, 'toto', 42)
    assert provider.support_poi(poi)

    invalid_poi = {}
    assert not provider.support_poi(invalid_poi)


def car_park_maker(divia_class, search_pattern):
    def _test():

        parking_places = ParkingPlaces(available=4, occupied=3)

        provider = divia_class("fake.url", {'Divia'}, 'toto', 42)
        divia_response = """
        {
            "records":[
                {
                    "fields": {
                        "%s": "42",
                        "%s": 4,
                        "%s": 7
                    }
                }
            ]
        }
        """ % (
            search_pattern.id_park,
            search_pattern.available,
            search_pattern.total,
        )

        import json

        provider._call_webservice = MagicMock(return_value=json.loads(divia_response))
        info = provider.get_informations(poi)
        assert info == parking_places
        assert not hasattr(info, "available_PRM")
        assert not hasattr(info, "occupied_PRM")

        provider._call_webservice = MagicMock(return_value=None)
        assert provider.get_informations(poi) is None

        divia_response = """
        {
            "records":[
                {
                    "fields": {
                    }
                }
            ]
        }
        """

        provider._call_webservice = MagicMock(return_value=json.loads(divia_response))
        assert provider.get_informations(poi) is None

        divia_response = """
        {
            "records":[
            ]
        }
        """
        provider._call_webservice = MagicMock(return_value=json.loads(divia_response))
        assert provider.get_informations(poi) is None

        divia_response = (
            """
        {
            "records":[
                {
                    "fields": {
                        "%s": "42"
                    }
                }
            ]
        }
        """
            % search_pattern.id_park
        )
        empty_parking = ParkingPlaces(available=None, occupied=None, available_PRM=None, occupied_PRM=None)
        provider._call_webservice = MagicMock(return_value=json.loads(divia_response))
        assert provider.get_informations(poi) == empty_parking

        # Test matching coords
        divia_response = """
        {
            "records":[
                {
                    "fields": {
                        "%s": "42",
                        "%s": 4,
                        "%s": 7,
                        "coordonnees" : [%s, %s]
                    }
                }
            ]
        }
        """ % (
            search_pattern.id_park,
            search_pattern.available,
            search_pattern.total,
            realtime_divia_hector_malot_paris_parking_coords.get('lat'),
            realtime_divia_hector_malot_paris_parking_coords.get('lon'),
        )

        # inside the tolerance (by default tolerance=500m)
        # difference between the 2 points = 60m
        parking_places = ParkingPlaces(available=4, occupied=3)
        provider._call_webservice = MagicMock(return_value=json.loads(divia_response))
        info = provider.get_informations(poi_hector_malot_paris_parking_with_coords)
        assert info == parking_places
        assert not hasattr(info, "available_PRM")
        assert not hasattr(info, "occupied_PRM")

        # outside the tolerance (by default tolerance=500m)
        # difference between the 2 points ~= 328Km
        provider._call_webservice = MagicMock(return_value=json.loads(divia_response))
        assert provider.get_informations(poi_tours_parking_with_coords) == None

    return _test


divia_pr_park_test = car_park_maker(
    DiviaPRParkProvider,
    SearchPattern(id_park='numero_parc', available='nb_places_libres', total='nombre_places'),
)


divia_pr_others_test = car_park_maker(
    DiviaProvider,
    SearchPattern(id_park='numero_parking', available='nombre_places_libres', total='nombre_places'),
)
