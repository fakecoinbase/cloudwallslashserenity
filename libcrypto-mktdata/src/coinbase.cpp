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

#include <cloudwall/crypto-mktdata/coinbase.h>

using namespace cloudwall::coinbase::marketdata;

using cloudwall::core::marketdata::kSideByName;
using cloudwall::core::marketdata::json_string_to_double;
using cloudwall::core::marketdata::Channel;
using cloudwall::core::marketdata::RawFeedMessage;

CoinbaseRawFeedClient::CoinbaseRawFeedClient(const Subscription& subscription,
        const OnRawFeedMessageCallback& callback) : RawFeedClient(new ix::WebSocket(), callback) {
    std::string url("wss://ws-feed.pro.coinbase.com/");
    websocket_->setUrl(url);

    // Setup a callback to be fired when a message or an event (open, close, error) is received
    websocket_->setOnMessageCallback(
            [this, subscription](const ix::WebSocketMessagePtr& msg)
            {
                if (msg->type == ix::WebSocketMessageType::Open) {
                    spdlog::info("Connected to Coinbase Pro exchange");

                    const std::list<Channel> &channels = subscription.get_channels();
                    for (const auto& channel : channels) {
                        rapidjson::Document d;
                        rapidjson::Pointer("/type").Set(d, "subscribe");

                        auto channel_json_ptr = "/channels/0/name";
                        rapidjson::Pointer(channel_json_ptr).Set(d, channel.get_name().c_str());

                        auto ccy_pair_opt = channel.get_ccy_pair();
                        if (ccy_pair_opt) {
                            auto ccy_pair = ccy_pair_opt.value();
                            auto id_json_ptr = "/channels/0/product_ids/0";
                            auto ccy_pair_txt = fmt::format("{0}-{1}", ccy_pair.get_base_ccy().get_ccy_code(),
                                                            ccy_pair.get_quote_ccy().get_ccy_code());
                            rapidjson::Pointer(id_json_ptr).Set(d, ccy_pair_txt.c_str());
                        }

                        std::stringstream ss;
                        rapidjson::OStreamWrapper osw(ss);
                        rapidjson::Writer<rapidjson::OStreamWrapper> writer(osw);
                        d.Accept(writer);

                        spdlog::info("Subscribing to channel: {}", ss.str().c_str());
                        this->websocket_->send(ss.str());
                    }
                } else if (msg->type == ix::WebSocketMessageType::Close) {
                    spdlog::info("Connection to Coinbase Pro closed");
                } else if (msg->type == ix::WebSocketMessageType::Message) {
                    SPDLOG_TRACE("Incoming message from Coinbase Pro: {}", msg->str.c_str());
                    callback_(RawFeedMessage(msg->str));
                } else if (msg->type == ix::WebSocketMessageType::Error) {
                    std::stringstream ss;
                    ss << "Connection error: " << msg->errorInfo.reason << std::endl;
                    ss << "# retries: " << msg->errorInfo.retries << std::endl;
                    ss << "Wait time (ms): " << msg->errorInfo.wait_time << std::endl;
                    ss << "HTTP Status: " << msg->errorInfo.http_status << std::endl;
                    spdlog::info(ss.str());
                } else if (msg->type == ix::WebSocketMessageType::Pong) {
                     spdlog::debug("received pong message");
                } else {
                    spdlog::error("Unknown message type");
                }
            });
}

CoinbaseEventClient::CoinbaseEventClient(const Subscription& subscription, const OnCoinbaseEventCallback& callback) {
    OnRawFeedMessageCallback raw_callback = [callback](const RawFeedMessage& message) {
        auto d = rapidjson::Document();
        const auto& raw_json = message.get_raw_json();
        d.Parse(raw_json.c_str());

        auto event_type = d["type"].GetString();
        if (strncmp("status", event_type, 6) == 0) {
            callback(ProductStatusEvent(d));
        } else if (strncmp("match", event_type, 5) == 0) {
            callback(MatchEvent(d));
        } else if (strncmp("ticker", event_type, 6) == 0) {
            callback(TickerEvent(d));
        }
    };
    this->raw_feed_client_ = new CoinbaseRawFeedClient(subscription, raw_callback);
}

ProductStatus::ProductStatus(rapidjson::Value::ConstValueIterator product_json_iter) {
    auto product_json = product_json_iter->GetObject();

    std::string base_ccy_id = product_json["base_currency"].GetString();
    std::string quote_ccy_id = product_json["quote_currency"].GetString();
    auto base_ccy = Currency(base_ccy_id);
    auto quote_ccy = Currency(quote_ccy_id);

    this->id_ = new std::string(product_json["id"].GetString());
    this->ccy_pair_ = new CurrencyPair(base_ccy, quote_ccy);
    this->base_min_size_ = json_string_to_double(product_json, "base_min_size");
    this->base_max_size_ = json_string_to_double(product_json, "base_max_size");
    this->base_increment_ = json_string_to_double(product_json, "base_increment");
    this->quote_increment_ = json_string_to_double(product_json, "quote_increment");
    this->min_market_funds_ = json_string_to_double(product_json, "min_market_funds");
    this->max_market_funds_ = json_string_to_double(product_json, "max_market_funds");
    this->margin_enabled_ = product_json["margin_enabled"].GetBool();
    this->limit_only_ = product_json["limit_only"].GetBool();
    this->cancel_only_ = product_json["cancel_only"].GetBool();
    this->post_only_ = product_json["post_only"].GetBool();

    this->status_ = new std::string(product_json["status"].GetString());
    this->status_message_ = new std::string(product_json["status_message"].GetString());
}

ProductStatus::~ProductStatus() {
    delete id_;
    delete ccy_pair_;
    delete status_;
    delete status_message_;
}

ProductStatusEvent::ProductStatusEvent(const std::string& raw_json) {
    this->products_ = new std::list<ProductStatus*>();
    auto d = rapidjson::Document();
    d.Parse(raw_json.c_str());
    init(d);
}

ProductStatusEvent::ProductStatusEvent(const rapidjson::Document& doc) {
    this->products_ = new std::list<ProductStatus*>();
    init(doc);
}

void ProductStatusEvent::init(const rapidjson::Document& doc) {
    const rapidjson::Value& products = doc["products"];
    for (rapidjson::Value::ConstValueIterator itr = products.Begin(); itr != products.End(); ++itr) {
        this->products_->emplace_back(new ProductStatus(itr));
    }
}

ProductStatusEvent::~ProductStatusEvent() {
    delete this->products_;
}

MatchEvent::MatchEvent(const rapidjson::Document& json) {
    this->trade_id_ = json["trade_id"].GetInt64();
    this->sequence_num_ = json["sequence"].GetInt64();
    this->maker_order_id_ = new std::string(json["maker_order_id"].GetString());
    this->taker_order_id_ = new std::string(json["taker_order_id"].GetString());
    this->size_ = json_string_to_double(json, "size");
    this->price_ = json_string_to_double(json, "price");
    this->timestamp_txt_ = new std::string(json["time"].GetString());

    // look up Side enum by name
    auto side_txt = json["side"].GetString();
    this->side_ = &kSideByName[side_txt];

    // we should cache the parsed CurrencyPair in a map for performance; ideally there should be only
    // one Currency per string currency code and one CurrencyPair per unique pair of currency codes
    auto product_id = json["product_id"].GetString();
    std::vector<std::string> product_id_parts;
    boost::split(product_id_parts, product_id, [](wchar_t ch) -> bool { return ch == (wchar_t) '-'; });
    std::string base_ccy_txt = product_id_parts[0];
    std::string quote_ccy_txt = product_id_parts[1];
    Currency base_ccy = Currency(base_ccy_txt);
    Currency quote_ccy = Currency(quote_ccy_txt);
    this->ccy_pair_ = new CurrencyPair(base_ccy, quote_ccy);
}

const std::chrono::system_clock::time_point* MatchEvent::parse_timstamp() const {
    auto tp = new std::chrono::system_clock::time_point();
    std::istringstream ss{*this->timestamp_txt_};
    ss >> date::parse("%FT%TZ", *tp);
    return tp;
}

MatchEvent::~MatchEvent() {
    delete this->maker_order_id_;
    delete this->taker_order_id_;
    delete this->timestamp_txt_;
}

TickerEvent::TickerEvent(const rapidjson::Document& json) {
    if (json.HasMember("trade_id")) {
        this->last_trade_id_ = std::move(std::optional<long>(json["trade_id"].GetInt64()));
    } else {
        this->last_trade_id_ = std::nullopt;
    }

    this->sequence_num_ = json["sequence"].GetInt64();

    this->best_bid_ = json_string_to_double(json, "best_bid");
    this->best_ask_ = json_string_to_double(json, "best_ask");
    this->open_24h_ = json_string_to_double(json, "open_24h");
    this->high_24h_ = json_string_to_double(json, "high_24h");
    this->low_24h_ = json_string_to_double(json, "low_24h");
    this->volume_24h_ = json_string_to_double(json, "volume_24h");
    this->volume_30d_ = json_string_to_double(json, "volume_30d");

    if (json.HasMember("last_size")) {
        auto last_size = json_string_to_double(json, "last_size");
        this->last_size_ = std::move(std::optional<double>(last_size));
    } else {
        this->last_size_ = std::nullopt;
    }
    this->last_price_ = json_string_to_double(json, "price");

    if (json.HasMember("time")) {
        auto timestamp_txt = new std::string(json["time"].GetString());
        this->timestamp_txt_ = std::move(std::optional<std::string*>(timestamp_txt));
    } else {
        this->timestamp_txt_ = std::nullopt;
    }

    // look up Side enum by name
    if (json.HasMember("side")) {
        auto side_txt = json["side"].GetString();
        this->last_trade_side_ = std::move(std::optional<Side*>(&kSideByName[side_txt]));
    } else {
        this->last_trade_side_ = std::nullopt;
    }

    // same as above, we should cache the parsed CurrencyPair in a map for performance
    auto product_id = json["product_id"].GetString();
    std::vector<std::string> product_id_parts;
    boost::split(product_id_parts, product_id, [](wchar_t ch) -> bool { return ch == (wchar_t) '-'; });
    std::string base_ccy_txt = product_id_parts[0];
    std::string quote_ccy_txt = product_id_parts[1];
    Currency base_ccy = Currency(base_ccy_txt);
    Currency quote_ccy = Currency(quote_ccy_txt);
    this->ccy_pair_ = new CurrencyPair(base_ccy, quote_ccy);
}

const std::chrono::system_clock::time_point* TickerEvent::parse_timstamp() const {
    if (!this->timestamp_txt_) {
        return nullptr;
    } else {
        auto tp = new std::chrono::system_clock::time_point();
        std::istringstream ss{**this->timestamp_txt_};
        ss >> date::parse("%FT%TZ", *tp);
        return tp;
    }
}

TickerEvent::~TickerEvent() {
    delete this->ccy_pair_;
    if (this->timestamp_txt_) {
        delete this->timestamp_txt_.value();
    }
}
