import psycopg2
import yfinance

conn = psycopg2.connect(host="localhost", dbname="serenity", user="postgres", password="password")
cur = conn.cursor()

ticker = yfinance.Ticker("BTC-USD")
marks = ticker.history(period="max")

cur.execute("SELECT mark_type_id FROM serenity.mark_type WHERE mark_code = %s", ("YahooDailyClose",))
print(cur.fetchone())




