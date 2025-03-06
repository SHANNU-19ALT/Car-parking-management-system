from app import app, db

# Wrap in app context
with app.app_context():
    db.create_all()
    print("Database initialized successfully!")
