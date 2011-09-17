#!/usr/bin/python

from datetime import datetime
from BeautifulSoup import BeautifulSoup
import json
import urllib2
import sqlite3
import sys
import re
import os

class GameSpotInfo:
    def __init__(self):
        self.id = None
        self.title = None
        self.system = None
        self.boxart = None
        self.release_date_text = None
        self.summary = None
    
class SearchResult:
    def __init__(self):
        self.id = None
        self.title = None
        self.system = None
        self.link = None
        self.score = None
        self.release_date_text = None
        self.summary = None
        self.boxart = None
        self.tags = None
        self.index = None
        self.page = None

    def __repr__(self):
        return repr([ self.id, \
                    self.title, \
                    self.system, \
                    self.link, \
                    self.score, \
                    self.release_date_text, \
                    self.summary, \
                    self.boxart, \
                    self.tags, \
                    self.index, \
                    self.page ])
        
class GameSpot:

    @staticmethod
    def search(query):
        html = get_html_from_ajax_search(query)
        
        if not html:
            return None
        soup = BeautifulSoup(html)
        i = 0
        page = 0
        allresults = []
        
        game_results = soup.findAll("li", "game_result")
        for game_result in game_results:
            res = SearchResult()
            result_title = game_result.find("div", "result_title")
            if result_title:
                a = result_title.find("a")
                if a:
                    res.link = a["href"][:a["href"].find("index.html")]
                    res.id = GameSpot.get_id(res.link)
                    res.title = a.text[:a.text.rfind("(")].strip()
                    res.system = a.text[a.text.rfind("(") + 1 : a.text.rfind(")")]
            
            boxshot = game_result.find("div", "boxshot")
            if boxshot:
                img = boxshot.find("img")
                if img:
                    res.boxart = img["src"]
                    
            details = game_result.find("div", "details")
            if details:
                dts = details.text.strip().split("|")
                for dt in dts:
                    dt = dt.replace("&nbsp;", "")
                    print "dt: \"" + dt + "\""
                    match = re.search("Review Score:(?P<score>.+)", dt)
                    if match:
                        res.score = match.group("score").strip()
                        continue
                    match = re.search("Release Date: (?P<date>.+)", dt)
                    if match:
                        res.release_date_text = match.group("date").strip()
                        continue
            
            deck = game_result.find("div", "deck")
            if deck:
                res.summary = deck.text.strip()
            
            tags = game_result.find("div", "tags")
            if tags:
                res.tags = []
                for tag in tags.findAll("a"):
                    res.tags.append(tag.text.strip())
                
            res.index = i
            res.page = page
            allresults.append(res)
            i = i + 1
        return allresults
            
    @staticmethod
    def get_info(link):
        return None
        
    @staticmethod
    def get_id(link):
        l = link.replace("http://www.gamespot.com/", "")
        l = l[:len(l)-1]
        l = l.replace("/", "_")
        return l
    
    @staticmethod
    def get_link(id):
        return ""

def get_search_url(query):
    return "http://www.gamespot.com/search.html?qs=%s" % query.replace(":", "").replace("-", "").replace("_", "").replace(" ", "+")

def get_ajax_search_url(query):
    return "http://www.gamespot.com/pages/search/search_ajax.php?q=%s&type=game&offset=0&tags_only=false&sort=rank" % query.replace(":", "").replace("-", "").replace("_", "").replace(" ", "%20")
 
"""
Must use this crazy workaround, or gamespot wont return any results
This is where things like Wireshark come in handy ;)
"""
def get_html_from_ajax_search(query):
    try:
        url1 = get_ajax_search_url(query)
        request = urllib2.Request(url1)
        request.add_header("User-Agent", "Mozilla/5.001 (windows; U; NT4.0; en-US; rv:1.0) Gecko/25250101")
        request.add_header("Cookie", "hello_from_gs=1")
        request.add_header("Referer", get_search_url(query))
        request.add_header("X-Request", "JSON")
        request.add_header("X-Requested-With", "XMLHttpRequest")
        request.add_header("Accept", "application/json")
        js = json.load(urllib2.urlopen(request))
        return js["search_results"]
    except:
        print "Error accessing:", url1
        return None 
 
def get_html(url):
    try:
        request = urllib2.Request(url)
        request.add_header("User-Agent", "Mozilla/5.001 (windows; U; NT4.0; en-US; rv:1.0) Gecko/25250101")
        html = urllib2.urlopen(request).read()
        return html
    except:
        print "Error accessing:", url
        return None 
    
def main():
    if len(sys.argv) == 2:
        results = GameSpot.search(sys.argv[1])
        for result in results:
            print result, "\n"
            print GameSpot.get_info(result.link), "\n"

if __name__ == "__main__":
    main()
    