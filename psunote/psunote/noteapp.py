import flask

import models
import forms


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )

@app.route("/tags")
def tags_view_all():
    db = models.db
    tags = db.session.execute(db.select(models.Tag)).scalars()
    return flask.render_template(
        "tags-view-all.html",
        tags=tags,
    )

@app.route("/tags/delete/<int:tag_id>", methods=["POST"])
def tags_delete(tag_id):
    db = models.db
    tag = db.session.execute( 
        db.select(models.Tag).where(models.Tag.id == tag_id)
    ).scalars().first()
    
    if tag:
        notes_with_tag = db.session.execute(
            db.select(models.Note).where(models.Note.tags.any(id=tag.id))
        ).scalars().all()

        for note in notes_with_tag:
            note.tags.remove(tag)

        db.session.delete(tag)
        db.session.commit()
        flask.flash("ลบได้นะ", "success")
    else:
        flask.flash("Tag not found!", "error")

    return flask.redirect(flask.url_for('tags_view_all'))


@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))

@app.route("/notes/edit/<int:note_id>", methods=["GET", "POST"])
def notes_edit(note_id):
    db = models.db
    note = db.session.execute(
        db.select(models.Note).where(models.Note.id == note_id)
    ).scalars().first()

    if not note:
        flask.flash("Note not found!", "error")
        return flask.redirect(flask.url_for("index"))

    form = forms.NoteForm(obj=note)

    return flask.render_template("notes-edit.html", form=form)




@app.route("/notes/delete/<int:note_id>", methods=["POST"])
def notes_delete(note_id):
    db = models.db
    note = db.session.execute(
        db.select(models.Note).where(models.Note.id == note_id)
    ).scalars().first()
    if note:
        db.session.delete(note)
        db.session.commit()
        flask.flash("ลบได้นะ", "success")
    else:
        flask.flash("Note not found!", "error")
    return flask.redirect(flask.url_for("index"))

@app.route("/tags/edit/<int:tag_id>", methods=["GET", "POST"])
def tags_edit(tag_id):
    db = models.db
    tag = db.session.execute(
        db.select(models.Tag).where(models.Tag.id == tag_id)
    ).scalars().first()

    if not tag:
        flask.flash("Tag not found!", "error")
        return flask.redirect(flask.url_for("tags_view_all"))

    if flask.request.method == "POST":
        tag_name = flask.request.form.get("tag_name").strip()
        if tag_name:
            tag.name = tag_name
            db.session.commit()
            flask.flash("Tag updated successfully!", "success")
            return flask.redirect(flask.url_for("tags_view_all"))

    notes = db.session.execute(
        db.select(models.Note).join(models.Note.tags).where(models.Tag.id == tag_id)
    ).scalars().all()

    return flask.render_template("tags-view.html", tag=tag, notes=notes)

@app.route("/note/remove_tag/<int:note_id>/<int:tag_id>", methods=["POST"])
def note_remove_tag(note_id, tag_id):
    db = models.db
    note = db.session.execute(
        db.select(models.Note).where(models.Note.id == note_id)
    ).scalars().first()

    tag = db.session.execute(
        db.select(models.Tag).where(models.Tag.id == tag_id)
    ).scalars().first()

    if note and tag:
        note.tags.remove(tag)
        db.session.commit()
        flask.flash("Tag removed from note!", "success")

    return flask.redirect(flask.url_for("tags_view", tag_name=tag.name))


@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    if not tag:
        flask.flash("Tag not found!", "error")
        return flask.redirect(flask.url_for("tags_view_all"))
    
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag=tag,
        tag_name=tag_name,
        notes=notes,
    )


if __name__ == "__main__":
    app.run(debug=True)
