import os
from cloudflare import Cloudflare
from cloudflare.types import dns

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


def get_dns_record(
    dns_record_id: str,
    zone_id: str,
) -> dns.Record:
    record = client.dns.records.get(
        dns_record_id=dns_record_id, zone_id=zone_id
    )
    if record is None:
        raise ValueError("No record found")

    return record
