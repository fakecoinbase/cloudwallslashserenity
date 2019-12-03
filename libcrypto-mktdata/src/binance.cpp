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

#include <boost/algorithm/string.hpp>

#include <cloudwall/crypto-mktdata/binance.h>

using namespace cloudwall::binance::marketdata;

using cloudwall::core::marketdata::Channel;
using cloudwall::core::marketdata::RawFeedMessage;

BinanceRawFeedClient::BinanceRawFeedClient(const Subscription& subscription,
                                           const OnRawFeedMessageCallback& callback)
            : RawFeedClient(new ix::WebSocket(), callback) {

    std::stringstream ss;
    ss << "wss://stream.binance.com:9443/stream?streams=";
    const std::list<Channel> &channels = subscription.get_channels();
    for (auto channel : channels) {
        spdlog::info("Subscribing to channel: {}", channel.get_name());
        auto base_ccy =  boost::algorithm::to_lower_copy(channel.get_ccy_pair().value().get_base_ccy().get_ccy_code());
        auto quote_ccy =  boost::algorithm::to_lower_copy(channel.get_ccy_pair().value().get_quote_ccy().get_ccy_code());
        ss << base_ccy << quote_ccy << "@" << channel.get_name() << "/";
    }
    auto url = ss.str();
    url.pop_back();
    websocket_->setUrl(url);

    // Setup a callback to be fired when a message or an event (open, close, error) is received
    websocket_->setOnMessageCallback(
            [this, subscription](const ix::WebSocketMessagePtr& msg)
            {
                if (msg->type == ix::WebSocketMessageType::Open) {
                    spdlog::info("Connected to Binance exchange");
                } else if (msg->type == ix::WebSocketMessageType::Close) {
                    spdlog::info("Connection to Binance closed");
                } else if (msg->type == ix::WebSocketMessageType::Message) {
                    SPDLOG_TRACE("Incoming message from Binance: {}", msg->str.c_str());
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
