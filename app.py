
import uuid
from datetime import datetime
from flask import Flask, redirect, render_template, url_for

from utils.helper import Helper

app = Flask(__name__)

today_codes = str(uuid.uuid5(uuid.NAMESPACE_DNS, datetime.now().strftime('%Y%m%d'))).split('-')

@app.errorhandler(404)
def page_not_found(e):
    # Redirect to a specific endpoint, like 'today', or a custom 404 page
    return redirect(url_for('today', code='guest')), 302
  
@app.route('/<code>')
def today(code): 
    matches, played, won = Helper().fetch_matches('', '=', '')
    return render_template('index.html', today_codes=today_codes, code=code, header="Today Games Predictions", matches=matches, played=played, won=won, get_background_color=Helper().get_background_color, highlight_analysis=Helper().highlight_analysis)

@app.route('/tomorrow/<code>')
def tomorrow(code):    
    matches, played, won = Helper().fetch_matches('+1', '=', '')
    return render_template('index.html', today_codes=today_codes, code=code, header="Tomorrow Games Predictions", matches = matches, played = played, won = won, get_background_color=Helper().get_background_color, highlight_analysis=Helper().highlight_analysis )

@app.route('/yesterday/<code>')
def yesterday(code):    
    matches, played, won = Helper().fetch_matches('-1', '=')
    return render_template('index.html', today_codes=today_codes, code=code, header="Yesterday's Predictions Results", matches = matches, played = played, won = won, get_background_color=Helper().get_background_color, highlight_analysis=Helper().highlight_analysis )

@app.route('/history/<code>')
def history(code):    
    matches, played, won = Helper().fetch_matches('-7', '>=')
    return render_template('index.html', today_codes=today_codes, code=code, header="Last 7-Days Predictions Results", matches = matches, played = played, won = won, get_background_color=Helper().get_background_color, highlight_analysis=Helper().highlight_analysis )

@app.route('/download/<code>')
def download(code):    
    return render_template('download.html', today_codes=today_codes, code=code)

if __name__ == '__main__':
    app.run(debug=True)
