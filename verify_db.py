import sqlalchemy
from sqlalchemy.orm import sessionmaker

# Define the SQLite database URL
DATABASE_URL = "sqlite:///conflicts.db"

# Create a SQLAlchemy engine
engine = sqlalchemy.create_engine(DATABASE_URL)

# Create a session factory
SessionFactory = sessionmaker(bind=engine)

def verify_data():
    with SessionFactory() as session:
        print("Verifying database content...\n")

        tables = ["authors", "papers", "funders", "institutions", "author_funders"]
        
        for table_name in tables:
            print(f"--- Table: {table_name} ---")
            
            # Get row count
            count_query = sqlalchemy.text(f"SELECT COUNT(*) FROM {table_name}")
            row_count = session.execute(count_query).scalar_one()
            print(f"Row count: {row_count}")
            
            # Get one sample row
            if row_count > 0:
                sample_query = sqlalchemy.text(f"SELECT * FROM {table_name} LIMIT 1")
                sample_row = session.execute(sample_query).first()
                print(f"Sample row: {sample_row}")
            else:
                print("No rows in table.")
            print("\n")

if __name__ == "__main__":
    verify_data()
