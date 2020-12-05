#!/usr/bin/env python3

import heapq
import bs4 as bs
from urllib.parse import urlparse
import urllib.request
import requests
import re
import nltk
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import string

def combine_sim(p, all):
    print('combining...')
    combined = p
    for answer in all:
        for para in answer:
            if p == para.text or len(para.text.strip()) < 70:
                continue
            if similar([p, para.text]):
                combined += para.text

    return combined



def similar(documents):
    print('cleaning...')
    cleaned = list(map(clean_text, documents))
    try:
        vectorizer = CountVectorizer().fit_transform(cleaned)
        vectors = vectorizer.toarray()
        threshold = cosine_sim_vectors(vectors[0], vectors[1])
        if threshold >= 0.5:
            return True

    except Exception as e:
        return False

    return False

def cosine_sim_vectors(vec1, vec2):
    vec1 = vec1.reshape(1, -1)
    vec2 = vec2.reshape(1, -1)

    return cosine_similarity(vec1, vec2)[0][0]


def clean_text(text):
    text = ''.join([word for word in text if word not in string.punctuation])
    text = text.lower()
    text = ' '.join([word for word in text.split() if word not in nltk.corpus.stopwords.words('english')])


    return text



def summarize(article_text):
    print('summarizing...')
    article_text = re.sub(r'\[[0-9]*\]', ' ', article_text)
    article_text = re.sub(r'\s+', ' ', article_text)

    formatted_aricle_text = re.sub('[^a-zA-Z]', ' ', article_text)
    formatted_aricle_text = re.sub(r'\s+', ' ', formatted_aricle_text)

    sentence_list = nltk.sent_tokenize(article_text)
    stopwords = nltk.corpus.stopwords.words('english')

    word_frequencies = {}

    for word in nltk.word_tokenize(formatted_aricle_text):
        if word not in stopwords:
            if word not in word_frequencies.keys():
                word_frequencies[word] = 1
            else:
                word_frequencies[word] += 1

    maximum_frequncy = max(word_frequencies.values())

    for word in word_frequencies.keys():
        word_frequencies[word] = (word_frequencies[word]/maximum_frequncy)

    sentence_scores = {}

    for sent in sentence_list:
        for word in nltk.word_tokenize(sent.lower()):
            if word in word_frequencies.keys():
                if len(sent.split(' ')) < 30:
                    if sent not in sentence_scores.keys():
                        sentence_scores[sent] = word_frequencies[word]
                    else:
                        sentence_scores[sent] += word_frequencies[word]

    summary_sentences = heapq.nlargest(5, sentence_scores, key=sentence_scores.get)
    summary = ' '.join(summary_sentences)

    return summary




links = []


article_text = ""


query = "The role of technology in the retail industry"
query = query.replace(' ', '+')
URL = f"https://google.com/search?q={query}"
USER_AGENT =  "Mozilla/5.0 (Linux; Android 7.0; SM-G930V Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.125 Mobile Safari/537.36"
headers = {"user-agent" : USER_AGENT}
print('googling...')
resp = requests.get(URL, headers=headers)

if resp.status_code == 200:
    print('googled...')
    soup = bs.BeautifulSoup(resp.content, "lxml")
    a = soup.find_all('a')
    for i in a:
        k = i.get('href')
        try:
            m = re.search("(?P<url>https?://[^\s]+)", k)
            n = m.group(0)
            rul = n.split('&')[0]
            domain = urlparse(rul)
            if(re.search('google.com', domain.netloc)):
                continue
            else:
                links.append(rul)
        except:
            continue


answers = []
limit = 7
for link in links:
    print('following links... ' + link)
    try:
        scraped_data = urllib.request.urlopen(link)
    except Exception as e:
        continue
    article = scraped_data.read()

    parsed_article = bs.BeautifulSoup(article,'lxml')

    paragraphs = parsed_article.find_all('p')

    answers.append(paragraphs)
    limit += 1

alike = []

for answer in answers:
    print('grouping...')
    for p in answer:
        combined = combine_sim(p.text, answers)
        print('combined...')
        print(combined)
        if len(combined.strip()) < 7:
            continue
        summary = summarize(combined)
        alike.append(summary)

article_text = ""

for p in alike:
    print(p)
