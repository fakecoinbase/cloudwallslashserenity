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

#ifndef LIBCRYPTO_MKTDATA_WEBSOCKET_CLIENT_H
#define LIBCRYPTO_MKTDATA_WEBSOCKET_CLIENT_H

#include <boost/filesystem.hpp>
#include <websocketpp/config/asio_client.hpp>
#include <websocketpp/client.hpp>

#include <optional>
#include <regex>
#include <string>

typedef websocketpp::client<websocketpp::config::asio_tls_client> client;
typedef websocketpp::lib::shared_ptr<websocketpp::lib::asio::ssl::context> context_ptr;

using websocketpp::lib::placeholders::_1;
using websocketpp::lib::placeholders::_2;
using websocketpp::lib::bind;

namespace cloudwall::websocket {
    class SSLContext {
    public:
        explicit SSLContext(const std::string &hostname) : hostname_(hostname) {
        }

        const std::string &get_hostname() const {
            return hostname_;
        }

    private:
        const std::string &hostname_;
    };

    class WebsocketMessage {
    public:
        WebsocketMessage(std::string payload) : payload_(payload) {
        }

        const std::string &get_payload() const {
            return payload_;
        }

    private:
        std::string payload_;
    };

    class Websocket {
    public:
        Websocket(const std::string &uri, boost::asio::io_context *ioc, SSLContext *ssl_ctx);

        void set_on_open_callback(std::function<void(Websocket *)> callback);

        void set_on_message_callback(std::function<void(Websocket *, const WebsocketMessage *)> callback);

        void set_on_close_callback(std::function<void(Websocket *)> callback);

        void connect();

        void send(const std::string &payload);

        void disconnect();

    private:
        const std::string &uri_;
        client *client_;
        client::connection_ptr conn_;

    };
}

#endif //LIBCRYPTO_MKTDATA_WEBSOCKET_CLIENT_H
