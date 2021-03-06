"""Test requirements module."""
import os
from unittest.mock import patch, call

from homeassistant import setup
from homeassistant.requirements import (
    CONSTRAINT_FILE, async_process_requirements)

from tests.common import (
    get_test_home_assistant, MockModule, mock_coro, mock_integration)


class TestRequirements:
    """Test the requirements module."""

    hass = None
    backup_cache = None

    # pylint: disable=invalid-name, no-self-use
    def setup_method(self, method):
        """Set up the test."""
        self.hass = get_test_home_assistant()

    def teardown_method(self, method):
        """Clean up."""
        self.hass.stop()

    @patch('os.path.dirname')
    @patch('homeassistant.util.package.is_virtual_env', return_value=True)
    @patch('homeassistant.util.package.install_package', return_value=True)
    def test_requirement_installed_in_venv(
            self, mock_install, mock_venv, mock_dirname):
        """Test requirement installed in virtual environment."""
        mock_venv.return_value = True
        mock_dirname.return_value = 'ha_package_path'
        self.hass.config.skip_pip = False
        mock_integration(
            self.hass,
            MockModule('comp', requirements=['package==0.0.1']))
        assert setup.setup_component(self.hass, 'comp', {})
        assert 'comp' in self.hass.config.components
        assert mock_install.call_args == call(
            'package==0.0.1',
            constraints=os.path.join('ha_package_path', CONSTRAINT_FILE))

    @patch('os.path.dirname')
    @patch('homeassistant.util.package.is_virtual_env', return_value=False)
    @patch('homeassistant.util.package.install_package', return_value=True)
    def test_requirement_installed_in_deps(
            self, mock_install, mock_venv, mock_dirname):
        """Test requirement installed in deps directory."""
        mock_dirname.return_value = 'ha_package_path'
        self.hass.config.skip_pip = False
        mock_integration(
            self.hass,
            MockModule('comp', requirements=['package==0.0.1']))
        assert setup.setup_component(self.hass, 'comp', {})
        assert 'comp' in self.hass.config.components
        assert mock_install.call_args == call(
            'package==0.0.1', target=self.hass.config.path('deps'),
            constraints=os.path.join('ha_package_path', CONSTRAINT_FILE))


async def test_install_existing_package(hass):
    """Test an install attempt on an existing package."""
    with patch('homeassistant.util.package.install_package',
               return_value=mock_coro(True)) as mock_inst:
        assert await async_process_requirements(
            hass, 'test_component', ['hello==1.0.0'])

    assert len(mock_inst.mock_calls) == 1

    with patch('homeassistant.util.package.is_installed', return_value=True), \
            patch(
                'homeassistant.util.package.install_package') as mock_inst:
        assert await async_process_requirements(
            hass, 'test_component', ['hello==1.0.0'])

    assert len(mock_inst.mock_calls) == 0
