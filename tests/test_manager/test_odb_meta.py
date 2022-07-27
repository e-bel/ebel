"""ODB interface tests."""

from .constants import test_client, USER, PASSWORD, SERVER, PORT, DB_NAME

bel = test_client


class TestConfig:
    """Test class for configuration settings."""

    def test_connection_params(self):
        """Test that the proper connection parameters are being called and used during client initialization."""
        default_params = {"name": DB_NAME, "user": USER, "password": PASSWORD, "server": SERVER, "port": PORT}
        client_config = {"name": bel.odb_db_name,
                         "user": bel.odb_user,
                         "password": bel.odb_password,
                         "server": bel.odb_server,
                         "port": bel.odb_port}

        # Check that the client configuration paramaters match the default ones initialized for testing
        assert all([client_config[param] == value for param, value in default_params.items()])
