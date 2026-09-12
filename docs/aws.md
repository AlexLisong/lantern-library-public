# Optional static deployment

The supported output is a static `dist/` directory. You can serve it with any
static web server. These optional scripts illustrate a Linux/nginx deployment;
they do not identify or configure a project-maintainer environment.

## Configuration

The optional deployer requires AWS CLI credentials, an existing Linux instance,
Python 3.12+, nginx, Certbot, a registered Certbot account, DNS pointing to your
instance, and a trusted SSH host key. Review the scripts before using sudo.

Copy `deploy/config.example.json` to an ignored location such as
`.aws-local/config.json` and fill in your own account, instance, region, profile,
SSH user, and hostname. Keep the SSH private key outside the repository.
`deploy/config.json` is also ignored to avoid accidental tracking of older local
configuration files.

```sh
npm test
npm run build
python3 deploy/deploy.py --config .aws-local/config.json --key /path/to/private-key.pem
```

The deployer requires a clean committed tree, checks account/instance/DNS,
builds an allowlisted archive, verifies checksums, and installs with strict SSH
host-key checking. The host installer uses `/opt/lantern-library/releases` and an
atomic `current` symlink. It configures only the supplied nginx hostname, verifies
HTTPS, and restores the previous activation if health checks fail.

## Verification and recovery

After deploying, check catalog/book routes, audio byte-range responses, downloads,
and page playback in a browser. Check other services if you share a host.
Maintain off-host copies of source and creative assets according to their licenses.

For rollback, identify a previously verified release, atomically point `current`
to it, validate nginx, reload it, and check HTTPS. Media and HTML must roll back
together. There is no application database to migrate. Review unused releases
before deleting them; the installer does not prune them automatically.
