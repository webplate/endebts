#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

import config as CONFIG
import endebts

from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'Zak8a9b7wvUkuBAMBLVKaAtBAM73CjuXeFBKw72Ti7jhf'

if CONFIG.PATH == 0:
    #use default path
    app_folder = os.path.split(os.path.abspath(__file__))[0]
    filename = os.path.join(app_folder, 'static', 'data', CONFIG.NAME + '.csv')
else:
    #use config path
    folder = os.path.split(CONFIG.PATH)[0]
    filename = os.path.join(folder, CONFIG.NAME + '.csv')

# compute debt graph from file
mainDebt=endebts.dettes(filename)
# to add actors later
added_actors = []

def valid_transaction(giver, receiver, description, amount):
    try:
        a = float(amount)
    except ValueError:
        a = 0
    if ( giver != ''
        and receiver != []
        and description != ''
        and a != 0):
            return True
    else:
        return False

def format_histo(histo):
    # format history (in reverse and no printed tuples)
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
    
def participants(summary):
    actors = []
    for a1, a2, amount in summary:
        if a1 not in actors:
            actors.append(a1)
        if a2 not in actors:
            actors.append(a2)
    return sorted(actors)

@app.route('/')
def main_page():
    mainDebt.update()
    if mainDebt.success:
        summary = round_summary(mainDebt.transacs_simple)
        summary = sort_summary(summary)
        equilibrium = get_equilibrium(summary)
        actors = participants(summary) + added_actors
        history = format_histo(mainDebt.history)
        #render page
        return render_template('main.html',
            name=CONFIG.NAME,
            summary=summary,
            history=history,
            actors=actors,
            money=CONFIG.MONEY,
            dl_button=CONFIG.DL_BUTTON,
            equilibrium=equilibrium,
            precise_version=False)
    else:
        return "Error in history file: " + str(filename)

@app.route('/full_precision')
def precise_page():
    mainDebt.update()
    if mainDebt.success:
        summary=mainDebt.transacs_simple
        summary = sort_summary(summary)
        equilibrium = get_equilibrium(summary)
        actors=mainDebt.acteurs + added_actors
        history=mainDebt.history
        #render page
        return render_template('main.html',
            name=CONFIG.NAME,
            summary=summary,
            history=format_histo(history),
            actors=actors,
            money=CONFIG.MONEY,
            dl_button=CONFIG.DL_BUTTON,
            equilibrium=equilibrium,
            precise_version=True)
    else:
        return "Error in history file: "+ str(filename)
    
@app.route('/add', methods=['POST', 'GET'])
def add_transaction():
    if request.method == 'POST':
        #extract receivers from request
        receivers = [item for item in request.form if request.form[item] == u'on']
        if valid_transaction(request.form['giver'],
                       receivers,
                       request.form['description'],
                       request.form['amount']):
            #write new transaction
            if mainDebt.success:
                new_trans=(request.form['giver'],
                            tuple(receivers),
                            request.form['amount'])
                mainDebt.ajoute(new_trans, request.form['description'])
                #remove actors to add (they should have been written in log now)
                global added_actors
                added_actors = []
            #redirect to main view
            return redirect(url_for('main_page'))
    # if the request method
    # was GET or invalid transaction
    flash("Invalid Transaction...", 'text-warning')
    #redirect to main view
    return redirect(url_for('main_page'))

@app.route('/rm_transaction', methods=['POST', 'GET'])
def rm_transaction():
    if request.method == 'POST':
        # extract line numbers to remove
        lines = [int(item[7:]) for item in request.form if request.form[item] == u'on']
        if mainDebt.success:
            mainDebt.comment(lines)

    #redirect to main view
    return redirect(url_for('main_page'))


@app.route('/add_user', methods=['POST', 'GET'])
def add_user():
    if request.method == 'POST':
        if (request.form['new_user'] != ''
        and request.form['new_user'] not in mainDebt.acteurs
        and request.form['new_user'] not in added_actors):
            added_actors.append(request.form['new_user'])
            #redirect to main view
            return redirect(url_for('main_page'))
    flash("Invalid username...", 'text-warning')
    #redirect to main view
    return redirect(url_for('main_page'))

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
