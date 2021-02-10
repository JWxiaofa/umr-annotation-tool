from flask import url_for, redirect, flash
from werkzeug.utils import secure_filename
from typing import List, Tuple
import json
from utils import html, process_exported_file
from flask_login import current_user

from flask import render_template, request, Blueprint
from umr_annot_tool import db
from umr_annot_tool.models import Sent, Doc, Annotation, User, Post
from umr_annot_tool.main.forms import UploadForm

main = Blueprint('main', __name__)
FRAME_DESC_FILE = "umr_annot_tool/resources/frames-arg_descriptions.json"


def load_file2db(filename: str, file_format: str, content_string: str, lang: str, sents: List[List[str]], has_annot: bool, sent_annots=None, doc_annots=None, aligns=None) -> None:
    existing_doc = Doc.query.filter_by(filename=filename, user_id=current_user.id).first()
    if existing_doc:
        doc_id = existing_doc.id
        existing_doc.content = content_string
        existing_doc.file_format = file_format
        existing_doc.lang = lang
        db.session.commit()
        flash('Your doc and sents already created.', 'success')
    else:
        doc = Doc(lang=lang, filename=filename, content=content_string, user_id=current_user.id, file_format=file_format)
        db.session.add(doc)
        db.session.commit()
        doc_id = doc.id
        flash('Your doc has been created!', 'success')
        for sent_of_tokens in sents:
            sent = Sent(content=" ".join(sent_of_tokens), doc_id=doc.id, user_id=current_user.id)
            db.session.add(sent)
            db.session.commit()
        flash('Your sents has been created.', 'success')

    if has_annot:
        print("sents from annot: ", sents)
        for i in range(len(sents)):
            existing = Annotation.query.filter(Annotation.sent_id == i+1, Annotation.doc_id == doc_id,
                                               Annotation.user_id == current_user.id).first()
            if existing:  # update the existing Annotation object
                print("upadating existing annotation")
                existing.annot_str = sent_annots[i]
                existing.doc_annot = doc_annots[i]
                existing.alignment = aligns[i]
                db.session.commit()
            else:
                annotation = Annotation(annot_str=sent_annots[i], doc_annot=doc_annots[i], alignment=aligns[i],
                                        author=current_user,
                                        sent_id=i+1,
                                        doc_id=doc_id,
                                        umr={}, doc_umr={})
                db.session.add(annotation)
                db.session.commit()
        flash('Your annotations has been created.', 'success')


@main.route("/upload", methods=['GET', 'POST'])
def upload():
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))

    form = UploadForm()
    if form.validate_on_submit():
        if form.file.data and form.file.data.filename:
            content_string = form.file.data.read().decode("utf-8")
            print("content_string: ", content_string)
            filename = secure_filename(form.file.data.filename)
            print('filename: ', filename)
            file_format = form.file_format.data
            print('file_format: ', file_format)
            lang = form.language_mode.data
            print('lang: ', lang)
            if file_format == 'exported_file':  # has annotation
                new_content_string, sents, sent_annots, doc_annots, aligns, new_user_id, new_lang = process_exported_file(content_string)
                load_file2db(filename=filename, file_format=file_format, content_string=new_content_string, lang=lang, sents=sents, has_annot=True, sent_annots=sent_annots, doc_annots=doc_annots, aligns=aligns)
            else:  # doesn't have annotation
                sents, _, _, _, _, _ = html(content_string, file_format)
                load_file2db(filename=filename, file_format=file_format, content_string=content_string, lang=lang, sents=sents, has_annot=False)
            return redirect(url_for('main.annotate', doc_id=Doc.query.filter_by(filename=filename, user_id=current_user.id).first().id))
        else:
            flash('Please upload a file and/or choose a language.', 'danger')
    return render_template('upload.html', title='upload', form=form)


@main.route("/annotate/<int:doc_id>", methods=['GET', 'POST'])
def annotate(doc_id):
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))
    doc = Doc.query.get_or_404(doc_id)
    print(doc.content)
    sents, sents_html, sent_htmls, df_htmls, gls, notes = html(doc.content, doc.file_format)
    frame_dict = json.load(open(FRAME_DESC_FILE, "r"))
    snt_id = 1
    if "set_sentence" in request.form:
        snt_id = int(request.form["sentence_id"])

    # if "prev_sentence" in request.form:
    #     snt_id = max(int(request.form["sentence_id"]) - 1, 1)
    #     print("snt_id: ", snt_id)
    # elif "next_sentence" in request.form:
    #     print("sanity check sentence id", int(request.form["sentence_id"]))
    #     snt_id = min(int(request.form["sentence_id"]) + 1, len(sents))

    # add to db
    if request.method == 'POST':
        try:
            amr_html = request.get_json(force=True)["amr"]
            # get rid of the head highlight tag
            amr_html = amr_html.replace('<span class="text-success">', '')
            amr_html = amr_html.replace('</span>', '')

            print("amr_html: ", amr_html)
            align_info = request.get_json(force=True)["align"]
            print("align_ino: ", align_info)
            snt_id_info = request.get_json(force=True)["snt_id"]
            print("snt_id_info: ", snt_id_info)
            umr_dict = request.get_json(force=True)["umr"]
            print("umr_dict: ", umr_dict)
            existing = Annotation.query.filter(Annotation.sent_id == snt_id_info, Annotation.doc_id == doc_id,
                                               Annotation.user_id == current_user.id).first()
            if existing:  # update the existing Annotation object
                print("upadating existing annotation")
                existing.annot_str = amr_html
                existing.alignment = align_info
                existing.umr = umr_dict
                db.session.commit()
            else:
                annotation = Annotation(annot_str=amr_html, doc_annot='', alignment=align_info, author=current_user,
                                        sent_id=snt_id_info,
                                        doc_id=doc_id,
                                        umr=umr_dict, doc_umr={})
                db.session.add(annotation)
                db.session.commit()

            return {"amr": amr_html}
        except:
            print("add current annotation and alignments to database failed")

    # load single annotation for current sentence from db used for load_history()
    try:
        curr_sent_annot = Annotation.query.filter(Annotation.sent_id == snt_id, Annotation.doc_id == doc_id,
                                                  Annotation.user_id == current_user.id).first().annot_str.replace("\n",
                                                                                                                   "")
    except:
        curr_sent_annot = ""
    try:
        curr_sent_align = Annotation.query.filter(Annotation.sent_id == snt_id, Annotation.doc_id == doc_id,
                                                  Annotation.user_id == current_user.id).first().alignment.replace("\n",
                                                                                                                   "")
    except:
        curr_sent_align = ""

    try:
        curr_sent_umr = Annotation.query.filter(Annotation.sent_id == snt_id, Annotation.doc_id == doc_id,
                                                Annotation.user_id == current_user.id).first().umr
    except:
        curr_sent_umr = {}

    print("curr_sent_annot", curr_sent_annot)
    print("curr_sent_align", curr_sent_align)
    print("curr_sent_umr", curr_sent_umr)
    print(type(curr_sent_umr))

    # load all annotations for current document used for export_annot()
    annotations = Annotation.query.filter(Annotation.doc_id == doc_id, Annotation.user_id == current_user.id).order_by(Annotation.sent_id).all()
    filtered_sentences = Sent.query.filter(Sent.doc_id == doc_id, Sent.user_id == current_user.id).all()
    all_annots = [annot.annot_str for annot in annotations]
    print("all_annots: ", all_annots)
    all_aligns = [annot.alignment for annot in annotations]
    print("all_aligns: ", all_aligns)
    all_doc_annots = [annot.doc_annot for annot in annotations]
    print("all_doc_annots: ", all_doc_annots)
    all_sents = [sent2.content for sent2 in filtered_sentences]
    print("all_sents: ", all_sents)
    exported_items = [list(p) for p in zip(all_sents, all_annots, all_aligns, all_doc_annots)]
    print("exported_items: ", exported_items)


    return render_template('index.html', lang=doc.lang, filename=doc.filename, snt_id=snt_id, doc_id=doc_id,
                           sents=sents, sents_html=sents_html, sent_htmls=sent_htmls, df_html=df_htmls, gls=gls,
                           notes=notes,
                           frame_dict=frame_dict,
                           curr_sent_align=curr_sent_align, curr_sent_annot=curr_sent_annot,
                           curr_sent_umr=curr_sent_umr,
                           exported_items=exported_items)


@main.route("/doclevel/<int:doc_id>", methods=['GET', 'POST'])
def doclevel(doc_id):
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))
    current_snt_id = 1
    if "set_sentence" in request.form:
        current_snt_id = int(request.form["sentence_id"])

    # add to db
    if request.method == 'POST':
        try:
            umr_html = request.get_json(force=True)["umr"]
            print("umr_html: ", umr_html)
            snt_id_info = request.get_json(force=True)["snt_id"]
            print("snt_id_info:", snt_id_info)
            umr_dict = request.get_json(force=True)["umr_dict"]
            existing = Annotation.query.filter(Annotation.sent_id == snt_id_info, Annotation.doc_id == doc_id,
                                               Annotation.user_id == current_user.id).first()
            if existing:  # update the existing Annotation object
                print("updating existing annotation")
                existing.doc_annot = umr_html
                existing.doc_umr = umr_dict
                db.session.commit()
            else:
                print("the sent level annotation of the current sent doesn't exist")
            return {"umr": umr_html}
        except:
            print("add doc level annotation to database failed")

    doc = Doc.query.get_or_404(doc_id)
    sents = Sent.query.filter(Sent.doc_id == doc.id, Sent.user_id == current_user.id).order_by(Sent.id).all()
    annotations = Annotation.query.filter(Annotation.doc_id == doc.id, Annotation.user_id == current_user.id).order_by(
        Annotation.sent_id).all()
    # annotations = Annotation.query.filter(Annotation.doc_id == doc.id).all()

    if doc.file_format == 'plain_text':
        sent_annot_pairs = list(zip(sents, annotations))
    else:
        _, sents_html, sent_htmls, df_html, gls, notes = html(doc.content, doc.file_format)
        sent_annot_pairs = list(zip(df_html, annotations))

    print("sent_annot_pairs: ", sent_annot_pairs)

    # print(annotations[0].annot_str)
    # print(annotations[1].annot_str)

    # sent, annot = sent_annot_pairs[0]
    # print("*********")
    # print('sent: ', sent.content)
    # print('annot: ', annot.annot_str)
    # sent2, annot2 = sent_annot_pairs[1]
    # print("*********")
    # print('sent: ', sent2.content)
    # print('annot: ', annot2.annot_str)

    # load all annotations for current document used for export_annot()
    all_annots = [annot.annot_str for annot in annotations]
    print("all_annots: ", all_annots)
    all_aligns = [annot.alignment for annot in annotations]
    print("all_aligns: ", all_aligns)
    all_doc_annots = [annot.doc_annot for annot in annotations]
    print("all_doc_annots: ", all_doc_annots)
    all_sents = [sent2.content for sent2 in sents]
    print("all_sents: ", all_sents)
    exported_items = [list(p) for p in zip(all_sents, all_annots, all_aligns, all_doc_annots)]
    print("exported_items: ", exported_items)

    try:
        current_sent_pair = sent_annot_pairs[current_snt_id - 1]
    except IndexError:
        flash('You have not created sentence level annotation yet')
        redirect(url_for('main.annotate', doc_id=doc_id))

    print("doc_annot: ", sent_annot_pairs[current_snt_id - 1][1].doc_annot)
    print("doc_umr: ", sent_annot_pairs[current_snt_id - 1][1].doc_umr)
    print("current_sent_table: ", sent_annot_pairs[current_snt_id-1][0])
    print("current_snt_id: ", current_snt_id)

    return render_template('doclevel.html', doc_id=doc_id, sent_annot_pairs=sent_annot_pairs, filename=doc.filename,
                           title='Doc Level Annotation', current_snt_id=current_snt_id,
                           current_sent_pair=current_sent_pair, exported_items=exported_items, lang=doc.lang, file_format=doc.file_format)


@main.route("/about")
def about():
    return render_template('about.html', title='About')


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
