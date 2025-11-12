from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
import os

app = Flask(__name__)
CORS(app)

# Connect to Heroku Postgres or local DB
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///local.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
 
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ==========================
# Database schema
# ==========================
class GameInstance(Base):
    __tablename__ = "tbl_game_inst"
    game_id = Column(Integer, primary_key=True, autoincrement=True)
    n_cust_served = Column(Integer, default=0)
    n_cust_satisfied = Column(Integer, default=0)
    n_cust_not_satisfied = Column(Integer, default=0)

Base.metadata.create_all(engine)

# ==========================
# API Endpoints
# ==========================

@app.route("/init_game", methods=["POST"])
def init_game():
    """Initialize a new game and return its ID"""
    db = SessionLocal()
    new_game = GameInstance()
    db.add(new_game)
    db.commit()
    game_id = new_game.game_id
    db.close()

    print(f'added new game with id {game_id}')
    return jsonify({"game_id": game_id})


@app.route("/update_game", methods=["POST"])
def update_game():
    """Update customer stats for a given game_id"""
    data = request.json
    game_id = data.get("game_id")
    served = data.get("n_cust_served")
    satisfied = data.get("n_cust_satisfied")
    not_satisfied = data.get("n_cust_not_satisfied")

    if game_id is None:
        return jsonify({"error": "Missing game_id"}), 400

    db = SessionLocal()
    game = db.query(GameInstance).filter(GameInstance.game_id == game_id).first()
    if not game:
        db.close()
        return jsonify({"error": "Game ID not found"}), 404

    # Update only provided fields
    if served is not None:
        game.n_cust_served = served
    if satisfied is not None:
        game.n_cust_satisfied = satisfied
    if not_satisfied is not None:
        game.n_cust_not_satisfied = not_satisfied

    db.commit()
    db.close()

    return jsonify({"status": "success", "game_id": game_id})


@app.route("/get_all", methods=["GET"])
def get_all():
    """Get all game records"""
    db = SessionLocal()
    records = db.query(GameInstance).order_by(GameInstance.game_id.desc()).all()
    db.close()

    result = [
        {
            "game_id": r.game_id,
            "n_cust_served": r.n_cust_served,
            "n_cust_satisfied": r.n_cust_satisfied,
            "n_cust_not_satisfied": r.n_cust_not_satisfied
        }
        for r in records
    ]
    return jsonify(result)

@app.route("/")
def home():
    return "Game API running with /init_game and /update_game endpoints."


if __name__ == "__main__":
    app.run(debug=True)
