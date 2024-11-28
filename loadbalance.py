import dataclasses
import requests


@dataclasses.dataclass
class Config:
    # localhost:1080
    panel_url: str
    panel_user: str
    panel_pass: str

    inbound_id: int
    config_email: int


def check_traffic(config: Config):
    session = requests.Session()

    # Login and set token
    session.post(
        url=f"https://{config.panel_url}/login",
        json={"username": config.panel_user, "password": config.panel_pass},
    )

    inbounds = session.get(
        url=f"https://{config.panel_url}/panel/inbound/list"
    ).json()["obj"]

    # TODO: No error handling
    # Get the inbound
    inbound = list(
        filter(lambda inb: inb["id"] == config.inbound_id, inbounds)
    )[0]

    # Get the config
    client = filter(
        lambda client: client["email"] == config.config_email,
        inbound["clientStats"],
    )

    # total = 0 means inf
    # total & up & total in Byte
    # Check reach the limit with some threshold for safety
    if (
        client["up"] + client["down"] > client["total"] - 1024 ^ 3
        and client["total"] > 0
    ):
        # Change the ip
        pass




    # Reset traffic on some condition
    # session.post(
    #     url=f"https://{config.panel_url}/panel/inbound/{config.inbound_id}/resetClientTraffic/{config.config_email}"
    # )
