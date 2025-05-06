KEYWORDS_DEPARTMENT = {
    "дорога": "Отдел транспорта",
    "мусор": "ЖКХ",
    "вода": "Коммунальные службы",
    "освещение": "Энергетика",
    "интернет": "Цифровизация",
    "экология": "Экология"
}

def match_department(text: str):
    for keyword, dept in KEYWORDS_DEPARTMENT.items():
        if keyword in text.lower():
            return dept
    return "Общие обращения"
