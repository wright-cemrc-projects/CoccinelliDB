import os
from app import create_app
from config import DevelopmentConfig, TestingConfig, ProductionConfig

# Map environment to config classes
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_map.get(config_name, DevelopmentConfig))

if __name__ == "__main__":
    app.run(debug=True, port=8080)
