import bpy
import json
import shutil

import time
import uuid

from pathlib import Path
from hashlib import md5
from ..utils.logger import logger


class ModelImporter:
    """模型导入器，处理不同格式的模型文件"""
    
    SUPPORTED_FORMATS = {
        'obj', 'fbx', 'glb', 'gltf', 'usdz', 'stl'
    }
    
    IMAGE_FORMATS = {
        'png', 'jpg', 'jpeg', 'tga', 'bmp', 'tiff', 'exr'
    }
    
    @classmethod
    def import_model(cls, file_path, file_format):
        """根据格式导入模型"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Model file does not exist: {file_path}")
        
        # 记录导入前的对象
        previous_objects = set(bpy.data.objects)
        previous_images = set(bpy.data.images)
        
        try:
            if file_format == "obj":
                bpy.ops.wm.obj_import(filepath=str(file_path))
            elif file_format in {"gltf", "glb"}:
                bpy.ops.import_scene.gltf(filepath=str(file_path))
            elif file_format == "fbx":
                cls._import_fbx_safe(file_path, previous_objects)
            elif file_format == "stl":
                bpy.ops.wm.stl_import(filepath=str(file_path))
            elif file_format == "usdz":
                cls._import_usdz_safe(file_path, previous_images)
            else:
                raise ValueError(f"Unsupported format: {file_format}")
                
        except Exception as e:
            logger.error(f"Failed to import model {file_path}: {e}")
            return None, []
        
        # 获取新导入的对象和图片
        new_objects = list(set(bpy.data.objects) - previous_objects)
        new_images = list(set(bpy.data.images) - previous_images)
        
        # 修复导入对象的材质色彩空间
        cls._fix_material_colorspaces(new_objects)
        
        return new_objects, new_images
    
    @classmethod
    def _import_fbx_safe(cls, fbx_path, previous_objects):
        """安全导入FBX文件，调整空节点显示大小"""

        bpy.ops.import_scene.fbx(filepath=str(fbx_path))
        
        new_objects = list(set(bpy.data.objects) - previous_objects)
        
        for obj in new_objects:
            if obj.type == 'EMPTY':
                obj.empty_display_size = 0.0001
                logger.debug(f"Set empty display size to 0.0001 for: {obj.name}")
    
    @classmethod
    def _import_usdz_safe(cls, usdz_path, previous_images):
        """安全导入USDZ文件，清理空对象"""
        # 保存原始环境贴图
        original_env = cls._get_current_environment_texture()
        
        # 导入USDZ
        texture_dir = usdz_path.with_suffix("")
        bpy.ops.wm.usd_import(
            filepath=str(usdz_path),
            import_textures_mode="IMPORT_COPY",
            import_textures_dir=str(texture_dir)
        )
        
        # 获取新导入的图片
        new_images = list(set(bpy.data.images) - previous_images)
        
        # 清理空对象和不需要的资源
        cls._cleanup_imported_scene(original_env, new_images)
    
    @classmethod
    def _get_current_environment_texture(cls):
        """获取当前环境贴图"""
        for scene in bpy.data.scenes:
            if scene.world and scene.world.use_nodes and scene.world.node_tree:
                for node in scene.world.node_tree.nodes:
                    if node.type == 'TEX_ENVIRONMENT' and node.image:
                        return node.image
        return None
    
    @classmethod
    def _cleanup_imported_scene(cls, original_env_texture, new_images=None):
        """清理导入的场景，移除空对象和处理贴图"""
        # 查找并移除空的父级对象
        imported_objects = [obj for obj in bpy.data.objects if obj.parent is None]
        
        for obj in imported_objects[:]:
            if obj.type == 'EMPTY' and not obj.children:
                logger.info(f"Removing empty object: {obj.name}")
                bpy.data.objects.remove(obj, do_unlink=True)
        
        # 处理新导入的贴图
        cls._process_imported_textures(original_env_texture, new_images)
    
    @classmethod
    def _process_imported_textures(cls, original_env_texture, new_images=None):
        """处理导入的贴图资源"""
        # 只处理新导入的图片，如果未提供则处理所有图片（向后兼容）
        images_to_process = new_images if new_images is not None else bpy.data.images
        
        for image in images_to_process:
            if not image.filepath:
                continue
                
            # 跳过环境贴图
            if image == original_env_texture:
                continue
                
            # 处理HDR文件
            if image.filepath.lower().endswith('.hdr'):
                cls._handle_hdr_texture(image, original_env_texture)
                continue
            
            # 重命名其他贴图避免冲突
            cls._rename_texture_file(image)
        
        # 打包所有资源
        bpy.ops.file.pack_all()
        logger.info("Assets packaged into Blend file")
    
    @classmethod
    def _handle_hdr_texture(cls, hdr_image, original_env):
        """处理HDR环境贴图"""
        if hdr_image != original_env:
            logger.info(f"Removing imported HDR texture: {hdr_image.name}")
            # 清理材质引用
            for material in bpy.data.materials:
                if material.use_nodes and material.node_tree:
                    for node in material.node_tree.nodes:
                        if node.type == 'TEX_ENVIRONMENT' and node.image == hdr_image:
                            node.image = None
            bpy.data.images.remove(hdr_image)
    
    @classmethod
    def _rename_texture_file(cls, image):
        """重命名贴图文件避免冲突"""
        import re
        
        try:
            original_path = Path(bpy.path.abspath(image.filepath))
            
            # 检查路径长度
            if len(str(original_path)) > 240:
                logger.warning(f"Path too long, skipping rename: {original_path.name}")
                return
            
            if not original_path.exists():
                logger.warning(f"Texture file does not exist, skipping: {original_path.name}")
                return
            
            # 检查是否已经重命名过（文件名开头是否为8位十六进制字符+下划线）
            if re.match(r'^[0-9a-f]{8}_', original_path.name):
                logger.debug(f"Texture already renamed, skipping: {original_path.name}")
                return
            
            # 生成新文件名（使用8位短UUID）
            new_name = f"{uuid.uuid4().hex[:8]}_{original_path.name}"
            new_path = original_path.parent / new_name
            
            # 移动文件
            shutil.move(str(original_path), str(new_path))
            
            # 更新图片引用
            image.filepath = str(new_path)
            image.name = new_name
            image.reload()
            
            logger.info(f"Texture renamed: {original_path.name} → {new_name}")
            
        except OSError as e:
            logger.error(f"File system error, rename failed for {image.name}: {e}")
        except Exception as e:
            logger.error(f"Failed to rename texture {image.name}: {e}")
    
    @classmethod
    def _fix_material_colorspaces(cls, objects):
        """修复材质的色彩空间设置"""
        COLOR_INPUTS = {"Base Color", "Emission"}
        DATA_INPUTS = {"Roughness", "Metallic", "Normal", "Alpha", "Specular"}
        
        def find_image_node(socket, visited=None):
            """递归查找连接到socket的图像纹理节点"""
            if visited is None:
                visited = set()
            
            if not socket or not socket.is_linked:
                return None
            
            link = socket.links[0]
            node = link.from_node
            
            if node in visited:
                return None
            visited.add(node)
            
            if node.type == 'TEX_IMAGE':
                return node
            
            # 递归查找输入节点
            for inp in node.inputs:
                img_node = find_image_node(inp, visited)
                if img_node:
                    return img_node
            
            return None
        
        for obj in objects:
            if not obj.data or not hasattr(obj.data, 'materials'):
                continue

            for mat in obj.data.materials:
                if not mat or not mat.use_nodes or not mat.node_tree:
                    continue
                
                # 查找Principled BSDF节点
                principled_node = next(
                    (n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), 
                    None
                )
                
                if not principled_node:
                    continue
                
                # logger.info(f"Fix material colorspace: {mat.name}")
                
                # 遍历Principled BSDF的输入
                for socket in principled_node.inputs:
                    img_node = find_image_node(socket)
                    if not img_node or not img_node.image:
                        continue
                    
                    img = img_node.image
                    socket_name = socket.name
                    
                    if socket_name in COLOR_INPUTS:
                        if img.colorspace_settings.name != 'sRGB':
                            img.colorspace_settings.name = 'sRGB'
                            logger.info(f"  {socket_name} → {img.name}: sRGB")
                    elif socket_name in DATA_INPUTS:
                        if img.colorspace_settings.name != 'Non-Color':
                            img.colorspace_settings.name = 'Non-Color'
                            logger.info(f"  {socket_name} → {img.name}: Non-Color")


class ModelCacheManager:
    """模型缓存管理器"""
    
    def __init__(self, cache_dir=None):
        self.cache_dir = Path(cache_dir) if cache_dir else Path(bpy.app.tempdir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def save_file(self, filename, content):
        """保存文件到缓存"""
        file_path = self.cache_dir / filename
        file_path.write_bytes(content)
        return file_path
    
    def cleanup_file(self, file_path, max_retries=5):
        """清理缓存文件"""
        for attempt in range(max_retries):
            try:
                Path(file_path).unlink(missing_ok=True)
                break
            except PermissionError:
                if attempt < max_retries - 1:
                    time.sleep(0.1)
                else:
                    logger.warning(f"Could not delete cache file: {file_path}")
    
    def save_event_cache(self, event_data):
        """保存事件数据到缓存"""
        cache_file = self.cache_dir / "model_event_cache.json"
        cache_file.write_text(json.dumps(event_data, indent=2))
        return cache_file


class MaterialBuilder:
    """材质构建器"""
    
    @staticmethod
    def create_pbr_material(obj, texture_images, material_name=None):
        """创建PBR材质"""
        if not obj or not texture_images:
            return None
        
        if material_name is None:
            material_name = f"pbr_{md5(obj.name.encode()).hexdigest()[:8]}"
        
        # 创建新材质
        material = bpy.data.materials.new(name=material_name)
        material.use_nodes = True
        
        # 清理默认节点
        node_tree = material.node_tree
        if not node_tree:
            return None
        node_tree.nodes.clear()
        
        # 创建节点
        bsdf_node = node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        output_node = node_tree.nodes.new(type='ShaderNodeOutputMaterial')
        
        # 定位节点
        bsdf_node.location = (0, 0)
        output_node.location = (300, 0)
        
        # 连接节点
        node_tree.links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])
        
        # 添加纹理节点
        texture_nodes = {}
        texture_types = {
            'diffuse': ('Base Color', 'RGBA'),
            'albedo': ('Base Color', 'RGBA'),
            'basecolor': ('Base Color', 'RGBA'),
            'metallic': ('Metallic', 'VALUE'),
            'roughness': ('Roughness', 'VALUE'),
            'normal': ('Normal', 'VECTOR')
        }
        
        y_offset = 0
        for texture_type, (input_name, socket_type) in texture_types.items():
            texture_node = node_tree.nodes.new(type='ShaderNodeTexImage')
            texture_node.location = (-300, y_offset)
            texture_nodes[texture_type] = texture_node
            y_offset -= 280
            
            # 连接到对应的BSDF输入
            if socket_type == 'VECTOR' and input_name == 'Normal':
                normal_map_node = node_tree.nodes.new(type='ShaderNodeNormalMap')
                normal_map_node.location = (-100, y_offset + 140)
                node_tree.links.new(texture_node.outputs['Color'], normal_map_node.inputs['Color'])
                node_tree.links.new(normal_map_node.outputs['Normal'], bsdf_node.inputs[input_name])
            else:
                node_tree.links.new(texture_node.outputs[socket_type], bsdf_node.inputs[input_name])
        
        # 分配贴图
        MaterialBuilder._assign_textures(texture_nodes, texture_images)
        
        # 应用到对象
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)
        
        return material
    
    @staticmethod
    def _assign_textures(texture_nodes, texture_images):
        """根据文件名分配贴图到对应的节点"""
        texture_mappings = {
            'diffuse': ['diffuse', 'albedo', 'basecolor', 'color'],
            'metallic': ['metallic', 'metalness'],
            'roughness': ['roughness', 'gloss'],
            'normal': ['normal', 'normals']
        }
        
        # 需要设置为Non-Color的贴图类型
        non_color_types = {'metallic', 'roughness', 'normal'}
        
        for image in texture_images:
            image_name_lower = image.name.lower()
            
            for texture_type, keywords in texture_mappings.items():
                if texture_type in texture_nodes:
                    if any(keyword in image_name_lower for keyword in keywords):
                        texture_nodes[texture_type].image = image
                        # 设置色彩空间
                        if texture_type in non_color_types:
                            image.colorspace_settings.name = 'Non-Color'
                        break


class ModelLoader:
    """主模型加载器"""
    
    def __init__(self, cache_manager=None):
        self.cache_manager = cache_manager or ModelCacheManager()
    
    def _import_model_file(self, file_path, file_format):
        """导入模型文件"""
        objects, images = ModelImporter.import_model(file_path, file_format)
        if objects:
            return objects[0]  # 返回第一个对象
        return None
    
    def _import_image_file(self, file_path):
        """导入图片文件"""
        try:
            return bpy.data.images.load(str(file_path))
        except Exception as e:
            logger.error(f"Failed to load image {file_path}: {e}")
            return None
    
    def _is_model_file(self, file_data):
        """检查是否为模型文件"""
        fmt = file_data['format'].lower()
        return fmt in ModelImporter.SUPPORTED_FORMATS
    
    def _is_image_file(self, file_data):
        """检查是否为图片文件"""
        fmt = file_data['format'].lower()
        return fmt in ModelImporter.IMAGE_FORMATS

    def load_from_bytes(self, data_bytes: bytes, filename: str, file_format: str, md5_hex: str | None = None):
        """从二进制数据加载模型。

        该方法应在 Blender 主线程被调用（通过 bpy.app.timers.register 调度），
        它会将数据写入缓存并调用现有的导入逻辑。
        """
        file_path = None
        try:
            # 保存到缓存目录
            file_path = self.cache_manager.save_file(filename, data_bytes)

            # 如果需要，可校验 md5
            if md5_hex:
                import hashlib
                if hashlib.md5(data_bytes).hexdigest() != md5_hex:
                    raise ValueError("MD5 mismatch for binary payload")

            # 调用已有导入逻辑
            file_format = file_format.lower()
            if file_format not in ModelImporter.SUPPORTED_FORMATS:
                raise ValueError(f"Unsupported format: {file_format}")

            # 导入模型或图片
            if file_format in ModelImporter.SUPPORTED_FORMATS:
                ModelImporter.import_model(file_path, file_format)

        except Exception as e:
            logger.error(f"load_from_bytes failed for {filename}: {e}")
            raise
        finally:
            # 清理临时文件
            if file_path is not None:
                try:
                    self.cache_manager.cleanup_file(file_path)
                except Exception:
                    pass

loader = ModelLoader()
