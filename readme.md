# Intersight SEL Collection Script

This Python script interacts with the Cisco Intersight API to collect and download System Event Logs (SEL) from servers managed by Intersight or operating in standalone mode.

## Key Features

- Retrieve a list of servers managed by Intersight.
- Fetch server settings.
- Trigger SEL collection for the servers.
- Download the generated SEL files to a local directory.

## Prerequisites

- Python 3.7 or higher
- Cisco Intersight account
- API key for authentication
- `.env` file with the following variables:
  - `INTERSIGHT_URL`: The base URL for the Intersight API.
  - `KEY_ID`: The API key ID.
  - `PRIVATE_KEY`: The path to the private key file.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/mabuelgh/intersight-sel-collection-script.git
    cd intersight-sel-collection-script
    ```

2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Create a `.env` file in the root directory and add the following variables:
    ```env
    INTERSIGHT_URL=your_intersight_url
    KEY_ID=your_api_key_id
    PRIVATE_KEY=path_to_your_private_key
    ```

## Usage

1. Run the script:
    ```bash
    python get_intersight_server_sel.py
    ```

2. The script will:
   - Retrieve the list of servers.
   - Trigger SEL collection for each server.
   - Wait for the SEL files to be generated.
   - Download the SEL files to the `SEL_logs` directory.

## Notes

- The script disables SSL verification for simplicity. Use caution in production environments.
- SEL files will be saved in the `SEL_logs` directory in the current working directory.

## Troubleshooting

- Ensure the `.env` file is correctly configured with valid credentials.
- Verify that the private key file path is correct and accessible.
- If the script fails to download SEL files, check the Intersight API connectivity and credentials.
- In `.env` file, `INTERSIGHT_URL` should be *"intersight.com"* or *"eu-central-1.intersight.com"* or your URL for Itersigh Appliance.