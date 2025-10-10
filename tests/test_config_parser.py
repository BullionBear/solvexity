"""
Test cases for the YAML configuration parser with environment variable substitution.
"""
import os
import tempfile
import pytest
from pathlib import Path
from solvexity.strategy.config.config_parser import yml_to_dict


class TestConfigParser:
    """Test suite for config parser with environment variable substitution."""
    
    def test_simple_substitution(self, tmp_path):
        """Test simple ${VAR} substitution."""
        # Set up environment
        os.environ['TEST_VAR'] = 'test_value'
        
        # Create test YAML
        yaml_content = """
        key: ${TEST_VAR}
        """
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text(yaml_content)
        
        # Parse and verify
        result = yml_to_dict(str(yaml_file))
        assert result['key'] == 'test_value'
        
        # Cleanup
        del os.environ['TEST_VAR']
    
    def test_default_value_substitution(self, tmp_path):
        """Test ${VAR:-default} substitution."""
        # Create test YAML with default values
        yaml_content = """
        with_default: ${UNSET_VAR:-default_value}
        empty_var: ${EMPTY_VAR:-default_for_empty}
        """
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text(yaml_content)
        
        # Set EMPTY_VAR to empty string
        os.environ['EMPTY_VAR'] = ''
        
        # Parse and verify
        result = yml_to_dict(str(yaml_file))
        assert result['with_default'] == 'default_value'
        assert result['empty_var'] == 'default_for_empty'
        
        # Cleanup
        del os.environ['EMPTY_VAR']
    
    def test_required_variable(self, tmp_path):
        """Test ${VAR:?error} substitution raises error if not set."""
        yaml_content = """
        required: ${REQUIRED_VAR:?This variable is required}
        """
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text(yaml_content)
        
        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            yml_to_dict(str(yaml_file))
        
        assert "REQUIRED_VAR" in str(exc_info.value)
        assert "This variable is required" in str(exc_info.value)
    
    def test_simple_var_format(self, tmp_path):
        """Test $VAR (simple format) substitution."""
        os.environ['SIMPLE_VAR'] = 'simple_value'
        
        yaml_content = """
        key: $SIMPLE_VAR
        """
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text(yaml_content)
        
        result = yml_to_dict(str(yaml_file))
        assert result['key'] == 'simple_value'
        
        del os.environ['SIMPLE_VAR']
    
    def test_nested_structure(self, tmp_path):
        """Test substitution in nested dictionaries and lists."""
        os.environ['HOST'] = 'localhost'
        os.environ['PORT'] = '5432'
        
        yaml_content = """
        database:
          host: ${HOST}
          port: ${PORT}
          servers:
            - server1.${HOST}
            - server2.${HOST}
        """
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text(yaml_content)
        
        result = yml_to_dict(str(yaml_file))
        assert result['database']['host'] == 'localhost'
        assert result['database']['port'] == '5432'
        assert result['database']['servers'][0] == 'server1.localhost'
        assert result['database']['servers'][1] == 'server2.localhost'
        
        del os.environ['HOST']
        del os.environ['PORT']
    
    def test_multiple_vars_in_one_string(self, tmp_path):
        """Test multiple variable substitutions in a single string."""
        os.environ['PROTOCOL'] = 'https'
        os.environ['DOMAIN'] = 'example.com'
        os.environ['PATH'] = '/api/v1'
        
        yaml_content = """
        url: ${PROTOCOL}://${DOMAIN}${PATH}
        """
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text(yaml_content)
        
        result = yml_to_dict(str(yaml_file))
        assert result['url'] == 'https://example.com/api/v1'
        
        del os.environ['PROTOCOL']
        del os.environ['DOMAIN']
        del os.environ['PATH']
    
    def test_no_substitution(self, tmp_path):
        """Test that substitution can be disabled."""
        os.environ['TEST_VAR'] = 'test_value'
        
        yaml_content = """
        key: ${TEST_VAR}
        """
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text(yaml_content)
        
        # Parse with substitution disabled
        result = yml_to_dict(str(yaml_file), substitute_env=False)
        assert result['key'] == '${TEST_VAR}'
        
        del os.environ['TEST_VAR']
    
    def test_docker_compose_style(self, tmp_path):
        """Test docker-compose.yml style configuration."""
        os.environ['NATS_USER'] = 'admin'
        os.environ['NATS_PASS'] = 'secret123'
        
        yaml_content = """
        services:
          nats:
            image: nats:latest
            command: "--user ${NATS_USER} --pass ${NATS_PASS} -js"
            ports:
              - "${NATS_PORT:-4222}:4222"
            environment:
              - NATS_USER=${NATS_USER}
              - NATS_PASS=${NATS_PASS}
        """
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text(yaml_content)
        
        result = yml_to_dict(str(yaml_file))
        assert 'admin' in result['services']['nats']['command']
        assert 'secret123' in result['services']['nats']['command']
        assert result['services']['nats']['ports'][0] == '4222:4222'
        assert result['services']['nats']['environment'][0] == 'NATS_USER=admin'
        
        del os.environ['NATS_USER']
        del os.environ['NATS_PASS']
    
    def test_numeric_values(self, tmp_path):
        """Test that numeric values are preserved correctly."""
        os.environ['TIMEOUT'] = '30'
        
        yaml_content = """
        timeout: ${TIMEOUT}
        fixed_number: 100
        """
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text(yaml_content)
        
        result = yml_to_dict(str(yaml_file))
        assert result['timeout'] == '30'  # String from env var
        assert result['fixed_number'] == 100  # Original numeric type preserved
        
        del os.environ['TIMEOUT']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

