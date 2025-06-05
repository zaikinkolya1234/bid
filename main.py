"""Application entry point."""

from bid.ui.app import run_app

# Data is fetched from the MOEX ISS API for stocks and from the Coingecko API
# for cryptocurrencies (prices are requested in USD). These services provide
# open HTTP endpoints that can be queried without authentication.

if __name__ == "__main__":
    run_app()
