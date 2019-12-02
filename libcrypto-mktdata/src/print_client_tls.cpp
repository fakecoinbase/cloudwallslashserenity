#include <cloudwall/crypto-mktdata/websocket_client.h>

int main(int argc, char* argv[]) {
    std::string hostname = "ws-feed.pro.coinbase.com";
    std::string uri = "wss://" + hostname;

    auto ioc = new boost::asio::io_context();
    auto ssl_ctx = new cloudwall::websocket::SSLContext(hostname);
    auto ws = cloudwall::websocket::Websocket(uri, ioc, ssl_ctx);
    ws.set_on_open_callback([](cloudwall::websocket::Websocket* ws) {
        ws->send("{\n"
                 "    \"type\": \"subscribe\",\n"
                 "    \"product_ids\": [\n"
                 "        \"ETH-USD\",\n"
                 "        \"ETH-EUR\"\n"
                 "    ],\n"
                 "    \"channels\": [\n"
                 "        \"matches\",\n"
                 "        \"heartbeat\",\n"
                 "        {\n"
                 "            \"name\": \"ticker\",\n"
                 "            \"product_ids\": [\n"
                 "                \"ETH-BTC\",\n"
                 "                \"ETH-USD\"\n"
                 "            ]\n"
                 "        }\n"
                 "    ]\n"
                 "}");
    });

    ws.set_on_message_callback([](const cloudwall::websocket::Websocket* ws,
            const cloudwall::websocket::WebsocketMessage *msg) {
        std::cout << msg->get_payload() << std::endl;
    });

    ws.connect();
    ioc->run();
}