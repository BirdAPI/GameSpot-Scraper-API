#!/usr/bin/python

from datetime import datetime
from BeautifulSoup import BeautifulSoup
import json
import urllib2
import sqlite3
import sys
import re
import os

class GamespotInfo:
    def __init__(self):
        self.id = None
        self.link = None
        self.title = None
        self.system = None
        self.boxart = None
        self.release_date_text = None
        self.summary = None
        self.score = None
        self.score_desc = None
        self.publisher = None
        self.developer = None
        self.genre = None
        self.esrb = None
        self.esrb_reason = None
        self.score = None
        self.score_desc = None
        self.critic_score = None
        self.critic_count = None
        self.user_score = None
        self.user_count = None
            
    def __repr__(self):
        return repr([ self.id, \
                    self.link, \
                    self.title, \
                    self.system, \
                    self.boxart, \
                    self.release_date_text, \
                    self.summary, \
                    self.score, \
                    self.score_desc, \
                    self.publisher, \
                    self.developer, \
                    self.genre, \
                    self.esrb, \
                    self.esrb_reason, \
                    self.score, \
                    self.score_desc, \
                    self.critic_score, \
                    self.critic_count, \
                    self.user_score, \
                    self.user_count ])
        
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
        
class Gamespot:

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
                    res.id = Gamespot.get_id(res.link)
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
    def get_info(id):
        #url = get_info_url(id)
        url = Gamespot.get_link(id)
        html = get_html(url)
        if not html:
            return None
        soup = BeautifulSoup(html)
        
        info = GamespotInfo()
        info.id = id
        info.link = url
        
        product_title = soup.find("h2", "product_title")
        if product_title:
            a = product_title.find("a")
            if a:
                info.title = a.text.strip()
        
        boxshot = soup.find("div", "boxshot")
        if boxshot:
            img = boxshot.find("img")
            if img:
                info.boxart = img["src"]
        
        #NOTE: For use with tech_info.html
        # platform_rank = soup.find("dt", "platform_rank")
        # if platform_rank:
            # info.system = platform_rank.text.replace("Rank:", "").strip()
            
        plat_name = soup.find("div", "plat_name")
        if plat_name:
            info.system = plat_name.text.replace("(", "").replace(")", "").strip()
        
        deck = soup.find("meta", attrs={"name":"description"})
        if deck:
            info.summary = deck["content"].strip()
        
        review_scores = soup.find("ul", "review_scores")
        if review_scores:
            (info.score, info.score_desc) = get_li_data_more(review_scores, "editor_score", "scoreword")
            (info.critic_score, info.critic_count) = get_li_data_more(review_scores, "critic_score")
            if info.critic_count:
                info.critic_count = info.critic_count.replace("reviews", "").strip()
            (info.user_score, info.user_count) = get_li_data_more(review_scores, "community_score")
            if info.user_count:
                info.user_count = info.user_count.replace(",", "").replace("votes", "").replace("vote", "").strip()
        
        esrb_module = soup.find("div", id="esrb_module")
        if esrb_module:
            p = esrb_module.find("p")
            if p:
                info.esrb_reason = p.text.strip()
        
        #NOTE: For use with tech_info.html
        # process_game_infos(soup)
        
        stats = soup.find("ul", "stats")
        info.publisher = get_li_span_data(stats, "publisher")
        info.developer = get_li_span_data(stats, "developer")
        info.genre = get_li_span_data(stats, "genre")
        info.release_date_text = get_li_span_data(stats, "date").replace("&raquo;", "").strip()
        info.esrb = get_li_span_data(stats, "maturity")
            
        return info
        
    @staticmethod
    def get_id(link):
        l = link.replace("http://www.gamespot.com/", "")
        l = l[:len(l)-1]
        l = l.replace("/", "_")
        return l
    
    @staticmethod
    def get_link(id):
        return "http://www.gamespot.com/%s/" % id.replace("_", "/")

def get_search_url(query):
    return "http://www.gamespot.com/search.html?qs=%s" % query.replace(":", "").replace("-", "").replace("_", "").replace(" ", "+")

def get_ajax_search_url(query, page=0):
    return "http://www.gamespot.com/pages/search/search_ajax.php?q=%s&type=game&offset=%i&tags_only=false&sort=rank" % (query.replace(":", "").replace("-", "").replace("_", "").replace(" ", "%20"), page * 10)

def get_info_url(id):
    return Gamespot.get_link(id) + "tech_info.html"
 
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
        request.add_header("Cookie", "hello_from_gs=1")
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

def process_game_info(info, type, value):
    if type == "Publisher":
        info.publisher = value
    elif type == "Developer":
        info.developer = value
    elif type == "Genre":
        info.genre = value
    elif type == "Release Date":
        info.release_date_text = value.replace("  ", " 0").replace("(more)", "")
    elif type == "ESRB":
        info.esrb = value
    elif type == u"ESRB\xa0Descriptors":
        info.esrb_reason = value
    elif type == u"Number\xa0of\xa0Players":
        info.num_players = value
    elif type == "Sound":
        info.sound = value
    else:
        print "Type: \"%s\", Value: \"%s\"" % (type, value)

def process_game_infos(soup):
    game_infos = soup.findAll("dl", "game_info")
    for game_info in game_infos:
        gi = "<html><body>" + str(game_info)
        gi = re.sub('<dt>([^:]+):</dt>', '<div class="\\1">', gi)
        gi = gi.replace("<dd>", "")
        gi = gi.replace("</dd>", "</div>")
        gi = gi + "</body></html>"
        soup2 = BeautifulSoup(gi)
        divs = soup2.findAll("div")
        for div in divs:
            type = div["class"]
            value = div.text.strip()
            process_game_info(info, type, value)
        
def get_li_data_more(node, type, more_class="more"):
    r1 = None
    r2 = None
    li = node.find("li", type)
    if li:
        data = li.find("span", "data")
        if data:
            r1 = data.text.strip()
        more = li.find("span", more_class)
        if more:
            r2 = more.text.strip()
    return (r1, r2)

def get_li_span_data(node, data_name):
    li = node.find("li", data_name)
    if li:
        data = li.find("span", "data")
        if data:
            return data.text.strip()
    return None    
    
def main():
    if len(sys.argv) == 2:
        results = Gamespot.search(sys.argv[1])
        for result in results:
            print result, "\n"
            print Gamespot.get_info(result.id), "\n"

if __name__ == "__main__":
    main()
    