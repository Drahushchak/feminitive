from flask_login import UserMixin
from app import db
from collections import Counter

def recalcultate(mapper, connection, target):
    pass



class User(UserMixin, db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    email       = db.Column(db.String(100), unique=True)
    password    = db.Column(db.String(100))
    name        = db.Column(db.String(1000))
    sources     = db.relationship('Source', backref='user', lazy=True, cascade="all, delete")

    def __str__(self):
        return self.name

    def get_source(self, source_id):
        return next((source for source in self.sources if source.id==source_id) , None)

class Source(db.Model):
    id      = db.Column(db.Integer, primary_key=True)
    name    = db.Column(db.String(1000))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    words   = db.relationship('Word', backref='source', lazy=True, cascade="all, delete")

    def __str__(self):
        return self.name

    def wordform_counter(self, word_part:str, number=None):
        return sum([word.wordform_counter(word_part, number) for word in self.words], Counter())


class Word(db.Model):
    id                  = db.Column(db.Integer, primary_key=True)
    spelling            = db.Column(db.String(1000))
    source_id           = db.Column(db.Integer, db.ForeignKey('source.id'), nullable=False)
    grammatical_cases   = db.relationship('GrammaticalCase', backref='word', lazy=True, cascade="all, delete")
    
    def __str__(self):
        return self.spelling

    def wordform_counter(self, word_part:str, number=None):
        return sum([case.wordform_counter(word_part) for case in self.grammatical_cases if not number or number==case.number], Counter())

class GrammaticalCase(db.Model):
    id                      = db.Column(db.Integer, primary_key=True)
    number                  = db.Column(db.Enum('singular', 'plural', name='number'))
    word_form_id            = db.Column(db.Integer, db.ForeignKey('word.id'), nullable=False)
    nominative_id           = db.Column(db.Integer, db.ForeignKey('word_form.id'), unique=True)
    genitive_id             = db.Column(db.Integer, db.ForeignKey('word_form.id'), unique=True)
    dative_id               = db.Column(db.Integer, db.ForeignKey('word_form.id'), unique=True)
    accusative_id           = db.Column(db.Integer, db.ForeignKey('word_form.id'), unique=True)
    instrumental_id         = db.Column(db.Integer, db.ForeignKey('word_form.id'), unique=True)
    locative_id             = db.Column(db.Integer, db.ForeignKey('word_form.id'), unique=True)
    vocative_id              = db.Column(db.Integer, db.ForeignKey('word_form.id'), unique=True)
    nominative              = db.relationship("WordForm", foreign_keys="GrammaticalCase.nominative_id", cascade="all, delete")
    genitive                = db.relationship("WordForm", foreign_keys="GrammaticalCase.genitive_id", cascade="all, delete")
    dative                  = db.relationship("WordForm", foreign_keys="GrammaticalCase.dative_id", cascade="all, delete")
    accusative              = db.relationship("WordForm", foreign_keys="GrammaticalCase.accusative_id", cascade="all, delete")
    instrumental            = db.relationship("WordForm", foreign_keys="GrammaticalCase.instrumental_id", cascade="all, delete")
    locative                = db.relationship("WordForm", foreign_keys="GrammaticalCase.locative_id", cascade="all, delete")
    vocative                 = db.relationship("WordForm", foreign_keys="GrammaticalCase.vocative_id", cascade="all, delete")
# event.listen(User, 'after_insert', after_insert_listener)
    def __str__(self):
        return self.number

    def wordform_counter(self, word_part:str,):
        return Counter(filter(None,[
            getattr(self.nominative, word_part, None),
            getattr(self.genitive, word_part, None),
            getattr(self.dative, word_part, None),
            getattr(self.accusative, word_part, None),
            getattr(self.instrumental, word_part, None),
            getattr(self.locative, word_part, None),
            getattr(self.vocative, word_part, None)
        ]))

class WordForm(db.Model):
    id                  = db.Column(db.Integer, primary_key=True)
    spelling            = db.Column(db.String(1000), nullable=False)
    suffix              = db.Column(db.String(10), nullable=False)
    flexion             = db.Column(db.String(10))

    def __str__(self):
        return self.spelling