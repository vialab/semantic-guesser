#!/usr/bin/env python

import mechanize
import cookielib
import urllib
import logging
import sys
from bs4 import BeautifulSoup
from nltk.corpus import brown
import cPickle as pickle

CLAWS_WORD_LIMIT = 100000

def browser():
    br = mechanize.Browser()
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)

    br.set_handle_equiv(True)
    br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)

    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    
    return br

def parse(page):
    soup = BeautifulSoup(page)
    pre = soup.find('pre')
    tagged_text = pre.string

    tagged_sents = tagged_text.rstrip().lstrip().splitlines()  # ["i am fine", "you are fine"]
    tagged_sents = [ s.split(' ') for s in tagged_sents]
    tagged_sents = [ [tuple(word.split('_')) for word in s] for s in tagged_sents ]
    
    return tagged_sents

def tagtext(browser, text):
    browser.open('http://ucrel.lancs.ac.uk/claws/trial.html')

    # Select the first form
    browser.select_form(nr=0)

    browser.form['tagset'] = ['c7']
    browser.form['style'] = ['horiz']
    browser.form['text'] = text
    
    print "submitting text to Ucrel website..."
    
    response = browser.submit()
    
    print "response received..."
    
    return parse(response.read())

def tag(sents):
    br = browser()
    
    tagged_sents = []
    
    buffer = ''
    word_count = 0
    
    for l in sents:
        if len(l) + word_count > CLAWS_WORD_LIMIT:
            tagged_sents += tagtext(br, buffer)
            buffer = ''
            word_count = 0

        buffer += ' '.join(l) + '\n'
        word_count += len(l)
     
    tagged_sents += tagtext(br, buffer)   
    
    return tagged_sents


# test
brown_sents = brown.tagged_sents()
brown_claws_tagged = tag([ [ t[0] for t in s]  for s in brown_sents])
pickle.dump(brown_claws_tagged, open('/home/rafa/Desktop/brown_clawstags.pickle', 'w+'))


# tag('textual data rocks can you believe it?')
# print tag(['textual data rocks can you believe it?'.split(' ')])