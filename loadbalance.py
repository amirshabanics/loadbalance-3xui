import dataclasses
import requests
import typing
import random
import json
import time
import cloudflare_proxy


@dataclasses.dataclass
class XUIConfig:
    # localhost:1080
    panel_url: str
    panel_user: str
    panel_pass: str

    inbound_id: int
    config_email: int


@dataclasses.dataclass
class CloudflareDNSConfig:
    record_id: str
    zone_id: str
    domain: str

    # The origin server it refer to it
    origin_ip: str
    xui_config: XUIConfig

    # We need to refer to cloudflare that we proxy after we reach the traffic limit
    cloudflare_proxy_to: typing.Optional["CloudflareDNSConfig"] = None


# Example
# CONFIGS: list[CloudflareDNSConfig] = [
#     CloudflareDNSConfig(
#         record_id="x",
#         zone_id="a",
#         domain="c",
#         origin_ip="1.1.1.1",
#         xui_config=XUIConfig(
#             panel_url="p.com:2053",
#             panel_pass="pass",
#             panel_user="user",
#             inbound_id="1",
#             config_email="t",
#         ),
#     ),
#     CloudflareDNSConfig(
#         record_id="xx",
#         zone_id="aa",
#         domain="cc",
#         origin_ip="2.2.2.2",
#         xui_config=XUIConfig(
#             panel_url="d.com:2053",
#             panel_pass="pass",
#             panel_user="user",
#             inbound_id="1",
#             config_email="t",
#         ),
#     ),
# ]

CONFIGS = []


def proxy_cloudflare_Config(cloudflare_config: CloudflareDNSConfig):
    appropriate_config = list(
        filter(
            lambda c: c.cloudflare_proxy_to is None and c != cloudflare_config,
            CONFIGS,
        )
    )
    # Randomly choose a config
    random.shuffle(appropriate_config)

    if len(appropriate_config) == 0:
        # The state is when all our config reach to our limits
        # TODO: handle it
        raise Exception("No config remain")

    cloudflare_config.cloudflare_proxy_to = appropriate_config[0]
    cloudflare_proxy.update_subdomain_ip(
        dns_record_id=cloudflare_config.record_id,
        zone_id=cloudflare_config.zone_id,
        domain=cloudflare_config.domain,
        ip=cloudflare_config.cloudflare_proxy_to.origin_ip,
    )


def check_traffic(cloudflare_config: CloudflareDNSConfig):
    session = requests.Session()

    # Login and set token
    session.post(
        url=f"https://{cloudflare_config.xui_config.panel_url}/login",
        json={
            "username": cloudflare_config.xui_config.panel_user,
            "password": cloudflare_config.xui_config.panel_pass,
        },
    )

    inbounds = session.get(
        url=f"https://{cloudflare_config.xui_config.panel_url}/panel/inbound/list"
    ).json()["obj"]

    # TODO: No error handling
    # Get the inbound
    inbound = list(
        filter(
            lambda inb: inb["id"] == cloudflare_config.xui_config.inbound_id,
            inbounds,
        )
    )[0]

    # Get the config
    client = filter(
        lambda client: client["email"]
        == cloudflare_config.xui_config.config_email,
        inbound["clientStats"],
    )

    # total = 0 means inf
    # total & up & total in Byte
    # Check reach the limit with some threshold for safety
    if (
        client["total"] == 0
        or client["up"] + client["down"] < client["total"] - 1024 ^ 3
    ):
        # Change to real ip
        if cloudflare_config.cloudflare_proxy_to is not None:
            cloudflare_proxy.update_subdomain_ip(
                dns_record_id=cloudflare_config.record_id,
                zone_id=cloudflare_config.zone_id,
                domain=cloudflare_config.domain,
                ip=cloudflare_config.origin_ip,
            )
            cloudflare_config.cloudflare_proxy_to = None
        return

    proxy_cloudflare_Config(cloudflare_config=cloudflare_config)
    # Change all configs that proxy to the server
    for c in CONFIGS:
        if c.cloudflare_proxy_to == cloudflare_config:
            proxy_cloudflare_Config(cloudflare_config=c)

    # Reset traffic on some condition
    # session.post(
    #     url=f"https://{config.panel_url}/panel/inbound/{config.inbound_id}/resetClientTraffic/{config.config_email}"
    # )


def main():
    while True:
        for c in CONFIGS:
            check_traffic(c)

        with open("configs.json", "w") as file:
            json.dump(CONFIGS, file)
        time.sleep(60 * 60 * 1)  # every 1 hour


with open("configs.json", "r") as file:
    CONFIGS = json.load(file)
main()
