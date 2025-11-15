import requests
import os
import io
import time
import numpy as np
from PIL import Image

class ImageUploader:

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "server_url": ("STRING", {"default": "http://cloudflare-imgbed/upload", "placeholder": "https://cfbed.sanyue.de/api/upload.html"}),
                "api_token": ("STRING", {"default": "", "placeholder": "API Token (优先于authCode)"}),
                "upload_name_type": (["default", "index", "origin", "short"], {"default": "default"}),
                "return_format": (["default", "full"], {"default": "default"}),
            },
            "optional": {
                "auth_code": ("STRING", {"default": "", "placeholder": "上传认证码"}),
                "server_compress": ("BOOLEAN", {"default": True}),
                "upload_channel": (["telegram", "cfr2", "s3"], {"default": "telegram"}),
                "auto_retry": ("BOOLEAN", {"default": True}),
                "upload_folder": ("STRING", {"default": "/AI-AutoUpload", "placeholder": "相对路径，如img/test"}),
                "custom_filename": ("STRING", {"default": "", "placeholder": "原始文件名"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("status", "result", "error_detail")
    FUNCTION = "upload"
    CATEGORY = "文件上传/CloudFlare ImgBed"

    def upload(self, image, server_url, api_token, upload_name_type, return_format,
               auth_code="", server_compress=True, upload_channel="telegram",
               auto_retry=True, upload_folder="", custom_filename=""):
        try:
            img_tensor = image[0]
            img_np = (img_tensor * 255).clamp(0, 255).byte().cpu().numpy()
            pil_img = Image.fromarray(img_np)

            if custom_filename:
                filename = custom_filename
            else:
                filename = f"comfyui_{int(time.time())}"

            if not filename.endswith(('.png', '.jpg', '.jpeg')):
                filename += '.png'


            img_byte_arr = io.BytesIO()
            pil_img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            query_params = {
                "serverCompress": str(server_compress).lower(),
                "uploadChannel": upload_channel,
                "autoRetry": str(auto_retry).lower(),
                "uploadNameType": upload_name_type,
                "returnFormat": return_format,
            }

            if auth_code:
                query_params["authCode"] = auth_code
            if upload_folder:
                query_params["uploadFolder"] = upload_folder

            headers = {}
            if api_token:
                headers["Authorization"] = f"Bearer {api_token}"

            files = {
                "file": (filename, img_byte_arr, "image/png")
            }

            response = requests.post(
                url=server_url,
                params=query_params,
                files=files,
                headers=headers,
                timeout=60
            )

            response.raise_for_status()
            result = response.text
            return ("success", result, "无错误")
        except requests.exceptions.HTTPError as e:
            return ("failed", "", f"HTTP错误: {str(e)}，响应内容: {response.text if 'response' in locals() else '无'}")
        except requests.exceptions.ConnectionError:
            return ("failed", "", "连接错误：无法连接到服务器，请检查URL")
        except requests.exceptions.Timeout:
            return ("failed", "", "超时错误：服务器未在指定时间内响应")
        except Exception as e:
            return ("error", "", f"未知错误：{str(e)}")




NODE_CLASS_MAPPINGS = {
    "ImageUploader": ImageUploader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageUploader": "Image Uploader"
}
