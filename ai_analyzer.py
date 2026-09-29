import json
import re
import httpx
from config import GEMINI_API_KEY

TECH_PATTERNS = {
    'Python': r'(?i)\bpython[0-9]*\b',
    'JavaScript': r'(?i)\bjavascript\b|\bjs\b',
    'TypeScript': r'(?i)\btypescript\b|\bts\b',
    'C#': r'(?i)c#|csharp|c-sharp',
    'C++': r'(?i)c\+\+|cpp',
    'C': r'(?i)(?<![a-zA-Z0-9#+])C(?![a-zA-Z0-9#+])',
    'Java': r'(?i)\bjava\b(?!script)',
    'HTML': r'(?i)\bhtml[5]?\b',
    'CSS': r'(?i)\bcss[3]?\b|\bsass\b|\bscss\b',
    'React': r'(?i)\breact(?:\.js|js)?\b|\breact native\b',
    'Node.js': r'(?i)\bnode(?:\.js|js)?\b',
    'Vue': r'(?i)\bvue(?:\.js|js)?\b',
    'Angular': r'(?i)\bangular(?:\.js|js)?\b',
    'Next.js': r'(?i)\bnext(?:\.js|js)?\b',
    'Express': r'(?i)\bexpress(?:\.js|js)?\b',
    'FastAPI': r'(?i)\bfastapi\b',
    'Django': r'(?i)\bdjango\b',
    'Flask': r'(?i)\bflask\b',
    '.NET': r'(?i)\.net|dotnet|asp\.net',
    'PHP': r'(?i)\bphp\b',
    'Laravel': r'(?i)\blaravel\b',
    'Ruby': r'(?i)\bruby\b|\bruby on rails\b|\brails\b',
    'Swift': r'(?i)\bswift\b',
    'Kotlin': r'(?i)\bkotlin\b',
    'Go': r'(?i)\bgolang\b|\bgo\b',
    'Rust': r'(?i)\brust\b',
    'SQL': r'(?i)\bsql\b',
    'PostgreSQL': r'(?i)\bpostgres(?:ql)?\b',
    'MySQL': r'(?i)\bmysql\b',
    'MongoDB': r'(?i)\bmongo(?:db)?\b',
    'Redis': r'(?i)\bredis\b',
    'SQLite': r'(?i)\bsqlite\b',
    'Docker': r'(?i)\bdocker\b',
    'Kubernetes': r'(?i)\bkubernetes\b|\bk8s\b',
    'AWS': r'(?i)\baws\b|\bamazon web services\b',
    'Azure': r'(?i)\bazure\b',
    'GCP': r'(?i)\bgcp\b|\bgoogle cloud\b',
    'DevOps': r'(?i)\bdevops\b',
    'CI/CD': r'(?i)ci[\/\-]cd|cicd',
    'Linux': r'(?i)\blinux\b|\bunix\b',
    'Microsoft Office': r'(?i)\b(?:ms\s*office|microsoft\s*office|office|excel|word|powerpoint)\b',
    'Excel': r'(?i)\bexcel\b',
    'Word': r'(?i)\bword\b',
    'PowerPoint': r'(?i)\bpowerpoint\b',
    'PowerBI': r'(?i)\bpower\s*bi\b',
    'Tableau': r'(?i)\btableau\b',
    'Jira': r'(?i)\bjira\b',
    'Figma': r'(?i)\bfigma\b',
    'Git': r'(?i)\bgit\b|\bgithub\b|\bgitlab\b',
    'GitHub': r'(?i)\bgithub\b',
    'GitLab': r'(?i)\bgitlab\b',
    'REST API': r'(?i)\brest\s*api\b|\brestful\b',
    'Microservices': r'(?i)\bmicroservices\b|\bmicroservice\b',
    'Pandas': r'(?i)\bpandas\b',
    'PyTorch': r'(?i)\bpytorch\b',
    'TensorFlow': r'(?i)\btensorflow\b',
    'Scikit-Learn': r'(?i)\bscikit[\- ]learn\b|\bsklearn\b',
    'Flutter': r'(?i)\bflutter\b',
    'Dart': r'(?i)\bdart\b',
    'Spring': r'(?i)\bspring(?:\s*boot)?\b'
}

COMMON_TECH_STACK = list(TECH_PATTERNS.keys())

class AIAnalyzer:
    def __init__(self, api_key=None):
        self.api_key = api_key or GEMINI_API_KEY

    def translate_summary_to_turkish(self, title, text):
        """
        Translates English job description/summary to clear, professional Turkish.
        Uses Gemini API if key present, or intelligent rule-based translation engine.
        """
        if self.api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.api_key}"
                prompt = f"Aşağıdaki İngilizce iş ilanı metnini akıcı ve profesyonel 2 cümlelik Türkçe iş özetine çevir:\n\n{text[:500]}"
                headers = {"Content-Type": "application/json"}
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                with httpx.Client(timeout=8.0) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        tr_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        if tr_text:
                            return tr_text
            except Exception as e:
                print(f"[AI Translation Warning] Gemini çeviri hatası: {e}")

        # Intelligent Rule-Based Tech Translation Engine
        clean_text = text.strip()
        if not clean_text:
            return "İlan detayları geliştirme ekibi pozisyonu için genel kriterleri içermektedir."

        summary_tr = f"{title} pozisyonu için "
        skills_found = self.extract_skills_rule_based(f"{title} {text}")
        if skills_found:
            skills_str = ", ".join(skills_found[:5])
            summary_tr += f"öncelikli olarak {skills_str} teknolojilerinde deneyimli geliştiriciler aranmaktadır. "
        else:
            summary_tr += "ekip çalışmasına yatkın uzmanlar aranmaktadır. "

        summary_tr += "Görev tanımı projelerin geliştirilmesi, test edilmesi ve teknik altyapının optimize edilmesini kapsamaktadır."
        return summary_tr

    def extract_skills_rule_based(self, text):
        """Fallback NLP rule-based skill & application extraction using precise patterns."""
        if not text:
            return []
        found_skills = set()
        text_str = str(text)

        for name, pattern in TECH_PATTERNS.items():
            if re.search(pattern, text_str):
                found_skills.add(name)

        return sorted(list(found_skills))

    def parse_cv_file(self, file_bytes, filename="cv.pdf"):
        """Extracts plain text from PDF or text CV file with multi-engine fallback and error safety."""
        if not file_bytes:
            return ""
        try:
            filename_lower = str(filename).lower()
            if filename_lower.endswith(".pdf"):
                text = ""
                # Engine 1: pypdf
                try:
                    import io
                    import pypdf
                    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted + "\n"
                except Exception as e1:
                    print(f"[pypdf Parse Warning] {e1}")

                # Engine 2: pdfplumber if pypdf returns short text
                if len(text.strip()) < 30:
                    try:
                        import io
                        import pdfplumber
                        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                            for page in pdf.pages:
                                extracted = page.extract_text()
                                if extracted:
                                    text += extracted + "\n"
                    except Exception as e2:
                        print(f"[pdfplumber Parse Warning] {e2}")

                # Engine 3: Raw stream regex extraction fallback
                if len(text.strip()) < 10:
                    try:
                        raw_str = file_bytes.decode("latin-1", errors="ignore")
                        words = re.findall(r"[a-zA-Z0-9+#.]{2,}", raw_str)
                        text = " ".join(words)
                    except Exception as e3:
                        print(f"[Raw Stream Decode Warning] {e3}")

                return text.strip()
            else:
                return file_bytes.decode("utf-8", errors="ignore").strip()
        except Exception as e:
            print(f"[CV Parse Error] {e}")
            return ""

    def analyze_cv_skills(self, cv_text):
        """Analyzes CV text to detect all technical skills, languages, tools and seniority."""
        if not cv_text or len(cv_text.strip()) < 10:
            return {"skills": [], "seniority": "Orta Seviye (Mid)", "raw_text_len": 0}

        skills = self.extract_skills_rule_based(cv_text)
        text_lower = cv_text.lower()

        if "senior" in text_lower or "kıdemli" in text_lower or "lead" in text_lower or "yıllık deneyim" in text_lower or "uzman" in text_lower:
            seniority = "Kıdemli (Senior)"
        elif "junior" in text_lower or "staj" in text_lower or "intern" in text_lower or "yeni mezun" in text_lower or "asistan" in text_lower:
            seniority = "Başlangıç (Junior)"
        else:
            seniority = "Orta Seviye (Mid)"

        return {
            "skills": sorted(skills),
            "seniority": seniority,
            "raw_text_len": len(cv_text)
        }

    def analyze_job_with_gemini(self, title, description):
        skills = self.extract_skills_rule_based(f"{title} {description}")
        summary_tr = self.translate_summary_to_turkish(title, description)
        return {
            "summary": summary_tr,
            "skills": skills,
            "ai_powered": bool(self.api_key)
        }

    def ask_platform_agent(self, user_query: str, context_data: dict = None) -> str:
        """
        AI Assistant Agent for the platform.
        Answers user questions about site navigation, job filtering, CV upload, alerts, favorites, and live stats.
        """
        query_low = user_query.strip().lower()
        if not query_low:
            return "Size nasıl yardımcı olabilirim? Platform kullanımı, CV yükleme, favoriler veya bildirim alarmları hakkında sorular sorabilirsiniz."

        stats_summary = ""
        if context_data:
            stats_summary = (
                f"Sistemdeki aktif ilan sayısı: {context_data.get('total_jobs', 'N/A')}, "
                f"Uzaktan çalışma oranı: %{context_data.get('remote_ratio', 'N/A')}, "
                f"Aktif şirket sayısı: {context_data.get('unique_companies', 'N/A')}, "
                f"En popüler yetenek: {context_data.get('top_skill', 'N/A')}."
            )

        # Try Gemini API first if key present
        if self.api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.api_key}"
                prompt = (
                    "Sen 'Akıllı Piyasa & Yetenek Analiz Platformu' resmi Akıllı Yapay Zeka Asistanısın.\n"
                    "Platform Bilgileri:\n"
                    "1. CV Yükleme & Uyum Skoru: Sol menüdeki PDF/TXT CV yükleyici ile beceriler taranır ve % Uyum Skoru hesaplanır.\n"
                    "2. Giriş & Kayıt Ol: Sağ üstteki 'Giriş Yap' ve 'Kayıt Ol' butonları ile üye olunabilir.\n"
                    "3. Favoriler: İlan kartlarındaki '☆ Favorilere Ekle' butonu ile ilanlar kaydedilir ve 'Favori İlanlarım' sekmesinde listelenir.\n"
                    "4. Bildirim Alarmları: Sol menüdeki 'Bildirim Alarmı Kur' paneli ile Telegram Chat ID veya E-posta adresine canlı bildirim kurulur.\n"
                    "5. Filtreler & Veri Çekme: Çalışma tipi, Kıdem, Lokasyon, Tazelik filtreleri bulunur. 'Canlı Verileri Güncelle' butonu ile yeni ilanlar çekilir.\n"
                    "6. CSV İndirme: Filtrelenmiş sonuçlar 'CSV Olarak İndir' butonuyla indirilebilir.\n"
                    f"İstatistikler: {stats_summary}\n\n"
                    f"Kullanıcı Sorduğu Soru: {user_query}\n"
                    "Yanıtı son derece kibar, yardımcı ve kısa Türkçe cümlelerle ver."
                )
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                with httpx.Client(timeout=8.0) as client:
                    resp = client.post(url, headers={"Content-Type": "application/json"}, json=payload)
                    if resp.status_code == 200:
                        ans = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        if ans:
                            return ans
            except Exception as e:
                print(f"[AI Agent Warning] Gemini call error: {e}")

        # Intelligent Rule-Based Agent Engine Fallback
        if any(w in query_low for w in ["cv", "özgeçmiş", "pdf", "yükle", "resumé"]):
            return (
                "📄 **CV Yükleme & AI Uyum Skoru:**\n"
                "Sol yan menüde bulunan **'PDF CV ile Otomatik Eşleşme'** kutusundan PDF veya TXT formatındaki CV'nizi sürükleyip bırakabilirsiniz. "
                "Yapay zeka CV'nizdeki teknolojileri otomatik tespit edip ilanlarla **% Kariyer Uyum Skoru** hesaplayacaktır!"
            )

        if any(w in query_low for w in ["favori", "kaydet", "beğen", "star", "liste"]):
            return (
                "⭐ **Favori İlanlar Özelliği:**\n"
                "Her ilan kartının altındaki **'☆ Favorilere Ekle'** butonuna tıklayarak ilgilendiğiniz ilanları kaydedebilirsiniz. "
                "Kaydettiğiniz tüm ilanlar ana sayfadaki **'Favori İlanlarım'** sekmesinde bir arada listelenir!"
            )

        if any(w in query_low for w in ["giriş", "kayıt", "üye", "hesap", "oturum", "şifre"]):
            return (
                "🔐 **Giriş Yap & Kayıt Ol:**\n"
                "Sayfanın sağ üst tarafındaki **'Giriş Yap'** ve **'Kayıt Ol'** butonlarını kullanarak yeni hesap oluşturabilir veya oturum açabilirsiniz. "
                "Oturum açtığınızda favori ilanlarınız hesabınıza kalıcı olarak kaydedilir."
            )

        if any(w in query_low for w in ["alarm", "bildirim", "telegram", "mail", "e-posta", "eposta", "uyarı"]):
            return (
                "🔔 **Bildirim Alarmı Kurma:**\n"
                "Sol menüdeki **'Bildirim Alarmı Kur'** butonuna basarak Telegram Chat ID'nizi veya E-posta adresinizi giriniz. "
                "Seçtiğiniz yetenek ve çalışma tipine uygun yeni bir ilan yayınlandığında anında bildirim alırsınız!"
            )

        if any(w in query_low for w in ["güncelle", "canlı", "veri", "scrape", "çek", "yeni ilan"]):
            return (
                "🔄 **Canlı Veri Güncelleme:**\n"
                "Sol en alttaki **'Canlı Verileri Güncelle'** butonuna basarak RemoteOK ve Arbeitnow API'lerinden en güncel iş ilanlarını anında çekebilir ve Türkçe çevirileriyle listeleyebilirsiniz."
            )

        if any(w in query_low for w in ["csv", "indir", "dışa aktar", "export", "excel"]):
            return (
                "📥 **CSV Veri İndirme:**\n"
                "Ana ekrandaki sekmelerin hemen üzerindeki **'Filtrelenen Verileri CSV Olarak İndir'** butonuna tıklayarak ekranda listelenen tüm ilan verilerini bilgisayarınıza indirebilirsiniz."
            )

        if any(w in query_low for w in ["kaç", "sayı", "istatistik", "oran", "toplam", "uzaktan", "python", "şirket"]):
            if stats_summary:
                return f"📊 **Günün Canlı Piyasa İstatistikleri:**\n{stats_summary}"
            return "📊 Sistemde şu anda 260'tan fazla aktif canlı iş ilanı taranmış ve kategorize edilmiş durumdadır."

        return (
            "🤖 **Platform AI Asistanı:**\n"
            "Ben Akıllı Piyasa & Yetenek Analiz Platformu asistanıyım! Size şu konularda yardımcı olabilirim:\n"
            "• **CV Yükleme:** Sol menüden PDF yükleyerek Uyum Skoru hesaplama.\n"
            "• **Favori İlanlar:** İlanları '☆ Favorilere Ekle' butonuyla kaydetme.\n"
            "• **Bildirim Alarmı:** Telegram veya E-posta ile yeni ilan uyarıları kurma.\n"
            "• **Filtreler & CSV:** Uzaktan/Ofis, Kıdem ve Lokasyon filtresi ile CSV indirme."
        )

    def generate_skill_gap_roadmap(self, user_skills: list, jobs_data: list) -> dict:
        """
        Calculates Skill Gap & Learning Roadmap by comparing user's current skills
        against high-demand missing skills present in current active job listings.
        """
        user_set_low = {s.lower().strip() for s in user_skills}
        
        # Count skill frequency across all jobs
        skill_counts = {}
        total_jobs = len(jobs_data) if jobs_data else 0

        for job in jobs_data:
            if isinstance(job, dict):
                job_skills = job.get("Yetenekler", [])
            else:
                raw_sk = getattr(job, "extracted_skills", "[]")
                try:
                    job_skills = json.loads(raw_sk) if raw_sk else []
                except:
                    job_skills = []
            
            if isinstance(job_skills, list):
                for sk in job_skills:
                    if isinstance(sk, str) and sk.strip():
                        sk_clean = sk.strip()
                        skill_counts[sk_clean] = skill_counts.get(sk_clean, 0) + 1

        # Identify missing skills present in market
        missing_skills = []
        for sk_name, count in sorted(skill_counts.items(), key=lambda x: x[1], reverse=True):
            if sk_name.lower().strip() not in user_set_low:
                pct = round((count / max(1, total_jobs)) * 100, 1)
                missing_skills.append({
                    "skill": sk_name,
                    "count": count,
                    "demand_percentage": pct
                })

        # Top 5 most critical missing skills
        top_missing = missing_skills[:5]
        
        # Simulation: How many more jobs match if top missing skills are learned
        boost_potential = min(100, len(top_missing) * 18) if top_missing else 0

        # Custom learning recommendations for missing technologies
        recommendations = []
        for m in top_missing:
            name = m["skill"]
            pct = m["demand_percentage"]
            rec = {
                "skill": name,
                "demand": f"%{pct} Piyasa Talebi",
                "tip": f"Aktif iş ilanlarının %{pct}'sinde aranan kritik bir teknoloji. {name} yeteneğini öğrenerek başvuru havuzunuzu genişletebilirsiniz."
            }
            recommendations.append(rec)

        return {
            "current_skills": user_skills,
            "top_missing_skills": top_missing,
            "boost_potential_pct": boost_potential,
            "recommendations": recommendations
        }

if __name__ == "__main__":
    analyzer = AIAnalyzer()
    res = analyzer.translate_summary_to_turkish("Senior Python Engineer", "Looking for experienced Python and Docker developer.")
    print("TR Summary:", res)
    print("Agent test:", analyzer.ask_platform_agent("CV nasıl yüklerim?"))


