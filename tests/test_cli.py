"""
Basic tests for gemctl CLI.
"""

import pytest
from click.testing import CliRunner
from gemctl.cli import cli


class TestCLI:
    """Test basic CLI functionality."""
    
    def test_help_command(self):
        """Test that help command works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "Agentspace CLI" in result.output
    
    def test_engines_help(self):
        """Test engines help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['engines', '--help'])
        assert result.exit_code == 0
        assert "Manage Agentspace engines" in result.output
    
    def test_data_stores_help(self):
        """Test data-stores help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['data-stores', '--help'])
        assert result.exit_code == 0
        assert "Manage Agentspace data stores" in result.output
