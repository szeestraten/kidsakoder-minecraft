# -*- coding: utf-8 -*-
"""
flask_app.files
~~~~~~~~~~~~~~~

File storage controller
"""

import StringIO
import urllib2
from urlparse import urlparse
import os
import tempfile
import shutil
from zipfile import ZipFile
from flask_security import current_user
from flask import send_file, jsonify, safe_join, escape, Markup
from icalendar import Calendar, Event
from pytz import timezone
from models import Meeting, World
from flask_app import app
from werkzeug.datastructures import FileStorage


def safe_join_all(root_path, *args):
    """
    Splits UNIX-style paths, and joins all paths to a single safe path

    :param root_path: Absolute root path
    :param args: Several UNIX-style relative paths
    :return: Joined path
    """
    abs_path = root_path
    for arg in args:
        # Split into single folders
        path = arg.split('/')
        for folder in path:
            # Join all paths, one by one
            abs_path = safe_join(abs_path, folder)

    return abs_path


def search_for_file(path, filename):
    """
    Searches top down for a filename and returns the path to the folder of the file if found, False if not found

    :param path: Path to start looking from
    :param filename: File to look for
    :return: Absolute folder path or False if not found
    """
    for root, dirs, files in os.walk(path):
        for file in files:
            if file == filename:
                return root

    return False


def save_world_from_fme(url=None, description=""):
    """
    Save generated Minecraft world from FME cloud

    :param url: URL to FME Cloud
    :param description: Minecraft world description
    :return: JSON response
    """
    if url is None:
        return jsonify(
            success=False,
            message=u'Ingen URL mottatt'
        )
    # Check that the url is valid
    # Link example:
    # https://mc-sweco.fmecloud.com:443/fmedatadownload/results/FME_2E257068_1457457321707_15896.zip
    parse_result = urlparse(url)
    if not (parse_result.scheme == 'https' and
            parse_result.netloc == 'mc-sweco.fmecloud.com:443' and
            parse_result.path.startswith('/fmedatadownload/results/')):
        app.logger.warning('Invalid Minecraft world URL: ' + parse_result.geturl())
        return jsonify(
            success=False,
            message=Markup(u'Ugyldig <a href="') + escape(parse_result.geturl()) + Markup(u'">URL</a>')
        )

    # Open URL and save world file
    response = urllib2.urlopen(parse_result.geturl())
    world = save_world(response, description)
    return jsonify(
        success=True,
        message=u'Verden overført',
        world_id=str(world.id)
    )


def save_world(file_data=None, description=""):
    """
    Save file from form data or download

    :param file_data: The Minecraft world file data to be saved.
                      Either as a urllib2 response or a werkzeug FileStorage object
    :param description: Minecraft world description
    :return: World object
    """
    world = World(user_id=current_user.id)
    # Construct file name with world ID and user ID for reference. End with arbitrary string and zip extension
    # Example: 7_3_mc_world.zip
    file_ref_noext = str(world.id) + '_' + str(current_user.id) + '_' + 'mc_world'
    file_ref = file_ref_noext + '.zip'
    # Full path to save zip. Include filename, but not file extension
    if app.config['ABSOLUTE_WORLD_UPLOAD_PATH']:
        save_path = safe_join_all(app.config['ABSOLUTE_WORLD_UPLOAD_PATH'], file_ref_noext)
    else:
        save_path = safe_join_all(app.root_path, app.config['WORLD_UPLOAD_PATH'], file_ref_noext)
    temp_dir = tempfile.gettempdir()
    # Temporary zip file
    zip_path = safe_join_all(temp_dir, file_ref)
    # Temporary unzip directory
    unzip_path = safe_join_all(temp_dir, file_ref_noext)

    # Check if file_data comes from a form submission
    if isinstance(file_data, FileStorage):
        file_data.save(zip_path)
    else:  # Else assume file_data has read() function
        with open(zip_path, 'wb') as world_zip:
            world_zip.write(file_data.read())

    # Rezip
    #######
    with ZipFile(zip_path, 'r') as world_zip:
        # unzip file
        world_zip.extractall(unzip_path)
    # Locate minecraft world inside unzipped directory
    level_path = search_for_file(unzip_path, 'level.dat')
    # Make zip file
    shutil.make_archive(save_path, 'zip', level_path)

    # Clean up temp files
    try:
        # Remove zip file
        os.remove(zip_path)
    except OSError:
        pass
    try:
        # Remove unzip directory
        shutil.rmtree(unzip_path)
    except OSError:
        pass

    # Save world details to database
    world.file_ref = file_ref
    world.description = description
    world.store()
    return world


def generate_world_preview(world_ref):
    """
    Generate a preview from a Minecraft world zip file

    :param world_ref: File name of the zip file
    :return: Celery AsyncResult
    """
    from tasks import generate_preview_task
    # World ref without file extension
    if world_ref.endswith('.zip'):
        world_ref_noext = world_ref[0:-4]
    # Create file path
    if app.config['ABSOLUTE_WORLD_UPLOAD_PATH']:
        zip_path = safe_join_all(app.config['ABSOLUTE_WORLD_UPLOAD_PATH'], world_ref)
    else:
        zip_path = safe_join_all(app.root_path, app.config['WORLD_UPLOAD_PATH'], world_ref)
    # Open file:
    temp_dir = tempfile.gettempdir()
    unzip_path = safe_join_all(temp_dir, world_ref_noext)
    with ZipFile(zip_path, 'r') as world_zip:
        # unzip file
        world_zip.extractall(unzip_path)

    # Locate minecraft world inside unzipped directory.
    world_path = search_for_file(unzip_path, 'level.dat')
    # Path to put preview
    preview_path = safe_join_all(app.root_path, app.config['PREVIEW_STORAGE_PATH'], world_ref)
    # Texture path
    texturepack_path = safe_join_all(app.root_path, app.config['TEXTUREPACK_PATH'])
    # Create overviewer config file
    config_path = safe_join_all(temp_dir, 'overviewer_config_%s' % world_ref)
    with open(config_path, 'w+') as cfile:
        cfile.writelines(
            ['worlds["world"] = "%s" \n \n' % world_path,
             'renders["normalrender"] = { \n',
             '  "world": "world", \n',
             '  "title": "Kart over din Minecraft-verden", \n',
             '} \n \n', 'outputdir = "%s" \n' % preview_path,
             'texturepath = "%s" \n' % texturepack_path,
             'defaultzoom = 12 \n'
             ])
    # Call overviewer to generate
    # Note: singleton arg tuple needs a trailing comma
    result = generate_preview_task.apply_async((config_path, unzip_path), task_id=world_ref)
    return result


def export_calendar_for_user(cal_user_id=None, filename="export"):
    """
    Create and export iCalendar file with the meetings of the chosen user

    :param cal_user_id: User ID to create calendar for
    :param filename: Filename for the ics file
    :return: ics file wrapped in a response
    """
    if cal_user_id is None:
        # Defaults to current user
        cal_user_id = current_user.id

    meeting_list = Meeting.get_user_meetings(cal_user_id)
    tz = timezone(app.config['TIMEZONE'])
    cal = Calendar()
    for meeting in meeting_list:
        event = Event()
        event.add('summary', meeting.title)
        event.add('dtstart', tz.localize(meeting.start_time))
        event.add('dtend', tz.localize(meeting.end_time))
        event.add('description',
                  u'Møte generert av %s. Antall deltakere: %s. ' % (app.config['APP_NAME'],
                                                                    meeting.participant_count))
        cal.add_component(event)

    export = StringIO.StringIO()
    export.writelines(cal.to_ical())
    export.seek(0)
    return send_file(export,
                     attachment_filename=filename + '.ics',
                     as_attachment=True)


def delete_world_file(file_ref):
    """
    Delete a Minecraft world zip file

    :param file_ref: The file to delete
    :return: True if the file was removed, False if not
    """
    file_path = safe_join_all(app.root_path, app.config['WORLD_UPLOAD_PATH'], file_ref)
    try:
        os.remove(file_path)
        return True
    except OSError:
        app.logger.warning('Could not remove: ' + file_path)
        return False


def delete_world_preview(file_ref):
    """
    Delete a generated world preview.
    Runs as a celery task to improve web app response time

    :param file_ref: Filename of the preview to delete
    :return: Celery AsyncResult
    """
    from tasks import delete_preview_task
    dir_path = safe_join_all(app.root_path, app.config['PREVIEW_STORAGE_PATH'], file_ref)
    result = delete_preview_task.delay(dir_path)
    return result
