# CS6111 Advanced Database Systems - Relation Extraction System (ISE Algorithm)

# Team Members
Aishwarya Sarangu (als2389)

Rishabh Gupta (rg3334)

# Submitted Files
* **project2.py:** script to run Relation Extraction and obtain tuples
* **requirements.txt:** all dependencies to run the code
* **spacy_help_functions.py:** script to process and annotate text through linguistic analysis
* **spanbert.py:** classifier to extract required relations from text documents

# Installing Dependencies

```
$ sudo apt-get update
$ pip3 install beautifulsoup4
$ pip3 install -U pip setuptools wheel
$ pip3 install -U spacy
$ python3 -m spacy download en_core_web_lg
```

### Install Spanbert Dependencies

```
$ cd SpanBERT
$ pip3 install -r requirements.txt
$ bash download_finetuned.sh
```

Finally, place the ```pretrained_spanbert``` folder under the ```SpanBERT``` directory.


# Running the program

```
$ ./project2.py AIzaSyC3gsw3bEoyTWHBk2akQ2uLP4IkeuyE_zg 31a218a86791fb76c <relation_to_extract> <threshold> "<search_query>" <# of tuples>
```
  
  # Project Design
  
  The project has the file ```project2.py``` which combines:
  
  * Core logic of webpage extraction
  * Calling spacy to split the text into sentences and extract named entities
  * Calling SpanBERT to predict the corresponding relations, and extract all instances of the relation into set X specified by input parameter r.
  Once the instances for the required relation are all extracted, tuples in X are filtered based on confidence values (higher than threshold). 
  
  In case of duplicate entries in X, the tuple with higher confidence is considered. 
  
  When X contains at least the desired number of tuples, the program is terminated and the tuples are returned to the user. If not, a new query is selected using entities from set X and the process is repeated.
  
  The code primarily contains three procedures whose functionalities are as follows:
  
 * **process_webpage:** This function extracts the actual plain text from a webpage using Beautiful Soup, trims the irrelevant data and maintains the character limit of the document at 20,000.
 * **extract_tuples:** This function extracts tuples using Iterative Set Expansion algorithm. Once the processed document is obtained from each URL, the document is passed onto ```extract_relations``` defined in ```spacy_help_functions.py``` to get the various entities in the document which are then fed to the SpanBERT model to obtain relation predictions among the entities. Since the SpanBERT model is computationally expensive, we only pass those entity pairs that are relevant to the relation in question. Following this, the predictions are filtered to eliminate any duplicates and records that have a confidence level lower than the threshold. The resulting tuples are returned to ```extract_tuples```, which then sorts the results and updates the query in the next iteration. This process continnues till the total number of tuples retrieved equals/exceeds the number of tuples requested.
  * **update_query:** This function finds a new query using the highest confidence tuple in the sorted_dict. Given the set X of tuples sorted in decreasing order of confidence, a tuple y is selected to be the new query such that: (a) y has not been used for querying yet and (b) y has an extraction confidence that is highest among the tuples in X that have not yet been used for querying. The new query is created from tuple y by concatenating the attribute values together. If no such y tuple exists, the process is halted. (ISE has "stalled" before retrieving k high-confidence tuples.)
  
# Handling Non-HTML Files
We look for the field fileFormat in the results returned by the custom search api to figure out which results are non-html ones. We ignore the relevance information provided by the user for those results.
  
# API Key & Engine ID
* Google Custom Search Engine JSON API Key: AIzaSyC3gsw3bEoyTWHBk2akQ2uLP4IkeuyE_zg
* Engine ID: 31a218a86791fb76c
