"""Deploy verified static output using an explicitly supplied private configuration."""
import argparse,datetime,hashlib,json,re,socket,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--key',type=Path,required=True);p.add_argument('--config',type=Path,required=True);a=p.parse_args()
    cfg=json.loads(a.config.expanduser().read_text())
    if not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+',cfg['hostname']) or len(cfg['hostname'])>253:raise SystemExit('Invalid hostname')
    if not re.fullmatch(r'[a-z_][a-z0-9_-]*',cfg['sshUser']):raise SystemExit('Invalid SSH user')
    def aws(*args):return json.loads(subprocess.check_output(['aws','--profile',cfg['profile'],'--region',cfg['region'],*args,'--output','json']))
    identity=aws('sts','get-caller-identity')
    if identity['Account']!=cfg['account']:raise SystemExit('AWS account does not match the deployment configuration')
    instance=aws('ec2','describe-instances','--instance-ids',cfg['instance'])['Reservations'][0]['Instances'][0]
    if instance['State']['Name']!='running':raise SystemExit('Target instance is not running')
    ip=instance['PublicIpAddress']
    if socket.gethostbyname(cfg['hostname'])!=ip:raise SystemExit('DNS does not point to the expected AWS instance')
    subprocess.run(['python3','scripts/build.py'],cwd=ROOT,check=True)
    sha=subprocess.check_output(['git','rev-parse','--short','HEAD'],cwd=ROOT,text=True).strip()
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise SystemExit('Commit source before deployment')
    release=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+sha
    work=ROOT/'.build/deploy';work.mkdir(parents=True,exist_ok=True);archive=work/(release+'.tar.gz')
    with tarfile.open(archive,'w:gz') as tar:
        for path in sorted((ROOT/'dist').rglob('*')):
            if path.is_file():tar.add(path,arcname=str(path.relative_to(ROOT/'dist')))
    checksum=hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()
    target=f'{cfg["sshUser"]}@{ip}';key=str(a.key.expanduser().resolve())
    ssh=['ssh','-i',key,'-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',target]
    remote='/tmp/lantern-library-'+release
    subprocess.run([*ssh,'mkdir',remote],check=True)
    subprocess.run(['scp','-i',key,'-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',str(archive),str(ROOT/'deploy/install.py'),target+':'+remote+'/'],check=True)
    # Shell arguments contain only fixed paths and validated generated identifiers.
    command=f"echo '{checksum}  {remote}/{archive.name}' | sha256sum -c - && sudo python3 {remote}/install.py {remote}/{archive.name} {release} {cfg['hostname']}"
    subprocess.run([*ssh,command],check=True)
    (work/'last-deployment.json').write_text(json.dumps({'release':release,'sha':sha,'url':'https://'+cfg['hostname'],'archiveSha256':checksum},indent=2)+'\n')
    print('Live: https://'+cfg['hostname'])

if __name__=='__main__':main()
