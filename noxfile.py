import os

import nox


@nox.session(python=['2.7', '3.7'])
def tests(session):
    session.install('pytest')
    session.run('pytest')
