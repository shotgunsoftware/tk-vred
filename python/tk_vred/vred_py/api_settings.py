# Copyright (c) 2023 Autodesk.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk.

from .base import VREDPyBase

from sgtk.platform.qt import QtCore, QtGui


class VREDPySetting(VREDPyBase):
    """VRED Python API material helper class."""

    def __init__(self, vred_py):
        """Initialize"""
        super(VREDPySetting, self).__init__(vred_py)

    def get_unfold_settings(
        self,
        iterations=1,
        prevent_border_intersections=True,
        prevent_triangle_flips=True,
        map_size=1024,
        room_space=0,
    ):
        """
        Return the settings for unfold.

        Holds settings for UV unfold with Unfold3D.

        Default settings are returned for decore unless specific values passed by parameters.

        :param iterations: Set the number of Optimize iterations being applied when unfolding
            UVs with Unfold3D. Default is 1.
                 -1 - Disables Optimize during Unfold.
                  0 - Enables Optimize only in case triangle flips or border intersections
                      happen during the Unfold.
                >=1 - Optimize also runs after the unfold.
        :type iterations: int
        :param map_size: Sets the texture map size (in pixels) for room space used by
            anti-border self intersection. Default is 1024 pixels.
        :type prevent_border_intersections: bool
        :param prevent_triangle_flips: Activate the anti-triangle flip algorithm. Default is
            True.
        :type prevent_triangle_flips: bool
        :type map_size: int
        :param prevent_border_intersections: Activate the anti-border self intersection
            algorithm. The room space parameter is taken into account for this. Default is
            True.
        :param room_space: Sets the room space in pixels, in relation to the map size. The room
            space is the minimum space allowed between borders within one island for the
            anti-border self intersection algorithm. This setting only has an effect if the
            anti-border self intersection is enabled (with prevent_border_intersections). Avoid
            large values, because it can slow down the unfold calculations and create
            distortion. Default is 0.
        :type room_space: int
        """

        settings = self.vred_py.vrdUVUnfoldSettings()

        settings.setIterations(iterations)
        settings.setPreventBorderIntersections(prevent_border_intersections)
        settings.setPreventTriangleFlips(prevent_triangle_flips)
        settings.setMapSize(map_size)
        settings.setRoomSpace(room_space)

        return settings

    def get_layout_settings(
        self,
        resolution=256,
        iterations=1,
        pre_rotate_mode=None,
        pre_scale_mode=None,
        translate=True,
        rotate=False,
        rotate_step=90.0,
        rotate_min=0.0,
        rotate_max=360.0,
        island_padding=0.0,
        tile_padding=0.0,
        tiles_u=1,
        tiles_v=1,
        tile_assign_mode=None,
        box=QtGui.QVector4D(0.0, 1.0, 0.0, 1.0),
        post_scale_mode=None,
    ):
        """
        Return the settings for layout.

        Holds settings for UV layout (packing of UV islands in the UV space) with Unfold3D.

        Default settings are returned for decore unless specific values passed by parameters.

        :param resolution: Determines the resolution of the packing grid used to place UV
            islands next to each other in the UV space. Higher values are slower, but produce
            better results when there are a lot of smaller islands. Default 256.
        :type resolution: int
        :param iterations: Set the number of trials the packing algorithm will take to achieve
            the desired result. More iterations are slower, but can increase accuracy. Default
            1.
        :type iterations: int
        :param pre_rotate_mode: Sets how the islands are re-oriented in a pre-process phase
            before packing. Default vrUVTypes.PreRotateMode.YAxisToV
        :param pre_rotate_mode: vrUVTypes.PreRotateMode
        :param pre_scale_mode: Sets how the islands are rescaled in a pre-process phase before
            packing. Default vrUVTypes.PreScaleMode.Keep3DArea
        :type pre_scale_mode: vrUVTypes.PreScaleMode
        :param translate: Default True.
        :type translate:
        :param rotate: Set whether UV islands may be rotated during the packing process.
            Default False.
        :type rotate: bool
        :param rotate_step: Set rotation step for the optimization of island orientation. Only
            used if rotation optimization is enabled with
            vrdUVLayoutSettings.setRotate(enable). Rotation optimization begins at the minimum
            value, see vrdUVLayoutSettings.setRotateMin(rMinDeg), then progressively increases
            by the rotation step as necessary, up to the maximum value, see
            vrdUVLayoutSettings.setRotateMax(rMaxDeg). The angle step in degrees. Please note,
            rotate_step = 0.0 disables the rotation optimization. Small values incur slower
            packing speeds. Default 90 degrees.
        :type rotate_step: float
        :param rotate_min: Set the minimum allowable orientation for UV islands during the
            packing process. Only used if rotation is enabled with
            vrdUVLayoutSettings.setRotate(enable).
        :type rotate_min: float
        :param rotate_max: Set the maximum allowable orientation for UV islands during the
            packing process. Only used if rotation is enabled with
            vrdUVLayoutSettings.setRotate(enable).
        :type rotate_max: float
        :param island_padding: Set padding between islands in UV unit. Padding in UV unit.
            Value must be >= 0.0, negative values are clamped to 0.
        :type island_padding: float
        :param tile_padding: Set padding on top/left/right/bottom of the tiles in UV unit.
            Padding in UV unit. Value must be >= 0.0, negative values are clamped to 0.
            Default 0.0
        :type tile_padding: float
        :param tiles_u: Specify tiling to distribute islands to more than one tile. Default 1.
        :type tiles_u: int
        :param tiles_v: Specify tiling to distribute islands to more than one tile. Default 1.
        :type tiles_v: int
        :param tile_assign_mode: Set how islands are distributed to the available tiles. In
            VRED, this is the UV editor Island Distribution field. Default
            vrUVTypes.TileAssignMode.Distribute
        :type tile_assign_mode: vrUVTypes.TileAssignMode
        :param box: Set the UV space box in which the islands will be packed (packing region).
            Box as (U_min, U_max, V_min, V_max). In VRED, this is the UV Editor Packing Region
            U min/max, V min/max field. Default (0.0, 1.0, 0.0, 1.0).
        :type box: QtGui.QVector4D
        :param post_scale_mode: Sets how the packed islands are scaled into the box after
            packing. In VRED, this is the UV editor Scale Mode field. Default
            vrUVTypes.PostScaleMode.Uniform
        :type post_scale_mode: vrUVTypes.PostScaleMode
        """

        pre_rotate_mode = (
            pre_rotate_mode or self.vred_py.vrUVTypes.PreRotateMode.YAxisToV
        )
        pre_scale_mode = (
            pre_scale_mode or self.vred_py.vrUVTypes.PreScaleMode.Keep3DArea
        )
        tile_assign_mode = (
            tile_assign_mode or self.vred_py.vrUVTypes.TileAssignMode.Distribute
        )
        post_scale_mode = (
            post_scale_mode or self.vred_py.vrUVTypes.PostScaleMode.Uniform
        )

        settings = self.vred_py.vrdUVLayoutSettings()

        settings.setBox(box)
        settings.setIslandPadding(island_padding)
        settings.setIterations(iterations)
        settings.setPostScaleMode(post_scale_mode)
        settings.setPreRotateMode(pre_rotate_mode)
        settings.setPreScaleMode(pre_scale_mode)
        settings.setResolution(resolution)
        settings.setRotate(rotate)
        settings.setRotateMax(rotate_max)
        settings.setRotateMin(rotate_min)
        settings.setRotateStep(rotate_step)
        settings.setTileAssignMode(tile_assign_mode)
        settings.setTilePadding(tile_padding)
        settings.setTilesU(tiles_u)
        settings.setTilesV(tiles_v)
        settings.setTranslate(translate)

        return settings

    def get_texture_bake_settings(
        self,
        hide_transparent_objects=True,
        external_reference_location=None,
        renderer=None,
        samples=128,
        share_lightmaps_for_clones=True,
        use_denoising=True,
        use_existing_resolution=False,
        min_resolution=64,
        max_resolution=256,
        texel_density=200.00,
        edge_dilation=2,
    ):
        """
        Return the settings for textures in baking.

        Default settings are returned for decore unless specific values passed by parameters.

        :param hide_tarnsparent_objects: Sets if transparent objects should be hidden. This
            option controls if objects with transparent materials will be hidden during the
            lightmap calculation process. When hidden, they do not have any effect on the
            light and shadow calculation. Default True.
        :type hide_tarnsparent_objects: bool
        :param external_reference_location: Sets an external reference location. The external
            reference location is a path to a folder were the lightmap texture will be stored
            after the baking is done. In that case the lightmap texture is externally
            referenced. If no external reference location is set, the lightmap texture will
            exist only within the project file. Default None.
        :type external_reference_location: str
        :param renderer: Sets which raytracing renderer is used to generate the lightmaps.
            Default vrBakeTypes.Renderer.CPURayTracing
        :type renderer: vrBakeTypes.Renderer
        :param samples: Sets the number of samples. The number of samples per pixel defines
            the quality of the lightmap. The higher the number, the better the quality but the
            longer the calculation. Default 128.
        :type samples: int
        :param share_lightmaps_for_clones: Sets if given clones will share the same lightmap or
            if separate lightmaps will be created for each clone. Default True.
        :type share_lightmaps_for_clones: bool
        :param use_denoising: Sets if denoising should be used or not. Denoising is a
            post-process of the final lightmap texture and tries to reduce noise based on AI
            algorithms. Default True.
        :type use_denoising: bool
        :param use_existing_resolution: Sets if an existing lightmap resolution should be kept.
            If the geometry already has a valid lightmap, its resolution is used for the new
            bake process. Default False.
        :type use_existing_resolution: bool
        :param min_resolution: Sets the minimum resolution for the lightmap.
            - Equal values for minimum and maximum resolution will enforce a fixed resolution.
            - Otherwise a resolution between minimum and maximum is automatically calculated.
        :type min_resolution: int
        :param max_resolution: Sets the maximum resolution for the lightmap.
            - Equal values for minimum and maximum resolution will enforce a fixed resolution.
            - Otherwise a resolution between minimum and maximum is automatically calculated.
        :type max_resolution: int
        :param texel_density: Sets the texel density in pixels per meter. The texel density is
            used for the automatic lightmap resolution calculation. The lightmap resolution
            will be calculated using this value and the object’s size as well as the covered UV
            space, clamped by the minimum and maximum resolution. Default 200.00
        :type texel_density: float
        :param edge_dilation: Sets the edge dilation in pixels. Sets the number of pixels the
            valid bake areas will be extended by. This is necessary to prevent the rendering of
            black seams at UV island borders. Default 2.
        :type edge_dilation: int
        """

        renderer = renderer or self.vred_py.vrBakeTypes.Renderer.CPURayTracing

        settings = self.vred_py.vrdTextureBakeSettings()

        settings.setEdgeDilation(edge_dilation)
        settings.setHideTransparentObjects(hide_transparent_objects)
        settings.setMaximumResolution(max_resolution)
        settings.setMinimumResolution(min_resolution)
        settings.setRenderer(renderer)
        settings.setSamples(samples)
        settings.setShareLightmapsForClones(share_lightmaps_for_clones)
        settings.setTexelDensity(texel_density)
        settings.setUseDenoising(use_denoising)
        settings.setUseExistingResoluiton(use_existing_resolution)
        if external_reference_location:
            settings.setExternalReferenceLocation(external_reference_location)

        return settings

    def get_illumination_bake_settings(
        self,
        ambient_occlusion_max_dist=3000.00,
        ambient_occlusion_min_dist=1.00,
        ambient_occlusion_weight=None,
        color_bleeding=False,
        direct_illumination_mode=None,
        indirect_illumination=True,
        indirections=1,
        lights_layer=-1,
        material_override=True,
        material_override_color=QtCore.Qt.white,
    ):
        """
        Return the settings for illumination in baking.

        Settings for texture baking with vrBakeService.bakeToTexture.

        Default settings are returned for decore unless specific values passed by parameters.

        :param ambient_occlusion_max_dist: Sets the ambient occlusion maximum distance. Sets
            the maximum distance of objects to be taken into account for the ambient occlusion
            calculation. Distance in mm. Default 3000.00
        :type ambient_occlusion_max_dist: float
        :param ambient_occlusion_min_dist: Sets the ambient occlusion minimum distance. Sets
            the minimum distance of objects to be taken into account for the ambient occlusion
            calculation. Distance in mm. Default 1.00
        :type ambient_occlusion_min_dist: float
        :param ambient_occlusion_weight: Sets the ambient occlusion weight mode. Sets how the
            ambient occlusion samples in the hemisphere above the calculation point are
            weighted. Default vrBakeTypes.AmbientOcclusionWeight.Unifrom
        :type ambient_occlusion_weight: vrBakeTypes.AmbientOcclusionWeight
        :param color_bleeding: Sets if color bleeding should be used. This affects the indirect
            illumination. If disabled the indirect illumination result is grayscale. Default
            False.
        :type color_bleeding: bool
        :param direct_illumination_mode: Sets the direct illumination mode. This mode defines
            the kind of data which will be baked. Default
            vrBakeTypes.DirectIlluminationMode.AmbientOcclusion
        :type direct_illumination_mode: vrBakeTypes.DirectIlluminationMode
        :param indirect_illumination: Sets if indirect illumination should be evaluated.
            Default True.
        :type indirect_illumination: bool
        :param indirections: Sets the number of indirections. Defines the number of calculated
            light bounces. Default 1.
        :type indirections: int
        :param lights_layer: Only available for texture baking. Sets if only lights from a
            specific layer should be baked. See vrdBaseLightNode.setBakeLayer(layer). For the
            bake layer of incandescence in emissive materials use API v1 vrFieldAccess. -1
            (default) means light layer setting is ignored, i.e. all lights are baked
            regardless of their layer setting. Value >= 0 means only lights with matching layer
            number are evaluated.
        :type lights_layer: int
        :param material_override: Sets if a global material override should be used. If
            enabled, all geometries will have a global diffuse material override during the
            bake calculation. Default True.
        :type material_override: bool
        :param material_override_color: Sets the color of the override material. Default white.
        :type material_override_color: QtGui.QColor

        :return: The settings for illumination in baking.
        :rtype: vrdIlluminationBakeSettings
        """

        direct_illumination_mode = (
            direct_illumination_mode
            or self.vred_py.vrBakeTypes.DirectIlluminationMode.AmbientOcclusion
        )
        ambient_occlusion_weight = (
            ambient_occlusion_weight
            or self.vred_py.vrBakeTypes.AmbientOcclusionWeight.Uniform
        )

        settings = self.vred_py.vrdIlluminationBakeSettings()

        settings.setAmbientOcclusionMaximumDistance(ambient_occlusion_max_dist)
        settings.setAmbientOcclusionMinimumDistance(ambient_occlusion_min_dist)
        settings.setAmbientOcclusionWeight(ambient_occlusion_weight)
        settings.setColorBleeding(color_bleeding)
        settings.setDirectIlluminationMode(direct_illumination_mode)
        settings.setIndirectIllumination(indirect_illumination)
        settings.setIndirections(indirections)
        settings.setLightsLayer(lights_layer)
        settings.setMaterialOverride(material_override)
        settings.setMaterialOverideColor(material_override_color)

        return settings

    def get_decore_settings(
        self,
        resolution=1024,
        quality_steps=8,
        correct_face_normals=False,
        decore_enabled=False,
        decore_mode=None,
        sub_object_mode=None,
        transparent_object_mode=None,
    ):
        """
        Return settings for object decoring/optimization.

        Decoring removes redundant geometry that is inside other geometry, like screws and
        mountings inside a door covering. A virtual camera flies around the selected object,
        takes screen shots, and removes any non-visible geometry.

        Default settings are returned for decore unless specific values passed by parameters.

        :param resolution: Defines the resolution of the images taken. A higher resolution
            gives more precise results. Default 1024.
        :type resolution: int
        :param quality_steps: Defines the number of images taken during the analysis. A higher
            value gives more accurate results. Default 8.
        :type quality_steps: int
        :param correct_face_normals: If enabled, flips polygon normals pointing away from the
            camera, if they are encountered during the analysis. Default False.
        :type correct_face_normals: bool
        :param decore_enabled: Defines if decoring is enabled. Default False.
        :type decore_enabled: bool
        :param decore_mode: Defines the action to be taken, when geometry is determined to be
            inside another and non-visible. Default vrGeometryTypes.DecoreMode.Remove.
        :type decore_mode: vrGeometryTypes.DecoreMode
        :param sub_object_mode: Defines how sub objects are taken into account. Default
            vrGeometryTypes.DecoreSubObjectMode.Triangles.
        :type sub_object_mode: vrGeometryTypes.DecoreSubObjectMode
        :param transparent_object_mode: Defines how transparent objects should be handled.
            Default vrGeometryTypes.DecoreTransparentObjectMode.Ignore.
        :type transparent_object_mode: vrGeometryTypes.DecoreTransparentObjectMode

        :return: The decore settings.
        :rtype: vrdDecoreSettings
        """

        decore_mode = decore_mode or self.vred_py.vrGeometryTypes.DecoreMode.Remove
        sub_object_mode = (
            sub_object_mode
            or self.vred_py.vrGeometryTypes.DecoreSubObjectMode.Triangles
        )
        transparent_object_mode = (
            transparent_object_mode
            or self.vred_py.vrGeometryTypes.DecoreTransparentObjectMode.Ignore
        )

        settings = self.vred_py.vrdDecoreSettings()

        settings.setResolution(resolution)
        settings.setQualitySteps(quality_steps)
        settings.setCorrectFaceNormals(correct_face_normals)
        settings.setDecoreEnabled(decore_enabled)
        settings.setDecoreMode(decore_mode)
        settings.setSubObjectMode(sub_object_mode)
        settings.setTransparentObjectMode(transparent_object_mode)

        return settings
