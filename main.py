import os
import shutil
import tempfile
import certifi

from bid.ui.app import run_app


def _configure_certs():
    """Ensure CURL and requests use a certificate path without non-ASCII chars."""
    try:
        src = certifi.where()
        dst = os.path.join(tempfile.gettempdir(), "cacert.pem")
        if not os.path.exists(dst):
            shutil.copyfile(src, dst)
        os.environ.setdefault("CURL_CA_BUNDLE", dst)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", dst)
    except Exception as exc:
        print(f"Failed to configure certificates: {exc}")

if __name__ == "__main__":
    _configure_certs()
    run_app()
