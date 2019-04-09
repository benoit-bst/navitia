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
from .tests_mechanism import AbstractTestFixture, dataset, mock_equipment_providers
from .equipment_mock import *

default_date_filter = '_current_datetime=20120801T000000&'
TCL_escalator_filter = 'filter=stop_point.has_code_type(%22TCL_ESCALIER%22)&'
TCL_elevator_filter = 'filter=stop_point.has_code_type(%22TCL_ASCENCEUR%22)&'

@dataset({"main_routing_test": {}})
class TestEquipment(AbstractTestFixture):
    """
    Test the structure of the equipment_reports api
    """

    def test_equipment_reports_end_point(self):
        """
        simple equipment_reports call
        """
        with mock_equipment_providers(data=standard_mock_escalator_data):
            response = self.query_region('equipment_reports?' + default_date_filter)

            warnings = get_not_null(response, 'warnings')
            assert len(warnings) == 1
            assert warnings[0]['id'] == 'beta_endpoint'

            equipment_reports = get_not_null(response, 'equipment_reports')
            for equipment_report in equipment_reports:
                is_valid_equipment_report(equipment_report)
            assert len(equipment_reports) == 3

            assert line_reports[0]['line']['id'] == 'A'
            assert len(line_reports[0]['stop_area_equipments']) == 1
            assert line_reports[0]['stop_area_equipments'][0]['stop_area']['uri'] == 'stopA'
            assert line_reports[0]['stop_area_equipments'][0]['equipment_details']['id'] == '1'
            assert line_reports[0]['stop_area_equipments'][0]['equipment_details']['embedded_type'] == 'escalator'
            assert line_reports[0]['line']['id'] == 'A'
            assert len(line_reports[0]['stop_area_equipments']) == 1
            assert line_reports[0]['stop_area_equipments'][0]['stop_area']['uri'] == 'stopA'
            assert line_reports[0]['stop_area_equipments'][0]['equipment_details']['id'] == '1'
            assert line_reports[0]['stop_area_equipments'][0]['equipment_details']['embedded_type'] == 'escalator'


        with mock_equipment_providers(data=standard_mock_elevator_data):
            response = self.query_region('equipment_reports?' + default_date_filter)

            equipment_reports = get_not_null(response, 'equipment_reports')
            for equipment_report in equipment_reports:
                is_valid_equipment_report(equipment_report)

        with mock_equipment_providers(data=standard_mock_mixed_data):
            response = self.query_region('equipment_reports?' + default_date_filter)

            equipment_reports = get_not_null(response, 'equipment_reports')
            for equipment_report in equipment_reports:
                is_valid_equipment_report(equipment_report)


    def test_equipment_reports_with_filter(self):
        """
        equipment_reports call with filter
        """
        with mock_equipment_providers(data=standard_mock_escalator_data):
            response = self.query_region('equipment_reports?' + default_date_filter + TCL_escalator_filter)

            equipment_reports = get_not_null(response, 'equipment_reports')
            for equipment_report in equipment_reports:
                is_valid_equipment_report(equipment_report)


        with mock_equipment_providers(data=standard_mock_elevator_data):
            response = self.query_region('equipment_reports?' + default_date_filter + TCL_elevator_filter)

            equipment_reports = get_not_null(response, 'equipment_reports')
            for equipment_report in equipment_reports:
                is_valid_equipment_report(equipment_report)


        with mock_equipment_providers(data=standard_mock_mixed_data):
            response = self.query_region('equipment_reports?' + default_date_filter + TCL_escalator_filter)

            equipment_reports = get_not_null(response, 'equipment_reports')
            for equipment_report in equipment_reports:
                is_valid_equipment_report(equipment_report)


    def test_equipment_reports_with_wrong_id(self):

        """
        wrong id test
        """
        with mock_equipment_providers(data=wrong_mock_with_bad_id_data):
            response = self.query_region('equipment_reports?' + default_date_filter)


