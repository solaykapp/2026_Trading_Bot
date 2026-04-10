import os
import time
import logging
import requests
import git
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

GITHUB_TOKEN     = os.getenv('GITHUB_TOKEN', '')
GITHUB_REPO      = os.getenv('GITHUB_REPO', 'solaykapp/2026_Trading_Bot')
RENDER_API_KEY   = os.getenv('RENDER_API_KEY', '')
SERVICE_ID       = os.getenv('SERVICE_ID', '')
TELEGRAM_TOKEN   = os.getenv('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('deploy.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger('DeployManager')


def push_to_github(msg):
    if not GITHUB_TOKEN:
        log.error('GITHUB_TOKEN missing in .env')
        return False
    try:
        repo = git.Repo('.')
        with repo.config_writer() as cw:
            cw.set_value('user', 'name', 'Osama-Deploy-Bot')
            cw.set_value('user', 'email', 'deploy@osama-trading.com')
        repo.git.add('-A')
        if not repo.is_dirty(untracked_files=True):
            log.info('No changes to push')
            return True
        repo.index.commit(msg)
        origin = repo.remote(name='origin')
        origin.set_url('https://' + GITHUB_TOKEN + '@github.com/' + GITHUB_REPO + '.git')
        origin.push()
        log.info('GitHub push OK: ' + GITHUB_REPO)
        return True
    except git.InvalidGitRepositoryError:
        log.error('Not a git repo. Run: git init && git remote add origin ...')
        return False
    except Exception as e:
        log.error('GitHub failed: ' + str(e).replace(GITHUB_TOKEN, '***'))
        return False


def get_deploy_status():
    if not RENDER_API_KEY or not SERVICE_ID:
        return {}
    try:
        url = 'https://api.render.com/v1/services/' + SERVICE_ID + '/deploys?limit=1'
        r = requests.get(url, headers={'Authorization': 'Bearer ' + RENDER_API_KEY}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data:
                return data[0].get('deploy', {})
    except Exception as e:
        log.error('Render API error: ' + str(e))
    return {}


def wait_for_deploy(timeout=300):
    if not RENDER_API_KEY or not SERVICE_ID:
        log.warning('Render not configured — skipping')
        return {'status': 'skipped'}
    log.info('Watching Render deploy...')
    start = time.time()
    last_status = ''
    while time.time() - start < timeout:
        deploy = get_deploy_status()
        status = deploy.get('status', 'unknown')
        if status != last_status:
            log.info('Render: ' + status)
            last_status = status
        if status == 'live':
            log.info('Deploy completed!')
            return {'status': 'live'}
        if status in ('failed', 'canceled', 'error'):
            log.error('Deploy failed: ' + status)
            return {'status': status}
        time.sleep(10)
    return {'status': 'timeout'}


def send_telegram(github_ok, result, msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    status = result.get('status', 'unknown')
    icons = {'live': 'OK', 'failed': 'FAILED', 'timeout': 'TIMEOUT', 'skipped': 'SKIPPED'}
    text = (icons.get(status, '?') + ' Deploy Result\n'
            + 'Repo: ' + GITHUB_REPO + '\n'
            + 'Time: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n'
            + 'GitHub: ' + ('OK' if github_ok else 'FAILED') + '\n'
            + 'Render: ' + status + '\n'
            + 'Commit: ' + msg[:80])
    try:
        requests.post('https://api.telegram.org/bot' + TELEGRAM_TOKEN + '/sendMessage',
            json={'chat_id': TELEGRAM_CHAT_ID, 'text': text}, timeout=10)
        log.info('Telegram sent')
    except Exception as e:
        log.error('Telegram failed: ' + str(e))


def deploy(commit_message=''):
    log.info('=' * 50)
    log.info('Starting deploy cycle')
    log.info('=' * 50)
    if not GITHUB_TOKEN:
        log.error('Add GITHUB_TOKEN to .env file')
        return
    msg = commit_message or 'Auto Deploy ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    github_ok = push_to_github(msg)
    if not github_ok:
        send_telegram(False, {'status': 'skipped'}, msg)
        return
    log.info('Waiting 15s for Render...')
    time.sleep(15)
    result = wait_for_deploy()
    send_telegram(github_ok, result, msg)
    log.info('Done: ' + result.get('status', 'unknown'))


if __name__ == '__main__':
    deploy()