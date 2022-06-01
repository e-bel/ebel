"""API methods."""
import connexion
import webbrowser

from flask_cors import CORS

application = connexion.FlaskApp(__name__)
application.add_api('openapi.yml')

CORS(application.app, expose_headers=["Content-Disposition"])


def run(host: str = '0.0.0.0', port: int = 5000, debug_mode: bool = True, open_browser: bool = False):
    """Run the API server.

    Parameters
    ----------
    host: str
        Server or host for the API service.
    port: int
        The defined port to run the API server.
    debug_mode: bool
        Whether bebug mode should be enabled.
    open_browser: bool
        If True, automatically opens browser to API UI.
    """
    url = f'http://{host}:{port}/ui'
    if open_browser:
        webbrowser.open(url)
    print(f'Starting web server {url}')
    application.run(host=host, port=port, debug=debug_mode)


if __name__ == '__main__':
    run()
