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

#ifndef CRYPTO_MKTDATA_BINANCE_H
#define CRYPTO_MKTDATA_BINANCE_H

#include <cloudwall/crypto-mktdata/core.h>

using cloudwall::core::marketdata::OnRawFeedMessageCallback;
using cloudwall::core::marketdata::RawFeedClient;
using cloudwall::core::marketdata::Subscription;

/// @brief Binance websocket API
/// @see https://github.com/binance-exchange/binance-official-api-docs/blob/master/web-socket-streams.md
namespace cloudwall::binance::marketdata {
    class BinanceRawFeedClient : public RawFeedClient {
    public:
        BinanceRawFeedClient(const Subscription& subscription, const OnRawFeedMessageCallback& callback);

        ~BinanceRawFeedClient() = default;
    };
}

#endif //CRYPTO_MKTDATA_BINANCE_H
