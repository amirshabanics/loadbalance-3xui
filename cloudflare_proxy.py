import os
from cloudflare import Cloudflare

client = Cloudflare(
    # This is the default and can be omitted
    api_email=os.environ.get("CLOUDFLARE_EMAIL"),
    # This is the default and can be omitted
    api_key=os.environ.get("CLOUDFLARE_API_KEY"),
)


# domain @ or the subdomain name
def update_subdomain_ip(
    dns_record_id: str, zone_id: str, domain: str, ip: str
):
    client.dns.records.update(
        dns_record_id=dns_record_id,
        zone_id=zone_id,
        name=domain,
        type="A",
        proxied=True,
        content=ip,
    )
