import requests
from config import DOPPLER_TOKEN, PROJECT, CONFIG

print(DOPPLER_TOKEN)
print(PROJECT)
print(CONFIG)   


def get_secrets(token: str):
    """
    Retrieve all doppler secrets for config given a service access token
    """
    url = "https://api.doppler.com/v3/configs/config/secrets"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    print(response.text)
    return response.json()

def get_tailscale_api_token(client_id: str, client_secret: str):
    """
    Authenticate with the tailscale oauth api to retrieve an api token
    """
    url = "https://api.tailscale.com/api/v2/oauth/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, data=data)
    return response.json().get("access_token")

def create_tailscale_ephemeral_key(token: str):
    """
    Create a new tailscale ephemeral key
    """
    url = "https://api.tailscale.com/api/v2/tailnet/-/keys"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {
        "capabilities": {
            "devices": {
                "create": {
                    "reusable": True,
                    "ephemeral": True,
                    "preauthorized": True,
                    "tags": [ "tag:all" ]
                }
            }
        },
        "expirySeconds": 86400,
        "description": "ephem token"
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json().get("key")

def update_doppler_secret(token: str, project: str, config: str, tailscale_token: str):
    """
    Update a doppler secret
    """
    url = f"https://api.doppler.com/v3/configs/config/secrets"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {
        "project": project,
        "config": config,
        "change_requests": [
            {
                "name": "TAILSCALE_TOKEN",
                "originalName": "TAILSCALE_TOKEN",
                "value": tailscale_token
            }
        ],
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# 1. Retrieve the tailscale oauth client details by using the doppler api to retrieve the secrets
secrets = get_secrets(DOPPLER_TOKEN)
tailscale_client_id = secrets.get("secrets").get("OAUTH_DEVICES_CLIENT_ID").get("raw")
tailscale_client_secret = secrets.get("secrets").get("OAUTH_DEVICES_CLIENT_SECRET").get("raw")

# 2. Use the tailscale oauth client details to authenticate with tailscale
access_token = get_tailscale_api_token(tailscale_client_id, tailscale_client_secret)

# 3. Create a new tailscale ephemeral key
ephemeral_key = create_tailscale_ephemeral_key(access_token)

# 4. Update the TAILSCALE_TOKEN secret in doppler with the new tailscale ephemeral key
update_doppler_secret(DOPPLER_TOKEN, PROJECT, CONFIG, ephemeral_key)

print("Updated TAILSCALE_TOKEN secret in doppler with new ephemeral key")