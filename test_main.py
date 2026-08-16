import os
import pytest
from main import DatabaseManager

@pytest.fixture
def db():
    """ტესტებისთვის დროებითი ბაზის შექმნა"""
    test_db_name = "test_lingolens.db"
    db_mgr = DatabaseManager(db_name=test_db_name)
    yield db_mgr
    # ტესტის დასრულების შემდეგ ბაზის წაშლა
    if os.path.exists(test_db_name):
        os.remove(test_db_name)

def test_offline_dictionary(db):
    """ამოწმებს ოფლაინ ლექსიკონის თარგმნას"""
    translation = db.translate_offline("hello world")
    assert translation == "გამარჯობა სამყარო"

def test_history_addition(db):
    """ამოწმებს ისტორიაში ჩანაწერის დამატებას"""
    db.add_history("book", "წიგნი")
    history = db.get_history()
    assert len(history) > 0
    assert history[0][0] == "book"
    assert history[0][1] == "წიგნი"

def test_flashcard_saving(db):
    """ამოწმებს Flashcard-ის შენახვას"""
    result = db.save_flashcard("water", "წყალი")
    assert result is True
