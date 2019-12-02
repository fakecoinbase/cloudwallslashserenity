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

#include <gtest/gtest.h>
#include <cloudwall/crypto-mktdata/bitfinex.h>

using namespace std::chrono_literals;

using cloudwall::bitfinex::marketdata::BitfinexRawFeedClient;
using cloudwall::core::marketdata::Channel;
using cloudwall::core::marketdata::Currency;
using cloudwall::core::marketdata::CurrencyPair;
using cloudwall::core::marketdata::RawFeedMessage;

TEST(BitfinexRawFeedClient, connect) {
    auto ccy_pair = CurrencyPair(Currency("BTC"), Currency("USD"));
    std::list<Channel> channels ({
        Channel("trades", ccy_pair),
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
    auto client = BitfinexRawFeedClient(sub, callback);
    client.connect();
    for (int i = 0; i < 5; i++) {
        std::this_thread::sleep_for(1s);
    }
    client.disconnect();
    ASSERT_TRUE(*msg_count > 0);
}