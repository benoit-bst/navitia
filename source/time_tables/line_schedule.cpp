#include "line_schedule.h"
#include "thermometer.h"
#include "parse_request.h"
#include "type/pb_converter.h"
#include "ptreferential/ptreferential.h"


namespace navitia { namespace timetables {

std::vector<vector_stopTime> get_all_stop_times(const vector_idx &journey_patterns, const type::DateTime &dateTime, const type::DateTime &max_datetime, type::Data &d) {
    std::vector<vector_stopTime> result;

    //On cherche les premiers journey_pattern_points de toutes les journey_patterns
    std::vector<type::idx_t> first_journey_pattern_points;
    for(type::idx_t journey_pattern_idx : journey_patterns) {
        first_journey_pattern_points.push_back(d.pt_data.journey_patterns[journey_pattern_idx].journey_pattern_point_list.front());
    }

    //On fait un next_departures sur ces journey_pattern points
    auto first_dt_st = get_stop_times(first_journey_pattern_points, dateTime, max_datetime, std::numeric_limits<int>::max(), d);

    //On va chercher tous les prochains horaires
    for(auto ho : first_dt_st) {
        result.push_back(vector_stopTime());
        type::DateTime dt = ho.first;
        for(type::idx_t stidx : d.pt_data.vehicle_journeys[d.pt_data.stop_times[ho.second].vehicle_journey_idx].stop_time_list) {
            dt.update(d.pt_data.stop_times[stidx].departure_time);
            result.back().push_back(std::make_pair(dt, stidx));
        }
    }
    return result;
}

std::vector<vector_string> make_matrice(const std::vector<vector_stopTime> & stop_times, Thermometer &thermometer, type::Data &d) {
    std::vector<vector_string> result;

    //On initilise le tableau vide
    for(unsigned int i=0; i<thermometer.get_thermometer().size(); ++i) {
        result.push_back(vector_string());
        result.back().resize(stop_times.size());
    }

    //On remplit le tableau
    int y=0;
    for(vector_stopTime vec : stop_times) {
        std::vector<uint32_t> orders = thermometer.match_journey_pattern(d.pt_data.journey_patterns[d.pt_data.vehicle_journeys[d.pt_data.stop_times[vec.front().second].vehicle_journey_idx].journey_pattern_idx]);
        int order = 0;
        for(dt_st dt_idx : vec) {
            result[orders[order]][y] = iso_string(dt_idx.first.date(),  dt_idx.first.hour(), d);
            ++order;
        }
        ++y;
    }

    return result;
}


pbnavitia::Response line_schedule(const std::string & filter, const std::string &str_dt, uint32_t duration, const uint32_t max_depth, type::Data &d) {
    RequestHandle parser("LINE_SCHEDULE", "", str_dt, duration, d);
    parser.pb_response.set_requested_api(pbnavitia::LINE_SCHEDULE);

    if(parser.pb_response.has_error()) {
        return parser.pb_response;
    }
    Thermometer thermometer(d);

    for(type::idx_t line_idx : navitia::ptref::make_query(type::Type_e::eLine, filter, d)) {
        auto schedule = parser.pb_response.mutable_line_schedule()->add_schedules();
        auto journey_patterns = d.pt_data.lines[line_idx].get(type::Type_e::eJourneyPattern, d.pt_data);
        //On récupère les stop_times
        auto stop_times = get_all_stop_times(journey_patterns, parser.date_time, parser.max_datetime, d);
        std::vector<vector_idx> journey_pattern_point_journey_patterns;
        for(auto journey_pattern_idx : journey_patterns) {
            journey_pattern_point_journey_patterns.push_back(vector_idx());
            for(auto rpidx : d.pt_data.journey_patterns[journey_pattern_idx].journey_pattern_point_list) {
                journey_pattern_point_journey_patterns.back().push_back(d.pt_data.journey_pattern_points[rpidx].stop_point_idx);
            }
        }
        thermometer.generate_thermometer(journey_pattern_point_journey_patterns);
        //On remplit l'objet header
        pbnavitia::LineScheduleHeader *header = schedule->mutable_header();
        for(vector_stopTime vec : stop_times) {
            fill_pb_object(line_idx, d, header->add_items()->mutable_line(), max_depth-1);
        }
        //On génère la matrice
        std::vector<vector_string> matrice = make_matrice(stop_times, thermometer, d);

        pbnavitia::Table *table = schedule->mutable_table();
        for(unsigned int i=0; i < thermometer.get_thermometer().size(); ++i) {
            type::idx_t spidx=thermometer.get_thermometer()[i];
            const type::StopPoint & sp = d.pt_data.stop_points[spidx];
            pbnavitia::TableLine * line = table->add_lines();
            line->set_stop_point(sp.name);

            for(unsigned int j=0; j<stop_times.size(); ++j) {
                line->add_stop_times(matrice[i][j]);
            }
        }


    }

    return parser.pb_response;

}
}}
