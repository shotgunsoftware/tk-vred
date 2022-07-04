Headless Mode
#############

It is possible to run ``tk-vred`` in headless mode using the `Bootstrap API <https://developer.shotgridsoftware.com/tk-core/initializing.html#bootstrap-api>`_.

.. warning::
    In order to be able to bootstrap ``tk-vred``, you need to ensure that the
    ``SHOTGUN_ENABLE`` environment variable doesn't exist or is set to ``0`` otherwise
    the engine won't start.

Here is an example of how to bootstrap ``tk-vred`` in headless mode::

    import os
    import sgtk

    # Create a Toolkit Core API instance based on a project path or
    # path that points directly at a pipeline configuration.
    tk = sgtk.sgtk_from_path("/site/project_root")

    # Specify the context the DCC will be started up in.
    context = tk.context_from_path("/site/project_root")

    # Using a core factory method, construct a SoftwareLauncher
    # subclass for the desired tk engine.
    software_launcher = sgtk.platform.create_engine_launcher(tk, context, "tk-vred")

    # Use the SoftwareLauncher instance to find a list of VRED versions installed on the
    # local filesystem. A list of SoftwareVersion instances is returned.
    software_versions = software_launcher.scan_software()

    # Ask the SoftwareLauncher instance to prepare an environment to launch VRED in.
    # For simplicity, use the first version returned from the list of software_versions.
    launch_info = software_launcher.prepare_launch(software_versions[0].path)

    # Make sure the SHOTGUN_ENABLE environment variable is correctly set
    env = launch_info.environment.copy()
    env["SHOTGUN_ENABLE"] = "0"

    # Launch VRED!
    launch_command = "%s %s" % (launch_info.path, launch_info.args)
    subprocess.Popen([launch_command, "-hide_gui"], env=env)

