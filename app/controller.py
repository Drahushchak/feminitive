from itertools import count
from yaml import dump
from app import app
import yaml, json
from tempfile import SpooledTemporaryFile
from app.models import *
from typing import *
from collections import Counter
import random
from flask_login import current_user


def get_valid_file_format(file_name: str) -> str:
    for file_format in app.config['ALLOWED_EXTENSIONS']:
        if file_name.lower().endswith(file_format):
            return file_format

def loads_file(file: SpooledTemporaryFile, file_format: str) -> dict:
    result = dict()
    if file_format=='yaml':
        result = yaml.load(file.read())
    elif file_format=='json':
        result = json.loads(file.read())
    return result

def is_valid_data(data: dict) -> bool:
    if not isinstance(data, dict): raise Exception(data)
    for word, word_value in data.items():
        if not isinstance(word, str): raise Exception(word)
        if 'root' not in word_value and not word_value.get('root'): raise Exception(word_value)
        if word_value:
            if not isinstance(word_value, dict): raise Exception(word_value)
            for number, number_value in word_value.items():
                if not isinstance(number, str): raise Exception(number)
                if number in ('singular','plural') and number_value:
                    for grammatical_case, grammatical_case_value in number_value.items():
                        if not isinstance(number, str): raise Exception(number)
                        if grammatical_case not in ('nominative', 'genitive', 'dative', 'accusative', 'instrumental', 'locative', 'vocative'): raise Exception(grammatical_case)
                        if grammatical_case_value:
                            if not isinstance(grammatical_case_value, dict): raise Exception(grammatical_case_value)
                            if not all((isinstance(key, str) and key and key in ('spelling', 'suffix', 'flexion')) for key, value in grammatical_case_value.items()): raise Exception(grammatical_case_value)
    return True

def upsert_data(user: User, name: str, data: dict) -> bool:
    source = Source(
        name=name, 
        user_id=user.id, 
        words=[
            Word(
                root=word_value['root'],
                spelling=word_spelling,
                grammatical_cases=[
                    GrammaticalCase(
                        number=number,
                        **{
                            grammatical_case: WordForm(**grammatical_case_value)
                            for grammatical_case, grammatical_case_value in number_value.items()
                            if grammatical_case_value
                        }
                    )
                    for number, number_value in word_value.items() if number in ('singular', 'plural')
                    if number_value
                ]
            )
            for word_spelling, word_value in data.items()
            if word_value
        ]
    )
    db.session.add(source)
    db.session.commit()
    return True

def generate_dashboard_data(sources: List[Source]):
    dashboard:Dict[str, Dict[str, Any]] = dict()
    dashboard["suffix_count_singular"] = dict()
    dashboard["suffix_count_singular"]['chart'] = wordform_counter_chart(sources, 'suffix', 'singular', "Suffix Count")
    dashboard["suffix_count_singular"]['table'] = counter_table(dashboard["suffix_count_singular"]['chart'])


    if len(sources)>1:
        dashboard["word_counter"] = dict()
        dashboard["word_counter"]['chart'] = word_counter_chart(word_counter(sources))
        dashboard["word_counter"]['table'] = counter_table(dashboard["word_counter"]['chart'])
        dashboard["root_counter"] = dict()
        source_roots = root_counter(sources)
        dashboard["root_counter"]['chart'] = root_counter_chart(source_roots)
        dashboard["root_counter"]['table'] = counter_table(dashboard["root_counter"]['chart'])
        dashboard["root_counter_unique"]=dict()
        dashboard["root_counter_unique"]['table'] = root_counter_unique_table(source_roots)
        # dashboard["root_unique_suffix_counter"] = dict()
        # dashboard["root_unique_suffix_counter"]['chart'] = root_unique_suffix_counter_chart(root_unique_suffix_counter(sources))
        # dashboard["root_unique_suffix_counter"]['table'] = counter_table(dashboard["root_unique_suffix_counter"]['chart'])

    

    return dashboard

def root_counter_unique_table(source_roots):
    return {
        "header": "Unique roots",
        "content": [
            ["Source", "Root", "Suffixes"],
            *[
                [source, root, ', '.join([
                    suffix 
                    for current_user_source in [s for s in current_user.sources if s.name==source] 
                    for current_user_word in [w for w in current_user_source.words if w.get_joined_roots()==root] 
                    for current_user_grammatical_case in current_user_word.grammatical_cases 
                    if current_user_grammatical_case.number=='singular' and (suffix:=getattr(current_user_grammatical_case.nominative, 'suffix', False))
                ])]
                for source, source_value in source_roots.items()
                for root in source_value['unique']['roots']

            ]
        ]
    }

# def root_unique_suffix_counter(sources):
#     sources_roots_unique_suffixes = {
#         source.name: {
#             word.get_joined_roots('-'): suffixes
#             for word in source.words
#             if (suffixes:={
#                 case.nominative.suffix
#                 for case in word.grammatical_cases
#                 if case.number=='singular' and getattr(case, 'nominative') and all(matches:=[
#                     case.nominative.suffix!=other_case.nominative.suffix and other_word.get_joined_roots('-')==word.get_joined_roots('-')
#                     for other_source in [s for s in sources if s!=source]
#                     for other_word in other_source.words
#                     for other_case in [c for c in other_word.grammatical_cases if c.number=='singular' and getattr(c, 'nominative')]
#                     if other_word.get_joined_roots('-')==word.get_joined_roots('-')
#                 ]) and bool(matches)
#             })
#         }
#         for source in sources}
#     print(sources_roots_unique_suffixes)

# def root_unique_suffix_counter_chart(s):
#     pass

def root_counter_chart(source_words: Dict[str, Dict[str, Dict[str, Any]]]) -> str:
    labels = list(next(iter(source_words.values())).keys())
    return json.dumps({
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [{
            "label": source_name,
            "backgroundColor": generate_rgb(),
            "data": [source[label]['count'] for label in labels]
            } for source_name, source in source_words.items()]
        },
        "options": {
            "title": {
                "display": True,
                "text": "Root comparison"
            },
            "tooltips": {
                "intersect": False
            },
            "scales": {
                "yAxes": [{
                    "ticks": {
                        "beginAtZero": True
                    }
                }]
            }
        }
    })

def root_counter(sources: List[Source]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    sources_roots: Dict[str, Dict[str, Dict[str, Any]]] = {
        source.name: {
            "total": {
                "roots": (roots:=set(map(lambda word: word.get_joined_roots(), source.words))),
                "count": len(roots)
            }
        }
        for source in sources
    }
    for i in sources_roots:
        sources_roots[i]['common'] = {
            "roots": (not_unique_roots:=(sources_roots[i]["total"]["roots"] & {z for y, v in sources_roots.items() for z in v["total"]["roots"] if i!=y})),
            "count": len(not_unique_roots)
        }
    for i in sources_roots:
        sources_roots[i]['unique'] = {
            "roots": (unique_roots:=(sources_roots[i]["total"]["roots"] - {z for y, v in sources_roots.items() for z in v["total"]["roots"] if i!=y})),
            "count": len(unique_roots)
        }

    return sources_roots

def word_counter_chart(source_words: Dict[str, Dict[str, Dict[str, Any]]]) -> str:
    labels = list(next(iter(source_words.values())).keys())
    return json.dumps({
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [{
            "label": source_name,
            "backgroundColor": generate_rgb(),
            "data": [source[label]['count'] for label in labels]
            } for source_name, source in source_words.items()]
        },
        "options": {
            "title": {
                "display": True,
                "text": "Word comparison"
            },
            "tooltips": {
                "intersect": False
            },
            "scales": {
                "yAxes": [{
                    "ticks": {
                        "beginAtZero": True
                    }
                }]
            }
        }
    })



def word_counter(sources: List[Source]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    sources_words: Dict[str, Dict[str, Dict[str, Any]]] = {
        source.name: {
            "total": {
                "words": (words:=set(map(lambda word: word.spelling, source.words))),
                "count": len(words)
            }
        }
        for source in sources
    }
    for i in sources_words:
        sources_words[i]['common'] = {
            "words": (not_unique_words:=(sources_words[i]["total"]["words"] & {z for y, v in sources_words.items() for z in v["total"]["words"] if i!=y})),
            "count": len(not_unique_words)
        }
    for i in sources_words:
        sources_words[i]['unique'] = {
            "words": (unique_words:=(sources_words[i]["total"]["words"] - {z for y, v in sources_words.items() for z in v["total"]["words"] if i!=y})),
            "count": len(unique_words)
        }

    return sources_words

def wordform_counter_chart(sources: List[Source], word_part, number=None, name="Suffix Count"):
    wordform_counter = [source.wordform_counter(word_part, number) for source in sources]
    wordform_counter = [OrderedDict(sorted(counter.items(), key=lambda t: t[1], reverse=True)) for counter in wordform_counter]
    labels = list(sum(map(Counter, wordform_counter), Counter()).keys())
    datasets = [[count.get(label, 0) for label in labels] for count in wordform_counter]
    
    return json.dumps({
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [{
            "label": sources[i].name,
            "backgroundColor": generate_rgb(),
            "data": data
            } for i, data in enumerate(datasets)]
        },
        "options": {
            "title": {
                "display": True,
                "text": name
            },
            "tooltips": {
                "intersect": False
            },
            "scales": {
                "yAxes": [{
                    "ticks": {
                        "beginAtZero": True
                    }
                }]
            }
        }
    })

def counter_table(chart):
    chart = json.loads(chart)
    return {
        "content":  [
            ["Sources", *chart["data"]["labels"]],
            *[
                [data["label"], *data["data"]] 
                for data in chart["data"]["datasets"] 
            ]
        ]
    }
        

def generate_rgb():
    return f"rgb{(random.randint(0,255),random.randint(0,255),random.randint(0,255))}"

def test_chart():
    return json.dumps({
    "type": "line",

    "data": {
        "labels": ["January", "February", "March", "April", "May", "June", "July"],
        "datasets": [{
            "label": "My First dataset",
            "backgroundColor": "rgb(255, 99, 132)",
            "borderColor": "rgb(255, 99, 132)",
            "data": [0, 10, 5, 2, 20, 30, 45]
        }]
    },
    "options": {}
    })