from flask import Flask
from .routes import main_bp

def create_app():
    app = Flask(__name__)
    
    app.register_blueprint(main_bp)
    
    return app

def main():
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main()
