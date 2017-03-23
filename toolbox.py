import sys
import wotdapp

def make_mod(username):
    with wotdapp.app.app_context():
        u = wotdapp.models.User.query.filter_by(username=username).first()
        if u is None:
            return '{0} is not a recognized user'.format(username)
        if u.isMod:
            return '{0} is already a moderator'.format(username)
        u.isMod = True
        wotdapp.db.session.add(u)
        wotdapp.db.session.commit()
        return '{0} is now a moderator'.format(username)

def remove_mod(username):
    with wotdapp.app.app_context():
        u = wotdapp.models.User.query.filter_by(username=username).first()
        if u is None:
            return '{0} is not a recognized user'.format(username)
        if not u.isMod:
            return '{0} is not a current moderator'.format(username)
        u.isMod = False
        wotdapp.db.session.add(u)
        wotdapp.db.session.commit()
        return '{0} is no longer a moderator'.format(username)

def replace_db():
    with wotdapp.app.app_context():
        wotdapp.db.drop_all()
        wotdapp.db.create_all()
        return 'Dropped all tables. Created all tables.'


if __name__ == '__main__':
    method = sys.argv[1]

    if method == 'mod':
        print(make_mod(sys.argv[2]))

    if method == 'rmmod':
        print(remove_mod(sys.argv[2]))

    if method == 'newdb':
        wipe = raw_input('This will delete all data. Are you sure? (Y/n): ')
        if wipe == 'Y':
            print(replace_db())