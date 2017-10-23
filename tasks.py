import re

from invoke import task


@task
def release(ctx):
    """Tag, build, then upload to PyPI"""
    INIT_FILE = 'pg_grant/__init__.py'
    init_data = open(INIT_FILE).read()
    metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", init_data))

    ctx.run("git tag v{0} -m '{0} release'".format(metadata['version']))

    ctx.run('rm dist/*', warn=True)
    ctx.run('python setup.py sdist bdist_wheel')
    ctx.run('twine upload dist/*')
