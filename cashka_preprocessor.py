
# Файл: main.py

# Импортируем словари с данными
from personality_processor import chashka, main_points
import re

class PersonalityProcessor:
    """
    Класс для полной обработки словаря с точками личности,
    формирующий итоговый словарь с подробными описаниями.
    """
    def __init__(self, cup_dict: dict):
        """
        Инициализирует процессор.

        Args:
            cup_dict (dict): Исходный словарь вида {'Основная чашка': {'Точка А': 21, ...}}.
        """
        if not isinstance(cup_dict, dict) or not cup_dict:
            raise ValueError("cup_dict должен быть непустым словарем.")
        
        self.cup_dict = cup_dict
        # Сохраняем импортированные словари как атрибуты класса для удобства доступа
        self.chashka_descriptions = chashka
        self.main_points_explanations = main_points
        self._final_result = None  # Для кеширования результата

    def get_full_description(self) -> dict:
        """
        Выполняет всю цепочку обработки и возвращает итоговый словарь.
        Результат кешируется после первого вызова.
        """
        if self._final_result is not None:
            return self._final_result

        # Шаг 1: Преобразовать исходный словарь в список
        formatted_list = self._dict_to_list()
        
        # Шаг 2: Создать словарь с базовыми описаниями
        base_descriptions = self._create_description_dict(formatted_list)
        
        # Шаг 3: Добавить пояснения к каждой точке
        full_descriptions = self._add_point_explanations(base_descriptions)
        
        self._final_result = full_descriptions
        return self._final_result
    
    # --- Новый метод для очистки текста ---
    def _clean_text(self, text: str) -> str:
        """
        [Внутренний метод] Очищает строку от лишних пробелов,
        переносов строк и повторяющихся пробелов,
        делая её более читабельной.
        """
        if not isinstance(text, str):
            return ""

        # --- НОВАЯ ЛОГИКА ---
        # Шаг 1: Заменяем все переносы строк на один пробел.
        # Это также заменяет группы переносов, как \n\n, на один пробел.
        text = text.replace('\n', ' ')

        # Шаг 2: Удаляем заголовки Markdown (#, ##, ### и т.д.)
        # Здесь `^` будет соответствовать началу всей строки.
        text = re.sub(r'^#+\s*', '', text)
        
        # Шаг 3: Удаляем множественные пробелы между словами, оставляя только один.
        text = re.sub(r' +', ' ', text)
        
        # Удаляем пробелы в начале и конце строки и возвращаем результат
        return text.strip()

    def _dict_to_list(self) -> list:
        """[Внутренний метод] Преобразует cup_dict в список строк."""
        result_list = []
        for inner_dict in self.cup_dict.values():
            for point, value in inner_dict.items():
                result_list.append(f'{point} = {value}')
        return result_list

    def _create_description_dict(self, formatted_list: list) -> dict:
        """[Внутренний метод] Создает словарь с описаниями, фильтруя ненужные."""
        final_dict = {}
        points_to_ignore = {'Точка М', 'Точка Н', 'Точка О', 'Точка П'}

        for item in formatted_list:
            parts = item.split(' = ')
            point_name, value_str = parts[0], parts[1]

            if point_name in points_to_ignore and value_str == 'None':
                continue
            
            # Ключ для поиска в словаре chashka формируется с "= 1"
            description_key = f"{point_name} = {value_str}"
            description = self.chashka_descriptions.get(description_key, "Описание для этой точки не найдено.")
            
            # Применяем очистку сразу после получения описания
            final_dict[item] = self._clean_text(description)
            
        return final_dict

    def _add_point_explanations(self, descriptions_dict: dict) -> dict:
        """[Внутренний метод] Добавляет пояснения из main_points."""
        combined_dict = {}
        for key, value in descriptions_dict.items():
            point_name = key.split(' = ')[0]
            explanation = self.main_points_explanations.get(point_name, "")
            
            # Применяем очистку к пояснению перед объединением
            cleaned_explanation = self._clean_text(explanation)
            
            if cleaned_explanation and value != "Описание для этой точки не найдено.":
                combined_description = f"{cleaned_explanation} {value}"
            else:
                combined_description = value
                
            combined_dict[key] = combined_description
            
        return combined_dict

# --- КАК ИСПОЛЬЗОВАТЬ КЛАСС ---

if __name__ == "__main__":
    # 1. Ваш исходный словарь, который вы получаете на вход
    input_cup_dict = {
        'Основная чашка': {
            'Точка А': 21, 'Точка Б': 7, 'Точка В': 21, 'Точка Г': 5,
            'Точка Д': 6, 'Точка Л': 16, 'Точка Е': 6, 'Точка К': 16,
            'Точка Ж': 12, 'Точка З': 12, 'Точка И': 2, 'Точка Й': 10,
            'Точка М': 1, 'Точка Н': None, 'Точка О': None, 'Точка П': None
        }
    }

    # 2. Создаем экземпляр класса, передавая ему словарь
    processor = PersonalityProcessor(input_cup_dict)

    # 3. Вызываем единственный публичный метод для получения результата
    final_result = processor.get_full_description()

    # 4. Выводим результат
    import json
    print(json.dumps(final_result, indent=4, ensure_ascii=False))