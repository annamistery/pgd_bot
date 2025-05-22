
# класс PGD_Person с применением % 22 для всех расчётов
from collections import Counter
class PGD_Person_Mod:
    """ Класс возвращает словарь со значениями для каждой позиции в чашке с расчетами по модулю 22 """

    def __init__(self, name, date, sex):
        self.name = name
        self.date = date
        self.sex = sex.upper()

    def calculate_points(self):
        # Основная чашка
        try:
            X1, X2, X3 = map(int, self.date.split('.'))
        except Exception as e:
            return f"Ошибка формата даты: {e}"

        point_A = X1 % 22
        point_B = X2
        sum_year = sum([int(d) for d in str(X3)])
        point_V = sum_year % 22
        point_G = (point_A + point_B + point_V) % 22
        point_D = (point_A + point_B) % 22
        point_L = (22 - point_D) % 22
        point_E = (point_B + point_V) % 22
        point_K = (22 - point_E) % 22
        point_J = (point_D + point_E) % 22
        point_Z = (abs(point_D - point_E) + point_J) % 22
        point_I = (point_J + point_Z) % 22
        point_Y = (point_A + point_V + point_Z) % 22

        point_M = point_N = point_O = point_P = None

        if self.sex == 'Ж':
            point_M = (point_G + point_I + point_L) % 22
            point_N = (point_M + point_Y) % 22
        elif self.sex == 'М':
            point_O = (point_G + point_I + point_K) % 22
            point_P = (point_O + point_Y) % 22
        else:
            None
        #Родовые данности
        
        RSD = point_J
        
        if self.sex == 'Ж':
            ROPP = (point_L + point_E) % 22
            
        elif self.sex == 'М':  
            ROPP = (point_D + point_K) % 22
            
        else: None
        
        RCO = (RSD + ROPP)%22
        
        RUS = point_I
        
        if self.sex == 'Ж':
            ISD = abs(RSD - point_N)
            IOPP = abs(ROPP - point_N)
            IUS = abs(RUS - point_N)
        elif self.sex == 'М':
            ISD = abs(RSD - point_P)  
            IOPP = abs(ROPP - point_P)
            IUS = abs(RUS - point_P)
        else:
            None    
            
        ICO = (ISD + IOPP) %22
        
        
        return {"Основная чашка":
            {"Первый период 0-30 лет. Характерные уроки и этапы на этот возраст.": point_A,
            "Второй период 30-60 лет. Характерные уроки и этапы на этот возраст.": point_B,
            "После 60ти лет. Характерные уроки и этапы на этот возраст.": point_V,
            "Точка входа: то с чем человек пришёл в этот мир. Некий опыт, уже имеющийся с предыдущих жизней. Важно вспомнить и пользоваться им.": point_G,
            "Инь, женская сущность. Женское проявленное в социальной сфере, общении, отношениях. Фильтр на партнёршу для мужчин": point_D,
            "Как проявляется профессионализм – для женской диагностики. Ожидания в совместной жизн, чего вы хотите от партнёрши или как Вы будете себя с ней вести – для мужской диагностики": point_L,
            "Ян, мужская сущность, проявленная в социальной  сфере, общении, отношениях – для мужской диагностики. Внутренний мужчина или фильтры при выборе партнёра в женской диагностике.": point_E,
            "Мужское проявленное в социальной сфере, общении, отношениях. Ожидания от партнёра или поведение с ним - для женской диагностики": point_K,
            "Сущность.Способ действия.Самое сильное качество.": point_J,
            "Намерение/мотивация ЗАЧЕМ (ты это делаешь)? Характер, данность, пока не станешь осознанным.": point_Z,
            "Уравновешивающее число. Дзен-сила. Выход. КУДА (реализуешь)?": point_I,
            "Точка выхода. Урок, тот опыт, за которым ты пришёл в эту жизнь, чему нужно научиться во внешнем мире. Ключ к пониманию и представлению.": point_Y,
            "Внутренняя личность. Внутренний мир. Для женской диагностики": point_M,
            "Соединение внутреннего и внешнего мира. Урок. Для женской диагностики": point_N,
            "Внутренняя личность. Внутренний мир.Для мужской диагностики": point_O,
            "Соединение внутреннего и внешнего мира. Урок. Для мужской диагностики": point_P}, 
            "Родовые данности":
            {"Способ действия, доставшийся по наследству. Так действовали у тебя в роду предки.": RSD, 
                "Отношения с противоположным полом, доставшиеся по наследству, опыт предков.": ROPP, 
                "К чему было важно прийти в отношениях предшествующим поколениям, их проявление себя, какие они были в этих отношениях и что у вас есть в генах.": RCO,
                "Родовая уравновешивающая сила": RUS},
            "Перекрёсток": {"Способ действия по индвидуальной карте личности, твои наработки, твоя манера поведения. ": ISD, 
                            "Отношения с противоположным полом, которые ты строишь сам по индвидуальной карте личности, твои наработки, твоя манера поведения. ": IOPP,
                            "К чему важно прийти в отношениях, проявление себя, какой я в этих отношениях.": ICO, 
                            "Индивидуальная уравновешивающая сила.": IUS}   
        }
    
    def tasks(self):
        dict_points = self.calculate_points()

        # ===== Карма Рода (KR): ≥ 3 повтора в "Основная чашка"
        lst_1 = [v for v in dict_points["Основная чашка"].values() if v is not None]
        counter_1 = Counter(lst_1)
        result_1 = [elem for elem in set(lst_1) if counter_1[elem] >= 3]
        KR = sum(result_1) % 22 if result_1 else None

        # ===== Личная Карма Отношений (LKO): ≥ 3 повтора в "Основная чашка" + "Родовые данности"
        lst_2 = [v for v in dict_points["Основная чашка"].values() if v is not None]
        lst_2 += [v for v in dict_points["Родовые данности"].values() if v is not None]
        counter_2 = Counter(lst_2)
        result_2 = [elem for elem in set(lst_2) if counter_2[elem] >= 3]
        LKO = sum(result_2) % 22 if result_2 else None

        # ===== Божественный Налог (BN): ≥ 3 повтора в "Основная чашка" + "Перекрёсток"
        lst_3 = [v for v in dict_points["Основная чашка"].values() if v is not None]
        lst_3 += [v for v in dict_points["Перекрёсток"].values() if v is not None]
        counter_3 = Counter(lst_3)
        result_3 = [elem for elem in set(lst_3) if counter_3[elem] >= 3]
        BN = sum(result_3) % 22 if result_3 else None

        return {
            "Карма рода. Наследственность, прошлый опыт). Что в тебе уже есть и над чем надо работать.": KR,
            "Личная карма отношений. Слушая себя, к чему важно прийти в этой жизни.": LKO,
            "Божественный налог. Обобщающий аспект, к чему нужно прийти в результате путешествия и движения души.": BN
        }
    

    
    def periods_person(self):
        dict_points = self.calculate_points()

        # Забираем значения из чашки, исключая None
        lst_1 = [v for v in dict_points["Основная чашка"].values() if v is not None]
        counter = Counter(lst_1)

        # Берём только те значения, которые повторяются 2 и более раз
        result_1 = [elem for elem in set(lst_1) if counter[elem] >= 2]

        if not result_1:
            return None

        # Период 1: значения от 1 до 10 включительно
        values_1 = [x for x in result_1 if x is not None and 1 <= x <= 10]
        period_1 = sum(values_1) % 22 if values_1 else None

        # Период 2: значения от 11 до 20 включительно
        values_2 = [x for x in result_1 if x is not None and 11 <= x <= 20]
        period_2 = sum(values_2) % 22 if values_2 else None

        # Период 3: значения от 0 до 21 включительно (включая 0!)
        values_3 = values_3 = [x for x in result_1 if x in (0, 21)]

        period_3 = sum(values_3) % 22 if values_3 else None

        
        # Период 4: сумма тех, что заданы (если хотя бы один есть)
        if any(p is not None for p in (period_1, period_2, period_3)):
            period_4 = sum(p for p in (period_1, period_2, period_3) if p is not None) % 22
        else:
            period_4 = None


        return {
            "Бизнес периоды": {
            "1-й период": period_1,
            "2-й период": period_2,
            "3-й период": period_3,
            "4-й период": period_4
        }
    }

if __name__ == "__main__":   
    # Протестируем обновлённый класс
    name = 'Анастасия'
    date = '09.10.1988'
    sex = 'Ж'
    person_mod = PGD_Person_Mod(name, date, sex)
    result_mod = person_mod.calculate_points()
    KR = person_mod.tasks()
    buisines_periods = person_mod.periods_person()
    print(name)
    print(KR)
    print(buisines_periods)
    print(result_mod)

# Импорт повторно после сброса состояния
from collections import Counter

# Повторное определение класса и выполнение
class PGD_Pair:
        
    def __init__(self, name_1, date_1, name_2, date_2):
        self.name_1 = name_1
        self.name_2 = name_2
        self.date_1 = date_1
        self.date_2 = date_2

    def main_pair(self):
        try:
            X1, X2, X3 = map(int, self.date_1.split('.'))
            Y1, Y2, Y3 = map(int, self.date_2.split('.'))
        except Exception as e:
            return f"Ошибка формата даты: {e}"
        
        XY1 = (X1 + Y1) % 22
        XY2 = (X2 + Y2) % 22
        sum_year_X = sum([int(d) for d in str(X3)])
        sum_year_Y = sum([int(d) for d in str(Y3)])
        XY3 = sum_year_X + sum_year_Y

        point_A = XY1 % 22
        point_B = XY2 % 22
        point_V = XY3 % 22
        point_G = (point_A + point_B + point_V) % 22
        point_D = (point_A + point_B) % 22
        point_L = (22 - point_D) 
        point_E = (point_B + point_V) % 22
        point_K = (22 - point_E)
        point_J = (point_D + point_E) % 22
        point_Z = (abs(point_D - point_E) + point_J) % 22
        point_I = (point_J + point_Z) % 22
        point_Y = (point_A + point_V + point_Z) % 22

        point_M = (point_G + point_I + point_L) % 22
        point_N = (point_M + point_Y) % 22
        point_O = (point_G + point_I + point_K) % 22
        point_P = (point_O + point_Y) % 22

        RSD = point_J
        ROPP = abs(((point_L + point_E)%22) - ((point_D + point_K)%22))
        RCO = (RSD + ROPP) % 22
        RUS = point_I

        ISD = (abs(point_J - point_N) + abs(point_J - point_P)) % 22
        IOPP = (abs(ROPP - point_N) + abs(ROPP - point_P)) % 22
        ICO = (ISD + IOPP) % 22
        IUS = (abs(RUS - point_N) + abs(RUS - point_P)) % 22

        return {
            "Основная чашка": {
                "Отношения между конкретной женщиной и конкретным мужчиной до 30 лет.": point_A,
                "Отношения между конкретной женщиной и конкретным мужчиной с 30 до 60 лет.": point_B,
                "Отношения между конкретной женщиной и конкретным мужчиной после 60 лет.": point_V,
                "Точка входа. Опыт данной пары, уже имеющийся у них с предыдущих жизней. Важно вспомнить и пользоваться им.": point_G,
                "Инь, женская сущность в отношениях. Женское проявленное в социальной сфере, общении, отношениях.": point_D,
                "Задача/урок женщины в этой жизни в отношениях. А также отношение женщины к своему спутнику и окружающим её мужчинам.": point_L,
                "Ян, мужская сущность в отношениях. Мужское проявленное в социальной сфере, общении, друг с другом.": point_E,
                "Задача/урок мужчины в этой жизни в отношениях. А также отношение мужчины к своей спутнице и окружающим его женщинам.": point_K,
                "Сущность. Способ действия. Самое сильное качество пары.": point_J,
                "Намерение/мотивация ЗАЧЕМ (вы вместе это делаете)? Характер, данность, пока не станете осознанными.": point_Z,
                "Уравновешивающее число. Дзен-сила. Выход. КУДА (реализуете)?": point_I,
                "Опыт, за-за которого пара сошлась вместе, чему им нужно научиться во внешнем мире. Ключ к пониманию и представлению.": point_Y,
                "Внутренняя личность. Внутренний мир женщины и ее вклад в отношения.": point_M,
                "Соединение внутреннего и внешнего мира для женщины в данных отношениях. Урок.": point_N,
                "Внутренняя личность. Внутренний мир мужчины и его вклад в отношения.": point_O,
                "Соединение внутреннего и внешнего мира для мужчины в данных отношениях. Урок.": point_P
            }, 
            "Родовые данности": {
                "Способ действия, доставшийся по наследству. Так действовали у вас в родовой линии предки. ": RSD,
                "Отношения с противоположным полом, доставшиеся вам по наследству, опыт предков.": ROPP,
                "К чему было важно прийти в отношениях предшествующим поколениям, их проявление себя, какие они были в этих отношениях и что у вас есть в генах.": RCO,
                "Уравновешивающая сила в прошлых жизнях или в судьбе ваших предков.": RUS
            },
            "Перекрёсток": {
                "Способ действия по индвидуальной карте личности, твои наработки, твоя манера поведения. ": ISD,
                "Отношения друг с другом, которые вы строите сами по индвидуальной карте личности, ваши наработки, ваши манеры поведения в отношениях друг с другом.": IOPP,
                "К чему важно прийти в отношениях друг с другом, проявление себя, какие вы в этих отношениях.": ICO,
                "Уравновешивающая сила в вашей совместной личностной карте в этой жизни.": IUS
            }   
        }

    def tasks(self):
        dict_points = self.main_pair()

        lst_1 = list(dict_points["Основная чашка"].values())
        counter = Counter(lst_1)   
        result_1 = [elem for elem in set(lst_1) if counter[elem] >= 3]
        KR = sum(result_1) % 22 if result_1 else None  

        lst_2 = lst_1 + list(dict_points["Перекрёсток"].values())
        counter = Counter(lst_2)    
        result_2 = [elem for elem in set(lst_2) if counter[elem] >= 3]
        LKO = sum(result_2) % 22 if result_2 else None

        lst_3 = lst_1 + list(dict_points["Родовые данности"].values())
        counter = Counter(lst_3)  
        result_3 = [elem for elem in set(lst_3) if counter[elem] >= 3]
        BN = sum(result_3) % 22 if result_3 else None

        return {"Сверхзадачи": {
            "Карма рода. Ретроградный аспект (наследственность, прошлый опыт). Что в вас как в паре уже есть и над чем надо работать для улучшения или изменения кармы.": KR,
            "Личная карма отношений. Слушая себя и друг друга, к чему важно прийти в этой жизни в совместных отношениях.": LKO,
            "Божественный налог. Обобщающий аспект, к чему нужно прийти в результате путешествия и движения душ.": BN
        }}
        
    def periods_pair(self):
            dict_points = self.main_pair()

            # Забираем значения из чашки, исключая None
            lst_1 = [v for v in dict_points["Основная чашка"].values() if v is not None]
            counter = Counter(lst_1)

            # Берём только те значения, которые повторяются 2 и более раз
            result_1 = [elem for elem in set(lst_1) if counter[elem] >= 2]

            if not result_1:
                return None

            # Период 1: значения от 1 до 10 включительно
            values_1 = [x for x in result_1 if x is not None and 1 <= x <= 10]
            period_1 = sum(values_1) % 22 if values_1 else None

            # Период 2: значения от 11 до 20 включительно
            values_2 = [x for x in result_1 if x is not None and 11 <= x <= 20]
            period_2 = sum(values_2) % 22 if values_2 else None

            # Период 3: значения от 0 до 21 включительно (включая 0!)
            values_3 = [x for x in result_1 if x is not None and x == 21 or x == 0]
            period_3 = sum(values_3) % 22 if values_3 else None

        
            # Период 4: сумма тех, что заданы (если хотя бы один есть)
            if any(p is not None for p in (period_1, period_2, period_3)):
                period_4 = sum(p for p in (period_1, period_2, period_3) if p is not None) % 22
            else:
                period_4 = None


            return {
            "Бизнес периоды": {
            "1-й период": period_1,
            "2-й период": period_2,
            "3-й период": period_3,
            "4-й период": period_4
        }
    }    
        
        
        
    def tasks_business (self):
            try:
                X1, X2, X3 = map(int, self.date_1.split('.'))
                Y1, Y2, Y3 = map(int, self.date_2.split('.'))
            except Exception as e:
                return f"Ошибка формата даты: {e}"
        
            XY1 = (X1 + Y1) % 22
            XY2 = (X2 + Y2) % 22
            sum_year_X = sum([int(d) for d in str(X3)])
            sum_year_Y = sum([int(d) for d in str(Y3)])
            XY3 = sum_year_X + sum_year_Y
            
            periods = self.periods_pair()
            
            Z1 = (XY1 + XY2) + (XY2 + XY3)
            Z2 = abs((XY1 + XY2) - (XY2 + XY3))
            Z3 = Z1 + Z2
            
            task_1 = (X1 + sum_year_X  + Z3)%22
            task_2 = (Y1 + sum_year_Y + Z3) %22
            conditions =(task_1 + task_2 + periods["Бизнес периоды"]["4-й период"]) %22
            
            return {"Задача первого":task_1, "Задача второго": task_2, "Условия сотрудничества": conditions}

if __name__ == "__main__":
    name_1 = "Ирина"
    name_2 = "Григорий"
    date_1 = "10.02.1978"
    date_2 = "23.01.1974"
    
    pair_mod = PGD_Pair(name_1, date_1, name_2, date_2)
    result_mod = pair_mod.main_pair()
    KR = pair_mod.tasks()
    print(f'Cовместная диагностика: {name_1} и {name_2}')
    print(result_mod)
    pair_main = pair_mod.main_pair()
    periods = pair_mod.periods_pair()
    tasks_business = pair_mod.tasks_business()
    print(f'Бизнес-периоды партнёров: {name_1}, {name_2}')
    print(periods)
    print(F'Задачи партнёров: {name_1}, {name_2}')
    print(tasks_business) 



    
                
            
            