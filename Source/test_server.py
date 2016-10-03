from click.testing import CliRunner
from server import program

def test_config_command():
    runner = CliRunner()
    result = runner.invoke(program, ['config'])
    assert result.exit_code == 0
    for tag in ('Concurrency', 'Clients', 'Script', 'Database', 'Log level',
                'Return path', 'Envelope', 'SMTP host', 'SMTP port'):
        assert tag in result.output
