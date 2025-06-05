"""Application entry point."""

from bid.ui.app import run_app

# Data is fetched from the MOEX ISS API for stocks and from Coingecko for
# cryptocurrencies. These services provide open HTTP endpoints that can be
# queried without authentication.

if __name__ == "__main__":
    run_app()
