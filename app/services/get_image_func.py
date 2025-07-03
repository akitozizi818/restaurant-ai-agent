import os
import httpx
import aiofiles
from typing import Optional
from dotenv import load_dotenv

async def save_place_photo_locally(
    place_id: str, 
    google_api_key: str, 
    save_dir: str = "images"
) -> Optional[str]:
    
    load_dotenv()

    google_api_key = os.getenv("GOOGLE_API_KEY")
    """
    指定されたplace_idの最初の写真を取得し、ローカルに保存する。

    Args:
        place_id (str): Google Place ID。
        google_api_key (str): Google Cloud APIキー。
        save_dir (str): 画像を保存するディレクトリ。

    Returns:
        Optional[str]: 保存された画像のファイルパス。失敗した場合はNone。
    """
    if not google_api_key:
        print("[ImageDownloader] エラー: Google APIキーが指定されていません。")
        return None

    details_url = f"https://places.googleapis.com/v1/places/{place_id}"
    headers = {
        "X-Goog-Api-Key": google_api_key,
        "X-Goog-FieldMask": "photos" # 写真情報のみをリクエスト
    }

    async with httpx.AsyncClient() as client:
        try:
            # 1. Place IDから写真のリソース名を取得
            res = await client.get(details_url, headers=headers)
            res.raise_for_status()
            data = res.json()
            
            photos = data.get("photos")
            if not photos:
                print(f"[ImageDownloader] place_id '{place_id}' には写真がありません。")
                return None
            
            photo_resource_name = photos[0].get("name") # 最初の写真を利用
            if not photo_resource_name:
                return None

            # 2. 写真データを取得
            photo_url = f"https://places.googleapis.com/v1/{photo_resource_name}/media?maxWidthPx=800&key={google_api_key}"
            photo_res = await client.get(photo_url, follow_redirects=True, timeout=15)
            photo_res.raise_for_status()
            
            image_content = await photo_res.aread()
            content_type = photo_res.headers.get("content-type", "image/jpeg")
            extension = ".jpg" if "jpeg" in content_type else ".png"

            # 3. ローカルに保存
            os.makedirs(save_dir, exist_ok=True)
            file_path = os.path.join(save_dir, f"{place_id}{extension}")
            
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(image_content)
            
            print(f"[ImageDownloader] 画像を {file_path} に保存しました。")
            return file_path

        except httpx.HTTPStatusError as e:
            print(f"[ImageDownloader] APIエラーが発生しました: {e.response.text}")
            return None
        except Exception as e:
            print(f"[ImageDownloader] 予期せぬエラーが発生しました: {e}")
            return None