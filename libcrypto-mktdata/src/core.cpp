// Copyright 2019 Kyle F. Downey
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <cloudwall/crypto-mktdata/core.h>

#include <sstream>

using namespace cloudwall::core::marketdata;

Currency::Currency(const std::string& ccy_code) : ccy_code_(ccy_code) {}

CurrencyPair::CurrencyPair(const Currency& base_ccy, const Currency& quote_ccy)
        : base_ccy_(base_ccy), quote_ccy_(quote_ccy) { }

Channel::Channel(const std::string &name, const std::optional<CurrencyPair> &ccy_pair)
        : name_(name), ccy_pair_(ccy_pair) { }

Subscription::Subscription(const std::list<Channel>& channels): channels_(channels) { }

RawFeedMessage::RawFeedMessage(const std::string &raw_json) : raw_json_(raw_json) {
}

double fastparse_double(const char* val_txt) {
    double val = 0.0;
    boost::spirit::qi::parse(val_txt, &val_txt[strlen(val_txt)], boost::spirit::qi::double_, val);
    return val;
}

double cloudwall::core::marketdata::json_string_to_double(
        rapidjson::GenericObject<true, rapidjson::GenericValue<rapidjson::UTF8<char>>> json, const char* field_name) {
    const char* val_txt = json[field_name].GetString();
    return fastparse_double(val_txt);
}

double cloudwall::core::marketdata::json_string_to_double(const rapidjson::Document& json, const char* field_name) {
    const char* val_txt = json[field_name].GetString();
    return fastparse_double(val_txt);
}
