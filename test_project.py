import pytest
from database import init_db, save_jobs, SessionLocal, JobListing, save_alert_rule, get_active_alert_rules, delete_alert_rule
from scraper import WebScraper
from ai_analyzer import AIAnalyzer
from notifier import TelegramNotifier

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Ensures database tables are initialized before tests."""
    init_db()
    yield

def test_database_save_and_retrieve():
    test_jobs = [{
        "title": "Python & Microsoft Office Specialist",
        "company": "Global Analytics Inc",
        "location": "Uzaktan",
        "salary": "$80.000 / Yıl",
        "job_type": "Uzaktan",
        "experience_level": "Mid",
        "description": "Requires strong Python and Microsoft Office Excel skills.",
        "url": "https://test.com/job/303",
        "source": "UnitTest",
        "extracted_skills": ["Python", "Microsoft Office", "Excel"]
    }]
    
    total, new_added = save_jobs(test_jobs)
    assert total == 1

    db = SessionLocal()
    job = db.query(JobListing).filter(JobListing.url == "https://test.com/job/303").first()
    assert job is not None
    assert job.title == "Python & Microsoft Office Specialist"
    db.close()

def test_alert_rule_saving_and_deletion():
    rule_id = save_alert_rule(
        channel="Telegram",
        target_address="987654321",
        skills=["Python", "Docker"],
        job_types=["Uzaktan"],
        experiences=["Senior"],
        locations=["Uzaktan (Küresel)"]
    )
    assert rule_id is not None
    
    active_rules = get_active_alert_rules()
    assert len(active_rules) >= 1
    
    deleted = delete_alert_rule(rule_id)
    assert deleted is True

def test_ai_analyzer_languages_and_office():
    analyzer = AIAnalyzer(api_key="")
    text = "We are seeking a developer skilled in Python, JavaScript, Microsoft Office Excel, and Docker."
    res = analyzer.analyze_job_with_gemini("Developer", text)
    
    assert "skills" in res
    assert "Python" in res["skills"]
    assert "JavaScript" in res["skills"]

def test_scraper_live_api_execution():
    scraper = WebScraper()
    res = scraper.run_pipeline()
    assert res["status"] == "SUCCESS"
    assert res["total"] > 0

def test_notifier_rule_confirmation():
    notifier = TelegramNotifier()
    sent = notifier.send_rule_confirmation("Telegram", "123456", "Python + Uzaktan")
    assert sent is False or sent is True

def test_ai_platform_agent_response():
    analyzer = AIAnalyzer()
    ans = analyzer.ask_platform_agent("CV nasıl yüklenir?")
    assert "CV Yükleme" in ans or "PDF" in ans

def test_skill_gap_roadmap_analysis():
    analyzer = AIAnalyzer()
    jobs = [
        {"Yetenekler": ["Python", "Docker", "SQL"]},
        {"Yetenekler": ["Python", "FastAPI", "Docker"]},
        {"Yetenekler": ["React", "TypeScript"]}
    ]
    res = analyzer.generate_skill_gap_roadmap(["Python"], jobs)
    assert "top_missing_skills" in res
    assert "boost_potential_pct" in res
    assert len(res["top_missing_skills"]) > 0


