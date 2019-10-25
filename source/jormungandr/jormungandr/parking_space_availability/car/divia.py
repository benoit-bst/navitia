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
import jmespath
from collections import namedtuple

import logging
from jormungandr import app
from jormungandr.parking_space_availability.car.common_car_park_provider import CommonCarParkProvider
from jormungandr.parking_space_availability.car.parking_places import ParkingPlaces
from jormungandr.street_network.utils import crowfly_distance_between_coords

DEFAULT_DIVIA_FEED_PUBLISHER = None
DEFAULT_DIVIA_TOLARANCE_FOR_POI_COORDS_MATCHING = 500

SearchPattern = namedtuple('SearchPattern', ['id_park', 'available', 'total'])


def divia_maker(search_patterns):
    class _DiviaProvider(CommonCarParkProvider):
        # search patterns are different depending on divia's dataset
        id_park = None
        available = None
        total = None

        def __init__(
            self, url, operators, dataset, timeout=1, feed_publisher=DEFAULT_DIVIA_FEED_PUBLISHER, **kwargs
        ):
            self.provider_name = 'DIVIA'
            self.log = logging.LoggerAdapter(
                logging.getLogger(__name__), extra={'provider_name': self.provider_name}
            )
            self.divia_tolerance_for_poi_coords_matching = kwargs.get(
                'divia_tolerance_for_poi_coords_matching',
                app.config.get(
                    str('DIVIA_TOLARANCE_FOR_POI_COORDS_MATCHING'),
                    DEFAULT_DIVIA_TOLARANCE_FOR_POI_COORDS_MATCHING,
                ),
            )

            super(_DiviaProvider, self).__init__(url, operators, dataset, timeout, feed_publisher, **kwargs)

        def _match_poi_coords_with_divia_provider_parking_coords(self, poi, divia_provider_parking, tolerance):
            """
            return true if the distance between poi coordinates and real time Divia praking coordinates are <= tolerance
            """
            if poi is None:
                self.log.error('poi is empty, can not match with realtime data')
                return False

            if divia_provider_parking is None:
                self.log.error('real time divia parking is empty. Can not match with theoric poi')
                return False

            def _poi_coords(poi):
                """
                return the (lat,lon) couple for a given POI
                """
                if (
                    poi.get('coord') is not None
                    and poi['coord'].get('lat') is not None
                    and poi['coord'].get('lon') is not None
                ):
                    return (float(poi['coord']['lat']), float(poi['coord']['lon']))
                else:
                    return None

            def _divia_parking_coords(divia_provider_parking):
                """
                return the (lat,lon) couple for a given real time divia provider parkings
                """
                if (
                    divia_provider_parking.get('fields') is not None
                    and divia_provider_parking['fields'].get('coordonnees') is not None
                ):
                    if len(divia_provider_parking['fields']['coordonnees']) > 1:
                        return (
                            float(divia_provider_parking['fields']['coordonnees'][0]),
                            float(divia_provider_parking['fields']['coordonnees'][1]),
                        )
                    else:
                        return None

            poi_coords = _poi_coords(poi)
            if poi_coords is None:
                self.log.error(
                    'poi with properties.ref={} does not have valid coordinates for matching'.format(
                        poi['properties']['ref']
                    )
                )
                # if coordinates does not exist, the matching is only on ID
                return True

            divia_parking_coords = _divia_parking_coords(divia_provider_parking)
            if divia_parking_coords is None:
                self.log.error(
                    'divia parking {} does not have valid coordinates for matching'.format(
                        divia_provider_parking['fields']['numero_parking']
                    )
                )
                # if coordinates does not exist, the matching is only on ID
                return True
            if crowfly_distance_between_coords(poi_coords, divia_parking_coords) <= tolerance:
                return True
            else:
                return False

        def process_data(self, data, poi):
            park = jmespath.search(
                'records[?to_number(fields.{})==`{}`]|[0]'.format(self.id_park, poi['properties']['ref']), data
            )
            if park and self._match_poi_coords_with_divia_provider_parking_coords(
                poi, park, self.divia_tolerance_for_poi_coords_matching
            ):
                available = jmespath.search('fields.{}'.format(self.available), park)
                nb_places = jmespath.search('fields.{}'.format(self.total), park)
                if available is not None and nb_places is not None and nb_places >= available:
                    occupied = nb_places - available
                else:
                    occupied = None
                return ParkingPlaces(available, occupied, None, None)

    _DiviaProvider.id_park = search_patterns.id_park
    _DiviaProvider.available = search_patterns.available
    _DiviaProvider.total = search_patterns.total

    return _DiviaProvider


DiviaProvider = divia_maker(
    SearchPattern(id_park='numero_parking', available='nombre_places_libres', total='nombre_places')
)


DiviaPRParkProvider = divia_maker(
    SearchPattern(id_park='numero_parc', available='nb_places_libres', total='nombre_places')
)
