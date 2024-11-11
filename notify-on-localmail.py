import os
import getpass
import logging
import mailbox
import shutil
import socket
import xdg
import dbus


def parse_messages(mbox):
    subject = ''
    count = 0

    for key in mbox.keys():
        msg = mbox.get_message(key)

        flags = msg.get_flags()
        # R: read
        # D: deleted
        if 'R' in flags or 'D' in flags:
            continue

        count += 1
        subject = msg['subject']
        msg.add_flag('R')
        mbox.update({key: msg})
    return subject, count


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # check whether another instance of this script is already running
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('localhost', 15151))
    except OSError:
        logging.debug("Another instance is already running")
        return

    mail_file_copy_path = xdg.BaseDirectory.save_data_path('notify-on-localmail') + '/mail'
    mail_file_copy_lock_path = mail_file_copy_path + '.lock'
    mail_file_path = '/var/mail/' + getpass.getuser()

    if os.path.getmtime(mail_file_copy_path) >= os.path.getmtime(mail_file_path):
        logging.debug('No new mail')
        return

    shutil.copy(mail_file_path, mail_file_copy_path)

    # remove any stale mail lock files since we already make sure there
    # are no other instances of the programming running
    if os.path.isfile(mail_file_copy_lock_path):
        logging.debug('Removing stale lock')
        os.remove(mail_file_copy_lock_path)

    mbox = mailbox.mbox(mail_file_copy_path)

    mbox.lock()
    try:
        subject, count = parse_messages(mbox)
        mbox.flush()
    except Exception as e:
        logging.error('Failed to parse message: %s', e)
        raise e
    finally:
        mbox.unlock()

    if count == 0:
        logging.debug('No new mail')
        return

    if count > 1:
        subject = str.format('{} new mails', count)

    bus_name = "org.freedesktop.Notifications"

    dbus_obj = dbus.SessionBus().get_object(bus_name, "/org/freedesktop/Notifications")
    dbus_obj = dbus.Interface(dbus_obj, bus_name)
    # https://specifications.freedesktop.org/notification-spec/latest/protocol.html#command-notify
    app_name = 'notify on local mail'
    replaces_id = 0
    app_icon = 'mail-unread'
    summary = 'New local mail'
    body = subject
    actions = []
    hints = {}
    expire_timeout = 0
    dbus_obj.Notify(app_name, replaces_id, app_icon, summary, body, actions, hints, expire_timeout)


if __name__ == "__main__":
    main()
