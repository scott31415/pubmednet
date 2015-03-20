# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 08:05:51 2015

@author: Scott
"""

import urllib.request
import urllib.parse
from xml.etree.ElementTree import parse
from collections import defaultdict
#import nltk
from nltk.stem.snowball import SnowballStemmer
#from xml.etree.ElementTree import fromstring
#import sys
#import matplotlib.pyplot as plt
import numpy as np

import networkx as nx
from networkx.readwrite import json_graph
import json

import random
import math

site = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
db='pubmed'
retmode='xml'

class TopicSearch:
    def __init__(self,term_str):
        self._terms = []
        self._stem_terms = []
        self._id_list = []
        self._top_authors = []
        self._first_author = set()
        self._last_author = set()
        self._num4author = defaultdict(int)
        self._impact4author = defaultdict(float)
        self._text4author = defaultdict(str)
        self._coauthors = {}
        self._author4pmid = defaultdict(set)
        self._pmid4author = defaultdict(set)
        self._cite4author = defaultdict(set)
        self._citation_net = defaultdict(set)
        self._metric = {}
       
        self._num_author_limit = 100

        self._process_query(term_str)

    def _process_query(self,term_str):
        self._terms = term_str.split()
        #snowball_stemmer = SnowballStemmer("english")

        #self._stem_terms = [snowball_stemmer.stem(x) for x in self._terms]
        self._id_list = self._get_ids(self._terms)    
        summary_doc = self._get_docs(self._id_list)
        self._process_doc(summary_doc)    

    def _get_ids(self,terms,num_max=100000):
        term_str = '+'.join(terms)
        #term='antibody+AND+aggregation'
        field='abstract'
        retmax=str(num_max)
        sort_method='relevance'
        num_to_get = 100000

        search_cmd = site+'esearch.fcgi?db='+db+'&term='+term_str+'&retmax='+retmax+'&field='+field+'&sort='+sort_method
        f = urllib.request.urlopen(search_cmd)
        doc = parse(f)
        f.close()

        uids = []
        for uid in doc.iterfind('IdList/Id'):
            uids.append(uid.text)
    
        num_records = int(doc.findtext('Count'))
        #print(num_records)
        if num_records > num_max:
            num_calls = int((num_records-1)/num_max)+1
            for i in range(1,num_calls):
                retstart=str(i*num_max)
                search_cmd = site+'esearch.fcgi?db='+db+'&term='+term_str+'&retstart'+retstart+'&retmax='+retmax+'&field='+field+'&sort='+sort_method
                f = urllib.request.urlopen(search_cmd)
                doc = parse(f)
                f.close()

                for uid in doc.iterfind('IdList/Id'):
                    uids.append(uid.text)

        if len(uids) > num_to_get: 
            random.shuffle(uids)
            uids = uids[:num_to_get]

        id_list=','.join(uids)
        return id_list
     
    def _get_docs(self,id_list):
        parms = {
            'id' : id_list,
            'retmode' : retmode,
            'db' : db
        }

        querystring = urllib.parse.urlencode(parms)
        fetch_url = site+'efetch.fcgi/post'
        f = urllib.request.urlopen(fetch_url,querystring.encode('ascii'))

        summary_doc = parse(f)
        f.close()
    
        return summary_doc

    def _process_doc(self,summary_doc):
        for article in summary_doc.iterfind('PubmedArticle'):
            #abstract_text = article.findtext('MedlineCitation/Article/Abstract/AbstractText')
            #abstract_valid = check_terms_in_one_sentence(abstract_text,terms,stem_terms)
            pmid = article.findtext('MedlineCitation/PMID') 
            #title = article.findtext('MedlineCitation/Article/ArticleTitle')         
            authors = []
            for author in article.iterfind('MedlineCitation/Article/AuthorList/Author'):
                lastname = author.findtext('LastName')
                forename = author.findtext('ForeName')
                if not lastname or not forename:
                    continue
                #aname = ','.join([lastname,forename])
                aname = ' '.join([forename,lastname])
                authors.append(aname)

            if len(authors) == 0:
                continue             

            self._first_author.add(authors[0])
            self._last_author.add(authors[-1]) 
 
            citations = []          
            for citation in article.iterfind('MedlineCitation/CommentsCorrectionsList/CommentsCorrections'):
                cite_pmid = citation.findtext('PMID')
                if cite_pmid:
                    citations.append(cite_pmid)
                    self._citation_net[cite_pmid].add(pmid)
            
            for author in authors:
                self._num4author[author] += 1
                #if abstract_text is not None:
                #    self._text4author[author] += abstract_text
                self._author4pmid[pmid].add(author)
                self._pmid4author[author].add(pmid)
                for citation in citations:
                    self._cite4author[author].add(citation)
            
            for i in range(len(authors)):
                if authors[i] not in self._coauthors:
                    self._coauthors[authors[i]] = defaultdict(int)
                for j in range(i+1,len(authors)):
                    self._coauthors[authors[i]][authors[j]]+=1
                    if authors[j] not in self._coauthors:
                        self._coauthors[authors[j]] = defaultdict(int)
                    self._coauthors[authors[j]][authors[i]]+=1
   
        for author in list(self._num4author):
            if author not in self._first_author and author not in self._last_author:
                del self._num4author[author]
                del self._pmid4author[author]
                continue
            #num_cited = 0
            for pmid in self._pmid4author[author]:
                if pmid in self._citation_net:
                    #self._impact4author[author] += math.sqrt(len(self._citation_net[pmid]))    
                    num_others = 0
                    for cite_pmid in self._citation_net[pmid]:
                        if cite_pmid not in self._pmid4author[author]:
                            num_others += 1
                    self._impact4author[author] += math.sqrt(num_others)
                    if author == 'David Baker':
                        print('{0} gets cited {1} times'.format(pmid,len(self._citation_net[pmid])))
                    #num_cited += len(self._citation_net[pmid])
            #self._citenum4author[author] = num_cited
            self._impact4author[author] += self._num4author[author]     

        num_author_max = min(len(self._num4author),self._num_author_limit)                    
        #self._top_authors = sorted(self._num4author.keys(),key=lambda x:self._num4author[x],reverse=True)[:num_author_max]
        self._top_authors = sorted(self._num4author.keys(),key=lambda x:self._impact4author[x],reverse=True)[:num_author_max]

        #all_scores = list(self._impact4author.values())
        self._metric = self._impact4author 

    def plot_coauthor_network(self,fname):
        nxg = nx.Graph()
        for author in self._top_authors:
            url = self.get_author_url(author,self._terms)
            nxg.add_node(author,size=self._metric[author],url=url)
        for i in range(len(self._top_authors)):
            author1 = self._top_authors[i]
            if author1 not in self._coauthors:
                continue
            for j in range(i+1,len(self._top_authors)):
                author2 = self._top_authors[j]
                if author2 in self._coauthors[author1]:
                    nxg.add_edge(author1,author2,weight=self._coauthors[author1][author2])
        nld = json_graph.node_link_data(nxg)
        json.dump(nld,open(fname,'w')) 

    def get_author_url(self,author,terms):
        fields = author.split(' ')
        author_fullname = '%20'.join(fields)
        #firstname = '%20'.join(fields[1].split())    
        #lastname = fields[0]
        #author_fullname = firstname+'%20'+lastname
        term_str = '%20'.join(terms)
        ncbi_link='http://www.ncbi.nlm.nih.gov/pubmed?term=('
        ncbi_link+=author_fullname
        ncbi_link+='%5BAuthor%20-%20Full%5D)%20AND%20'
        ncbi_link+=term_str
        return ncbi_link
 
    def check_terms_in_one_sentence(self,abstract_text,terms,stem_terms):
        try:
            sentences = nltk.tokenize.sent_tokenize(abstract_text)
        except TypeError:
            return False

        abstract_valid = False
        for sent in sentences:
            sent_valid = True
            for i in range(len(terms)):
                if terms[i] not in sent and stem_terms[i] not in sent:
                    sent_valid = False
                    break
                if sent_valid:
                    abstract_valid = True
                    break
    
        return abstract_valid






