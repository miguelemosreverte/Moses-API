from flask import request
from flask_api import FlaskAPI
import subprocess
import os
from TTT.main import TTT

app = FlaskAPI(__name__)
ALLOWED_EXTENSIONS = set(['txt', 'pdf'])

ttt = TTT()

LM_DIR = "/home/moses/language_models/"
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def translate(text):
    UNTRANSLATED_FILEPATH = "/home/moses/temp/Untranslated.txt"
    with open(UNTRANSLATED_FILEPATH, "w") as f:
        f.write(text.encode('utf-8'))
    return ttt._machine_translation(UNTRANSLATED_FILEPATH)


@app.route("/PrepareCorpusTest", methods=['GET'])
def preparation():
    source='/home/moses/Downloads/api/news-commentary-v8.de-en.en.txt'
    target='/home/moses/Downloads/api/news-commentary-v8.de-en.de.txt'
    return ttt._prepare_corpus("/home/moses/language_models","en","de",source,target,target)

@app.route("/GetAllAvailableLanguageModelNames", methods=['GET'])
def get_dir_listing():
    return [o for o in os.listdir(LM_DIR) if os.path.isdir(os.path.join(LM_DIR,o))]


@app.route("/Train", methods=['GET'])
def training():
    return ttt._train()

@app.route("/SetLM/<language_model_name>", methods=['GET'])
def setLM(language_model_name):
    """
    Changes the Language Model to be used by TTT
    """
    #TODO find out why there is always a closing brace in the incomming message
    ttt.language_model_name = language_model_name.replace('}','')
    return ttt.language_model_name

@app.route("/Translate/<text>", methods=['GET'])
def user_get(text):
    """
    Translate text
    """
    text = translate(text.encode('utf8').decode('utf8'))
    return text

@app.route("/PrepareCorpus", methods=['POST', 'PUT'])
def uploadCorpus():
    """
    PreparesCorpus
    """

    LM_FILEPATH = "/home/moses/temp/LanguageModel.txt"
    TM_source_FILEPATH = "/home/moses/temp/TranslationModel_source.txt"
    TM_target_FILEPATH = "/home/moses/temp/TranslationModel_target.txt"

    TM_source = request.form['TM_source']
    TM_target = request.form['TM_target']
    LM = request.form['LM']
    source_lang = request.form['source_lang']
    target_lang = request.form['target_lang']
    LM_name = request.form['LM_name']

    if (TM_source and TM_target and LM and source_lang and target_lang and LM_name):

        with open(LM_FILEPATH, "w") as f:
            f.write(LM.encode('utf-8'))
        with open(TM_source_FILEPATH, "w") as f:
            f.write(TM_source.encode('utf-8'))
        with open(TM_target_FILEPATH, "w") as f:
            f.write(TM_target.encode('utf-8'))

        newpath = '/home/moses/language_models/' + LM_name
        if not os.path.exists(newpath):
            os.makedirs(newpath)
        return ttt._prepare_corpus(newpath,source_lang,target_lang,TM_source_FILEPATH,TM_target_FILEPATH,LM_FILEPATH)
    else:
        return ('Error reading file...\n')


@app.route("/Evaluate", methods=['POST','PUT'])
def evaluate():

    WER = request.form.get('WER') != None
    PER = request.form.get('PER') != None
    HTER = request.form.get('HTER') != None
    BLEU = request.form.get('BLEU') != None
    BLEU2GRAM = request.form.get('BLEU2GRAM') != None
    BLEU3GRAM = request.form.get('BLEU3GRAM') != None
    BLEU4GRAM = request.form.get('BLEU4GRAM') != None

    UneditedMT = request.form['UneditedMT']
    EditedMT = request.form['EditedMT']
    #checkbox_indexes = [WER,PER,HTER, GTM, BLEU,BLEU2GRAM,BLEU3GRAM,BLEU4GRAM]

    return ttt.evaluate([WER,PER,HTER,BLEU,BLEU2GRAM,BLEU3GRAM,BLEU4GRAM],UneditedMT.encode('utf-8'),EditedMT.encode('utf-8'))
