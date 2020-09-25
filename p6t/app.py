#!/usr/bin/env python3
from flask import Flask
from p6t.settings import settings
app = Flask(__name__, instance_relative_config=True)


@app.route("/hello")
def hello():
    return "Hello, World!"

# apply the blueprints to the app
from p6t import cxml

app.register_blueprint(cxml.bp)
app.secret_key = settings.SESSION_SECRET_KEY

# make url_for('index') == url_for('blog.index')
# in another app, you might define a separate main index here with
# app.route, while giving the blog blueprint a url_prefix, but for
# the tutorial the blog will be the main index
# app.add_url_rule("/", "cxml")

if __name__ == "__main__":
    app.run()
