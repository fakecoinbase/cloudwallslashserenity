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

#include <cloudwall/crypto-mktdata/bitmex.h>
#include <iostream>

using namespace cloudwall::bitmex::marketdata;
using cloudwall::core::marketdata::Channel;
using cloudwall::core::marketdata::RawFeedClient;
using cloudwall::core::marketdata::RawFeedMessage;

BitMexRawFeedClient::BitMexRawFeedClient(const Subscription& subscription, const OnRawFeedMessageCallback& callback)
        : RawFeedClient(new ix::WebSocket(), callback) {

    std::string url("wss://www.bitmex.com/realtime/");
    websocket_->setUrl(url);

    // Setup a callback to be fired when a message or an event (open, close, error) is received
    websocket_->setOnMessageCallback(
            [this, subscription](const ix::WebSocketMessagePtr& msg)
            {
                if (msg->type == ix::WebSocketMessageType::Open) {
                    spdlog::info("Connected to BitMEX exchange");

                    rapidjson::Document d;
                    rapidjson::Pointer("/op").Set(d, "subscribe");

                    int i = 0;
                    const std::list<Channel> &channels = subscription.get_channels();
                    for (auto channel_iter = channels.begin(); channel_iter != channels.end(); i++, channel_iter++) {
                        auto topic = (*channel_iter).get_name();
                        auto ccy_pair_opt = (*channel_iter).get_ccy_pair();
                        auto arg_json_ptr = fmt::format("/args/{0}", i);

                        if (ccy_pair_opt) {
                            auto ccy_pair = ccy_pair_opt.value();
                            auto ccy_pair_txt = fmt::format("{0}:{1}{2}", topic, ccy_pair.get_base_ccy().get_ccy_code(),
                                                            ccy_pair.get_quote_ccy().get_ccy_code());
                            rapidjson::Pointer(arg_json_ptr.c_str()).Set(d, ccy_pair_txt.c_str());
                        } else {
                            rapidjson::Pointer(arg_json_ptr.c_str()).Set(d, topic.c_str());
                        }
                    }

                    std::stringstream ss;
                    rapidjson::OStreamWrapper osw(ss);
                    rapidjson::Writer<rapidjson::OStreamWrapper> writer(osw);
                    d.Accept(writer);

                    spdlog::info("Subscribing to channel: {}", ss.str().c_str());
                    this->websocket_->send(ss.str());
                } else if (msg->type == ix::WebSocketMessageType::Close) {
                    spdlog::info("Connection to BitMEX closed");
                } else if (msg->type == ix::WebSocketMessageType::Message) {
                    SPDLOG_TRACE("Incoming message from BitMEX: {}", msg->str.c_str());
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
