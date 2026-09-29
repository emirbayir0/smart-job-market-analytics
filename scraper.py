import time
import re
import random
import httpx
from bs4 import BeautifulSoup
from database import save_jobs, log_event
from ai_analyzer import AIAnalyzer

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

class WebScraper:
    def __init__(self):
        self.headers = {"User-Agent": random.choice(USER_AGENTS)}
        self.ai_analyzer = AIAnalyzer()

    def clean_html(self, raw_html):
        if not raw_html:
            return ""
        soup = BeautifulSoup(raw_html, "html.parser")
        text = soup.get_text(separator=" ")
        return re.sub(r"\s+", " ", text).strip()

    def fetch_remoteok_jobs(self):
        jobs = []
        try:
            url = "https://remoteok.com/api"
            with httpx.Client(timeout=15.0, headers=self.headers, follow_redirects=True) as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    for item in data[1:30]:
                        title = item.get("position", "Yazılım Uzmanı")
                        company = item.get("company", "Küresel Teknoloji Şirketi")
                        desc_raw = item.get("description", "")
                        clean_desc = self.clean_html(desc_raw)
                        tags = item.get("tags", [])
                        
                        salary_min = item.get("salary_min")
                        salary_max = item.get("salary_max")
                        if salary_min and salary_max:
                            salary_str = f"${salary_min:,} - ${salary_max:,} / Yıl"
                        else:
                            salary_str = "Rekabetçi Maaş"

                        job_url = item.get("url") or item.get("apply_url") or f"https://remoteok.com/job/{item.get('id')}"
                        skills = set(self.ai_analyzer.extract_skills_rule_based(f"{title} {clean_desc} {' '.join(tags)}"))
                        for tag in tags:
                            if tag.strip():
                                skills.add(tag.title())
                        
                        title_lower = title.lower()
                        if "senior" in title_lower or "lead" in title_lower or "principal" in title_lower:
                            exp_level = "Kıdemli (Senior)"
                        elif "junior" in title_lower or "entry" in title_lower or "intern" in title_lower:
                            exp_level = "Başlangıç (Junior)"
                        else:
                            exp_level = "Orta Seviye (Mid)"

                        # Automatic English to Turkish translation for job summary
                        summary_tr = self.ai_analyzer.translate_summary_to_turkish(title, clean_desc)

                        jobs.append({
                            "title": title,
                            "company": company,
                            "location": item.get("location") or "Uzaktan (Küresel)",
                            "salary": salary_str,
                            "job_type": "Uzaktan",
                            "experience_level": exp_level,
                            "description": summary_tr,
                            "url": job_url,
                            "source": "RemoteOK Canlı API",
                            "extracted_skills": list(skills)
                        })
        except Exception as e:
            print(f"[RemoteOK Scraper Warning] Live API çekme hatası: {e}")
        return jobs

    def fetch_arbeitnow_jobs(self):
        jobs = []
        try:
            url = "https://www.arbeitnow.com/api/job-board-api"
            with httpx.Client(timeout=15.0, headers=self.headers) as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    for item in data[:30]:
                        title = item.get("title", "Yazılım Mühendisi")
                        company = item.get("company_name", "Teknoloji Şirketi")
                        desc_raw = item.get("description", "")
                        clean_desc = self.clean_html(desc_raw)
                        job_url = item.get("url")
                        tags = item.get("tags", [])

                        skills = set(self.ai_analyzer.extract_skills_rule_based(f"{title} {clean_desc} {' '.join(tags)}"))
                        
                        remote_flag = item.get("remote", False)
                        job_type = "Uzaktan" if remote_flag else "Ofis / Hibrit"

                        title_lower = title.lower()
                        if "senior" in title_lower or "lead" in title_lower:
                            exp_level = "Kıdemli (Senior)"
                        elif "junior" in title_lower or "intern" in title_lower:
                            exp_level = "Başlangıç (Junior)"
                        else:
                            exp_level = "Orta Seviye (Mid)"

                        summary_tr = self.ai_analyzer.translate_summary_to_turkish(title, clean_desc)

                        jobs.append({
                            "title": title,
                            "company": company,
                            "location": item.get("location") or "Avrupa / Global",
                            "salary": "Belirtilmedi",
                            "job_type": job_type,
                            "experience_level": exp_level,
                            "description": summary_tr,
                            "url": job_url,
                            "source": "Arbeitnow Küresel API",
                            "extracted_skills": list(skills)
                        })
        except Exception as e:
            print(f"[Arbeitnow Scraper Warning] API çekme hatası: {e}")
        return jobs

    def fetch_linkedin_jobs(self):
        jobs = []
        try:
            keywords = ["python", "yazılım", "developer", "microsoft office"]
            for kw in keywords:
                url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={kw}&location=Turkey"
                with httpx.Client(timeout=15.0, headers=self.headers, follow_redirects=True) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        cards = soup.find_all("div", class_="base-card")
                        for c in cards[:8]:
                            try:
                                title_elem = c.find("h3", class_="base-search-card__title")
                                comp_elem = c.find("h4", class_="base-search-card__subtitle")
                                loc_elem = c.find("span", class_="job-search-card__location")
                                link_elem = c.find("a", class_="base-card__full-link")
                                
                                title = title_elem.text.strip() if title_elem else "Yazılım Uzmanı"
                                company = comp_elem.text.strip() if comp_elem else "LinkedIn İlanı"
                                loc = loc_elem.text.strip() if loc_elem else "Türkiye"
                                job_url = link_elem["href"].split("?")[0] if link_elem else "https://linkedin.com"
                                
                                skills = set(self.ai_analyzer.extract_skills_rule_based(title))
                                title_lower = title.lower()
                                if "senior" in title_lower or "kıdemli" in title_lower or "lead" in title_lower:
                                    exp_level = "Kıdemli (Senior)"
                                elif "junior" in title_lower or "stajyer" in title_lower or "intern" in title_lower:
                                    exp_level = "Başlangıç (Junior)"
                                else:
                                    exp_level = "Orta Seviye (Mid)"

                                jobs.append({
                                    "title": title,
                                    "company": company,
                                    "location": loc,
                                    "salary": "Rekabetçi Maaş",
                                    "job_type": "Uzaktan" if "remote" in loc.lower() or "uzaktan" in loc.lower() else "Ofis / Hibrit",
                                    "experience_level": exp_level,
                                    "description": f"{company} firmasının LinkedIn üzerinde yayınladığı {title} pozisyonu.",
                                    "url": job_url,
                                    "source": "LinkedIn İş İlanları",
                                    "extracted_skills": list(skills)
                                })
                            except Exception:
                                continue
        except Exception as e:
            print(f"[LinkedIn Scraper Warning] {e}")
        return jobs

    def fetch_kariyernet_jobs(self):
        jobs = []
        try:
            url = "https://www.kariyer.net/is-ilanlari?kw=yazilim"
            with httpx.Client(timeout=15.0, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    links = soup.find_all("a", href=True)
                    job_links = [l for l in links if "/is-ilani/" in l["href"]]
                    seen_urls = set()
                    for jl in job_links[:12]:
                        try:
                            href = jl["href"]
                            full_url = "https://www.kariyer.net" + href if href.startswith("/") else href
                            if full_url in seen_urls:
                                continue
                            seen_urls.add(full_url)
                            
                            text_raw = jl.text.strip()
                            lines = [line.strip() for line in text_raw.split("\n") if line.strip() and "Sponsorlu" not in line]
                            if len(lines) >= 2:
                                title = lines[0]
                                company = lines[1]
                                loc = lines[2] if len(lines) > 2 else "Türkiye"
                            else:
                                title = text_raw[:40] if text_raw else "Yazılım Geliştirici"
                                company = "Kariyer.net İşveren"
                                loc = "Türkiye"

                            skills = set(self.ai_analyzer.extract_skills_rule_based(f"{title} {text_raw}"))
                            title_lower = title.lower()
                            if "senior" in title_lower or "kıdemli" in title_lower or "uzman" in title_lower:
                                exp_level = "Kıdemli (Senior)"
                            elif "junior" in title_lower or "stajyer" in title_lower or "asistan" in title_lower:
                                exp_level = "Başlangıç (Junior)"
                            else:
                                exp_level = "Orta Seviye (Mid)"

                            jobs.append({
                                "title": title,
                                "company": company,
                                "location": loc,
                                "salary": "Piyasa Standartlarında",
                                "job_type": "Uzaktan" if "uzaktan" in loc.lower() or "remote" in loc.lower() else "Ofis / Hibrit",
                                "experience_level": exp_level,
                                "description": f"{company} firması Kariyer.net ilanıdır: {title}",
                                "url": full_url,
                                "source": "Kariyer.net",
                                "extracted_skills": list(skills)
                            })
                        except Exception:
                            continue
        except Exception as e:
            print(f"[Kariyer.net Scraper Warning] {e}")
        return jobs

    def dispatch_alerts_for_new_jobs(self, new_jobs):
        """Checks newly saved jobs against active DB alert rules and sends notifications."""
        if not new_jobs:
            return
        try:
            from database import get_active_alert_rules
            from notifier import TelegramNotifier
            import json

            rules = get_active_alert_rules()
            if not rules:
                return

            notifier = TelegramNotifier()
            for rule in rules:
                skills_f = json.loads(rule.skills_filter) if rule.skills_filter else []
                types_f = json.loads(rule.job_type_filter) if rule.job_type_filter else []
                levels_f = json.loads(rule.experience_filter) if rule.experience_filter else []

                for job in new_jobs:
                    match_skills = True
                    if skills_f:
                        job_skills = [s.lower() for s in job.get("extracted_skills", [])]
                        match_skills = any(sf.lower() in job_skills for sf in skills_f)

                    match_type = True
                    if types_f:
                        match_type = job.get("job_type") in types_f

                    match_level = True
                    if levels_f:
                        match_level = job.get("experience_level") in levels_f

                    if match_skills and match_type and match_level:
                        if rule.channel == "Telegram":
                            notifier.send_new_job_alert(job, custom_chat_id=rule.target_address)
                        else:
                            print(f"[E-Posta Otomatik Alarm] {rule.target_address} adresine yeni ilan gönderildi: {job.get('title')}")
        except Exception as e:
            print(f"[Alert Dispatch Error] Otomatik alarm gönderiminde hata: {e}")

    def run_pipeline(self):
        print("[Scraper] Canlı veri kaynaklarından (LinkedIn, Kariyer.net, RemoteOK, Arbeitnow) veriler çekiliyor...")
        try:
            all_live_jobs = []
            remoteok_data = self.fetch_remoteok_jobs()
            arbeitnow_data = self.fetch_arbeitnow_jobs()
            linkedin_data = self.fetch_linkedin_jobs()
            kariyernet_data = self.fetch_kariyernet_jobs()
            
            all_live_jobs.extend(remoteok_data)
            all_live_jobs.extend(arbeitnow_data)
            all_live_jobs.extend(linkedin_data)
            all_live_jobs.extend(kariyernet_data)

            total, new_added = save_jobs(all_live_jobs)

            msg = f"{total} adet canlı ilan (LinkedIn, Kariyer.net, RemoteOK, Arbeitnow) tarandı ve Türkçe'ye çevrildi. {new_added} yeni ilan veritabanına kaydedildi."
            log_event(total, new_added, status="SUCCESS", message=msg)
            print(f"[Scraper SUCCESS] {msg}")
            return {"status": "SUCCESS", "total": total, "new_added": new_added, "message": msg}
        except Exception as e:
            err_msg = f"Kazıma hatası: {str(e)}"
            log_event(0, 0, status="ERROR", message=err_msg)
            print(f"[Scraper ERROR] {err_msg}")
            return {"status": "ERROR", "message": err_msg}

if __name__ == "__main__":
    from database import init_db
    init_db()
    scraper = WebScraper()
    res = scraper.run_pipeline()
    print(res)
