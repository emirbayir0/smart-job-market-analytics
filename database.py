import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL

Base = declarative_base()

class JobListing(Base):
    __tablename__ = "job_listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255), default="Uzaktan / Belirtilmedi")
    salary = Column(String(100), default="Belirtilmedi")
    job_type = Column(String(50), default="Uzaktan")
    experience_level = Column(String(50), default="Orta Seviye")
    description = Column(Text, nullable=True)
    url = Column(String(500), unique=True, nullable=False)
    source = Column(String(100), default="Web Scraper")
    extracted_skills = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)

class ScrapeLog(Base):
    __tablename__ = "scrape_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_scraped = Column(Integer, default=0)
    new_added = Column(Integer, default=0)
    status = Column(String(50), default="SUCCESS")
    message = Column(Text, default="")

class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel = Column(String(50), default="Telegram")
    target_address = Column(String(255), nullable=False)
    skills_filter = Column(Text, default="[]")
    job_type_filter = Column(Text, default="[]")
    experience_filter = Column(Text, default="[]")
    location_filter = Column(Text, default="[]")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserFavorite(Base):
    __tablename__ = "user_favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    job_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def register_user(username, email, password):
    db = SessionLocal()
    try:
        username_clean = username.strip()
        email_clean = email.strip().lower()
        if db.query(User).filter(User.username == username_clean).first():
            return False, "Bu kullanıcı adı zaten alınmış."
        if db.query(User).filter(User.email == email_clean).first():
            return False, "Bu e-posta adresi zaten kayıtlı."

        new_user = User(
            username=username_clean,
            email=email_clean,
            password_hash=hash_password(password)
        )
        db.add(new_user)
        db.commit()
        return True, "Kayıt başarılı! Şimdi giriş yapabilirsiniz."
    except Exception as e:
        db.rollback()
        return False, f"Kayıt hatası: {e}"
    finally:
        db.close()

def authenticate_user(username_or_email, password):
    db = SessionLocal()
    try:
        query_val = username_or_email.strip()
        hashed = hash_password(password)
        user = db.query(User).filter(
            ((User.username == query_val) | (User.email == query_val.lower())) &
            (User.password_hash == hashed)
        ).first()
        if user:
            return True, {"id": user.id, "username": user.username, "email": user.email}
        return False, "Kullanıcı adı/e-posta veya şifre hatalı."
    finally:
        db.close()

def toggle_user_favorite(user_id, job_id):
    db = SessionLocal()
    try:
        existing = db.query(UserFavorite).filter(
            UserFavorite.user_id == user_id,
            UserFavorite.job_id == job_id
        ).first()
        if existing:
            db.delete(existing)
            db.commit()
            return False, "Favorilerden çıkarıldı."
        else:
            new_fav = UserFavorite(user_id=user_id, job_id=job_id)
            db.add(new_fav)
            db.commit()
            return True, "Favorilere eklendi!"
    except Exception as e:
        db.rollback()
        return False, f"Hata: {e}"
    finally:
        db.close()

def get_user_favorite_job_ids(user_id):
    db = SessionLocal()
    try:
        favs = db.query(UserFavorite.job_id).filter(UserFavorite.user_id == user_id).all()
        return set([f[0] for f in favs])
    finally:
        db.close()

def dispatch_alerts_for_new_jobs(new_jobs):
    """Checks newly saved jobs against active DB alert rules and sends notifications."""
    if not new_jobs:
        return
    try:
        from notifier import TelegramNotifier
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
        print(f"[Alert Dispatch Error] {e}")

def save_jobs(jobs_data):
    db = SessionLocal()
    new_added = 0
    new_jobs_list = []
    try:
        for job in jobs_data:
            existing = db.query(JobListing).filter(JobListing.url == job["url"]).first()
            if not existing:
                skills_json = json.dumps(job.get("extracted_skills", []))
                new_job = JobListing(
                    title=job["title"],
                    company=job["company"],
                    location=job.get("location", "Uzaktan"),
                    salary=job.get("salary", "Belirtilmedi"),
                    job_type=job.get("job_type", "Uzaktan"),
                    experience_level=job.get("experience_level", "Orta Seviye"),
                    description=job.get("description", ""),
                    url=job["url"],
                    source=job.get("source", "Otomatik Scraper"),
                    extracted_skills=skills_json
                )
                db.add(new_job)
                new_added += 1
                new_jobs_list.append(job)
        db.commit()
        if new_added > 0:
            dispatch_alerts_for_new_jobs(new_jobs_list)
        return len(jobs_data), new_added
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def save_alert_rule(channel, target_address, skills, job_types, experiences, locations):
    """Saves a new user alert rule to the database."""
    db = SessionLocal()
    try:
        rule = AlertRule(
            channel=channel,
            target_address=target_address,
            skills_filter=json.dumps(skills),
            job_type_filter=json.dumps(job_types),
            experience_filter=json.dumps(experiences),
            location_filter=json.dumps(locations),
            is_active=True
        )
        db.add(rule)
        db.commit()
        return rule.id
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_active_alert_rules():
    """Retrieves all active alert rules."""
    db = SessionLocal()
    try:
        return db.query(AlertRule).filter(AlertRule.is_active == True).all()
    finally:
        db.close()

def delete_alert_rule(rule_id):
    """Deactivates/deletes an alert rule by ID."""
    db = SessionLocal()
    try:
        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if rule:
            db.delete(rule)
            db.commit()
            return True
        return False
    finally:
        db.close()

def log_event(total_scraped, new_added, status="SUCCESS", message=""):
    db = SessionLocal()
    try:
        log = ScrapeLog(
            total_scraped=total_scraped,
            new_added=new_added,
            status=status,
            message=message
        )
        db.add(log)
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully with AlertRule model.")
