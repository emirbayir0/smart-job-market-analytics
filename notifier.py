import json
import httpx
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

class TelegramNotifier:
    def __init__(self, token=None, chat_id=None):
        self.token = token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID

    def send_message(self, text, custom_chat_id=None):
        """Sends markdown formatted text message to Telegram."""
        target = custom_chat_id or self.chat_id
        if not self.token or not target:
            print(f"[Notifier - Simulation] Telegram Bot Token/Chat ID ayarlanmamış. Mesaj:\n{text}\n")
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": target,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, json=payload)
                return resp.status_code == 200
        except Exception as e:
            print(f"[Notifier Error] Telegram bildirimi gönderilemedi: {e}")
            return False

    def send_rule_confirmation(self, channel, target_address, filter_summary):
        """Sends an immediate confirmation alert when a user creates a new alert rule."""
        if channel == "Telegram":
            msg = (
                f"*YENİ BİLDİRİM ALARMI KURULDU*\n\n"
                f"*Kanal:* Telegram Bot\n"
                f"*Filtre Kriterleri:* {filter_summary}\n\n"
                f"Bu kriterlere uyan yeni bir canlı iş ilanı eklendiğinde size buradan otomatik bildirim gönderilecektir!"
            )
            return self.send_message(msg, custom_chat_id=target_address)
        else:
            # E-Mail Notification Simulation / Dispatched Log
            print(f"[Notifier - E-Posta] {target_address} adresine onay e-postası gönderildi: Kriterler ({filter_summary})")
            return True

    def send_new_job_alert(self, job, custom_chat_id=None):
        """Formats and dispatches a high-priority job alert."""
        message = (
            f"*YENİ İŞ İLANI ALERTI*\n\n"
            f"*Pozisyon:* {job.get('title')}\n"
            f"*Şirket:* {job.get('company')}\n"
            f"*Lokasyon:* {job.get('location')} ({job.get('job_type')})\n"
            f"*Maaş:* {job.get('salary')}\n"
            f"*Kıdem:* {job.get('experience_level')}\n"
            f"*Yetenekler:* {', '.join(job.get('extracted_skills', []))}\n\n"
            f"[İlana Başvur (Orijinal Site)]({job.get('url')})"
        )
        return self.send_message(message, custom_chat_id=custom_chat_id)

if __name__ == "__main__":
    notifier = TelegramNotifier()
    sent = notifier.send_rule_confirmation("Telegram", "123456", "Python + Uzaktan + Kıdemli")
    print("Rule Confirmation Sent:", sent)
