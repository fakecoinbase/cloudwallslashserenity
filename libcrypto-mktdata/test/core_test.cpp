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
#include <cloudwall/crypto-mktdata/core.h>

using namespace std::chrono_literals;
using namespace cloudwall::core::marketdata;

TEST(Currency, init) {
    Currency ccy1 = Currency("BTC");
    Currency ccy2 = Currency("ETH");

    ASSERT_EQ("BTC", ccy1.get_ccy_code());
    ASSERT_EQ("ETH", ccy2.get_ccy_code());
    ASSERT_TRUE(ccy1 == ccy1);
    ASSERT_FALSE(ccy1 == ccy2);
}

TEST(ProductId, init) {
    Currency ccy1 = Currency("BTC");
    Currency ccy2 = Currency("ETH");
    Currency ccy3 = Currency("USD");
    CurrencyPair p1 = CurrencyPair(ccy1, ccy3);
    CurrencyPair p2 = CurrencyPair(ccy2, ccy3);

    ASSERT_EQ("BTC", p1.get_base_ccy().get_ccy_code());
    ASSERT_EQ("ETH", p2.get_base_ccy().get_ccy_code());
    ASSERT_EQ("USD", p1.get_quote_ccy().get_ccy_code());
    ASSERT_EQ("USD", p2.get_quote_ccy().get_ccy_code());
    ASSERT_TRUE(p1 == p1);
    ASSERT_FALSE(p1 == p2);
}

TEST(Side, lookup) {
    Side buy = kSideByName["buy"];
    Side sell = kSideByName["sell"];

    ASSERT_EQ(Side::buy, buy);
    ASSERT_EQ(Side::sell, sell);
}