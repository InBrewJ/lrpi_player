import pytest
from Server import appFactory
import os
from time import sleep


@pytest.fixture()
def app():
    current_working_directory = os.getcwd()

    os.environ["LRPI_SETTINGS_PATH"] = f"{current_working_directory}/pytest_faux_usb/settings.json"

    app = appFactory()
    app.config.update({
        "TESTING": True,
    })

    # other setup can go here

    yield app

    # clean up / reset resources here


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


class TestLrpiPlayerSmokeTests:
    def test_server_starts(self, client):
        response = client.get("/status")

        # the server returns an error when it first starts
        # bad design (so far!) but this is what we expect
        assert b"1" in response.data

    def test_server_returns_tracklist(self, client):

        response = client.get("/get-track-list")

        expected_track_list = [
            {
                'ID': 'b4f1020c48a28b3cdf6be408c4f585d7', 'IsDir': True, 'MimeType': 'inode/directory', 'ModTime': '2023-02-24T17:15:40.908032Z', 'Name': 'Misophonia', 'Path': 'Misophonia', 'Size': -1
            },
            {
                'ID': '3eb6e775e805ceae25d1a654de85c467', 'IsDir': True, 'MimeType': 'inode/directory',
                'ModTime': '2023-02-24T17:15:40.920031Z', 'Name': 'Synthesia', 'Path': 'Synthesia', 'Size': -1
            },
            {
                'ID': '494c2af90288e87f304b0e2a3e37d65d', 'IsDir': True, 'MimeType': 'inode/directory', 'ModTime': '2023-02-24T17:15:40.892035Z', 'Name': 'Tales_of_Bath', 'Path': 'Tales_of_Bath', 'Size': -1
            }
        ]

        assert response.json == expected_track_list

    def test_server_returns_tablet_ui(self, client):
        response = client.get("/")

        assert response.status_code == 200

    def test_server_returns_status(self, client):
        client.get("/get-track-list")
        response = client.get("/status")

        expected_track_list = [
            {
                'ID': 'b4f1020c48a28b3cdf6be408c4f585d7', 'IsDir': True, 'MimeType': 'inode/directory', 'ModTime': '2023-02-24T17:15:40.908032Z', 'Name': 'Misophonia', 'Path': 'Misophonia', 'Size': -1
            },
            {
                'ID': '3eb6e775e805ceae25d1a654de85c467', 'IsDir': True, 'MimeType': 'inode/directory',
                'ModTime': '2023-02-24T17:15:40.920031Z', 'Name': 'Synthesia', 'Path': 'Synthesia', 'Size': -1
            },
            {
                'ID': '494c2af90288e87f304b0e2a3e37d65d', 'IsDir': True, 'MimeType': 'inode/directory', 'ModTime': '2023-02-24T17:15:40.892035Z', 'Name': 'Tales_of_Bath', 'Path': 'Tales_of_Bath', 'Size': -1
            }
        ]

        expected_status = {
            'canControl': True,
            'error': '',
            'master_ip': '',
            'paired': False,
            'playerState': '',
            'playerType': 'VLC',
            'playlist': expected_track_list,
            'position': -0.001,
            'slave_url': None,
            'source': '',
            'subsPath': '',
            'trackDuration': 0,
            'volume': 0
        }

        assert response.json == expected_status

    def test_server_plays_one_track_no_lights(self, client):
        known_folder_id = "b4f1020c48a28b3cdf6be408c4f585d7"
        known_track_id = "a4a2ea32026a9a858de80d944a0c7f98"

        client.get("/get-track-list")
        client.get(
            f"/get-track-list?id={known_folder_id}")

        client.get(f"/play-single-track?id={known_track_id}")

        sleep(4)

        status_response = client.get("/status")

        expected_playlist = [
            {
                'ID': 'a4a2ea32026a9a858de80d944a0c7f98', 'IsDir': False, 'MimeType': 'video/mp4',
                'ModTime': '2023-02-24T17:15:40.908032Z', 'Name': 'ff-16b-2c-folder2.mp4', 'Path': 'ff-16b-2c-folder2.mp4', 'Size': 3079106
            }
        ]

        status_response = status_response.json

        assert status_response['canControl'] == True
        assert status_response['playerState'] == 'Playing'
        assert status_response['trackDuration'] == 187.11
        assert status_response['position'] > 0
        assert status_response['playlist'] == expected_playlist
        assert status_response['volume'] > 20
        assert "ff-16b-2c-folder2.mp4" in status_response['source']

    def test_server_skip_forward_works(self, client):
        known_folder_id = "b4f1020c48a28b3cdf6be408c4f585d7"
        known_track_id = "a4a2ea32026a9a858de80d944a0c7f98"

        client.get("/stop")

        client.get("/get-track-list")
        client.get(
            f"/get-track-list?id={known_folder_id}")

        client.get(f"/play-single-track?id={known_track_id}")

        sleep(4)

        # skip forward to the same track
        client.get(f"/crossfade?id={known_track_id}&interval=4")

        sleep(4)

        status_response = client.get("/status")

        print("* stat" * 30)
        print(status_response)
        print("*" * 30)

        status_response = status_response.json

        assert status_response['canControl'] == True
        assert status_response['playerState'] == 'Playing'
        assert status_response['trackDuration'] == 187.11
        assert status_response['position'] > 0
        assert status_response['volume'] == 70
        assert "ff-16b-2c-folder2.mp4" in status_response['source']