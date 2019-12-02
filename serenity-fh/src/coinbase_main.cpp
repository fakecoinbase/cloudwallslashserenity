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

#include <spdlog/spdlog.h>

#include <cloudwall/crypto-mktdata/coinbase.h>
#include "../capnp/serenity-fh.capnp.h"

#include <capnp/message.h>
#include <capnp/serialize.h>
#include <zmq.hpp>

using cloudwall::coinbase::marketdata::CoinbaseEvent;
using cloudwall::coinbase::marketdata::CoinbaseEventClient;
using cloudwall::coinbase::marketdata::MatchEvent;
using cloudwall::coinbase::marketdata::OnCoinbaseEventCallback;
using cloudwall::core::marketdata::Channel;
using cloudwall::core::marketdata::Currency;
using cloudwall::core::marketdata::CurrencyPair;
using cloudwall::core::marketdata::Side;
using cloudwall::serenity::TradeMessage;

int main(int argc, const char *argv[]) {
    zmq::context_t context (1);
    zmq::socket_t publisher (context, ZMQ_PUB);
    publisher.bind("tcp://*:5556");

    auto ccy_pair = CurrencyPair(Currency("BTC"), Currency("USD"));
    std::list<Channel> channels({
            Channel("matches", ccy_pair),
    });
    auto sub = Subscription(channels);
    const OnCoinbaseEventCallback& callback = [&publisher](const CoinbaseEvent& event) {
      if (CoinbaseEvent::EventType::match==event.getCoinbaseEventType()) {
          const auto& specific = dynamic_cast<const MatchEvent&>(event);

          capnp::MallocMessageBuilder message;
          TradeMessage::Builder builder = message.initRoot<TradeMessage>();
          builder.setPrice(specific.get_price());
          builder.setSize(specific.get_size());

          const auto& ccy_pair = specific.get_currency_pair();
          builder.setTradedProductId(fmt::format("{0}-{1}/coinbase", ccy_pair.get_base_ccy().get_ccy_code(),
                  ccy_pair.get_quote_ccy().get_ccy_code()));

          // invert convention to match Coinbase Pro UI
          if (specific.get_side()==Side::buy) {
              builder.setSide(cloudwall::serenity::Side::SELL);
          } else {
              builder.setSide(cloudwall::serenity::Side::BUY);
          }
          kj::Array<capnp::word> words = messageToFlatArray(message);
          auto bytes = words.asBytes();
          publisher.send(bytes.begin(), bytes.size());
      }
    };

    auto client = CoinbaseEventClient(sub, callback);
    client.connect();
    spdlog::info("Coinbase Pro feed handler <READY>");

    while (publisher.connected()) {
        // continue subscribing to marketdata
    }
}
