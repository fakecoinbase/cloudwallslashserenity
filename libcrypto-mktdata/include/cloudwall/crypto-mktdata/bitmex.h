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

#ifndef CRYPTO_MKTDATA_BITMEX_H
#define CRYPTO_MKTDATA_BITMEX_H

#include <cloudwall/crypto-mktdata/core.h>

using cloudwall::core::marketdata::OnRawFeedMessageCallback;
using cloudwall::core::marketdata::RawFeedClient;
using cloudwall::core::marketdata::Subscription;

/// @brief BitMEX websocket API
/// @see https://www.bitmex.com/app/wsAPI
namespace cloudwall::bitmex::marketdata {
    class BitMexRawFeedClient : public RawFeedClient {
    public:
        BitMexRawFeedClient(const Subscription& subscription, const OnRawFeedMessageCallback& callback);

        ~BitMexRawFeedClient() = default;
    };
}

#endif //CRYPTO_MKTDATA_BITMEX_H
