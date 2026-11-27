# Domain and DNS: how aledb.org reaches the app

How a request for `https://aledb.org` ends up at the Django app, who controls
each step, and what has to be renewed. Checked 2026-11-27.

Everything on this page is public information: anyone can read it from DNS, the
registration record or the TLS certificate. Account names, logins and the people
who hold them are deliberately not recorded here.

## Request path

| Step | What | Where it is controlled |
|---|---|---|
| 1. Registration | `aledb.org`, registered 2017-07-25 at Squarespace Domains (formerly Google Domains) | Registrar account, outside Azure |
| 2. DNS zone | Nameservers `ns-cloud-c1` to `c4.googledomains.com` | Same registrar account |
| 3. A records | `aledb.org` and `www.aledb.org` point to `4.231.249.59` | Same registrar account |
| 4. Public IP | `4.231.249.59` is the public IP of the single production Azure VM | Azure portal |
| 5. nginx | Listens on 80 and 443 for `aledb.org`, `www.aledb.org` and the bare IP; port 80 redirects to HTTPS | `ops/host/etc/nginx/sites-available/default` |
| 6. TLS | Let's Encrypt certificate for `aledb.org` and `www.aledb.org`, terminated by nginx | certbot on the host |
| 7. App | nginx proxies to daphne in the `aledb-web` container on `127.0.0.1:8000`; `/static` and `/aledata` are served from disk by nginx | `docker-compose-prod-asgi-host-nginx.yml` |

The zone also has MX records pointing to Mailgun, so mail for the domain depends
on the same DNS zone.

## Azure is not in the DNS path

The domain is not registered through Azure and Azure DNS does not serve it. The
only Azure piece is the VM and its public IP.

There is a resource named after the domain in the Azure subscription. It is not
used: public DNS delegates to the registrar's nameservers, so nothing in Azure
answers queries for `aledb.org`. Before deleting it, open it in the portal and
compare its records with the live zone (commands below).

## What has to be renewed

| Item | Expires | Renewal |
|---|---|---|
| Domain registration | 2027-07-25 | In the registrar account. Whether auto-renew is on is only visible there. |
| TLS certificate | Every 90 days | Automatic: the `snap.certbot.renew` systemd timer runs twice a day. |

If the registration lapses, the site and mail for the domain stop resolving even
though the VM is healthy.

## What breaks if something changes

- **The VM's public IP changes** (for example the VM is recreated without
  keeping the IP resource): update both A records at the registrar, the
  `server_name` and redirect lines in the nginx config, and `ALLOWED_HOSTS` in
  the Django settings.
- **A new hostname is needed** (for example `staging.aledb.org`): add the record
  at the registrar, then issue a certificate with
  `sudo certbot --nginx -d <hostname>`.
- **The nameservers are moved** (for example to Azure DNS): copy every record
  first, including the MX records, or mail stops.

## How to verify

```bash
# Registrar, registration and expiry dates, nameservers
curl -sL https://rdap.org/domain/aledb.org | python3 -m json.tool | less

# Live DNS records
dig +short aledb.org A
dig +short www.aledb.org A
dig +short aledb.org NS
dig +short aledb.org MX

# Public IP of this VM, as Azure sees it (run on the host)
curl -s -H Metadata:true \
  "http://169.254.169.254/metadata/loadbalancer?api-version=2021-02-01"

# Certificate names and expiry
echo | openssl s_client -connect aledb.org:443 -servername aledb.org 2>/dev/null \
  | openssl x509 -noout -subject -dates -ext subjectAltName

# Renewal timer
systemctl list-timers | grep certbot
```
