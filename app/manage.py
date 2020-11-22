from flask_migrate import Migrate, MigrateCommand
from app import app
import fire


class Manager(object):

    def migrate(self):
        manager = Migrate(app)
        manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
  fire.Fire(Manager)