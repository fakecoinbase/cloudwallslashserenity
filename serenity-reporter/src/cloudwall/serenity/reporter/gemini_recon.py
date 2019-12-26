import fire
import gemini


def reconcile_gemini(gemini_api_key: str, gemini_api_secret: str):
    client = gemini.PrivateClient(gemini_api_key, gemini_api_secret)
    print(client.get_past_trades("BTCUSD"))
    print(client.api_query('/v1/transfers', {})
)


if __name__ == '__main__':
    fire.Fire(reconcile_gemini)
