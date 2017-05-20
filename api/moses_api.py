from flask import request, send_file
from flask_api import FlaskAPI
import subprocess
import zipfile
import os
import io
from TTT.main import TTT

app = FlaskAPI(__name__)
ttt = TTT()


def translate(language_model_name,text):
    return ttt._machine_translation(language_model_name,text)


@app.route("/PrepareCorpusTest", methods=['GET'])
def preparation():
    source='/home/moses/Downloads/api/news-commentary-v8.de-en.en.txt'
    target='/home/moses/Downloads/api/news-commentary-v8.de-en.de.txt'
    return ttt._prepare_corpus("/home/moses/language_models","en","de",source,target,target)

@app.route("/GetAllAvailableLanguageModelNames", methods=['GET'])
def get_dir_listing():
    LM_DIR = "/home/moses/language_models/"
    return [o for o in os.listdir(LM_DIR) if os.path.isdir(os.path.join(LM_DIR,o))]


@app.route("/Train/<language_model_name>", methods=['GET'])
def training(language_model_name):
    return ttt._train(language_model_name)


@app.route("/GetLM/<language_model_name>", methods=['GET'])
def getLM(language_model_name):
    """
    Asks for the zip file of the Language Model to be used by TTT
    """
    def zipdir(path, ziph):

        lenDirPath = len('/home/moses/language_models/')
        # ziph is zipfile handle
        for root, dirs, files in os.walk(path):
            for file in files:
                filePath = os.path.join(root, file)
                ziph.write(filePath , filePath[lenDirPath :] )

    memory_file = io.BytesIO()
    zf = zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED)
    zipdir('/home/moses/language_models/' + language_model_name, zf)
    zf.close()
    memory_file.seek(0)

    return send_file(memory_file, attachment_filename=language_model_name+'.zip', as_attachment=True)

@app.route("/Translate", methods=['POST'])
def translate_post():
    """
    Translate text
    """
    language_model_name = request.form.get('LM_name')
    text = request.form.get('text')
    return translate(language_model_name,text.encode('utf8').decode('utf8'))

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

    return ttt.evaluate([WER,PER,HTER,BLEU,BLEU2GRAM,BLEU3GRAM,BLEU4GRAM],UneditedMT.encode('utf-8'),EditedMT.encode('utf-8'))
