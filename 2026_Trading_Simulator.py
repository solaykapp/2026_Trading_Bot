"""
╔══════════════════════════════════════════════════════════════════╗
║     🚀 Deploy Manager                                            ║
║     GitHub Push → Render Auto-Deploy → Telegram إشعار           ║
║     Project: 2026_Trading_Bot | OSAMA TRADING SYSTEM            ║
╚══════════════════════════════════════════════════════════════════╝

الاستخدام:
    python deploy_manager.py

ما يفعله:
    1. يرفع الكود لـ GitHub
    2. Render يكتشف الـ push ويبدأ النشر تلقائياً
    3. يراقب حالة النشر حتى يكتمل
    4. يرسل إشعار تليجرام بالنتيجة
"""

import os
import time
import logging
import requests
import git
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

# ══════════════════════════════════════════════════════════════
# الإعدادات
# ══════════════════════════════════════════════════════════════
GITHUB_TOKEN     = os.getenv("GITHUB_TOKEN",     "")
GITHUB_REPO      = os.getenv("GITHUB_REPO",      "solaykapp/2026_Trading_Bot")
RENDER_API_KEY   = os.getenv("RENDER_API_KEY",   "")
SERVICE_ID       = os.getenv("SERVICE_ID",        "")
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN",   "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

RENDER_API_BASE  = "https://api.render.com/v1"
DEPLOY_TIMEOUT   = 300   # أقصى وقت انتظار للنشر (ثانية)
POLL_INTERVAL    = 10    # كل كم ثانية نتحقق من حالة النشر

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("deploy.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("DeployManager")


# ══════════════════════════════════════════════════════════════
# 1. رفع الكود لـ GitHub
# ══════════════════════════════════════════════════════════════
def push_to_github(commit_message: str = "") -> bool:
    """
    رفع جميع التغييرات لـ GitHub.
    Render سيكتشف الـ push تلقائياً ويبدأ النشر.
    """
    if not GITHUB_TOKEN:
        log.error("GITHUB_TOKEN غير موجود في .env")
        return False

    try:
        repo = git.Repo(".")

        with repo.config_writer() as cw:
            cw.set_value("user", "name",  "Osama-Deploy-Bot")
            cw.set_value("user", "email", "deploy@osama-trading.com")

        # إضافة جميع التغييرات
        repo.git.add("-A")

        if not repo.is_dirty(untracked_files=True):
            log.info("لا توجد تغييرات جديدة للرفع")
            return True  # ليس خطأ — الكود محدّث أصلاً

        msg = commit_message or f"🚀 Deploy | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        repo.index.commit(msg)

        origin = repo.remote(name="origin")
        origin.set_url(f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git")
        origin.push()

        log.info(f"✅ GitHub: تم الرفع بنجاح → {GITHUB_REPO}")
        return True

    except git.InvalidGitRepositoryError:
        log.error("المجلد ليس Git repo. شغّل: git init && git remote add origin ...")
        return False
    except Exception as e:
        safe = str(e).replace(GITHUB_TOKEN, "***") if GITHUB_TOKEN else str(e)
        log.error(f"GitHub فشل: {safe}")
        return False


# ══════════════════════════════════════════════════════════════
# 2. مراقبة النشر على Render
# ══════════════════════════════════════════════════════════════
def get_latest_deploy() -> dict:
    """جلب آخر عملية نشر على Render."""
    if not RENDER_API_KEY or not SERVICE_ID:
        return {}

    try:
        headers  = {"Authorization": f"Bearer {RENDER_API_KEY}"}
        url      = f"{RENDER_API_BASE}/services/{SERVICE_ID}/deploys?limit=1"
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            deploys = response.json()
            if deploys:
                return deploys[0].get("deploy", {})
    except Exception as e:
        log.error(f"Render API خطأ: {e}")
    return {}


def trigger_manual_deploy() -> str:
    """تشغيل نشر يدوي على Render (احتياطي إذا لم يكتشف GitHub تلقائياً)."""
    if not RENDER_API_KEY or not SERVICE_ID:
        return ""

    try:
        headers  = {"Authorization": f"Bearer {RENDER_API_KEY}"}
        url      = f"{RENDER_API_BASE}/services/{SERVICE_ID}/deploys"
        response = requests.post(url, headers=headers, timeout=15)

        if response.status_code in (200, 201):
            deploy = response.json().get("deploy", {})
            deploy_id = deploy.get("id", "")
            log.info(f"Render: تم تشغيل النشر اليدوي | ID: {deploy_id}")
            return deploy_id
    except Exception as e:
        log.error(f"Render trigger خطأ: {e}")
    return ""


def wait_for_deploy(timeout: int = DEPLOY_TIMEOUT) -> dict:
    """
    مراقبة حالة النشر حتى يكتمل أو ينتهي الوقت.
    يُعيد dict بالحالة النهائية.
    """
    if not RENDER_API_KEY or not SERVICE_ID:
        log.warning("Render غير مهيّأ — تخطي المراقبة")
        return {"status": "skipped"}

    log.info(f"⏳ مراقبة النشر على Render (أقصى {timeout} ثانية)...")
    start_time    = time.time()
    last_status   = ""

    while time.time() - start_time < timeout:
        deploy = get_latest_deploy()
        status = deploy.get("status", "unknown")

        if status != last_status:
            elapsed = int(time.time() - start_time)
            log.info(f"   Render [{elapsed}s]: {status}")
            last_status = status

        # حالات نهائية
        if status == "live":
            log.info("✅ Render: النشر اكتمل بنجاح!")
            return {"status": "live", "deploy": deploy}

        if status in ("failed", "canceled", "error"):
            log.error(f"❌ Render: النشر فشل | الحالة: {status}")
            return {"status": status, "deploy": deploy}

        time.sleep(POLL_INTERVAL)

    log.warning(f"⏰ انتهى وقت الانتظار ({timeout}s) — تحقق من Render يدوياً")
    return {"status": "timeout"}


# ══════════════════════════════════════════════════════════════
# 3. إشعار تليجرام
# ══════════════════════════════════════════════════════════════
def send_deploy_notification(github_ok: bool, render_result: dict, commit_msg: str):
    """إرسال إشعار تليجرام بنتيجة النشر الكاملة."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return

    render_status = render_result.get("status", "unknown")
    deploy_info   = render_result.get("deploy", {})

    # أيقونة حسب النتيجة
    status_icons = {
        "live":    "✅",
        "failed":  "❌",
        "timeout": "⏰",
        "skipped": "⚠️",
        "canceled": "🚫",
    }
    icon = status_icons.get(render_status, "❓")

    # رابط الخدمة على Render
    service_url = deploy_info.get("serviceURL", f"https://dashboard.render.com/web/{SERVICE_ID}")

    message = (
        f"{icon} *نتيجة النشر*\n"
        f"{'━' * 32}\n"
        f"📦 المشروع: `{GITHUB_REPO}`\n"
        f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"📤 *GitHub*: {'✅ تم الرفع' if github_ok else '❌ فشل'}\n"
        f"🚀 *Render*: `{render_status}`\n\n"
        f"📝 *آخر تغيير*:\n`{commit_msg[:100]}`\n\n"
        f"{'━' * 32}\n"
        f"🔗 [GitHub](<https://github.com/{GITHUB_REPO}>) | "
        f"[Render]({service_url})"
    )

    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id":                  TELEGRAM_CHAT_ID,
                "text":                     message,
                "parse_mode":               "Markdown",
                "disable_web_page_preview": True
            },
            timeout=10
        )
        log.info("📬 إشعار تليجرام أُرسل")
    except Exception as e:
        log.error(f"تليجرام فشل: {e}")


# ══════════════════════════════════════════════════════════════
# 4. الدالة الرئيسية
# ══════════════════════════════════════════════════════════════
def deploy(commit_message: str = ""):
    """
    تسلسل النشر الكامل:
    GitHub Push → Render Auto-Deploy → مراقبة → تليجرام
    """
    log.info("=" * 60)
    log.info("   🚀 بدء عملية النشر الكاملة")
    log.info("=" * 60)

    msg = commit_message or f"🚀 Auto Deploy | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # الخطوة 1: GitHub
    github_ok = push_to_github(msg)
    if not github_ok:
        log.error("فشل الرفع لـ GitHub — إيقاف العملية")
        send_deploy_notification(False, {"status": "skipped"}, msg)
        return

    # الخطوة 2: انتظر Render يكتشف الـ push (عادةً 10-30 ثانية)
    log.info("⏳ انتظار Render لاكتشاف التغييرات...")
    time.sleep(15)

    # الخطوة 3: مراقبة النشر
    render_result = wait_for_deploy()

    # إذا لم يبدأ Render تلقائياً، شغّله يدوياً
    if render_result.get("status") == "skipped":
        log.info("تشغيل النشر يدوياً على Render...")
        trigger_manual_deploy()
        time.sleep(10)
        render_result = wait_for_deploy()

    # الخطوة 4: إشعار تليجرام
    send_deploy_notification(github_ok, render_result, msg)

    log.info("=" * 60)
    log.info(f"   {'✅ اكتمل النشر' if render_result.get('status') == 'live' else '⚠️ تحقق من النتيجة'}")
    log.info("=" * 60)


if __name__ == "__main__":
    deploy()