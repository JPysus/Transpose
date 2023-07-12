from flask import Flask, send_from_directory

def create_app():
    app = Flask(__name__, static_folder='static')
    from .views import views
    
    @app.route('/images/<path:filename>')
    def base_static(filename):
        return send_from_directory(app.root_path + '/images/', filename)
        
    app.register_blueprint(views, url_prefix='/')
    return app