import os
import logging

import snapcraft
import snapcraft.common
import snapcraft.plugins.maven


logger = logging.getLogger(__name__)


# Jenkins wants fonts.
fontconfig = """<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<!-- /etc/fonts/fonts.conf file to configure system font access -->
<fontconfig>
<!-- The xdg prefix will be replaced by XDG_DATA_HOME -->
<dir prefix="xdg">fonts</dir>
</fontconfig>
"""

class JenkinsPlugin(snapcraft.plugins.maven.MavenPlugin):

    def __init__(self, name, options, project):
        super().__init__(name, options, project)
        self.build_packages.append('maven')

    def env(self, root):
        # Jenkins wants fonts.
        env = ['XDG_DATA_HOME=%s/usr/share' % root,
               'FONTCONFIG_PATH=%s/etc/fonts' % root]
        return super().env(root) + env

    def build(self):
        # Calling the superclass build would spawn mvn, but we still want to
        # clean the build directory.
        snapcraft.BasePlugin.build(self)

        # Test.
        [print('{}: {}'.format(k,v)) for k,v in os.environ.items()]
        mvn_cmd = ['mvn', 'install', '-pl', 'war', '-am', '-DskipTests']
        if self._use_proxy():
            settings_path = os.path.join(self.partdir, 'm2', 'settings.xml')
            snapcraft.plugins.maven._create_settings(settings_path)
            mvn_cmd += ['-s', settings_path]

        self.run(mvn_cmd)

        src = os.path.join(self.builddir, 'war', 'target', 'jenkins.war')
        target = os.path.join(self.installdir, 'war', 'jenkins.war')
        self.run(['install', '-D', src, target])

        # Jenkins wants fonts.
        fontconfig_dir = os.path.join(self.installdir, 'etc', 'fonts')
        os.makedirs(fontconfig_dir, exist_ok=True)
        with open(os.path.join(fontconfig_dir, 'fonts.conf'), 'w') as fp:
            fp.write(fontconfig)
