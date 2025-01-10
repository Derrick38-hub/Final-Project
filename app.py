from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.ext.declarative import declarative_base

from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI
app = FastAPI()

# CORS settings
origins = [
    "http://localhost",
    "http://127.0.0.1:5500",  # Add the live server's origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up the database URL (adjust this to match your MySQL credentials)
DATABASE_URL = 'mysql+pymysql://root@localhost:3306/testdb3'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Define the Book model
class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)

    # Relationship to authors through the association table
    authors = relationship("Author", secondary="author_books", back_populates="books")

# Update the Author model
class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)

    # Relationship to books through the association table
    books = relationship("Book", secondary="author_books", back_populates="authors")

# Association table for many-to-many relationship
author_books = Table(
    "author_books",
    Base.metadata,
    Column("author_id", Integer, ForeignKey("authors.id"), primary_key=True),
    Column("book_id", Integer, ForeignKey("books.id"), primary_key=True),
)

# Create the tables
Base.metadata.create_all(bind=engine)

# Dependency to handle database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define the FastAPI routes

@app.get("/authors/")
def get_authors(db: Session = Depends(get_db)):
    authors = db.query(Author).all()
    return [{"id": author.id, "name": author.name} for author in authors]

@app.post("/authors/")
def create_author(author: dict = Body(...), db: Session = Depends(get_db)):
    name = author.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    new_author = Author(name=name)
    db.add(new_author)
    db.commit()
    db.refresh(new_author)
    return {"id": new_author.id, "name": new_author.name}

@app.post("/authors/delete/")
def delete_author(author: dict = Body(...), db: Session = Depends(get_db)):
    author_id = author.get("id")
    author_to_delete = db.query(Author).filter(Author.id == author_id).first()

    if not author_to_delete:
        raise HTTPException(status_code=404, detail="Author not found")

    db.delete(author_to_delete)
    db.commit()
    return {"message": f"Author {author_to_delete.name} deleted"}

@app.put("/authors/update/")
def update_author(author: dict = Body(...), db: Session = Depends(get_db)):
    author_id = author.get("id")
    new_name = author.get("name")

    if not author_id or not new_name:
        raise HTTPException(
            status_code=400, detail="Author ID, Name are required")

    author_to_update = db.query(Author).filter(Author.id == author_id).first()

    if not author_to_update:
        raise HTTPException(status_code=404, detail="Author not found")

    author_to_update.name = new_name
    db.commit()
    db.refresh(author_to_update)

    return {
        "id": author_to_update.id,
        "name": author_to_update.name,
        "message": "Author updated successfully"
    }

@app.get("/books/")
def get_books(db: Session = Depends(get_db)):
    books = db.query(Book).all()
    return [{"id": book.id, "title": book.title} for book in books]

@app.post("/books/")
def create_book(book: dict = Body(...), db: Session = Depends(get_db)):
    title = book.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    new_book = Book(title=title)
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return {"id": new_book.id, "title": new_book.title}

@app.put("/books/update/")
def update_book(book: dict = Body(...), db: Session = Depends(get_db)):
    book_id = book.get("id")
    new_title = book.get("title")

    if not book_id or not new_title:
        raise HTTPException(
            status_code=400, detail="Book ID and Title are required")

    book_to_update = db.query(Book).filter(Book.id == book_id).first()

    if not book_to_update:
        raise HTTPException(status_code=404, detail="Book not found")

    book_to_update.title = new_title
    db.commit()
    db.refresh(book_to_update)

    return {
        "id": book_to_update.id,
        "title": book_to_update.title,
        "message": "Book updated successfully"
    }

@app.get("/authors/{author_id}/books/")
def get_author_books(author_id: int, db: Session = Depends(get_db)):
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    return [{"id": book.id, "title": book.title} for book in author.books]

@app.post("/authors/enroll/")
def enroll_author(enrollment: dict = Body(...), db: Session = Depends(get_db)):
    author_id = enrollment.get("author_id")
    book_id = enrollment.get("book_id")

    if not author_id or not book_id:
        raise HTTPException(status_code=400, detail="Author ID, Book ID are required")

    author = db.query(Author).filter(Author.id == author_id).first()
    book = db.query(Book).filter(Book.id == book_id).first()

    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    author.books.append(book)
    db.commit()

    return {"message": f"Author {author.name} enrolled in book {book.title}"}

@app.get("/books/{book_id}/authors/")
def get_book_authors(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    return [{"id": author.id, "name": author.name} for author in book.authors]

@app.post("/authors/{author_id}/drop/")
def drop_author_from_book(author_id: int, book: dict = Body(...), db: Session = Depends(get_db)):
    book_id = book.get("book_id")
    author = db.query(Author).filter(Author.id == author_id).first()
    book = db.query(Book).filter(Book.id == book_id).first()

    if not author or not book:
        raise HTTPException(status_code=404, detail="Author or Book not found")

    author.books.remove(book)
    db.commit()
    db.refresh(author)
    return {"message": f"Author {author.name} dropped from book {book.title}"}
