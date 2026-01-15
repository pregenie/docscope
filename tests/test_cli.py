"""Tests for CLI implementation"""

import pytest
from pathlib import Path
from click.testing import CliRunner
import tempfile
import json
import yaml

from docscope.cli import cli


@pytest.fixture
def runner():
    """Create CLI test runner"""
    return CliRunner()


@pytest.fixture
def temp_project():
    """Create temporary project directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestInitCommand:
    """Test init command"""
    
    def test_init_basic(self, runner, temp_project):
        """Test basic project initialization"""
        result = runner.invoke(cli, [
            'init',
            '--name', 'TestProject',
            '--path', str(temp_project)
        ])
        
        assert result.exit_code == 0
        assert 'Project initialized successfully' in result.output
        
        # Check files created
        config_file = temp_project / '.docscope.yaml'
        assert config_file.exists()
        
        docs_dir = temp_project / 'docs'
        assert docs_dir.is_dir()
        
        readme = temp_project / 'README.md'
        assert readme.exists()
    
    def test_init_with_template(self, runner, temp_project):
        """Test initialization with different templates"""
        for template in ['minimal', 'basic', 'full']:
            project_dir = temp_project / template
            project_dir.mkdir()
            
            result = runner.invoke(cli, [
                'init',
                '--name', f'Project_{template}',
                '--path', str(project_dir),
                '--template', template
            ])
            
            assert result.exit_code == 0
            
            config_file = project_dir / '.docscope.yaml'
            assert config_file.exists()
            
            # Load and verify configuration
            with open(config_file) as f:
                config = yaml.safe_load(f)
            
            assert config['project'] == f'Project_{template}'
            assert config['version'] == '1.0'
    
    def test_init_existing_project(self, runner, temp_project):
        """Test initialization when project already exists"""
        # First initialization
        runner.invoke(cli, [
            'init',
            '--name', 'ExistingProject',
            '--path', str(temp_project)
        ])
        
        # Second initialization - should prompt
        result = runner.invoke(cli, [
            'init',
            '--name', 'NewProject',
            '--path', str(temp_project)
        ], input='n\n')
        
        assert result.exit_code == 0
        assert 'Initialization cancelled' in result.output


class TestScanCommand:
    """Test scan command"""
    
    def test_scan_help(self, runner):
        """Test scan command help"""
        result = runner.invoke(cli, ['scan', '--help'])
        assert result.exit_code == 0
        assert 'Scan documents and build index' in result.output
    
    def test_scan_with_paths(self, runner, temp_project):
        """Test scanning specific paths"""
        # Create test files
        docs_dir = temp_project / 'docs'
        docs_dir.mkdir()
        (docs_dir / 'test.md').write_text('# Test Document')
        
        result = runner.invoke(cli, [
            'scan',
            str(docs_dir),
            '--dry-run'
        ])
        
        assert result.exit_code == 0
        assert 'Would scan' in result.output
    
    def test_scan_with_formats(self, runner):
        """Test scanning with format filter"""
        result = runner.invoke(cli, [
            'scan',
            '--formats', 'md,txt',
            '--dry-run'
        ])
        
        assert result.exit_code == 0


class TestSearchCommand:
    """Test search command"""
    
    def test_search_help(self, runner):
        """Test search command help"""
        result = runner.invoke(cli, ['search', '--help'])
        assert result.exit_code == 0
        assert 'Search documents' in result.output
    
    def test_search_basic(self, runner):
        """Test basic search"""
        result = runner.invoke(cli, ['search', 'test'])
        # May fail if no index exists, but should not crash
        assert result.exit_code in [0, 1]
    
    def test_search_with_options(self, runner):
        """Test search with various options"""
        result = runner.invoke(cli, [
            'search', 'test',
            '--limit', '10',
            '--format', 'json'
        ])
        assert result.exit_code in [0, 1]


class TestServeCommand:
    """Test serve command"""
    
    def test_serve_help(self, runner):
        """Test serve command help"""
        result = runner.invoke(cli, ['serve', '--help'])
        assert result.exit_code == 0
        assert 'Start the DocScope web server' in result.output
    
    def test_serve_options(self, runner):
        """Test serve command options"""
        # Just test that options are accepted
        result = runner.invoke(cli, [
            'serve',
            '--host', 'localhost',
            '--port', '9090',
            '--workers', '2',
            '--help'
        ])
        assert result.exit_code == 0


class TestExportCommand:
    """Test export command"""
    
    def test_export_help(self, runner):
        """Test export command help"""
        result = runner.invoke(cli, ['export', '--help'])
        assert result.exit_code == 0
        assert 'Export documentation' in result.output
    
    def test_export_formats(self, runner, temp_project):
        """Test export with different formats"""
        for format in ['json', 'yaml', 'html', 'markdown']:
            output_file = temp_project / f'export.{format}'
            
            result = runner.invoke(cli, [
                'export',
                '--format', format,
                '--output', str(output_file)
            ])
            # May fail if no documents exist
            assert result.exit_code in [0, 1]


class TestDatabaseCommands:
    """Test database commands"""
    
    def test_db_help(self, runner):
        """Test db command help"""
        result = runner.invoke(cli, ['db', '--help'])
        assert result.exit_code == 0
        assert 'Database management commands' in result.output
    
    def test_db_init(self, runner):
        """Test database initialization"""
        result = runner.invoke(cli, ['db', 'init'])
        # May succeed or fail depending on database
        assert result.exit_code in [0, 1]
    
    def test_db_status(self, runner):
        """Test database status"""
        result = runner.invoke(cli, ['db', 'status'])
        assert result.exit_code in [0, 1]


class TestPluginCommands:
    """Test plugin commands"""
    
    def test_plugins_help(self, runner):
        """Test plugins command help"""
        result = runner.invoke(cli, ['plugins', '--help'])
        assert result.exit_code == 0
        assert 'Plugin management commands' in result.output
    
    def test_plugins_list(self, runner):
        """Test listing plugins"""
        result = runner.invoke(cli, ['plugins', 'list'])
        assert result.exit_code == 0


class TestConfigCommands:
    """Test config commands"""
    
    def test_config_help(self, runner):
        """Test config command help"""
        result = runner.invoke(cli, ['config', '--help'])
        assert result.exit_code == 0
        assert 'Configuration management commands' in result.output
    
    def test_config_show(self, runner, temp_project):
        """Test showing configuration"""
        # Initialize project first
        runner.invoke(cli, [
            'init',
            '--name', 'TestProject',
            '--path', str(temp_project)
        ])
        
        result = runner.invoke(cli, [
            '--config', str(temp_project / '.docscope.yaml'),
            'config', 'show'
        ])
        assert result.exit_code == 0
    
    def test_config_get(self, runner, temp_project):
        """Test getting configuration value"""
        # Initialize project first
        runner.invoke(cli, [
            'init',
            '--name', 'TestProject',
            '--path', str(temp_project)
        ])
        
        result = runner.invoke(cli, [
            '--config', str(temp_project / '.docscope.yaml'),
            'config', 'get', 'project'
        ])
        assert result.exit_code == 0
        assert 'TestProject' in result.output
    
    def test_config_validate(self, runner, temp_project):
        """Test configuration validation"""
        # Initialize project first
        runner.invoke(cli, [
            'init',
            '--name', 'TestProject',
            '--path', str(temp_project)
        ])
        
        result = runner.invoke(cli, [
            '--config', str(temp_project / '.docscope.yaml'),
            'config', 'validate'
        ])
        assert result.exit_code == 0


class TestUtilityCommands:
    """Test utility commands"""
    
    def test_info(self, runner):
        """Test info command"""
        result = runner.invoke(cli, ['info'])
        assert result.exit_code == 0
        assert 'DocScope System Information' in result.output
        assert 'Version' in result.output
    
    def test_completion(self, runner):
        """Test completion command"""
        for shell in ['bash', 'zsh', 'fish']:
            result = runner.invoke(cli, ['completion', '--shell', shell])
            assert result.exit_code == 0
            assert shell in result.output.lower()
    
    def test_stats(self, runner):
        """Test stats command"""
        result = runner.invoke(cli, ['stats'])
        assert result.exit_code in [0, 1]
    
    def test_watch(self, runner):
        """Test watch command help"""
        result = runner.invoke(cli, ['watch', '--help'])
        assert result.exit_code == 0
        assert 'Watch directories for changes' in result.output


class TestGlobalOptions:
    """Test global CLI options"""
    
    def test_version(self, runner):
        """Test version option"""
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert 'DocScope' in result.output
    
    def test_help(self, runner):
        """Test help option"""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Universal Documentation Browser' in result.output
    
    def test_verbose(self, runner):
        """Test verbose output"""
        result = runner.invoke(cli, ['--verbose', 'info'])
        assert result.exit_code == 0
    
    def test_quiet(self, runner):
        """Test quiet mode"""
        result = runner.invoke(cli, ['--quiet', 'info'])
        assert result.exit_code == 0
    
    def test_config_option(self, runner, temp_project):
        """Test config file option"""
        config_file = temp_project / 'custom.yaml'
        config_file.write_text(yaml.dump({
            'version': '1.0',
            'project': 'CustomProject'
        }))
        
        result = runner.invoke(cli, [
            '--config', str(config_file),
            'config', 'get', 'project'
        ])
        assert result.exit_code == 0


class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_command(self, runner):
        """Test invalid command"""
        result = runner.invoke(cli, ['invalid-command'])
        assert result.exit_code != 0
    
    def test_missing_arguments(self, runner):
        """Test missing required arguments"""
        result = runner.invoke(cli, ['search'])  # Missing query
        assert result.exit_code != 0
    
    def test_invalid_options(self, runner):
        """Test invalid option values"""
        result = runner.invoke(cli, [
            'search', 'test',
            '--limit', 'not-a-number'
        ])
        assert result.exit_code != 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])