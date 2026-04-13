from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.get("/health")
def health():
    return {"status": "API running"}
