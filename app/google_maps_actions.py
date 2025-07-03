# app/google_maps_actions.py
import os
import googlemaps
from vertexai.generative_models import GenerativeModel

class GoogleMapsActions:
    def __init__(self, gemini_model: GenerativeModel, ngrok_base_url: str):
        self.gmaps = googlemaps.Client(key=os.getenv("Maps_API_KEY"))
        self.gemini_model = gemini_model
        self.maps_api_key = os.getenv("Maps_API_KEY")
        self.ngrok_base_url = ngrok_base_url

    def search_and_format_restaurants(self, query: str, max_results: int = 3) -> list:
        if not self.gmaps:
            print("Google Maps client not initialized.")
            return []
        print(f"Google Mapsで検索中: {query}")
        try:
            places_result = self.gmaps.places(query=query, language='ja')
            
            formatted_restaurants = []
            for place in places_result.get('results', [])[:max_results]:
                place_id = place.get('place_id')
                if not place_id:
                    continue

                # ★★★ ここが修正点 ① ★★★
                # 詳細情報取得のリクエストから 'types' を削除
                fields = ['name', 'formatted_address', 'website', 'rating', 'user_ratings_total', 'photo', 'reviews', 'place_id']
                details = self.gmaps.place(place_id=place_id, fields=fields, language='ja').get('result', {})
                
                # ★★★ ここが修正点 ② ★★★
                # 整形用の関数に、最初の検索結果(place)も渡すようにする
                formatted_restaurant = self._format_place_details(details, place)
                formatted_restaurants.append(formatted_restaurant)
            
            return formatted_restaurants
        except Exception as e:
            print(f"Google Maps APIの処理中にエラーが発生しました: {e}")
            return []

    def _get_photo_url(self, photo_reference: str, max_width: int = 800) -> str:
        if not photo_reference or not self.maps_api_key:
            return "https://placehold.co/600x400/EFEFEF/AAAAAA?text=No+Image"
        return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photoreference={photo_reference}&key={self.maps_api_key}"

    def _summarize_reviews_by_ai(self, reviews: list) -> tuple:
        if not self.gemini_model or not reviews:
            return "口コミの要約はありません。", "特筆すべき点はありません。"
        review_texts = " ".join([review.get('text', '') for review in reviews[:3]])
        if not review_texts: return "高評価です！", "特にネガティブな点はありません。"
        prompt = f"あなたはプロのグルメ評論家です。以下の飲食店の口コミを分析し、ポジティブな点とネガティブな点を、それぞれ50字程度の箇条書きで要約してください。\n\n---口コミ---\n{review_texts}\n\n---要約---\n【ポジティブな点】:\n【ネガティブな点】:\n"
        try:
            response = self.gemini_model.generate_content(prompt)
            good_summary = response.text.split("【ポジティブな点】:")[1].split("【ネガティブな点】:")[0].strip()
            bad_summary = response.text.split("【ネガティブな点】:")[1].strip()
            return good_summary, bad_summary
        except Exception as e:
            print(f"AIによる口コミ要約中にエラーが発生しました: {e}")
            return "口コミ多数で高評価です。", "特筆すべきネガティブな点はありません。"

    # ★★★ ここが変更点 ① ★★★
    # 口コミと店名からジャンルを推定する新しい関数を追加
    def _extract_genre_by_ai(self, restaurant_name: str, reviews: list) -> str:
        """AIを使って店名と口コミから最も的確なジャンルを抽出する"""
        if not self.gemini_model:
            return "その他"
            
        review_texts = " ".join([review.get('text', '') for review in reviews[:5]])
        if not review_texts:
            return "その他"

        prompt = f"""あなたはプロのグルメアナリストです。
        以下の店名と口コミを参考に、この飲食店の最も的確なジャンルを一つだけ、簡潔に答えてください。
        (例: 家系ラーメン, 寿司, イタリアン, カフェ, 焼肉)

        ---店名---
        {restaurant_name}

        ---口コミ---
        {review_texts}

        ---ジャンル---
        """
        try:
            response = self.gemini_model.generate_content(prompt)
            # AIの回答から余分なテキストを取り除く
            genre = response.text.strip().replace("ジャンル:", "").replace("【ジャンル】", "").strip()
            return genre or "その他"
        except Exception as e:
            print(f"AIによるジャンル抽出中にエラーが発生しました: {e}")
            return "その他"
        
    # ★★★ ここが修正点 ③ ★★★
    # 引数に place を追加
    def _format_place_details(self, details: dict, place: dict) -> dict:
        photo_reference = details.get('photos', [{}])[0].get('photo_reference')
        reviews = details.get('reviews', [])
        restaurant_name = details.get('name', '名前不明')
        good_summary, bad_summary = self._summarize_reviews_by_ai(reviews)
        genre = self._extract_genre_by_ai(restaurant_name, reviews)

        # ★★★ ここが修正点 ④ ★★★
        # ジャンル情報は、詳細(details)ではなく、最初の検索結果(place)から取得する
        excluded_types = {'restaurant', 'food', 'point_of_interest', 'establishment'}
        genre_list = [t for t in place.get('types', []) if t not in excluded_types]
        
        return {
            "name": details.get('name', '名前不明'),
            "image_url": self._get_photo_url(photo_reference),
            "rating": details.get('rating', 0.0),
            "userRatingCount": str(details.get('user_ratings_total', 0)),
            "address": details.get('formatted_address', '-'),
            "genre": genre,
            "url": details.get('website', f"https://www.google.com/maps/search/?api=1&query=Google&query_place_id={details.get('place_id')}"),
            "reviewGoodSummary": good_summary,
            "reviewBadSummary": bad_summary,
        }
