#include <cloudwall/crypto-mktdata/websocket_client.h>

/// Verify that one of the subject alternative names matches the given hostname
bool verify_subject_alternative_name(const char * hostname, X509 * cert) {
    STACK_OF(GENERAL_NAME) * san_names = nullptr;

    san_names = (STACK_OF(GENERAL_NAME) *) X509_get_ext_d2i(cert, NID_subject_alt_name, nullptr, nullptr);
    if (san_names == nullptr) {
        return false;
    }

    int san_names_count = sk_GENERAL_NAME_num(san_names);

    bool result = false;

    for (int i = 0; i < san_names_count; i++) {
        const GENERAL_NAME * current_name = sk_GENERAL_NAME_value(san_names, i);

        if (current_name->type != GEN_DNS) {
            continue;
        }

        char * dns_name = (char *) ASN1_STRING_get0_data(current_name->d.dNSName);

        // Make sure there isn't an embedded NUL character in the DNS name
        if (ASN1_STRING_length(current_name->d.dNSName) != strlen(dns_name)) {
            break;
        }
        // Compare expected hostname with the CN
        result = (strcasecmp(hostname, dns_name) == 0);
    }
    sk_GENERAL_NAME_pop_free(san_names, GENERAL_NAME_free);

    return result;
}

/// Verify that the certificate common name matches the given hostname
bool verify_common_name(const char * hostname, X509 * cert) {
    // Find the position of the CN field in the Subject field of the certificate
    int common_name_loc = X509_NAME_get_index_by_NID(X509_get_subject_name(cert), NID_commonName, -1);
    if (common_name_loc < 0) {
        return false;
    }

    // Extract the CN field
    X509_NAME_ENTRY * common_name_entry = X509_NAME_get_entry(X509_get_subject_name(cert), common_name_loc);
    if (common_name_entry == nullptr) {
        return false;
    }

    // Convert the CN field to a C string
    ASN1_STRING * common_name_asn1 = X509_NAME_ENTRY_get_data(common_name_entry);
    if (common_name_asn1 == nullptr) {
        return false;
    }

    char * common_name_str = (char *) ASN1_STRING_get0_data(common_name_asn1);

    // Make sure there isn't an embedded NUL character in the CN
    if (ASN1_STRING_length(common_name_asn1) != strlen(common_name_str)) {
        return false;
    }

    // Compare expected hostname with the CN
    std::string common_name_pattern = common_name_str;
    common_name_pattern = std::regex_replace( common_name_pattern, std::regex("\\*"), "[^.]+");
    auto common_name_regex = std::regex(common_name_pattern);
    return regex_match(hostname, common_name_regex);
}

/**
 * This code is derived from examples and documentation found ato00po
 * http://www.boost.org/doc/libs/1_61_0/doc/html/boost_asio/example/cpp03/ssl/client.cpp
 * and
 * https://github.com/iSECPartners/ssl-conservatory
 */
bool verify_certificate(const char * hostname, bool preverified, boost::asio::ssl::verify_context& ctx) {
    // The verify callback can be used to check whether the certificate that is
    // being presented is valid for the peer. For example, RFC 2818 describes
    // the steps involved in doing this for HTTPS. Consult the OpenSSL
    // documentation for more details. Note that the callback is called once
    // for each certificate in the certificate chain, starting from the root
    // certificate authority.

    // Retrieve the depth of the current cert in the chain. 0 indicates the
    // actual server cert, upon which we will perform extra validation
    // (specifically, ensuring that the hostname matches. For other certs we
    // will use the 'preverified' flag from Asio, which incorporates a number of
    // non-implementation specific OpenSSL checking, such as the formatting of
    // certs and the trusted status based on the CA certs we imported earlier.
    int depth = X509_STORE_CTX_get_error_depth(ctx.native_handle());

    // if we are on the final cert and everything else checks out, ensure that
    // the hostname is present on the list of SANs or the common name (CN).
    if (depth == 0 && preverified) {
        X509* cert = X509_STORE_CTX_get_current_cert(ctx.native_handle());

        return verify_subject_alternative_name(hostname, cert) ? true
                                                               : verify_common_name(hostname, cert);
    }

    return preverified;
}

context_ptr on_tls_init(const char * hostname, const websocketpp::connection_hdl&) {
    context_ptr ctx = websocketpp::lib::make_shared<boost::asio::ssl::context>(boost::asio::ssl::context::tlsv12);

    try {
        ctx->set_options(boost::asio::ssl::context::default_workarounds | // NOLINT(hicpp-signed-bitwise)
                         boost::asio::ssl::context::no_sslv2 |
                         boost::asio::ssl::context::no_sslv3 |
                         boost::asio::ssl::context::single_dh_use);


        ctx->set_verify_mode(boost::asio::ssl::verify_peer);
        ctx->set_verify_callback(bind(&verify_certificate, hostname, ::_1, ::_2));

        // Here we load the CA certificates of all CA's that this client trusts.
        boost::filesystem::path pem_path = boost::filesystem::path("/etc/ssl/certs/ca-certificates.crt");
        if (boost::filesystem::exists(pem_path)) {
            ctx->load_verify_file(pem_path.string());
        } else {
            ctx->load_verify_file("/etc/ssl/cert.pem");
        }
    } catch (std::exception& e) {
        std::cout << e.what() << std::endl;
    }
    return ctx;
}

cloudwall::websocket::Websocket::Websocket(const std::string &uri, boost::asio::io_context *ioc, SSLContext *ssl_ctx)
        : uri_(uri) {
    this->client_ = new client();
    client_->set_access_channels(websocketpp::log::alevel::all);
    client_->clear_access_channels(websocketpp::log::alevel::frame_payload);
    client_->set_error_channels(websocketpp::log::elevel::all);
    client_->set_tls_init_handler(bind(&on_tls_init, ssl_ctx->get_hostname().c_str(), ::_1));
    client_->init_asio(ioc);
}

void cloudwall::websocket::Websocket::set_on_open_callback(std::function<void(Websocket *)> callback) {
    client_->set_open_handler([this, callback](const websocketpp::connection_hdl& hdl) {
        callback(this);
    });
}

void cloudwall::websocket::Websocket::set_on_message_callback(std::function<void(Websocket *,
        const WebsocketMessage *)> callback) {
    client_->set_message_handler([this, callback](const websocketpp::connection_hdl& hdl,
            const client::message_ptr& msg) {
        callback(this, new WebsocketMessage(msg->get_payload()));
    });
}

void cloudwall::websocket::Websocket::set_on_close_callback(std::function<void(Websocket *)> callback) {
    client_->set_close_handler([this, callback](const websocketpp::connection_hdl& hdl) {
        callback(this);
    });
}

void cloudwall::websocket::Websocket::connect() {
    websocketpp::lib::error_code ec;
    conn_ = client_->get_connection(uri_, ec);
    client_->connect(conn_);
}

void cloudwall::websocket::Websocket::send(const std::string &payload) {
    conn_->send(payload, websocketpp::frame::opcode::text);
}

void cloudwall::websocket::Websocket::disconnect() {
    conn_->close(websocketpp::close::status::normal, "disconnecting");
}

