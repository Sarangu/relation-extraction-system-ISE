#!/usr/bin/python3

from googleapiclient.discovery import build
import requests
from bs4 import BeautifulSoup
import sys
import spacy
import spacy_help_functions as sp
import operator
import time
import re

from spanbert import SpanBERT

relation_mapping = {
    1: 'per:schools_attended',
    2: 'per:employee_of',
    3: 'per:cities_of_residence',
    4: 'org:top_members/employees'
}

entities_mapping = {
    1: ['ORGANIZATION', 'PERSON'],
    2: ['ORGANIZATION', 'PERSON'],
    3: ['LOCATION', 'CITY', 'COUNTRY', 'STATE_OR_PROVINCE', 'PERSON'],
    4: ['ORGANIZATION', 'PERSON']
}

API_KEY="AIzaSyC3gsw3bEoyTWHBk2akQ2uLP4IkeuyE_zg"
ENGINE_ID="31a218a86791fb76c"


def pretty_print(relations_dict):
    """
    Prints details in an ordered format
    :param relations_dict:
    :return:
    """
    print(f"================== ALL RELATIONS for per:schools_attended ( {len(relations_dict)} ) =================")
    for relation, conf in relations_dict.items():
        print(f"Confidence: {conf}\t| Subject: {relation[0]}\t| Object: {relation[2]}")


def extract_tuples(query, k, api_key=API_KEY, engine_id=ENGINE_ID, relation_index=1, threshold=0.9):
    """
    Extract tuples using Iterative Set Expansion algorithm
    @param query: seed query
    @param k: number of tuples
    @param api_key:
    @param engine_id:
    @param relation_index: one among keys of relation_mapping dict defined above
    @param threshold: extraction confidence threshold
    @return:
    """
    nlp = spacy.load("en_core_web_lg")
    spanbert = SpanBERT(pretrained_dir="./pretrained_spanbert")

    print(f"==========")
    print(f"Parameters:")
    print(f"Client key = {api_key}")
    print(f"Engine key = {engine_id}")
    print(f"Relation = {relation_mapping[relation_index]}")
    print(f"Threshold = {threshold}")
    print(f"Query = {query}")
    print(f"# of Tuples = {k}")
    print(f"Loading necessary libraries; This should take a minute or so ...)")

    final_sorted_dict = dict()
    # queries_seen_dict = dict()
    queries_seen = set()
    iteration_counter = 0
    current_tuples = 0

    service = build("customsearch", "v1",
                    developerKey=api_key)

    urls_visited = set()
    while current_tuples < k:
        # queries_seen_dict[tuple(sorted(query.lower().split()))] = 1
        queries_seen.add(tuple(sorted(query.lower().split())))
        query, continue_search = update_query(queries_seen, final_sorted_dict, query)

        if not continue_search:
            print(f"ISE has stalled before retrieving {k} high-confidence tuples.")
            return


        print(f"=========== Iteration: {iteration_counter} - Query: {query} ===========")
        response = service.cse().list(q=query, cx=engine_id).execute()
        results = response['items']

        for index, item in enumerate(results):
            url = item['formattedUrl']
            url = "".join(url.split())

            # only check html files
            if "fileFormat" not in item:
                print(f"\n\nURL( {index+1} / {len(results)}): {url}")
                if url in urls_visited:
                    print("\tWebpage already seen. Moving onto the next url.")
                    continue
                output, page_fetched = process_webpage(url)

                if not page_fetched:
                    print(f"\tRequest timeout of 20 sec reached. Skipping this webpage.")
                    continue

                doc = nlp(output)

                entities_of_interest = entities_mapping[relation_index]
                res = sp.extract_relations(doc, spanbert, entities_of_interest, threshold, relation_index)

                for key, value in res.items():
                    if key[1] == relation_mapping[relation_index]:
                        if key in final_sorted_dict.keys():
                            if final_sorted_dict[key] < value:
                                final_sorted_dict[key] = value
                        else:
                            final_sorted_dict[key] = value
            else:
                print(f"Skipping Non-HTML document at URL( {index+1} / {len(results)}): {item['formattedUrl']}")

            urls_visited.add(url)

        # sort based on confidence
        final_sorted_dict = dict(sorted(final_sorted_dict.items(), key=operator.itemgetter(1), reverse=True))

        current_tuples = len(final_sorted_dict)
        pretty_print(final_sorted_dict)

        iteration_counter += 1

    print(f"Total # of iterations = {iteration_counter}")


def process_webpage(html_url):
    """
    Extract the actual plain text from a webpage using Beautiful Soup
    @param html_url: url of webpage
    @return:
    """
    print(f"\tFetching text from url ...")

    # check if request times out
    try:
        response = requests.get(html_url, timeout=20)
    except requests.exceptions.ReadTimeout:
        return "", False

    html_content = response.content
    html_data = BeautifulSoup(html_content, 'html.parser')
    text = html_data.find_all(text=True)
    output = ''
    blacklist = [
        '[document]',
        'noscript',
        'header',
        'html',
        'meta',
        'head',
        'input',
        'script',
        'style',
        'footer',
        'copyright'
    ]

    for t in text:
        if t.parent.name not in blacklist:
            output += '{} '.format(t)

    output = output.replace('\n', ' ')
    output = output.replace('\t', ' ')
    output = output.replace('\r', ' ')
    output = output.replace(u'\xa0', u'')
    # Remove all single characters
    output = re.sub(r'\s+[a-zA-Z]\s+', ' ', output)
    # Substituting multiple spaces with single space
    output = re.sub(r'\s+', ' ', output, flags=re.I)

    if len(output) > 20000:
        print(f"\tTrimming webpage content from {len(output)} to 20000 characters")
        output = output[:20000]

    print(f"\tWebpage length (num characters): {len(output)}")
    return output, True


def update_query(queries_seen, sorted_tuples_dict, original_query):
    """
    Find a new query using the highest confidence tuple in the sorted_dict
    @param queries_seen: set of queries used
    @param sorted_tuples_dict: extracted entity pairs along with confidence
    @param original_query: last query
    @return:
    """
    if len(sorted_tuples_dict) == 0:
        return original_query, True

    for k in sorted_tuples_dict.keys():
        candidate_query = k[0] + " " + k[2]
        candidate_query_tuple = tuple(sorted(candidate_query.lower().split()))

        if candidate_query_tuple not in queries_seen:
            return candidate_query, True

    return "", False


def main():
    if len(sys.argv) < 5:
        print(f"Incorrect Usage: {sys.argv[0]} <google api key> <google engine id> <precision> <query>")
        return

    api_key = sys.argv[1]
    engine_id = sys.argv[2]
    relation_index = int(sys.argv[3])

    if relation_index > 4 or relation_index < 0:
        print(f"r can only be an integer between 1 and 4.")
        return

    threshold = float(sys.argv[4])
    if threshold < 0 or threshold > 1:
        print(f"Threshold should be between 0 and 1.")
        return

    seed_query = sys.argv[5]
    num_tuples = int(sys.argv[6])
    if num_tuples <= 0:
        print(f"Number of tuples to return must be greater than 0.")
        return

    start = time.time()
    print(f"Start Time: {start}")
    extract_tuples(seed_query, num_tuples, api_key, engine_id, relation_index, threshold)
    end = time.time()
    print(f"Elapsed time: {end - start} seconds.")


if __name__ == "__main__":
    main()
