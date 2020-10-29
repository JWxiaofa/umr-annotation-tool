from flask import url_for, redirect
from werkzeug.utils import secure_filename
from typing import List, Dict
import attr
import json
import xml.etree.ElementTree as ET
from utils import parse_xml
from bs4 import BeautifulSoup
from flask_login import current_user

from flask import render_template, request, Blueprint
from umr_annot_tool import db
from umr_annot_tool.models import Sent, Doc, Annotation, User, Post
from umr_annot_tool.main.forms import UploadForm

main = Blueprint('main', __name__)
FRAME_DESC_FILE = "umr_annot_tool/resources/frames-arg_descriptions.json"


# FRAME_DESC_FILE = "/umr_annot_tool/resources/frames_chinese.json"


@attr.s()
class Sentence:
    words: List[str] = attr.ib()
    id: int = attr.ib()
    length: int = attr.ib()


@attr.s()
class ArgTokenParser:
    frame_dict: Dict = attr.ib()

    @classmethod
    def from_json(cls, frame_file: str):
        frame_dict = json.load(open(frame_file, "r"))
        return cls(frame_dict)

    def parse(self, token: str) -> Dict:
        senses = []
        token_pattern = token + "-"
        for sense in self.frame_dict:
            if sense.startswith(token_pattern):
                senses.append({"name": sense, "desc": self._desc2str(sense)})
        if not senses:
            senses.append({"name": token, "desc": token + "\nThis is placeholder"})
        return {"res": senses}

    def _desc2str(self, name: str) -> str:
        temp = [name]
        desc: Dict = self.frame_dict[name]
        for pair in desc.items():
            temp.append(": ".join(pair))
        return "\n".join(temp)


frame_parser = ArgTokenParser.from_json(FRAME_DESC_FILE)
snts = []
target_language = ['Default']
df_html = []
gls = []
notes = []
filename = []


@main.route("/annotate", methods=['GET', 'POST'])
def annotate():
    try:
        sentence_content = " ".join(snts[0].words)
    except IndexError:
        return redirect(url_for('main.upload'))
    if request.method in ['GET', 'POST']:
        # snt_id = request.form["sentence_id"]
        # sentence_db = " ".join(snts[int(snt_id)].words)
        # print("sentence_db: ", sentence_db)

        try:
            token = request.get_json(force=True)["selected"]
            # orig_token = request.get_json(force=True)["selected_tok"]
            # selected_sentId = request.get_json(force=True)["selected_sentId"]
            # selected_index = snts[int(selected_sentId)].words.index(orig_token)

            print(token)
            print(frame_parser.parse(token))
            return frame_parser.parse(token)
        except:
            pass

        # load_history annotation
        try:
            # document_name = request.get_json(force=True)["documentName"]
            history_sent_id = request.get_json(force=True)["history_sent_id"]
            print("history_sent_id: ", history_sent_id)
            history_sent = " ".join(snts[int(history_sent_id)-1].words)
            print("history_sent: ", history_sent)
            sent_id = Sent.query.filter(Sent.content == history_sent).first().id
            print("sent_id: ", sent_id)
            doc_id = Sent.query.filter(Sent.content == history_sent).first().doc_id
            print("doc_id: ", doc_id)
            history_annot = Annotation.query.filter(Annotation.sent_id == sent_id, Annotation.doc_id == doc_id,
                                                    Annotation.user_id == current_user.id).first().annot_str
            history_align = Annotation.query.filter(Annotation.sent_id == sent_id, Annotation.doc_id == doc_id,
                                                    Annotation.user_id == current_user.id).first().alignment
            print("history_annot: ", history_annot)
            print("history_align: ", history_align)
            return {"history_annot": history_annot, "history_align": history_align}
        except:
            pass

        # load annotations to save
        try:
            doc_name = request.get_json(force=True)["doc_name"]
            print("doc_name: ", doc_name)
            doc_id = Doc.query.filter(Doc.filename==doc_name).first().id
            print("doc_id: ", doc_id)
            annotations = Annotation.query.filter(Annotation.doc_id==doc_id).all()
            sentences2 = Sent.query.filter(Sent.doc_id==doc_id).all()
            all_annots = [annot.annot_str for annot in annotations]
            all_aligns = [annot.alignment for annot in annotations]
            all_sents2 = [sent2.content for sent2 in sentences2]
            print(list(zip(all_sents2, all_annots, all_aligns)))
            return {"annotations": list(zip(all_sents2, all_annots, all_aligns))}

        except:
            pass


        # add to db
        try:
            amr_html = request.get_json(force=True)["amr"]
            print("amr_html: ", amr_html)
            db_sent_id = request.get_json(force=True)["sentence_id"]
            print("db_sent_id: ", db_sent_id)
            align_info = request.get_json(force=True)["align"]
            print("align_ino:", align_info)

            print(snts)
            sentence2db = " ".join(snts[int(db_sent_id)-1].words)
            print("sentence2db: ", sentence2db)
            sent_id = Sent.query.filter(Sent.content == sentence2db).first().id
            print("sent_id", sent_id)
            doc_id = Sent.query.filter(Sent.content == sentence2db).first().doc_id
            print("doc_id", doc_id)
            print("current_user id", current_user.id)

            existing = Annotation.query.filter(Annotation.sent_id == sent_id, Annotation.doc_id == doc_id,
                                               Annotation.user_id == current_user.id).first()
            print(existing)
            if existing:  # update the existing Annotation object
                print("here")
                existing.annot_str = amr_html
                existing.alignment = align_info
                db.session.commit()
            else:
                annotation = Annotation(annot_str=amr_html, alignment=align_info, author=current_user, sent_id=sent_id, doc_id=doc_id)
                db.session.add(annotation)
                db.session.commit()
            return {"amr": amr_html}
        except:
            pass

        total_snts = len(snts)
        print(f"total_snts: {total_snts}")
        print(target_language)

        if "set_sentence" in request.form:
            snt_id = request.form["sentence_id"]
            return render_template('index.html', sentence_content=sentence_content, sentence=snts[int(snt_id) - 1],
                                   total_snts=total_snts, all_snts=snts,
                                   lang=target_language[0], filename=filename[0], df_html=df_html, gls=gls, notes=notes)
        else:
            return render_template('index.html', sentence_content=sentence_content, sentence=snts[0],
                                   total_snts=total_snts, all_snts=snts,
                                   lang=target_language[0], filename=filename[0], df_html=df_html, gls=gls, notes=notes)
    else:
        return render_template('index.html', sentence_content=sentence_content, sentence=Sentence([], 0, 0),
                               total_snts=0, all_snts=[],
                               lang=target_language[0], filename=filename[0], df_html=df_html, gls=gls, notes=notes)


@main.route("/upload", methods=['GET', 'POST'])
def upload():
    # existing = Annotation.query.filter(Annotation.sent_id == 1, Annotation.doc_id == 1,
    #                                    Annotation.user_id == current_user.id).first()

    form = UploadForm()
    if request.method == "POST":
        target_language[0] = form.autocomplete_input.data
        # print(target_language)

        file = request.files['file']
        filename.clear()
        filename.append(file.filename)
        secure_filename(filename[0])
        print("filename:" + filename[0])
        content_string = file.read()

        snts.clear()
        df_html.clear()
        try:
            print("I am here 1")
            ET.fromstring(content_string)
            print("I am here 2")
            sents, dfs, sents_gls, conv_turns = parse_xml(content_string)
            print(sents[0], dfs[0])
            for i, sent in enumerate(sents):
                snts.append(Sentence(sent, i, len(sent)))
            for df in dfs:
                df.columns = range(1, len(df.columns)+1)
                print(df)
                print(df.columns)
                html_str = df.to_html(classes="table table-striped", justify='center').replace('border="1"',
                                                                                               'border="0"')
                soup = BeautifulSoup(html_str, "html.parser")
                words_row = soup.findAll('tr')[1]
                words_row['id'] = 'current-words'
                # elements = soup.findAll('tr')[3:6]
                # for ele in elements:
                #     ele['class'] = 'optional-rows'
                gram_row = soup.findAll('tr')[4]
                gram_row['class'] = 'optional-rows'
                df_html.append(str(soup))
            for translation in sents_gls:
                gls.append(translation)
            for conv_turn in conv_turns:
                notes.append(conv_turn)

            # print("df_html: ", df_html[0])


        except ET.ParseError:
            print("content_str: ", content_string)
            sents = content_string.strip().decode('UTF-8').split('\n')
            for i, sent in enumerate(sents):
                snts.append(Sentence(sent.split(), i, len(sent.split())))

        if not Doc.query.filter_by(filename=filename[0]).first():  # this doc is not already added in
            doc = Doc(lang=target_language[0], filename=filename[0])
            db.session.add(doc)
            db.session.commit()

            for sent_str in sents:
                if isinstance(sent_str, list):
                    print("sent_str: ", " ".join(sent_str))
                    sent = Sent(content=" ".join(sent_str), doc_id=doc.id)
                elif isinstance(sent_str, str):
                    print("sent_str: ", sent_str)
                    sent = Sent(content=sent_str, doc_id=doc.id)
                else:
                    raise Exception("wrong sent_str type!!!!!!!!!")
                db.session.add(sent)
                db.session.commit()
    return render_template('upload.html', title='upload', form=form)


@main.route("/doclevel", methods=['GET', 'POST'])
def doclevel():
    return render_template('doclevel.html', title='Doc Level Annotation')


@main.route("/about")
def about():
    return render_template('about.html', title='About')


# this is corresponded to corey's video home page, also thinking about making it doclevel annotation page

@main.route("/")
@main.route("/display_post")
def display_post():
    # posts = Post.query.all()
    page = request.args.get('page', default=1, type=int)
    # posts = Post.query.paginate(page=page, per_page=2)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page,
                                                                  per_page=2)  # if we want to order the posts from the lastest to the oldest
    return render_template('display_post.html', posts=posts)


@main.route("/guidelines")
def guidelines():
    return render_template('guidelines.html')
