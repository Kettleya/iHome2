# -*- coding:utf-8 -*-
from iHome import create_app, db,models
from flask_migrate import Migrate, MigrateCommand, Manager

app = create_app('development')

manager = Manager(app)

Migrate(app, db)

manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
