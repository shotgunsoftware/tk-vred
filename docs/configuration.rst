Toolkit Configuration
####################################################

Like all Flow Production Tracking (FPTR) components, the FPTR VRED integration can be configured using the Toolkit configuration bundle. This documentation will cover the configuration using ``tk-config-default2``; while ``tk-config-basic`` can also be used, it is recommended to use ``tk-config-default2`` for the easiest set up.

Engine Configuration
-------------------------

The main configuration file for VRED is:  ``tk-config-default2/envs/includes/settings/tk-vred.yml``

You can find configuration settings in ``tk-vred/info.yml`` that can be added to ``tk-vred.yml``.

App Configuration
----------------------

Configuration settings for Toolkit Apps, that VRED supports, can be found in the application specific configuration file.

For example, the Scene Breaksown2 App, the configuration settings is:  ``tk-config-default2/envs/include/settings/tk-multi-breakdown2.yml``

In this file, you will find a section for VRED settings. In the application ``info.yml``, similar to the tk-vred info.yml, you will find settings that can be added to the application's configuration file.

Scene Breakdown2 App
******************************************

In ``tk-multi-breakdown2/info.yml``, you will see the available configuration settings, which can be added to tk-multi-breakdown2.yml:

**display_name**

    Modify the display name of the App in the Toolkit menu. Default is "Scene Breakdown".

**panel_mode**

    Set to True to run the App as a panel, or False to run as a dialog. Default is True.

**interactive_update**

    Set to True to show options dialog before updating a reference file.

    .. note::

        This setting is only applicable for VRED Source References; the VRED import options dialog will appear before updating the reference file. For VRED Smart References, no dialog will appear.
