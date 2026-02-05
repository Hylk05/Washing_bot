allowed_letter = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ '

def check_correct_name(text):
    print("name =", text)
    if len(text.split()) == 2 and all(letter in allowed_letter for letter in text):
        return text.lower().title()
    return None

def check_correct_room(text):
    if text.isdigit and len(text) == 3:
        return int(text)
    return 0
