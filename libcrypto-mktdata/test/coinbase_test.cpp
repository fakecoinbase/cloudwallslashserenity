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

#pragma clang diagnostic push
#pragma ide diagnostic ignored "cert-err58-cpp"

#include <chrono>
#include <thread>

#include <boost/filesystem/fstream.hpp>
#include <gtest/gtest.h>

#include <cloudwall/crypto-mktdata/coinbase.h>

using namespace std::chrono_literals;

using cloudwall::coinbase::marketdata::CoinbaseEvent;
using cloudwall::coinbase::marketdata::CoinbaseEventClient;
using cloudwall::coinbase::marketdata::CoinbaseRawFeedClient;
using cloudwall::coinbase::marketdata::MatchEvent;
using cloudwall::coinbase::marketdata::OnCoinbaseEventCallback;
using cloudwall::coinbase::marketdata::ProductStatusEvent;
using cloudwall::coinbase::marketdata::TickerEvent;
using cloudwall::core::marketdata::Channel;
using cloudwall::core::marketdata::Currency;
using cloudwall::core::marketdata::CurrencyPair;
using cloudwall::core::marketdata::RawFeedMessage;

TEST(CoinbaseProRawFeedClient, connect) {
    auto ccy_pair = CurrencyPair(Currency("BTC"), Currency("USD"));
    std::list<Channel> channels({
        Channel("status", { }),
        Channel("matches", ccy_pair),
        Channel("ticker", ccy_pair)
    });
    auto sub = Subscription(channels);
    int counter = 0;
    int* msg_count = &counter;
    const OnRawFeedMessageCallback& callback = [msg_count](const RawFeedMessage& msg) {
        (*msg_count)++;
        spdlog::info("Incoming message: {}", msg.get_raw_json());
        ASSERT_FALSE(msg.get_raw_json().empty());
    };
    auto client = CoinbaseRawFeedClient(sub, callback);
    client.connect();
    for (int i = 0; i < 5; i++) {
        std::this_thread::sleep_for(1s);
    }
    client.disconnect();
    ASSERT_TRUE(*msg_count > 0);
}

TEST(ProductStatusEvent, parse) {
    boost::filesystem::path test_path(__FILE__);
    boost::filesystem::path json_path = test_path.remove_filename().append("example_status_msg.json");
    boost::filesystem::ifstream ifs(json_path);

    std::stringstream sstr;
    sstr << ifs.rdbuf();
    auto event = ProductStatusEvent(sstr.str());
    auto first = event.get_products().front();

    ASSERT_EQ(48, event.get_products().size());
    ASSERT_EQ("ZEC-BTC", first->get_id());
    ASSERT_EQ("ZEC", first->get_currency_pair().get_base_ccy().get_ccy_code());
    ASSERT_DOUBLE_EQ(0.01, first->get_base_min_size());
    ASSERT_DOUBLE_EQ(1500, first->get_base_max_size());
    ASSERT_DOUBLE_EQ(0.0001, first->get_base_increment());
    ASSERT_DOUBLE_EQ(0.000001, first->get_quote_increment());
    ASSERT_DOUBLE_EQ(0.001, first->get_min_market_funds());
    ASSERT_DOUBLE_EQ(30, first->get_max_market_funds());
    ASSERT_FALSE(first->is_margin_enabled());
    ASSERT_FALSE(first->is_cancel_only());
    ASSERT_TRUE(first->is_limit_only());
    ASSERT_FALSE(first->is_post_only());
    ASSERT_EQ("online", first->get_status());
    ASSERT_EQ("", first->get_status_message());
}

TEST(MatchEvent, parse) {
    boost::filesystem::path test_path(__FILE__);
    boost::filesystem::path json_path = test_path.remove_filename().append("example_match_msg.json");
    boost::filesystem::ifstream ifs(json_path);

    std::stringstream sstr;
    sstr << ifs.rdbuf();
    auto doc = rapidjson::Document();
    doc.Parse(sstr.str().c_str());
    auto event = MatchEvent(doc);

    ASSERT_EQ(71767920, event.get_trade_id());
    ASSERT_EQ(10480841980, event.get_sequence_number());
    ASSERT_EQ("BTC", event.get_currency_pair().get_base_ccy().get_ccy_code());
    ASSERT_EQ("USD", event.get_currency_pair().get_quote_ccy().get_ccy_code());
    ASSERT_EQ(Side::sell, event.get_side());
    ASSERT_EQ("199d5dfe-f45b-4591-b635-6d8f585193e9", event.get_maker_order_id());
    ASSERT_EQ("116d20af-d723-4352-9398-d7b0e7c38a27", event.get_taker_order_id());
    ASSERT_DOUBLE_EQ(0.01671111, event.get_size());
    ASSERT_DOUBLE_EQ(11730.37, event.get_price());
    ASSERT_EQ("2019-08-08T16:09:40.587000Z", event.get_unparsed_timestamp());
    ASSERT_EQ(1565280580587000L, event.parse_timstamp()->time_since_epoch().count());
}

TEST(TickerEvent, parse) {
    boost::filesystem::path test_path(__FILE__);
    boost::filesystem::path json_path = test_path.remove_filename().append("example_ticker_msg.json");
    boost::filesystem::ifstream ifs(json_path);

    std::stringstream sstr;
    sstr << ifs.rdbuf();
    auto doc = rapidjson::Document();
    doc.Parse(sstr.str().c_str());
    auto event = TickerEvent(doc);

    ASSERT_EQ(71767920, event.get_last_trade_id().value());
    ASSERT_EQ(10480841980, event.get_sequence_number());
    ASSERT_EQ("BTC", event.get_currency_pair().get_base_ccy().get_ccy_code());
    ASSERT_EQ("USD", event.get_currency_pair().get_quote_ccy().get_ccy_code());
    ASSERT_EQ(Side::buy, *event.get_last_trade_side().value());
    ASSERT_DOUBLE_EQ(11730.36, event.get_best_bid_price());
    ASSERT_DOUBLE_EQ(11730.37, event.get_best_ask_price());
    ASSERT_NEAR(0.01, event.get_spread(), 0.001);
    ASSERT_DOUBLE_EQ(0.01671111, event.get_last_size().value());
    ASSERT_DOUBLE_EQ(11730.37, event.get_last_price());
    ASSERT_DOUBLE_EQ(11676.64, event.get_open_24h());
    ASSERT_DOUBLE_EQ(12088.00, event.get_high_24h());
    ASSERT_DOUBLE_EQ(11400.00, event.get_low_24h());
    ASSERT_DOUBLE_EQ(16759.18480858, event.get_volume_24h());
    ASSERT_DOUBLE_EQ(610078.3142738, event.get_volume_30d());
    ASSERT_EQ("2019-08-08T16:09:40.587000Z", *event.get_unparsed_timestamp().value());
    ASSERT_EQ(1565280580587000L, event.parse_timstamp()->time_since_epoch().count());
}

TEST(TickerEvent, parse_no_trade) {
    boost::filesystem::path test_path(__FILE__);
    boost::filesystem::path json_path = test_path.remove_filename().append("example_ticker_no_trade_msg.json");
    boost::filesystem::ifstream ifs(json_path);

    std::stringstream sstr;
    sstr << ifs.rdbuf();
    auto doc = rapidjson::Document();
    doc.Parse(sstr.str().c_str());
    auto event = TickerEvent(doc);

    ASSERT_FALSE(event.get_last_trade_id());
    ASSERT_EQ(10515750558, event.get_sequence_number());
    ASSERT_EQ("BTC", event.get_currency_pair().get_base_ccy().get_ccy_code());
    ASSERT_EQ("USD", event.get_currency_pair().get_quote_ccy().get_ccy_code());
    ASSERT_DOUBLE_EQ(11383.29, event.get_best_bid_price());
    ASSERT_DOUBLE_EQ(11384.84, event.get_best_ask_price());
    ASSERT_NEAR(1.55, event.get_spread(), 0.001);
    ASSERT_FALSE(event.get_last_trade_side());
    ASSERT_FALSE(event.get_last_size());
    ASSERT_DOUBLE_EQ(11388.13, event.get_last_price());
    ASSERT_DOUBLE_EQ(11401.69, event.get_open_24h());
    ASSERT_DOUBLE_EQ(11469.15, event.get_high_24h());
    ASSERT_DOUBLE_EQ(11088.88, event.get_low_24h());
    ASSERT_DOUBLE_EQ(8375.54663903, event.get_volume_24h());
    ASSERT_DOUBLE_EQ(550988.56550277, event.get_volume_30d());
    ASSERT_FALSE(event.get_unparsed_timestamp());
    ASSERT_FALSE(event.parse_timstamp());
}

TEST(CoinbaseEventClient, product_status_only) {
    std::list<Channel> channels({
            Channel("status", { })
    });
    auto sub = Subscription(channels);
    int counter = 0;
    auto msg_count = &counter;
    const OnCoinbaseEventCallback& callback = [msg_count](const CoinbaseEvent& event) {
      if (CoinbaseEvent::EventType::status == event.getCoinbaseEventType()) {
          (*msg_count)++;
          const auto& specific = dynamic_cast<const ProductStatusEvent&>(event);
          ASSERT_TRUE(!specific.get_products().empty());
      } else {
          FAIL();
      }
    };
    auto client = CoinbaseEventClient(sub, callback);
    client.connect();
    for (int i = 0; i < 5; i++) {
        std::this_thread::sleep_for(1s);
    }
    client.disconnect();
    ASSERT_TRUE(*msg_count > 0);
}

TEST(CoinbaseEventClient, matches_only) {
    auto ccy_pair = CurrencyPair(Currency("BTC"), Currency("USD"));
    std::list<Channel> channels({
            Channel("match", ccy_pair)
    });
    auto sub = Subscription(channels);
    const OnCoinbaseEventCallback& callback = [](const CoinbaseEvent& event) {
      if (CoinbaseEvent::EventType::match == event.getCoinbaseEventType()) {
          const auto& specific = dynamic_cast<const MatchEvent&>(event);
          ASSERT_EQ("BTC", specific.get_currency_pair().get_base_ccy().get_ccy_code());
          ASSERT_EQ("USD", specific.get_currency_pair().get_quote_ccy().get_ccy_code());
      } else {
          FAIL();
      }
    };
    auto client = CoinbaseEventClient(sub, callback);
    client.connect();
    for (int i = 0; i < 5; i++) {
        std::this_thread::sleep_for(1s);
    }
    client.disconnect();
}

TEST(CoinbaseEventClient, ticker_only) {
    auto ccy_pair = CurrencyPair(Currency("BTC"), Currency("USD"));
    std::list<Channel> channels({
            Channel("ticker", ccy_pair)
    });
    auto sub = Subscription(channels);
    int counter = 0;
    int* msg_count = &counter;
    const OnCoinbaseEventCallback& callback = [msg_count](const CoinbaseEvent& event) {
      if (CoinbaseEvent::EventType::ticker == event.getCoinbaseEventType()) {
          (*msg_count)++;
          const auto& specific = dynamic_cast<const TickerEvent&>(event);
          ASSERT_EQ("BTC", specific.get_currency_pair().get_base_ccy().get_ccy_code());
          ASSERT_EQ("USD", specific.get_currency_pair().get_quote_ccy().get_ccy_code());
      } else {
          FAIL();
      }
    };
    auto client = CoinbaseEventClient(sub, callback);
    client.connect();
    for (int i = 0; i < 5; i++) {
        std::this_thread::sleep_for(1s);
    }
    client.disconnect();
    ASSERT_TRUE(*msg_count > 0);
}
