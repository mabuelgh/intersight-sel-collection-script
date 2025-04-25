#!/usr/bin/env python

"""
This script interacts with the Intersight API to collect and download System Event Logs (SEL)
from servers managed by Intersight or operating in standalone mode.

Key functionalities:
- Retrieve a list of servers.
- Fetch server settings.
- Trigger SEL collection for the servers.
- Download the generated SEL files.

The script uses a `.env` file to load Intersight credentials and the base URL.
Ensure the `.env` file contains the following variables:
- INTERSIGHT_URL: The base URL for the Intersight API.
- KEY_ID: The API key ID.
- PRIVATE_KEY: The path to the private key file.

Note: The script disables SSL verification for simplicity. Use caution in production environments.
"""


import time
import os
import requests
import urllib3
import intersight

from dotenv import load_dotenv
from intersight_auth import IntersightAuth
from intersight import signing
from intersight.configuration import JSON_SCHEMA_VALIDATION_KEYWORDS
from intersight.api import equipment_api
from intersight.api import compute_api
from intersight.model.compute_server_setting import ComputeServerSetting

# This script use .env file to obtain Intersight credentials and URL
load_dotenv()
INTERSIGHT_URL = os.getenv("INTERSIGHT_URL")
KEY_ID = os.getenv("KEY_ID")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

urllib3.disable_warnings()
# Setup intersight metadata
conf = intersight.Configuration(
    ## FIXME "host" and "key" hardcoded
    host=f"https://{INTERSIGHT_URL}",
    signing_info=intersight.signing.HttpSigningConfiguration(
        key_id=KEY_ID,
        private_key_path=PRIVATE_KEY,
        signing_scheme=signing.SCHEME_HS2019,
        signing_algorithm=signing.ALGORITHM_ECDSA_MODE_FIPS_186_3,
        signed_headers=[
            signing.HEADER_REQUEST_TARGET,
            signing.HEADER_DATE,
            signing.HEADER_HOST,
            signing.HEADER_DIGEST,
        ],
    ),
)

conf.disabled_client_side_validations = ",".join(JSON_SCHEMA_VALIDATION_KEYWORDS)
conf.verify_ssl = False
conf.access_token = None
apiClient = intersight.ApiClient(conf)


def get_server_list():
    # Get all servers
    api_instance = compute_api.ComputeApi(apiClient)
    try:
        servers_list_from_api = api_instance.get_compute_physical_summary_list().results
        servers_moid_list = []
        for server in servers_list_from_api:
            if server.management_mode not in ["UCSM"]:
                servers_moid_list.append({"moid": server.moid})
        return servers_moid_list

    except Exception as e:
        print(e)



def get_server_settings(server):
    # Get server setting
    api_instance = compute_api.ComputeApi(apiClient)
    try:
        server_moid = server["moid"]
        filter = f"Parent.Moid eq '{server_moid}'"
        setting_results = api_instance.get_compute_server_setting_list(
            filter=filter
        ).results
        setting_result = setting_results[0].moid
        # print(f"Server {server_moid} setting: {setting_result}")
        server["setting_moid"] = setting_result
    except Exception as e:
        print(f"Impossible to get server settings for {server['moid']} : {e}")


def set_collect_sel(server):
    # Set SEL collection
    api_instance = compute_api.ComputeApi(apiClient)
    setting_moid = server["setting_moid"]
    server_setting = ComputeServerSetting(moid=setting_moid)
    server_setting.collect_sel = "Collect"
    try:
        api_instance.update_compute_server_setting(
            moid=setting_moid, compute_server_setting=server_setting
        )
        # print(f"SEL collection requested")
    except Exception as e:
        print(f"Impossible to set SEL collection for {server['moid']} : {e}")


def get_endpoint_logs(server):
    # Get endpoint logs
    api_instance = equipment_api.EquipmentApi(apiClient)
    try:
        server_moid = server["moid"]
        filter = f"Server.Moid eq '{server_moid}'"
        endpoint_results = api_instance.get_equipment_end_point_log_list(
            filter=filter
        ).results
        endpoint_moid = endpoint_results[0].moid
        endpoint_filename = endpoint_results[0].file_name
        # print(f"Server {server_moid} endpointlog: {endpoint_moid}")
        server["endpoint_moid"] = endpoint_moid
        server["endpoint_filename"] = endpoint_filename
    except Exception as e:
        print(f"Impossible to get endpoint logs for {server['moid']}: {e}")


def download_sel(server):
    ### We can't use the SDK here as the answer to the REST API is not expected by the SDK and create an exception
    # # We need to change the target to download the SEL
    # conf.host = "https://download.eu-central-1.intersight.com"
    # apiClient = intersight.ApiClient(conf)
    # api_instance = equipment_api.EquipmentApi(apiClient)
    # # get the response
    # try:
    #     api_response = api_instance.get_equipment_log_download_by_moid(moid=moid)
    #
    #     print(api_response)
    #
    #     folder_name = "SEL_logs"
    #     folder_path = os.path.join(os.getcwd(), folder_name)
    #     file_path = os.path.join(folder_path, filename+".txt")
    #     try:
    #         if not os.path.exists(folder_path):
    #             os.makedirs(folder_path)
    #             print(f"Folder '{folder_name}' created.")
    #
    #         with open(file_path, "w") as file:
    #             file.write(api_response)
    #             print(f"File '{filename}'.txt created in folder '{folder_name}'.")
    #
    #     except Exception as e:
    #         print(f"Impossible to save SEL file: {e}")
    # except Exception as e:
    #     print(e)

    # Instead of using the SDK, we will use the REST API library to download the SEL

    endpoint_moid = server["endpoint_moid"]
    filename = server["endpoint_filename"]

    auth = IntersightAuth(
        secret_key_filename=PRIVATE_KEY,
        api_key_id=KEY_ID,
    )
    # Intersight REST API Base URL
    burl = f"https://download.{INTERSIGHT_URL}/api/v1/"
    request_url = f"{burl}equipment/LogDownloads/{endpoint_moid}"
    try:
        response = requests.get(url=request_url, auth=auth)
        # print(response.content)
        try:
            folder_name = "SEL_logs"
            folder_path = os.path.join(os.getcwd(), folder_name)
            file_path = os.path.join(folder_path, filename)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                print(f"Folder '{folder_name}' created.")

            with open(file_path, "w") as file:
                file.write(response.content.decode("utf-8"))
                print(f"File '{filename}' created in folder '{folder_name}'.")
        except Exception as e:
            print(f"Impossible to save SEL file: {e}")
    except Exception as e:
        print(e)


def main():
    # This script will trigger the generation of SEL files and download them
    print(
        "Warning: This script will only fech SEL files for servers managed by Intersight or in standalone mode."
    )
    # Get list of all servers
    servers_moid_list = get_server_list()
    for server in servers_moid_list:
        # Collect Server setting MOID
        get_server_settings(server)
        # Sent instruction to generate SEL
        set_collect_sel(server)
        # Look for EndPoint Logs MOID
        get_endpoint_logs(server)
    # Wait for the SEL to be generated before downloading
    print("Waiting for SEL to be generated...")
    time.sleep(5)
    for server in servers_moid_list:
        if 'endpoint_moid' in server:
            # Download the SEL on the current folder
            download_sel(server)
    print("Finished downloading SEL files.")


if __name__ == "__main__":
    main()
