"""Tests for CLI basic functionality"""

import pytest
from click.testing import CliRunner
import tempfile
from pathlib import Path

from docscope.cli import cli
from docscope import __version__


def test_cli_version():
    """Test CLI version command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    
    assert result.exit_code == 0
    assert __version__ in result.output


def test_cli_help():
    """Test CLI help command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    
    assert result.exit_code == 0
    assert 'DocScope - Universal Documentation Browser' in result.output
    assert 'Commands:' in result.output


def test_init_command():
    """Test init command"""
    runner = CliRunner()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(cli, ['init', '--name', 'TestProject', '--path', tmpdir])
        
        assert result.exit_code == 0
        assert "Initialized DocScope project 'TestProject'" in result.output
        
        # Check files were created
        config_path = Path(tmpdir) / ".docscope.yaml"
        docs_path = Path(tmpdir) / "docs"
        readme_path = Path(tmpdir) / "README.md"
        
        assert config_path.exists()
        assert docs_path.exists()
        assert readme_path.exists()


def test_init_command_interactive():
    """Test init command with interactive prompt"""
    runner = CliRunner()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(cli, ['init', '--path', tmpdir], input='MyProject\n')
        
        assert result.exit_code == 0
        assert "Initialized DocScope project 'MyProject'" in result.output


def test_search_command_table_format():
    """Test search command with table format"""
    runner = CliRunner()
    result = runner.invoke(cli, ['search', 'test'])
    
    assert result.exit_code == 0
    assert 'Searching for:' in result.output
    assert 'test' in result.output


def test_search_command_json_format():
    """Test search command with JSON format"""
    runner = CliRunner()
    result = runner.invoke(cli, ['search', 'test', '--format', 'json'])
    
    assert result.exit_code == 0
    # Should contain JSON array
    assert '[' in result.output
    assert ']' in result.output


def test_scan_command():
    """Test scan command"""
    runner = CliRunner()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
        test_file = Path(tmpdir) / "test.md"
        test_file.write_text("# Test Document")
        
        result = runner.invoke(cli, ['scan', tmpdir])
        
        assert result.exit_code == 0
        assert 'Scanning documents' in result.output
        assert 'Scan complete' in result.output


def test_db_status_command():
    """Test database status command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['db', 'status'])
    
    assert result.exit_code == 0
    assert 'Database Status' in result.output
    assert 'Backend:' in result.output


def test_plugins_list_command():
    """Test plugins list command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['plugins', 'list'])
    
    assert result.exit_code == 0
    assert 'Installed Plugins' in result.output


def test_export_command():
    """Test export command"""
    runner = CliRunner()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "export.html"
        result = runner.invoke(cli, ['export', '--output', str(output_file)])
        
        assert result.exit_code == 0
        assert 'Exporting documentation' in result.output
        assert 'Export complete' in result.output


def test_verbose_flag():
    """Test verbose flag"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--verbose', 'search', 'test'])
    
    assert result.exit_code == 0


def test_quiet_flag():
    """Test quiet flag"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--quiet', 'search', 'test'])
    
    assert result.exit_code == 0
    # With quiet flag, output should be minimal
    assert len(result.output) > 0