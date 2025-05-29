import json
import requests
from time import sleep

FORECAST_CREATE_URL = "https://api.direct.yandex.ru/json/v4"
FORECAST_LIST_URL = "https://api.direct.yandex.ru/json/v4"
FORECAST_GET_URL = "https://api.direct.yandex.ru/json/v4"
WAIT_SECONDS = 2
MAX_ATTEMPTS = 10


def import_forecast_shows(token: str, forecast_body: dict):
    """
    Создаёт прогноз и возвращает список фраз и показов.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept-Language": "ru"
    }

    # Шаг 1: создаем прогноз
    forecast_create_payload = {
        "method": "CreateNewForecast",
        "token": token,
        "param": forecast_body
    }

    try:
        response = requests.post(FORECAST_CREATE_URL, json=forecast_create_payload, headers=headers)
        response_data = response.json()
        forecast_id = response_data.get("data")
        if not forecast_id:
            return {"error": "Не удалось получить ForecastId"}

    except Exception as e:
        return {"error": f"Ошибка при создании прогноза: {str(e)}"}

    # Шаг 2: проверяем статус прогноза через getForecastList
    for attempt in range(MAX_ATTEMPTS):
        sleep(WAIT_SECONDS)
        forecast_list_payload = {
            "method": "GetForecastList",
            "token": token
        }

        try:
            list_response = requests.post(FORECAST_LIST_URL, json=forecast_list_payload, headers=headers)
            list_data = list_response.json().get("data", [])
        except Exception as e:
            return {"error": f"Ошибка при получении статуса прогноза: {str(e)}"}

        forecast_status = None
        for item in list_data:
            if item["ForecastID"] == forecast_id:
                forecast_status = item["Status"]
                break

        if forecast_status == "Done":
            break
        elif forecast_status in ("Pending", "Processing"):
            continue
        else:
            return {"error": f"Неожиданный статус прогноза: {forecast_status}"}
    else:
        return {"error": f"Прогноз не был готов за {MAX_ATTEMPTS * WAIT_SECONDS} секунд"}

    # Шаг 3: получаем готовый прогноз
    forecast_get_payload = {
        "method": "GetForecast",
        "token": token,
        "param": forecast_id
    }

    try:
        final_response = requests.post(FORECAST_GET_URL, json=forecast_get_payload, headers=headers)
        final_data = final_response.json().get("data", {})
        phrases_data = [
            {
                "Phrase": phrase.get("Phrase"),
                "Shows": phrase.get("Shows")
            }
            for phrase in final_data.get("Phrases", [])
        ]
        return phrases_data

    except Exception as e:
        return {"error": f"Ошибка при получении прогноза: {str(e)}"}
