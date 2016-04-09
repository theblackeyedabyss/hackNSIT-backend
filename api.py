import os
import requests as re
from flask import Flask, jsonify, request, redirect, url_for,session
from flask.ext.cors import CORS
from flask_oauthlib.client import OAuth, OAuthException

from nutritionix import Nutritionix

from werkzeug import secure_filename

import cloudsight

from parse_rest.connection import register
from parse_rest.datatypes import Object
from parse_rest.user import User

register('O6H2V7pJzoOWntRT9hFqpxxHHdJTCLtA7xmnhHZ5', 'olPs7M45S8mx7RpdSOSbAqfZbfBKjLzDzqISSivP', master_key='ZSpZtkfRzOziXOOJEy9kGjaTDVaju64YQcbLeBRH')

auth = cloudsight.SimpleAuth('qAd-COIpRxvKVaNUKrJMMQ')
api = cloudsight.API(auth)

nix = Nutritionix(app_id="76986486", api_key="28882f3d105c4c9e3222a05eeafd049a")

UPLOAD_FOLDER = 'tmp'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
FACEBOOK_APP_ID = os.environ['FACEBOOK_APP_ID']
FACEBOOK_APP_SECRET = os.environ['FACEBOOK_APP_SECRET']

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)
app.secret_key = 'development'

oauth = OAuth(app)

facebook = oauth.remote_app(
    'facebook',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': 'email'},
    base_url='https://graph.facebook.com',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    access_token_method='GET',
    authorize_url='https://www.facebook.com/dialog/oauth'
)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route("/")
def helloWorld():
  return "Hello, world! <a href='https://github.com/CapsLockHacks/hackNSIT-backend'>Fork me on GitHub!</a>"

@app.route('/user/register', methods=[ 'POST'])
def user_register():
    if request.method == 'POST':
        user_name = request.form['user']
        password  = request.form['password']
        phone     = request.form['phone']
        u = User.signup("test1", "1234", phone="123123")
        return "Done!"



@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            response = api.image_request(file, file.filename, {
                'image_request[locale]': 'en-US',
            })

            status = api.image_response(response['token'])
            if status['status'] != cloudsight.STATUS_NOT_COMPLETED:
                # Done!
                pass
            status = api.wait(response['token'], timeout=30)

            #print(status)

            result = nix.search(status["name"], results="0:1").json()["hits"][0]["fields"]["item_id"]
			
            return jsonify(result=nix.item(id=result).json())


@app.route('/connect')
def login():
    callback = url_for(
        'facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True
    )
    return facebook.authorize(callback=callback)


@app.route('/login/authorized')
def facebook_authorized():
    resp = facebook.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    if isinstance(resp, OAuthException):
        return 'Access denied: %s' % resp.message

    session['oauth_token'] = (resp['access_token'], '')
    return redirect('/')


@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port,debug=True)
