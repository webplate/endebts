#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import csv
import re
import copy
import sys

import codecs, cStringIO

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

###Gestion du fichier d'historique
def generate_graph(histo):
    #ouvre fichier en lecture
    try:
        history=open(histo,'rb')
    except IOError :
        # create it if inexistant
        history=open(histo,'ab')
        history.close()
        history=open(histo,'rb')
    reader=UnicodeReader(history, delimiter='	', quotechar='"')
    transacs=[]
    transacs_full=[]
    for i, row in enumerate(reader):
        #permet les commentaires et ignore les lignes vides
        if len(row) != 0 and len(row[0]) != 0 and row[0][0] != "#":
            row[3]=tuple(re.split(',',row[3]))
            transacs.append((row[1],row[3],float(row[2])))
            transacs_full.append([i] + row)
    history.close()
    return transacs, transacs_full
    
def read_all(histo):
    #ouvre fichier en lecture
    try:
        history=open(histo,'rb')
    except IOError :
        return False
    reader=csv.reader(history, delimiter='	', quotechar='"')
    lines=[]
    for row in reader:
            lines.append(row)
    history.close()
    return lines

def actors_list(transacs):
    actors=[]
    for transac in transacs:
        if transac[0] not in actors:
            actors.append(transac[0])
        if type(transac[1]) != tuple:
            if transac[1] not in actors:
                actors.append(transac[1])
        else:
            for a in transac[1]:
                if a not in actors:
                    actors.append(a)
    actors.sort()
    return actors
    
def compute_total_spent(transacs):
    total = 0
    for t in transacs:
        total += t[2]
    return round(total, 2)

###Simplification du graph des endebtments
def detect_null(transacs):
    for transac in transacs[:]:
        if transac[2] == 0:
            return transac
    return False

def detect_doubl(transacs):
    for i in xrange(len(transacs)):
        for j in xrange(len(transacs)):
            if i != j:
                transac=transacs[i]
                transac2=transacs[j]
                #si deux transacs partagent destinataire et emetteur
                if (transac[0],transac[1]) == (transac2[0],transac2[1]):
                    return (transac,transac2,0)
                #si debt opposée
                elif (transac[0],transac[1]) == (transac2[1],transac2[0]):
                    return (transac,transac2,1)
    return False

def remove_doubl(doublon, transacs):
    (transac,transac2,operator)=doublon
    if operator == 0:
        transacs.append((transac[0],transac[1],transac[2]+transac2[2]))
    else:
        transacs.append((transac[0],transac[1],transac[2]-transac2[2]))
    transacs.remove(transac)
    transacs.remove(transac2)

def degroup(transacs):
    for transac in transacs[:]:
        #si transac destinée à un groupe
        if type(transac[1]) == tuple:
            #on décompose la transaction
            for i in transac[1]:
                if i != transac[0]:
                    transacs.append((transac[0],i,transac[2]/len(transac[1])))
            transacs.remove(transac)

def detect_cycle(transacs):
    for transacA in transacs:
        for transacB in transacs:
            for transacC in transacs:
                if transacA != transacB and transacA != transacC and transacB != transacC:
                    #si A donne à B, B donne à C et A donne à C
                    if transacA[1] == transacB[0] and transacB[1] == transacC[1] and transacA[0] == transacC[0]:
                        return (transacA,transacB,transacC)
    return False

def remove_cycle(cycle, transacs):
    (transacA,transacB,transacC)=cycle
    if transacB[2] < transacC[2]:
        transacs.append((transacA[0],transacA[1],transacA[2]-transacB[2]))
        transacs.append((transacC[0],transacC[1],transacC[2]+transacB[2]))
    else:
        transacs.append((transacA[0],transacA[1],transacA[2]+transacC[2]))
        transacs.append((transacB[0],transacB[1],transacB[2]+transacC[2]))
    transacs.remove(transacA)
    transacs.remove(transacB)
    transacs.remove(transacC)

def detect_cascad(transacs):
    for transac in transacs:
        for transac2 in transacs:
            if transac != transac2:
                if transac[1] == transac2[0]:
                    return (transac,transac2)
    return False

def detect_neg(transacs):
    for transac in transacs[:]:
        if transac[2] < 0:
            return transac
    return False

def remove_neg(transac, transacs):
    transacs.append((transac[1],transac[0],-transac[2]))
    transacs.remove(transac)

def remove_cascad(cascade, transacs):
    (transacD,transacE)=cascade
    if transacD[2] > transacE[2]:
        transacs.append((transacD[0],transacE[1],transacE[2]))
        transacs.append((transacD[0],transacD[1],transacD[2]-transacE[2]))
    else:
        transacs.append((transacD[0],transacE[1],transacD[2]))
        transacs.append((transacD[1],transacE[1],transacE[2]-transacD[2]))
    transacs.remove(transacD)
    transacs.remove(transacE)

def simplify(transacs):
    degroup(transacs)
    while True:
        # must be first for speed optimization (most frequent first)
        d_doubl=detect_doubl(transacs)
        if d_doubl != False:
            remove_doubl(d_doubl, transacs)
            continue
        d_nul=detect_null(transacs)
        #s'il existe une transaction nulle
        if d_nul != False:
            transacs.remove(d_nul)
            continue
        d_neg=detect_neg(transacs)
        if d_neg != False:
            remove_neg(d_neg, transacs)
            continue
        d_casc=detect_cascad(transacs)
        if d_casc != False:
            remove_cascad(d_casc, transacs)
            continue
        d_cycle=detect_cycle(transacs)
        if d_cycle != False:
            remove_cycle(d_cycle, transacs)
            continue
#la simplification est terminée:
#il ne reste plus de debts nulles, négatives, redondantes,
#cycliques, en cascade
        break

###tentative de création de l'objet "debts"
class debts:
    def __init__(self, histo):
        self.historyname=histo
        self.update()

    def update(self):
        try:
            transacs, self.history=generate_graph(self.historyname)
            self.success=True
        except:
            self.success=False
        if self.success:
            self.actors = actors_list(transacs)
            self.total = compute_total_spent(transacs)
            self.transacs_simple = transacs
            
            t = time.time()
            simplify(self.transacs_simple)
    
    def add(self, transac, description, dateandtime=None):
        #le temps par défaut est le temps local
        if dateandtime == None:
            dateandtime=time.localtime()
        #Détail de formatage
        if type(transac[1]) == tuple:
            destinataires = ""
            for i in transac[1]:
                destinataires += i
                destinataires += ","
            destinataires=destinataires[:-1]    #retire virgule finale
        else:
            destinataires=transac[1]
        #ajout de la transaction dans le format csv
        #si destinataire différent d'émetteur et montant non nul
        if transac[0] != destinataires and transac[2] != 0.0:
            transac=(time.strftime('%d/%m/%y %H:%M',dateandtime),
            transac[0], transac[2], destinataires, description)
            historique=open(self.historyname,'ab')
            writer=UnicodeWriter(historique, delimiter='	', quotechar='"')
            writer.writerow(transac)
            historique.close()
            self.update()
    
    def comment(self, line_nbs):
        full_histo = read_all(self.historyname)
        new_histo = []
        for i in range(len(full_histo)):
            #comment line if notified
            if i in line_nbs:
                new_histo.append(['#--'] + full_histo[i])
            else:
                #copy
                new_histo.append(full_histo[i])        
        #write commented version
        historique=open(self.historyname,'wb')
        writer=csv.writer(historique, delimiter='	', quotechar='"')
        writer.writerows(new_histo)
        historique.close()
        self.update()
