from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy import DateTime, select, Table, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import ipaddress

DATABASE_URI = 'sqlite:///instance/overburn.db'
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class PageHit(Base):
    __tablename__ = 'page_hit'
    id = Column(Integer, primary_key=True)
    page_url = Column(String(500))
    hit_type = Column(String(50))  # 'image', 'valid', 'invalid', 'suspicious'
    visit_datetime = Column(DateTime, default=datetime.utcnow)
    visitor_id = Column(String(100))  # IP or session ID
    referrer_url = Column(String(500))  # URL of the referring page
    user_agent = Column(String(500))  # String representing the client's user agent

def init_db():
    Base.metadata.create_all(engine)

def is_valid_ip(ip_addr):
    try:
        ipaddress.ip_address(ip_addr)
        return True
    except ValueError:
        return False

def track_page(request, response):
    page_url = request.path
    visitor_id = request.headers.get('X-Forwarded-For', request.remote_addr)
    referrer_url = request.referrer or ''
    user_agent = request.user_agent.string or ''

    if not is_valid_ip(visitor_id):
        hit_type = 'suspicious'
    elif ':NaN:' in user_agent:
        hit_type = 'suspicious'
    elif ':NaN:' in referrer_url:
        hit_type = 'suspicious'
    elif response.status_code == 404:
        hit_type = 'invalid'
    elif page_url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        hit_type = 'image'
    else:
        hit_type = 'valid'

    with Session() as session:
        new_hit = PageHit(page_url=page_url, hit_type=hit_type, visitor_id=visitor_id,referrer_url=referrer_url,user_agent=user_agent)
        session.add(new_hit)
        session.commit()

    return response


def fix_db_error():
    Base.metadata.reflect(bind=engine)
        # Access the 'pagehits' table definition using Base.metadata.tables
    pagehits_table = Base.metadata.tables['pagehits']

    with Session() as session:
        # Select all records from 'pagehits'
        select_stmt = select(pagehits_table)
        pagehits_records = session.execute(select_stmt).fetchall()

        # Prepare data for insertion into 'page_hit'
        page_hit_data = [
            {
                "page_url": record.page_url,
                "hit_type": record.hit_type,
                "visit_datetime": record.visit_datetime,
                "visitor_id": record.visitor_id,
                "referrer_url": record.referrer_url,
                "user_agent": record.user_agent,
            }
            for record in pagehits_records
        ]
        
        # Insert data into 'page_hit'
        session.bulk_insert_mappings(PageHit, page_hit_data)
        session.commit()

        # Drop the 'pagehits' table after successful data migration
        pagehits_table.drop(engine)
        print("Data migrated and 'pagehits' table dropped successfully.")
