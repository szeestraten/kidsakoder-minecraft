# -*- coding: utf-8 -*-
"""
flask_app.views
~~~~~~~~~~~~~~~

Routes and view definitions for the flask application.
"""

from flask import render_template, request, redirect, url_for, flash, send_from_directory, safe_join, jsonify
from flask_app import app
from models import Meeting, World
from flask_security import login_required, current_user, utils, roles_required
import forms
import files
import urllib2
import locale
import tasks


@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    """ Renders the home page """
    # Meeting list will be shown at the bottom of the page
    meeting_list = Meeting.get_user_meetings(current_user.id)
    # Selected world (in meeting tab) defaults to None and gets overridden if there is a world selected
    world = None
    # Default to world selection tab
    # 0 is world selection tab and 1 is meeting details tab
    set_tab = 0
    # Locale encoding used for day names
    # preferred_encoding = locale.getpreferredencoding()
    preferred_encoding = 'UTF-8'

    # A form is posted
    if request.method == 'POST':
        # If request is a redirect from map page, we will have a WorldForm
        world_form = forms.WorldForm(request.form)
        if world_form.validate():
            # Go to meeting details tab
            set_tab = 1
            # Show empty meeting form
            meeting_form = forms.MeetingForm()
            try:
                world_id = int(world_form.world_id.data)
                description = world_form.description.data
                world = World.get_by_id(world_id)
                if world:
                    # Update description if changed
                    if world.description != description:
                        world.description = description
                        world.store()
                    # Put world ID in meeting form for reference
                    meeting_form.world_id.process_data(str(world_id))
                else:  # World does not exist
                    flash(u'Den valgte Minecraft verdenen eksisterer ikke')
                    set_tab = 0

            except ValueError:
                # A number was not supplied as world ID
                flash(u'world_id ValueError')

            return render_template(
                'index.html',
                set_tab=set_tab,
                title=u'Hjem',
                meetings=meeting_list,
                form=meeting_form,
                world=world,
                action=url_for('home'),
                locale=preferred_encoding
            )

        # Check if a meeting form is posted
        form = forms.MeetingForm(request.form)
        if form.validate():
            # If valid, put data from form into Meeting object
            meeting = Meeting(user_id=current_user.id)
            form.populate_obj(meeting)
            if meeting.world_id:  # World ID will be none if the posted value is not an integer
                if World.exists(meeting.world_id):  # Check that the world exists in the database
                    meeting.store()

                    # Celery stuff
                    # tasks.meeting_test.apply_async()
                    tasks.meeting_test.apply_async(eta=meeting.start_time, expires=meeting.end_time)

                    flash(u'Nytt møte lagt til')
                    return redirect(url_for('home'))

                else:  # World does not exist
                    flash(u'Den valgte Minecraft verdenen eksisterer ikke')
                    set_tab = 1

            else:  # World probably not chosen
                flash(u'Ingen Minecraft verden valgt')
                set_tab = 0

        else:  # Form not valid
            flash(u'Feil i skjema!')
            set_tab = 1
            try:  # Insert world info
                world_id = int(form.world_id.data)
                world = World.get_by_id(world_id)
            except ValueError:
                pass

    else:  # If not POST
        # Serve blank form
        form = forms.MeetingForm()

    return render_template(
        'index.html',
        set_tab=set_tab,
        title=u'Hjem',
        meetings=meeting_list,
        form=form,
        world=world,
        action=url_for('home'),
        locale=preferred_encoding
    )


@app.route('/contact')
@app.route('/kontakt')
@login_required
def contact():
    """ Renders the contact page. """
    return render_template(
        'contact.html',
        title=u'Kontakt oss'
    )


@app.route('/bruker')
@login_required
def user():
    """ Renders the user settings page """
    return render_template(
        'user/user.html',
        title=u'Instillinger'
    )


@app.route('/bruker/endre_epost', methods=['GET', 'POST'])
@login_required
def change_email():
    """ Renders the change email page and stores the new email """
    form = forms.ChangeEmail(request.form)
    if form.validate_on_submit():
        # Check if password is valid, then store new password
        if utils.verify_password(form.password.data, current_user.password):
            current_user.email = form.new_email.data
            current_user.store()
            flash(u'E-post adressen ble oppdatert')
            return redirect(url_for('user'))  # Redirect to user settings page
        form.password.errors.append(u'Feil passord')

    return render_template(
        'user/change_email.html',
        title=u'Endre e-post',
        form=form,
        action=url_for('change_email')
    )


@app.route('/bruker/endre_navn', methods=['GET', 'POST'])
@login_required
def change_name():
    """ Renders the change name page and stores the new name """
    form = forms.ChangeName(request.form)
    if form.validate_on_submit():
        current_user.name = form.new_name.data
        current_user.store()
        flash(u'Navn ble oppdatert')
        return redirect(url_for('user'))

    # Show current name in form
    form.new_name.process_data(current_user.name)
    return render_template(
        'user/change_name.html',
        title=u'Endre navn',
        form=form,
        action=url_for('change_name')
    )


@app.route('/bruker/endre_passord', methods=['GET', 'POST'])
@login_required
def change_password():
    """ Renders the change password page and stores the new password """
    form = forms.ChangePassword(request.form)
    if form.validate_on_submit():
        # Check if password is valid, then hash and store new password
        if utils.verify_password(form.old_password.data, current_user.password):
            current_user.password = utils.encrypt_password(form.new_password.data)
            current_user.store()
            flash(u'Passordet ble endret')
            return redirect(url_for('user'))
        form.old_password.errors.append(u'Feil passord')

    return render_template(
        'user/change_password.html',
        title=u'Endre passord',
        form=form,
        action=url_for('change_password')
    )


@app.route('/bruker/endre_spillernavn', methods=['GET', 'POST'])
@login_required
def change_playername():
    """ Renders the change Minecraft playername page and stores the playername and its related uuid """
    form = forms.ChangePlayername(request.form)
    if form.validate_on_submit():
        # Check if password is valid, then store playername and uuid
        if utils.verify_password(form.password.data, current_user.password):
            current_user.mojang_playername = form.playername.data
            current_user.mojang_uuid = form.uuid.data
            current_user.store()
            flash(u'Minecraft spillernavnet ble oppdatert')
            return redirect(url_for('user'))
        form.password.errors.append(u'Feil passord')

    else:
        # Show current playername in form
        form.playername.process_data(current_user.mojang_playername)
        form.uuid.process_data(current_user.mojang_uuid)

    return render_template(
        'user/change_playername.html',
        title=u'Endre Minecraft spillernavn',
        form=form,
        action=url_for('change_playername')
    )


@app.route('/bruker/hent_mojang_uuid_proxy/<playername>')
@login_required
def get_mojang_uuid_proxy(playername):
    """ Proxy to asynchronously fetch mojang uuid related to a supplied Minecraft playername """
    response = urllib2.urlopen('https://api.mojang.com/users/profiles/minecraft/' + playername)
    return app.response_class(response.read(), mimetype='application/json')


@app.route('/edit_meeting/<int:meeting_id>', methods=['GET', 'POST'])
@login_required
def edit_meeting(meeting_id):
    """ Renders the edit meeting page and stores the edited meeting """
    # Get the meeting details based on the supplied ID
    meeting = Meeting.get_meeting_by_id(meeting_id)
    # Check if the current user can edit this meeting
    if meeting.user_id != current_user.id:
        flash(u'Du har ikke tilgang til å endre dette møtet!')
        return redirect(url_for('home'))

    if request.method == 'POST':
        form = forms.MeetingForm(request.form)
        # If valid, store the edited meeting details
        if form.validate():
            form.populate_obj(meeting)
            meeting.store()
            flash(u'Møtet ble endret!')
            return redirect(url_for('home'))
        else:
            flash(u'Feil i skjema!')

    else:  # GET
        # Feed meeting details to meeting form
        form = forms.MeetingForm(obj=meeting)

    return render_template(
        'edit_meeting.html',
        set_tab=1,
        form=form,
        action=url_for('edit_meeting', meeting_id=meeting_id)
    )


@app.route('/delete_meeting/', defaults={'meeting_id': None})
@app.route('/delete_meeting/<int:meeting_id>')
@login_required
def delete_meeting(meeting_id):
    """ Endpoint to asynchronously delete meeting """
    if not meeting_id:
        return jsonify(
            success=False,
            message=u'Ingen møte ID mottatt'
        )

    meeting = Meeting.get_meeting_by_id(meeting_id)
    # Check if user is owner
    if meeting.user_id == current_user.id:
        # Delete meeting from db before deleting world
        meeting.delete()

        # Object still exists in memory after deleting from db
        if meeting.world_id:
            # Also delete world if it's not favoured
            world = World.get_by_id(meeting.world_id)
            if meeting.user_id == world.user_id and not world.favourite:
                if world.delete():  # Will return false if in use by meeting
                    return jsonify(
                        success=True,
                        message=u'Møtet ble slettet',
                        world_id=world.id
                    )
        return jsonify(
            success=True,
            message=u'Møtet ble slettet'
        )
    return jsonify(
        success=False,
        message=u'Du har ikke tilgang til å slette dette møtet'
    )


@app.route('/delete_world/', defaults={'world_id': None})
@app.route('/delete_world/<int:world_id>')
@login_required
def delete_world(world_id):
    """ Endpoint to asynchronously delete Minecraft world """
    if not world_id:
        return jsonify(
            success=False,
            message=u'Ingen verden ID mottatt'
        )

    world = World.get_by_id(world_id)
    # Check if user is owner
    if world.user_id == current_user.id:
        if world.delete():  # Will return false if in use by meeting
            return jsonify(
                success=True,
                message=u'Minecraft verdenen ble slettet'
            )
        return jsonify(
            success=False,
            message=u'Denne Minecraft verdenen er registrert brukt i et møte'
        )
    return jsonify(
        success=False,
        message=u'Du har ikke tilgang til å slette denne Minecraft verdenen'
    )


@app.route('/fra_kart')
@login_required
def from_map():
    """ Renders the map area selection page to generate Minecraft world from real maps """
    form = forms.WorldForm()
    return render_template(
        'map/minecraft_kartverket.html',
        title=u'Kart',
        form=form,
        action=url_for('home')
    )


@app.route('/last_opp_verden/', methods=['GET', 'POST'])
@login_required
def world_upload():
    """ Endpoint to asynchronously get partial html form and upload Minecraft world zip file """
    # Do not give request.form as an argument since it will break file upload
    form = forms.WorldUpload()
    if form.validate_on_submit():
        world = files.save_world(
            file_data=form.world_file.data,
            description=form.description.data
        )
        # Return world ID with json so it can be used in meeting form
        return jsonify(
            success=True,
            world_id=world.id
        )

    return render_template(
        'world_upload.html',
        form=form
    )


@app.route('/mc_world_url', methods=['POST'])
@login_required
def mc_world_url():
    """ Endpoint to asynchronously pass Minecraft world url to server """
    url = str(request.form['url'])
    description = request.form['description']
    return files.save_world_from_fme(url=url, description=description)


@app.route('/get_world/<file_name>')
@login_required
def get_world(file_name):
    """ Asynchronously download Minecraft world """
    directory = safe_join(app.root_path, app.config['WORLD_UPLOAD_PATH'])
    return send_from_directory(directory, file_name, as_attachment=True, attachment_filename=file_name)


@app.route('/verden_info/', defaults={'world_id': None})
@app.route('/verden_info/<int:world_id>')
def world_info(world_id):
    """ Endpoint to asynchronously get Minecraft world info as partial html """
    if not world_id:
        return jsonify(
            success=False,
            message=u'Ingen verden ID mottatt'
        )
    world = World.get_by_id(world_id)
    return render_template(
        'world_info.html',
        world=world
    )


@app.route('/dine_verdener')
@login_required
def browse_worlds():
    """ Endpoint to asynchronously get Minecraft world list for the current user as partial html """
    world_list = World.get_user_worlds(current_user.id)
    return render_template(
        'browse_worlds.html',
        world_list=world_list
    )


@app.route('/veksle_favoritt/', defaults={'world_id': None})
@app.route('/veksle_favoritt/<int:world_id>')
@login_required
def toggle_favourite(world_id):
    """ Endpoint to asynchronously toggle a Minecraft world as favourite """
    if not world_id:
        return jsonify(
            success=False,
            message=u'Ingen verden ID mottatt'
        )

    world = World.get_by_id(world_id)
    # Check if current user is owner
    if current_user.id == world.user_id:
        # Invert current setting and store
        world.favourite = not world.favourite
        world.store()

        return jsonify(
            success=True,
            message=u'Lagret som favoritt' if world.favourite else u'Favoritt fjernet',
            favourite=world.favourite
        )
    return jsonify(
        success=False,
        message=u'Du har ikke tilgang til å lagre denne verdenen som favoritt'
    )


@app.route('/generate_preview/', defaults={'world_id': None})
@app.route('/generate_preview/<int:world_id>')
@login_required
def generate_preview(world_id):
    """ Not used? """
    if not world_id:
        return jsonify(
            success=False,
            message=u'Ingen verden ID mottatt'
        )
    w = World.get_by_id(world_id)
    world_ref = w.file_ref
    success = files.generate_world_preview(world_ref)
    if success:
        w.preview = True
        w.store()
        return 'Genererer forhåndsvisning. Dette kan ta noen minutter.'
    else:
        return 'Failure'


@app.route('/show_preview/', defaults={'world_id': None})
@app.route('/show_preview/<int:world_id>')
@login_required
def show_preview(world_id):
    """ Render Minecraft world preview page or generate preview if it doesn't exist """
    if not world_id:
        return jsonify(
            success=False,
            message=u'Ingen verden ID mottatt'
        )

    # TODO Check if preview files is present
    world = World.get_by_id(world_id)
    preview = tasks.generate_preview_task.AsyncResult(world.file_ref)
    if preview.status == 'PENDING':
        print(str(world_id) + " PENDING")
        # Probably not started. Start it.
        success = files.generate_world_preview(world.file_ref)
        if success:
            return jsonify(
                status='PENDING',
                message=u'Ingen forhåndsvisning lagret. Ber om forhåndsvisning...'
            )
        else:
            return jsonify(
                status='FAILED',
                message=u'Noe gikk galt!'
            )
    elif preview.status == 'SENT':
        print(str(world_id) + " SENT")
        # Received by the worker, and in queue. Tell user to wait.
        return jsonify(
            status='SENT',
            message=u'Forespørsel om forhåndsvisning er sendt. Hvis det er stor pågang kan dette ta en stund.'
        )
    elif preview.status == 'STARTED':
        print(str(world_id) + " STARTED")
        # Generating preview
        return jsonify(
            status='STARTED',
            message=u'Vi lager en forhåndsvisning. Dette kan ta noen minutter.'
        )
    elif preview.status == 'SUCCESS':
        print(str(world_id) + " SUCCESS")
        # Finished. Show the preview.
        print('forhåndsvisningen er ferdig')
        return render_template(
            'preview.html',
            world_ref=world.file_ref,
        ), 200


@app.route('/tjenerliste/', defaults={'meeting_id': None})
@app.route('/tjenerliste/<int:meeting_id>')
@login_required
def server_list(meeting_id):
    """ Render server list page for specified meeting """
    # TODO handle get servers
    # TODO check if user has access
    meeting = Meeting.get_meeting_by_id(meeting_id)
    return render_template(
            'server_list.html',
            title=u'Liste over tjenere',
            meeting=meeting,
            locale=locale.getpreferredencoding(),
            servers=[{'address': 'test.com', 'status': 'OK'}]
        )


@app.route('/restart_server/', defaults={'server_address': None})
@app.route('/restart_server/<string:server_address>')
@login_required
def restart_server(server_address):
    """placholder function for restarting servers"""
    print("restart server: %s " % server_address)
    return jsonify(
        success=True
    )


@app.route('/destroy_server/', defaults={'server_address': None})
@app.route('/destroy_server/<string:server_address>')
@login_required
def destroy_server(server_address):
    """placeholder function for destroying servers"""
    print("destroy server: %s " % server_address)
    return jsonify(
        success=True
    )


@app.route('/test_cloud', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def test_cloud():
    """ Test code """
    if request.method == 'POST':
        # TODO test code here
        server_list = [{'name': 'Test server', 'location': 1234},
                       {'name': 'Dead server', 'location': 5678}]
        return render_template(
            'test_cloud.html',
            title=u'Test cloud',
            server_list=server_list
        )

    return render_template(
        'test_cloud.html',
        title=u'Test cloud',
        server_list=[]
    )


@app.route('/export_calendar', methods=['GET'])
@login_required
def export_calendar():
    """ Export iCalendar file for current users meetings """
    return files.export_calendar_for_user(current_user.id)


@app.errorhandler(403)
def forbidden_403(error):
    """ 403 Forbidden """
    return render_template(
        '403.html',
        title='403'
    ), 403


@app.errorhandler(404)
def not_found_404(error):
    """ 404 Not Found """
    return render_template(
        '404.html',
        title='404'
    ), 404
