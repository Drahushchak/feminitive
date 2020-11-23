from yaml import dump
from app import app
import yaml, json
from tempfile import SpooledTemporaryFile
from app.models import *
from typing import *
from collections import Counter
import random


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
                    for gramatical_case, gramatical_case_value in number_value.items():
                        if not isinstance(number, str): raise Exception(number)
                        if gramatical_case not in ('nominative', 'genitive', 'dative', 'accusative', 'instrumental', 'locative', 'vocative'): raise Exception(gramatical_case)
                        if gramatical_case_value:
                            if not isinstance(gramatical_case_value, dict): raise Exception(gramatical_case_value)
                            if not all((isinstance(key, str) and key and key in ('spelling', 'suffix', 'flexion')) for key, value in gramatical_case_value.items()): raise Exception(gramatical_case_value)
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
    dashboard = dict()
    dashboard["suffix_count_singular"] = dict()
    dashboard["suffix_count_singular"]['chart'] = wordform_counter_chart(sources, 'suffix', 'singular', "Suffix Count Singular")
    dashboard["suffix_count_singular"]['table'] = wordform_counter_table(dashboard["suffix_count_singular"]['chart'])
    dashboard["suffix_count_plural"] = dict()
    dashboard["suffix_count_plural"]['chart'] = wordform_counter_chart(sources, 'suffix', 'plural', "Suffix Count Plural")
    dashboard["suffix_count_plural"]['table'] = wordform_counter_table(dashboard["suffix_count_plural"]['chart'])
    dashboard["flexion_count_singular"] = dict()
    dashboard["flexion_count_singular"]['chart'] = wordform_counter_chart(sources, 'flexion', 'singular', "Flexion Count Singular")
    dashboard["flexion_count_singular"]['table'] = wordform_counter_table(dashboard["flexion_count_singular"]['chart'])
    dashboard["flexion_count_plural"] = dict()
    dashboard["flexion_count_plural"]['chart'] = wordform_counter_chart(sources, 'flexion', 'plural', "Flexion Count Plural")
    dashboard["flexion_count_plural"]['table'] = wordform_counter_table(dashboard["flexion_count_plural"]['chart'])
    
    if len(sources)>1:
        dashboard["unique_word_comparison"] = dict()


    return dashboard
    # Suffix count singular


def wordform_counter_chart(sources, word_part, number=None, name="Suffix Count"):
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

def wordform_counter_table(chart):
    chart = json.loads(chart)
    return [
        ["Sources", *chart["data"]["labels"]],
        *[
            [data["label"], *data["data"]] 
            for data in chart["data"]["datasets"] 
        ]
    ]
        

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