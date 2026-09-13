import hashlib
from datetime import datetime, timedelta, timezone
from app.db.database import SessionLocal, engine
from app.models import Base, Category, Source, Article, RegionType

# Ensure tables exist
Base.metadata.create_all(bind=engine)


def get_url_hash(url: str) -> str:
    return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()


def seed_database():
    db = SessionLocal()
    try:
        print("[*] Starting BharatLens Phase 2 database seeding...")

        # 1. Seed 11 Categories
        categories_data = [
            {"name": "Politics", "slug": "politics", "display_order": 1},
            {"name": "Sports", "slug": "sports", "display_order": 2},
            {"name": "Technology", "slug": "technology", "display_order": 3},
            {"name": "Business", "slug": "business", "display_order": 4},
            {"name": "Movies / Entertainment", "slug": "movies-entertainment", "display_order": 5},
            {"name": "Education", "slug": "education", "display_order": 6},
            {"name": "Science", "slug": "science", "display_order": 7},
            {"name": "Health", "slug": "health", "display_order": 8},
            {"name": "Lifestyle", "slug": "lifestyle", "display_order": 9},
            {"name": "Crime", "slug": "crime", "display_order": 10},
            {"name": "Environment", "slug": "environment", "display_order": 11},
        ]

        category_map = {}
        for cat_dict in categories_data:
            existing = db.query(Category).filter(Category.slug == cat_dict["slug"]).first()
            if not existing:
                category = Category(**cat_dict, is_active=True)
                db.add(category)
                db.flush()
                category_map[cat_dict["slug"]] = category.id
                print(f"  + Added Category: {cat_dict['name']}")
            else:
                category_map[cat_dict["slug"]] = existing.id

        # 2. Seed Sources
        sources_data = [
            {"name": "The Hindu", "base_url": "https://thehindu.com", "country": "IN"},
            {"name": "Indian Express", "base_url": "https://indianexpress.com", "country": "IN"},
            {"name": "NDTV News", "base_url": "https://ndtv.com", "country": "IN"},
            {"name": "Times of India", "base_url": "https://timesofindia.indiatimes.com", "country": "IN"},
            {"name": "Mint", "base_url": "https://livemint.com", "country": "IN"},
            {"name": "Reuters Global", "base_url": "https://reuters.com", "country": "GLOBAL"},
            {"name": "BBC World", "base_url": "https://bbc.com", "country": "GLOBAL"},
        ]

        source_map = {}
        for src_dict in sources_data:
            existing = db.query(Source).filter(Source.name == src_dict["name"]).first()
            if not existing:
                source = Source(**src_dict)
                db.add(source)
                db.flush()
                source_map[src_dict["name"]] = source.id
                print(f"  + Added Source: {src_dict['name']}")
            else:
                source_map[src_dict["name"]] = existing.id

        # 3. Seed Sample Demo Articles
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        sample_articles = [
            # India - Technology - Gujarat
            {
                "title": "India Inaugurates First Commercial 2nm Semiconductor Fabrication Hub in Gujarat",
                "description": "The $10 billion semiconductor foundry represents a historic leap in national chip sovereignty, creating 35,000 advanced engineering jobs.",
                "canonical_url": "https://example.com/demo/articles/india-2nm-semiconductor-gujarat",
                "source_id": source_map.get("The Hindu"),
                "category_id": category_map.get("technology"),
                "region": "INDIA",
                "state": "Gujarat",
                "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80",
                "author": "Suresh Narayanan",
                "published_at": now - timedelta(hours=2),
            },
            # India - Politics - Telangana
            {
                "title": "Telangana Unveils Next-Gen AI City Masterplan on Hyderabad Outskirts",
                "description": "Spanning 200 acres near Mucherla, the AI City will host global computational research centers and open-source AI foundation labs.",
                "canonical_url": "https://example.com/demo/articles/telangana-ai-city-masterplan",
                "source_id": source_map.get("Indian Express"),
                "category_id": category_map.get("politics"),
                "region": "INDIA",
                "state": "Telangana",
                "image_url": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=800&q=80",
                "author": "K. V. Ramana",
                "published_at": now - timedelta(hours=4),
            },
            # India - Science - Karnataka
            {
                "title": "ISRO Shukrayaan-1 Completes Final Orbital Integration Test Ahead of Venus Mission",
                "description": "Equipped with synthetic aperture radar and atmospheric spectrometers, the spacecraft will study Venusian atmospheric volcanism.",
                "canonical_url": "https://example.com/demo/articles/isro-shukrayaan-venus-mission",
                "source_id": source_map.get("NDTV News"),
                "category_id": category_map.get("science"),
                "region": "INDIA",
                "state": "Karnataka",
                "image_url": "https://images.unsplash.com/photo-1614728894747-a83421e2b9c9?auto=format&fit=crop&w=800&q=80",
                "author": "Pooja Bhatia",
                "published_at": now - timedelta(hours=6),
            },
            # India - Sports - Maharashtra
            {
                "title": "India Wins Historic Test Series Finale at Lord's with Record 4th Innings Chase",
                "description": "Riding on twin centuries and an extraordinary tail-end partnership, Team India clinched a memorable series victory.",
                "canonical_url": "https://example.com/demo/articles/india-test-victory-lords",
                "source_id": source_map.get("Times of India"),
                "category_id": category_map.get("sports"),
                "region": "INDIA",
                "state": "Maharashtra",
                "image_url": "https://images.unsplash.com/photo-1531415074868-036b1c575351?auto=format&fit=crop&w=800&q=80",
                "author": "Rohit Sengupta",
                "published_at": now - timedelta(hours=8),
            },
            # India - Environment - Kerala
            {
                "title": "Western Ghats Ecological Corridor Expansion Gains Approval Across 4 Southern States",
                "description": "A contiguous 1,200 km wildlife corridor receives statutory sanctuary status to protect endangered lion-tailed macaques and Nilgiri tahrs.",
                "canonical_url": "https://example.com/demo/articles/western-ghats-corridor-expansion",
                "source_id": source_map.get("The Hindu"),
                "category_id": category_map.get("environment"),
                "region": "INDIA",
                "state": "Kerala",
                "image_url": "https://images.unsplash.com/photo-1511497584788-87676104235f?auto=format&fit=crop&w=800&q=80",
                "author": "Ananya Nair",
                "published_at": now - timedelta(hours=10),
            },
            # India - Business - Maharashtra
            {
                "title": "RBI Expands Cross-Border UPI Settlement to 18 Additional Countries",
                "description": "Travelers and cross-border businesses can now execute instantaneous merchant payments without foreign exchange surcharge.",
                "canonical_url": "https://example.com/demo/articles/rbi-cross-border-upi-expansion",
                "source_id": source_map.get("Mint"),
                "category_id": category_map.get("business"),
                "region": "INDIA",
                "state": "Maharashtra",
                "image_url": "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=800&q=80",
                "author": "Deepak Varma",
                "published_at": now - timedelta(hours=12),
            },
            # India - Health - Uttar Pradesh
            {
                "title": "AI-Powered Portable Tuberculosis Screening Rolled Out Across 5,000 Rural Clinics",
                "description": "Developed by AIIMS and Bengaluru researchers, the handheld battery-operated scanner delivers verified diagnostic results within 90 seconds.",
                "canonical_url": "https://example.com/demo/articles/ai-portable-tb-screening-rural",
                "source_id": source_map.get("NDTV News"),
                "category_id": category_map.get("health"),
                "region": "INDIA",
                "state": "Uttar Pradesh",
                "image_url": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=800&q=80",
                "author": "Dr. R. K. Saxena",
                "published_at": now - timedelta(hours=14),
            },
            # India - Education - Delhi
            {
                "title": "Delhi Higher Education Council Launches Unified Quantum Computing Student Fellowship",
                "description": "Over 1,000 undergraduate researchers across IIT Delhi, DTU, and DU will receive specialized quantum hardware access and monthly stipends.",
                "canonical_url": "https://example.com/demo/articles/delhi-quantum-computing-fellowship",
                "source_id": source_map.get("Indian Express"),
                "category_id": category_map.get("education"),
                "region": "INDIA",
                "state": "Delhi",
                "image_url": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=800&q=80",
                "author": "Meenakshi Iyer",
                "published_at": now - timedelta(hours=16),
            },
            # India - Crime - West Bengal
            {
                "title": "Indian Cyber Crime Coordination Centre Neutralizes Multi-State Deepfake Syndicate",
                "description": "Joint operations lead to the neutralization of an organized fraud network exploiting real-time synthetic voice spoofing.",
                "canonical_url": "https://example.com/demo/articles/cyber-crime-deepfake-bust",
                "source_id": source_map.get("Indian Express"),
                "category_id": category_map.get("crime"),
                "region": "INDIA",
                "state": "West Bengal",
                "image_url": "https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=800&q=80",
                "author": "Aritra Banerjee",
                "published_at": now - timedelta(hours=18),
            },
            # India - Entertainment - Tamil Nadu
            {
                "title": "National Cinema Conclave Honors Regional Pan-Indian Storytelling in Chennai",
                "description": "Filmmakers celebrate cultural authenticity, multilingual synchronization, and high-fidelity visual effects in Indian cinema.",
                "canonical_url": "https://example.com/demo/articles/national-cinema-conclave-chennai",
                "source_id": source_map.get("The Hindu"),
                "category_id": category_map.get("movies-entertainment"),
                "region": "INDIA",
                "state": "Tamil Nadu",
                "image_url": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=800&q=80",
                "author": "Vikram Sridhar",
                "published_at": now - timedelta(hours=20),
            },
            # India - Lifestyle - Rajasthan
            {
                "title": "Rajasthan Heritage Conservation Guild Restores 14th-Century Stepwells for Sustainable Tourism",
                "description": "Ancient stepwells (baoris) across Jodhpur and Bundi undergo ecological desilting and solar nighttime illumination.",
                "canonical_url": "https://example.com/demo/articles/rajasthan-stepwell-heritage-conservation",
                "source_id": source_map.get("The Hindu"),
                "category_id": category_map.get("lifestyle"),
                "region": "INDIA",
                "state": "Rajasthan",
                "image_url": "https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=800&q=80",
                "author": "Devendra Shekhawat",
                "published_at": now - timedelta(hours=22),
            },
            # International - Environment - Global
            {
                "title": "UN Climate Summit Concludes in Geneva with Binding Methane Reduction Treaty",
                "description": "Over 140 nations agree to enforce strict satellite monitoring and penalties for industrial flaring, marking an ambitious milestone.",
                "canonical_url": "https://example.com/demo/articles/un-methane-climate-treaty-geneva",
                "source_id": source_map.get("Reuters Global"),
                "category_id": category_map.get("environment"),
                "region": "INTERNATIONAL",
                "state": None,
                "image_url": "https://images.unsplash.com/photo-1569163139599-0f4517e36f51?auto=format&fit=crop&w=800&q=80",
                "author": "Claire Tremblay",
                "published_at": now - timedelta(hours=3),
            },
            # International - Technology - Global
            {
                "title": "Autonomous Commercial Aviation Crosses 10 Million Passengers in North America & Europe",
                "description": "Aviation safety regulators publish first comprehensive five-year safety audit showing zero pilotless fleet incidents.",
                "canonical_url": "https://example.com/demo/articles/autonomous-commercial-aviation-milestone",
                "source_id": source_map.get("BBC World"),
                "category_id": category_map.get("technology"),
                "region": "INTERNATIONAL",
                "state": None,
                "image_url": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=800&q=80",
                "author": "Marcus Vance",
                "published_at": now - timedelta(hours=5),
            },
            # International - Business - Global
            {
                "title": "Global Central Banks Announce Interoperable Digital Currency Settlement Corridor",
                "description": "The Project Agora initiative tests sub-second atomic cross-border settlement between Tokyo, London, Singapore, and New York.",
                "canonical_url": "https://example.com/demo/articles/global-cbdc-interoperable-corridor",
                "source_id": source_map.get("Reuters Global"),
                "category_id": category_map.get("business"),
                "region": "INTERNATIONAL",
                "state": None,
                "image_url": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=800&q=80",
                "author": "Elena Rostova",
                "published_at": now - timedelta(hours=7),
            },
            # International - Science - Global
            {
                "title": "James Webb Space Telescope Detects Atmospheric Water Vapor on Habitable-Zone Exoplanet",
                "description": "Spectroscopic analysis of K2-18b confirms rich water clouds and carbon signatures 120 light-years away in Leo constellation.",
                "canonical_url": "https://example.com/demo/articles/jwst-water-vapor-exoplanet",
                "source_id": source_map.get("Reuters Global"),
                "category_id": category_map.get("science"),
                "region": "INTERNATIONAL",
                "state": None,
                "image_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=800&q=80",
                "author": "Dr. Julian Thorne",
                "published_at": now - timedelta(hours=9),
            },
            # International - Sports - Global
            {
                "title": "World Athletics Council Approves Carbon-Neutral Smart Stadium Protocol for 2028 Games",
                "description": "Next-generation aerodynamic tracks and kinetic energy capture will power entire athletic villages.",
                "canonical_url": "https://example.com/demo/articles/world-athletics-smart-stadiums",
                "source_id": source_map.get("BBC World"),
                "category_id": category_map.get("sports"),
                "region": "INTERNATIONAL",
                "state": None,
                "image_url": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=800&q=80",
                "author": "David Miller",
                "published_at": now - timedelta(hours=11),
            },
        ]

        inserted_count = 0
        for art_dict in sample_articles:
            url_hash = get_url_hash(art_dict["canonical_url"])
            existing = db.query(Article).filter(Article.url_hash == url_hash).first()
            if not existing:
                article = Article(
                    **art_dict,
                    url_hash=url_hash,
                    fetched_at=now,
                    created_at=now,
                    is_demo=True,
                )
                db.add(article)
                inserted_count += 1

        db.commit()
        print(f"[*] Seeding complete: {inserted_count} sample articles added.")
    except Exception as e:
        db.rollback()
        print(f"[!] Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
