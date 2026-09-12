"""Root-only static release installer, restricted to Lantern Library paths."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys,tarfile,time

ROOT=Path('/opt/lantern-library');HOST=None
def run(*args):subprocess.run(args,check=True)
def nginx(tls):
    common=f'''    server_name {HOST};
    root {ROOT}/current;
    index index.html;
    charset utf-8;
    autoindex off;
    add_header X-Content-Type-Options nosniff always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;
    add_header Content-Security-Policy "default-src 'self'; img-src 'self' data:; media-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'" always;
    location ~ /\\. {{ deny all; }}
    location / {{ try_files $uri $uri/ =404; }}
    error_page 404 /404.html;
'''
    acme='    location ^~ /.well-known/acme-challenge/ { root /var/www/letsencrypt; }\n'
    if not tls:return 'server {\n    listen 80;\n'+common+acme+'}\n'
    return f'''server {{
    listen 80;
    server_name {HOST};
{acme}    location / {{ return 301 https://{HOST}$request_uri; }}
}}
server {{
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/{HOST}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{HOST}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
{common}}}
'''

def install(archive,release):
    if os.geteuid()!=0:raise SystemExit('Run with sudo')
    if not re.fullmatch(r'[0-9]{8}T[0-9]{6}Z-[a-z0-9]+',release):raise ValueError('Invalid release name')
    dest=ROOT/'releases'/release;dest.mkdir(parents=True,exist_ok=False)
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            p=Path(member.name)
            if p.is_absolute() or '..' in p.parts or not (member.isfile() or member.isdir()):raise ValueError('Unsafe archive member')
        tar.extractall(dest,filter='data')
    manifest=json.loads((dest/'checksums.json').read_text())
    actual={str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file() and p.name!='checksums.json'}
    if actual!=set(manifest):raise ValueError('Release file set differs from manifest')
    for name,digest in manifest.items():
        if hashlib.file_digest((dest/name).open('rb'),'sha256').hexdigest()!=digest:raise ValueError(f'Checksum mismatch: {name}')
    for p in dest.rglob('*'):p.chmod(0o755 if p.is_dir() else 0o644)
    dest.chmod(0o755)
    current=ROOT/'current';previous=os.readlink(current) if current.is_symlink() else None
    conf=Path('/etc/nginx/sites-available')/HOST;enabled=Path('/etc/nginx/sites-enabled')/HOST
    old_conf=conf.read_bytes() if conf.exists() else None
    was_enabled=enabled.is_symlink() or enabled.exists()
    link=ROOT/'current.next';link.unlink(missing_ok=True);link.symlink_to(dest);link.replace(current)
    try:
        cert=Path('/etc/letsencrypt/live')/HOST/'fullchain.pem'
        Path('/var/www/letsencrypt').mkdir(parents=True,exist_ok=True)
        conf.write_text(nginx(cert.exists()))
        if not enabled.exists():enabled.symlink_to(conf)
        run('nginx','-t');run('systemctl','reload','nginx')
        if not cert.exists():
            run('certbot','certonly','--webroot','-w','/var/www/letsencrypt','-d',HOST,'--non-interactive','--agree-tos')
            conf.write_text(nginx(True));run('nginx','-t');run('systemctl','reload','nginx')
        hook=Path('/etc/letsencrypt/renewal-hooks/deploy/lantern-library.sh')
        hook.parent.mkdir(parents=True,exist_ok=True)
        hook.write_text(f'#!/bin/sh\nif [ "$RENEWED_LINEAGE" = /etc/letsencrypt/live/{HOST} ]; then\n    nginx -t && systemctl reload nginx\nfi\n')
        hook.chmod(0o755)
        # nginx's reload signal returns before new TLS workers are necessarily ready.
        check=['curl','--fail','--silent','--show-error','--max-time','5','--resolve',f'{HOST}:443:127.0.0.1',f'https://{HOST}/','-o','/dev/null']
        for attempt in range(10):
            result=subprocess.run(check,capture_output=True,text=True)
            if result.returncode==0:break
            if attempt==9:raise RuntimeError('HTTPS health check failed: '+result.stderr.strip())
            time.sleep(1)
    except BaseException:
        if previous:
            link.unlink(missing_ok=True);link.symlink_to(previous);link.replace(current)
        else:current.unlink(missing_ok=True)
        if old_conf is not None:conf.write_bytes(old_conf)
        else:enabled.unlink(missing_ok=True);conf.unlink(missing_ok=True)
        if not was_enabled:enabled.unlink(missing_ok=True)
        subprocess.run(['nginx','-t'],check=False)
        subprocess.run(['systemctl','reload','nginx'],check=False)
        raise
    print(json.dumps({'release':release,'previous':previous,'url':f'https://{HOST}'}))

if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit('Usage: install.py ARCHIVE RELEASE HOSTNAME')
    HOST=sys.argv[3]
    if not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+',HOST) or len(HOST)>253:raise SystemExit('Invalid hostname')
    install(sys.argv[1],sys.argv[2])
