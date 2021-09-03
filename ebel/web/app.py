"""API methods."""
import connexion
import webbrowser

from flask_cors import CORS

application = connexion.FlaskApp(__name__)
application.add_api('openapi.yml')

CORS(application.app)


def run(port: int = 5000, debug_mode: bool = True, open_browser: bool = True):
    """Run the API server.

    Parameters
    ----------
    port: int
        The defined port to run the API server.
    debug_mode: bool
        Whether bebug mode should be enabled.
    open_browser: bool
        If True, automatically opens brower to API UI.
    """
    url = f'http://127.0.0.1:{port}/ui'
    if open_browser:
        webbrowser.open(url)
    print(f'Starting web server {url}')
    application.run(host='0.0.0.0', port=port, debug=debug_mode)


if __name__ == '__main__':
    run()
