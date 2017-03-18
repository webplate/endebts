#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import shutil

import config as CONFIG
import endebts

from flask import Flask, render_template, request, redirect, url_for, flash, make_response
# i18n
from flask_babel import Babel

app = Flask(__name__)
app.secret_key = 'Zak8a9b7wvUkuBAMBLVKaAtBAM73CjuXeFBKw72Ti7jhf'
babel = Babel(app)

# send translation according to browser header
@babel.localeselector
def get_locale():
    print(request.accept_languages.best_match(CONFIG.LANGUAGES.keys()))
    return request.accept_languages.best_match(CONFIG.LANGUAGES.keys())

# the global variable for storing endebtmentgraphs requested by users
# not reloading them everytime
GLOBALDEBTS = {}

def remove_dupli(l):
    out = []
    for i in l:
        if i not in out:
            out.append(i)
    return out

def valid_transaction(giver, receiver, description, amount):
    try:
        a = float(amount)
    except ValueError:
        a = 0
    if ( giver != ''
        and receiver != []
        and description != ''
        and len(description) < CONFIG.MAXDESCLEN
        and a != 0):
            return True
    else:
        return False

def format_histo(histo):
    # format history (in reverse and no visible tuples)
    history=histo[::-1]
    formated_hist = []
    for line in history:
        rcv_text = ''
        for r in line[4]:
            rcv_text += r + ', '
        rcv_text = rcv_text[:-2]
        formated_hist.append([line[0], line[1], line[2], line[3], rcv_text, line[5]])
    return formated_hist

def round_summary(transacs):
    # rounded summary from transactions
    rounded_summary = []
    for item in transacs:
        if round(item[2], 2) != 0:
            rounded_summary.append((item[0], item[1], round(item[2], 2)))
    return rounded_summary

def sort_summary(summary):
    #sort by ower
    sorted_summary = sorted(summary, key=lambda debt: debt[1])
    return sorted_summary
    
def get_equilibrium(summary):
    if len(summary) > 0:
        total = {}
        for t in summary:
            if t[0] not in total:
                total.update({t[0]: 0})
            if t[1] not in total:
                total.update({t[1]: 0})
            total[t[0]] = round(total[t[0]] + t[2], 2)
            total[t[1]] = round(total[t[1]] - t[2], 2)

        ordered = sorted(total.items(), key=lambda x: x[1])
        amplitude = max(ordered[-1][1], - ordered[0][1])
        coeffs = []
        for e in ordered:
            percent = round(100*e[1]/amplitude)
            if percent < 0:
                percent *= -1
            coeffs.append((e[0], e[1], percent))
        return coeffs
    else:
        return []
    
def participants(summary):
    actors = []
    for a1, a2, amount in summary:
        if a1 not in actors:
            actors.append(a1)
        if a2 not in actors:
            actors.append(a2)
    return sorted(actors)

def check_logname(logname):
    return logname.isalnum() and len(logname) < CONFIG.MAXLOGNAMELEN

def get_filename(logname):
    if CONFIG.PATH == 0:
        #use default path
        folder = os.path.split(os.path.abspath(__file__))[0]
        filename = os.path.join(folder, 'static', 'data', logname + '.csv')
    else:
        #use config path
        folder = os.path.split(CONFIG.PATH)[0]
        filename = os.path.join(folder, logname + '.csv')
    return folder, filename

def error_in_file(filename):
    return "<p>Error in history file: " + str(filename) + "</p> \
            <p>Maybe the PATH in config.py is incorrectly set</p> \
            <p>Maybe you have reached the maximum linecount of the database file. Just use another URL suffix :)</p>"

def get_debt(logname):
    """ Load debt object from global variable
    or create a new one and load it"""
    if logname in GLOBALDEBTS:
        GLOBALDEBTS[logname][0].update()
    else:
        folder, filename = get_filename(logname)
        # compute debt graph from file
        debt=endebts.debts(filename)
        # to add actors later
        added_actors = []
        GLOBALDEBTS.update({logname: [ debt, added_actors ]})
    return GLOBALDEBTS[logname]

def generate_main(logname):
    if check_logname(logname):
        debt, added_actors = get_debt(logname)
        folder, filename = get_filename(logname)
        if debt.success:
            summary = round_summary(debt.transacs_simple)
            actors = remove_dupli(participants(summary) + added_actors)
            summary = sort_summary(summary)
            actors = sorted(actors)
            equilibrium = get_equilibrium(summary)
            total_spent = debt.total
            history = format_histo(debt.history)
            #render page
            return render_template('main.html',
                name=logname,
                money=CONFIG.MONEY,
                summary=summary,
                history=history,
                actors=actors,
                equilibrium=equilibrium,
                total=total_spent,
                logname=logname)
        else:
            return error_in_file(filename)
    else:
        return "<p>Max length: 100.</p> \
            <p>Only alphanumeric characters are allowed.</p>"

@app.route('/')
def default_main_page():
    return redirect(url_for('main_page', logname='default'))

@app.route('/<string:logname>')
def main_page(logname):
    return generate_main(logname)

@app.route('/<string:logname>/add', methods=['POST', 'GET'])
def add_transaction(logname):
    if request.method == 'POST':
        #extract receivers from request
        receivers = [item for item in request.form if request.form[item] == u'on']
        if valid_transaction(request.form['giver'],
                       receivers,
                       request.form['description'],
                       request.form['amount']):
            debt, added_actors = get_debt(logname)
            #write new transaction
            if debt.success:
                new_trans=(request.form['giver'],
                            tuple(receivers),
                            request.form['amount'])
                added = debt.add(new_trans, request.form['description'], limit=CONFIG.MAXHISTORYLEN)
                #remove actors to add (they should have been written in log now)
                added_actors = []
                if not added:
                    folder, filename = get_filename(logname)
                    return error_in_file(filename)
            #redirect to main view
            return redirect(url_for('main_page', logname=logname))
    # if the request method
    # was GET or invalid transaction
    flash("Invalid Transaction...", 'text-warning')
    #redirect to main view
    return redirect(url_for('main_page', logname=logname))

@app.route('/<string:logname>/rm_transaction', methods=['POST', 'GET'])
def rm_transaction(logname):
    if request.method == 'POST':
        # extract line numbers to remove
        lines = [int(item[7:]) for item in request.form if request.form[item] == u'on']
        debt, added_actors = get_debt(logname)
        if debt.success:
            debt.comment(lines)

    #redirect to main view
    return redirect(url_for('main_page', logname=logname))


@app.route('/<string:logname>/add_user', methods=['POST', 'GET'])
def add_user(logname):
    if request.method == 'POST':
        debt, added_actors = get_debt(logname)
        if (request.form['new_user'] != ''
        and request.form['new_user'] not in debt.actors
        and request.form['new_user'] not in added_actors
        and len(request.form['new_user']) < CONFIG.MAXUSERLEN ):
            added_actors.append(request.form['new_user'])
            #redirect to main view
            return redirect(url_for('main_page', logname=logname))
    flash("Invalid username...", 'text-warning')
    #redirect to main view
    return redirect(url_for('main_page', logname=logname))

@app.route('/<string:logname>/download')
def download_log(logname):
    folder, filename = get_filename(logname)
    response = make_response(open(filename).read())
    response.content_type = "text/plain"
    response.mimetype = "text/plain"
    return response

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
