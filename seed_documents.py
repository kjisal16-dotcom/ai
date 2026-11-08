"""
MAHI AI Document Seeder Script
Ingests sample college documents into ChromaDB vector database and relational database.
"""
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import get_settings
from backend.app.core.logging import logger
from backend.app.db.session import SessionLocal, init_db
from backend.app.db.models import CollegeDocument, AuditLog
from backend.app.services.vector_service import vector_service

settings = get_settings()

SAMPLE_DOCS = [
    {
        "filename": "cs101_data_structures.txt",
        "title": "CS101 Data Structures & Algorithms Syllabus",
        "category": "syllabus",
        "department": "Computer Science",
    },
    {
        "filename": "college_academic_policy.txt",
        "title": "MAHI College Academic Regulations & Attendance Policy",
        "category": "policy",
        "department": "Administration",
    },
    {
        "filename": "faculty_guidelines.txt",
        "title": "Faculty Instructional & Rubric Evaluation Guidelines",
        "category": "guidelines",
        "department": "Academic Senate",
    },
]


def seed():
    logger.info("Initializing relational database tables...")
    init_db()
    db = SessionLocal()

    doc_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "documents"))

    for doc_meta in SAMPLE_DOCS:
        file_path = os.path.join(doc_dir, doc_meta["filename"])
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if already exists in SQL DB
        existing = db.query(CollegeDocument).filter(CollegeDocument.title == doc_meta["title"]).first()
        if existing:
            logger.info(f"Document '{doc_meta['title']}' already exists in database with {existing.chunk_count} chunks.")
            continue

        doc_record = CollegeDocument(
            title=doc_meta["title"],
            category=doc_meta["category"],
            department=doc_meta["department"],
            filename=doc_meta["filename"],
            chunk_count=0
        )
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)

        # Chunk and vectorize in ChromaDB
        chunks_count = vector_service.add_document(
            doc_id=str(doc_record.id),
            title=doc_meta["title"],
            content=content,
            category=doc_meta["category"],
            department=doc_meta["department"]
        )

        doc_record.chunk_count = chunks_count
        db.add(AuditLog(action="SEED_DOCUMENT", actor="system", details={"title": doc_meta["title"], "chunks": chunks_count}))
        db.commit()

        logger.info(f"Successfully seeded '{doc_meta['title']}' -> {chunks_count} vector chunks.")

    db.close()
    stats = vector_service.get_stats()
    logger.info(f"Seeding complete! ChromaDB now holds {stats.get('total_chunks', 0)} total chunks.")


if __name__ == "__main__":
    seed()
