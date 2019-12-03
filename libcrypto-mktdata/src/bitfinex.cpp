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

#include <iostream>

#include <boost/algorithm/string.hpp>

#include <cloudwall/crypto-mktdata/bitfinex.h>

using namespace cloudwall::bitfinex::marketdata;

using cloudwall::core::marketdata::Channel;
using cloudwall::core::marketdata::RawFeedMessage;

BitfinexRawFeedClient::BitfinexRawFeedClient(const Subscription& subscription, const OnRawFeedMessageCallback& callback)
        : RawFeedClient(new ix::WebSocket(), callback) {
    std::string url("wss://api-pub.bitfinex.com/ws/2");
    websocket_->setUrl(url);

    // Setup a callback to be fired when a message or an event (open, close, error) is received
    websocket_->setOnMessageCallback(
            [this, subscription](const ix::WebSocketMessagePtr& msg)
            {
                if (msg->type == ix::WebSocketMessageType::Open) {
                    spdlog::info("Connected to Bitfinex exchange");

                    const std::list<Channel> &channels = subscription.get_channels();
                    for (auto channel_iter : channels) {
                        std::stringstream ss;
                        rapidjson::OStreamWrapper osw(ss);

                        rapidjson::Document d;
                        rapidjson::Pointer("/event").Set(d, "subscribe");

                        const std::string &channel = channel_iter.get_name();
                        auto channel_json_ptr = "/channel";
                        rapidjson::Pointer(channel_json_ptr).Set(d, channel.c_str());

                        auto ccy_pair_opt = channel_iter.get_ccy_pair();
                        if (ccy_pair_opt) {
                            auto ccy_pair = ccy_pair_opt.value();
                            auto quote_ccy = ccy_pair.get_quote_ccy().get_ccy_code();
                            auto base_ccy = ccy_pair.get_base_ccy().get_ccy_code();
                            auto ccy_pair_txt = fmt::format("t{1}{2}", channel, base_ccy, quote_ccy);
                            auto sym_json_ptr = "/symbol";
                            rapidjson::Pointer(sym_json_ptr).Set(d, ccy_pair_txt.c_str());
                        }

                        rapidjson::Writer<rapidjson::OStreamWrapper> writer(osw);
                        d.Accept(writer);

                        spdlog::info("Subscribing to channel: {}", ss.str().c_str());
                        this->websocket_->send(ss.str());
                    }
                } else if (msg->type == ix::WebSocketMessageType::Close) {
                    spdlog::info("Connection to Bitfinex closed");
                } else if (msg->type == ix::WebSocketMessageType::Message) {
                    SPDLOG_TRACE("Incoming message from Bitfinex: {}", msg->str.c_str());
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
