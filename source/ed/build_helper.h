/* Copyright © 2001-2014, Canal TP and/or its affiliates. All rights reserved.
  
This file is part of Navitia,
    the software to build cool stuff with public transport.
 
Hope you'll enjoy and contribute to this project,
    powered by Canal TP (www.canaltp.fr).
Help us simplify mobility and open public transport:
    a non ending quest to the responsive locomotion way of traveling!
  
LICENCE: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
   
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.
   
You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
  
Stay tuned using
twitter @navitia 
IRC #navitia on freenode
https://groups.google.com/d/forum/navitia
www.navitia.io
*/

#pragma once

#include "utils/functions.h"
#include "type/data.h"
#include <boost/date_time/gregorian_calendar.hpp>
#include "georef/georef.h"
#include "type/meta_data.h"
#include "type/message.h"
#include "type/rt_level.h"
#include <memory>

/** Ce connecteur permet de faciliter la construction d'un réseau en code
 *
 *  Cela est particulièrement (voire exclusivement) utile pour les tests unitaires
 */

namespace ed {

struct builder;


/// Structure retournée à la construction d'un VehicleJourney
struct VJ {
    builder & b;
    nt::VehicleJourney* vj;

    /// Construit un nouveau vehicle journey
    VJ(builder & b, const std::string &line_name, const std::string &validity_pattern,
       bool is_frequency,
       bool wheelchair_boarding = true, const std::string& uri="",
       const std::string& meta_vj_name = "", const std::string& physical_mode = "");

    /// Ajout un nouveau stopTime
    /// Lorsque le depart n'est pas specifié, on suppose que c'est le même qu'à l'arrivée
    /// Si le stopPoint n'est pas connu, on le crée avec un stopArea ayant le même nom
    VJ& operator()(const std::string &stopPoint, int arrivee, int depart = -1, uint16_t local_traffic_zone = std::numeric_limits<uint16_t>::max(),
                   bool drop_off_allowed = true, bool pick_up_allowed = true);

    VJ& operator()(const std::string &stopPoint, const std::string& arrivee, const std::string& depart,
            uint16_t local_traffic_zone = std::numeric_limits<uint16_t>::max(), bool drop_off_allowed = true, bool pick_up_allowed = true);

    // set the shape to the last stop point
    VJ& st_shape(const navitia::type::LineString& shape);
};

struct SA {
    builder& b;
    navitia::type::StopArea* sa;

    /// Construit un nouveau stopArea
    SA(builder & b, const std::string & sa_name, double x, double y,
       bool create_sp = true, bool wheelchair_boarding = true);

    /// Construit un stopPoint appartenant au stopArea courant
    SA & operator()(const std::string & sp_name, double x = 0, double y = 0, bool wheelchair_boarding = true);
};

struct DisruptionCreator;

struct Impacter {
    Impacter(builder&, nt::disruption::Disruption&);
    builder& b;
    boost::shared_ptr<nt::disruption::Impact> impact;
    const nt::disruption::Disruption& get_disruption() const {
        return *impact->disruption;
    }
    Impacter& uri(const std::string& u) { impact->uri = u; return *this; }
    Impacter& application_periods(const boost::posix_time::time_period& p) {
        impact->application_periods.push_back(p);
        return *this;
    }
    Impacter& severity(nt::disruption::Effect,
                       std::string uri = "",
                       const std::string& wording = "",
                       const std::string& color = "#FFFF00",
                       int priority = 0);

    Impacter& severity(const std::string& uri); // link to existing severity
    Impacter& on(nt::Type_e type, const std::string& uri); // add elt in informed_entities
    Impacter& msg(nt::disruption::Message);
    Impacter& msg(const std::string& msg, nt::disruption::ChannelType = nt::disruption::ChannelType::email);
    Impacter& publish(const boost::posix_time::time_period& p) {
        //to ease use without a DisruptionCreator
        impact->disruption->publication_period = p;
        return *this;
    }
};

struct DisruptionCreator {
    builder& b;
    DisruptionCreator(builder&, const std::string& uri, nt::RTLevel lvl);

    Impacter& impact();
    DisruptionCreator& publication_period(const boost::posix_time::time_period& p) {
        disruption.publication_period = p;
        return *this;
    }
    DisruptionCreator& contributor(const std::string& c) {
        disruption.contributor = c;
        return *this;
    }
    DisruptionCreator& tag(const std::string& t);

    nt::disruption::Disruption& disruption;
    std::vector<Impacter> impacters;
};

struct builder {
    std::map<std::string, navitia::type::Line *> lines;
    std::map<std::string, navitia::type::StopArea *> sas;
    std::map<std::string, navitia::type::StopPoint *> sps;
    std::map<std::string, navitia::type::Network *> nts;
    std::multimap<std::string, navitia::type::VehicleJourney*> block_vjs;
    boost::gregorian::date begin;

    std::unique_ptr<navitia::type::Data> data = std::make_unique<navitia::type::Data>();
    navitia::georef::GeoRef street_network;

    /// Il faut préciser là date de début des différents validity patterns
    builder(const std::string & date, const std::string& publisher_name = "canal tp") : begin(boost::gregorian::date_from_iso_string(date)){
        data->meta->production_date = {begin, begin + boost::gregorian::years(1)};
        data->meta->timezone = "UTC"; //default timezone is UTC
		data->loaded = true;
        data->meta->instance_name = "builder";
        data->meta->publisher_name = publisher_name;
        data->meta->publisher_url = "www.canaltp.fr";
        data->meta->license = "ODBL";
    }

    /// Create a discrete vehicle journey (no frequency, explicit stop times)
    VJ vj(const std::string& line_name,
          const std::string& validity_pattern = "11111111",
          const std::string& block_id="",
          const bool wheelchair_boarding = true,
          const std::string& uri="",
          const std::string& meta_vj="",
          const std::string& physical_mode = "");

    VJ vj_with_network(const std::string& network_name,
          const std::string& line_name,
          const std::string& validity_pattern = "11111111",
          const std::string& block_id="",
          const bool wheelchair_boarding = true,
          const std::string& uri="",
          const std::string& meta_vj="",
          const std::string& physical_mode = "",
          bool is_frequency=false);

    VJ frequency_vj(const std::string& line_name,
                    uint32_t start_time,
                    uint32_t end_time,
                    uint32_t headway_secs,
                    const std::string& network_name = "default_network",
                    const std::string& validity_pattern = "11111111",
                    const std::string& block_id="",
                    const bool wheelchair_boarding = true,
                    const std::string& uri="",
                    const std::string& meta_vj="");

    /// Crée un nouveau stop area
    SA sa(const std::string & name, double x = 0, double y = 0,
          const bool create_sp = true, const bool wheelchair_boarding = true);
    SA sa(const std::string & name, navitia::type::GeographicalCoord geo,
          const bool create_sp = true, bool wheelchair_boarding = true) {
        return sa(name, geo.lon(), geo.lat(), create_sp, wheelchair_boarding);
    }

    DisruptionCreator disrupt(nt::RTLevel lvl, const std::string& uri);
    Impacter impact(nt::RTLevel lvl, std::string disruption_uri = "");

    /// Crée une connexion
    void connection(const std::string & name1, const std::string & name2, float length);
    void build_blocks();
    void finish();
    void generate_dummy_basis();
    void manage_admin();
    void build_autocomplete();
};

}
