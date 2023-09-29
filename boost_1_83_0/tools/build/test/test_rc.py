#!/usr/bin/env python3

# Copyright 2012 Jurko Gospodnetic
# Distributed under the Boost Software License, Version 1.0.
# (See accompanying file LICENSE.txt or copy at
# https://www.bfgroup.xyz/b2/LICENSE.txt)

# Tests rc toolset behaviour.

import BoostBuild


def included_resource_newer_than_rc_script():
    """
      When a .rc script file includes another resource file - the resource file
    being newer than the .rc script file should not cause the .rc script file
    to be considered old and force all of its dependents to rebuild.

    """
    toolsetName = "__myDummyResourceCompilerToolset__"

    # Used options rationale:
    #
    # -d4 & --debug-configuration
    #     Display additional information in case of test failure. In the past
    #   we have had testing system issues  causing this test to fail
    #   sporadically for which -d+3 output had been instrumental in getting to
    #   the root cause (a touched file's timestamp was not as new as it should
    #   have been).
    #
    # --ignore-site-config --user-config=
    #     Disable reading any external Boost Build configuration. This test is
    #   self sufficient so these options protect it from being adversly
    #   affected by any local (mis)configuration..
    t = BoostBuild.Tester(["-d4", "--debug-configuration",
        "--ignore-site-config", "--user-config=", "toolset=%s" % toolsetName],
        pass_toolset=False, use_test_config=False,
        translate_suffixes=False)

    # Prepare a dummy toolset so we do not get errors in case the default one
    # is not found and that we can test rc.jam functionality without having to
    # depend on the externally specified toolset actually supporting it exactly
    # the way it is required for this test, e.g. gcc toolset, under some
    # circumstances, uses a quiet action for generating its null RC targets.
    t.write(toolsetName + ".jam", """\
import feature ;
import rc ;
import type ;
local toolset-name = "%s" ;
feature.extend toolset : $(toolset-name) ;
rule init ( ) { }
rc.configure dummy-rc-command : <toolset>$(toolset-name) : <rc-type>dummy ;
module rc
{
    rule compile.resource.dummy ( targets * : sources * : properties * )
    {
        import common ;
        .TOUCH on $(targets) = [ common.file-touch-command ] ;
    }
    actions compile.resource.dummy { $(.TOUCH) "$(<)" }
}
# Make OBJ files generated by our toolset use the "obj" suffix on all
# platforms. We need to do this explicitly for <target-os> windows & cygwin to
# override the default OBJ type configuration (otherwise we would get
# 'ambiguous key' errors on those platforms).
local rule set-generated-obj-suffix ( target-os ? )
{
    type.set-generated-target-suffix OBJ : <toolset>$(toolset-name)
        <target-os>$(target-os) : obj ;
}
set-generated-obj-suffix ;
set-generated-obj-suffix windows ;
set-generated-obj-suffix cygwin ;
""" % toolsetName)

    t.write(
        toolsetName + '.py',
"""
from b2.build import feature, type as type_
from b2.manager import get_manager
from b2.tools import rc, common

MANAGER = get_manager()
ENGINE = MANAGER.engine()

toolset_name = "{0}"

feature.extend('toolset', [toolset_name])

def init(*args):
    pass

rc.configure(['dummy-rc-command'], ['<toolset>' + toolset_name], ['<rc-type>dummy'])

ENGINE.register_action(
    'rc.compile.resource.dummy',
    '''
    %s "$(<)"
    ''' % common.file_creation_command()
)

def set_generated_obj_suffix(target_os=''):
    requirements = ['<toolset>' + toolset_name]
    if target_os:
        requirements.append('<target-os>' + target_os)
    type_.set_generated_target_suffix('OBJ', requirements, 'obj')

set_generated_obj_suffix()
set_generated_obj_suffix('windows')
set_generated_obj_suffix('cygwin')
""".format(toolsetName)
    )

    # Prepare project source files.
    t.write("jamroot.jam", """\
ECHO "{{{" [ modules.peek : XXX ] [ modules.peek : NOEXEC ] "}}}" ;
obj xxx : xxx.rc ;
""")
    t.write("xxx.rc", '1 MESSAGETABLE "xxx.bin"\n')
    t.write("xxx.bin", "foo")

    def test1(n, expect, noexec=False):
        params = ["-sXXX=%d" % n]
        if noexec:
            params.append("-n")
            params.append("-sNOEXEC=NOEXEC")
        t.run_build_system(params)
        t.expect_output_lines("*NOEXEC*", noexec)
        obj_file = "xxx_res.obj"
        t.expect_output_lines("compile.resource.dummy *%s" % obj_file, expect)
        if expect and not noexec:
            expect("bin/%s/debug/%s" % (toolsetName, obj_file))
        t.expect_nothing_more()

    def test(n, expect):
        test1(n, expect, noexec=True)
        test1(n, expect)

    test(1, t.expect_addition)
    test(2, None)
    t.touch("xxx.bin")
    test(3, t.expect_touch)
    test(4, None)

    t.cleanup()


included_resource_newer_than_rc_script()