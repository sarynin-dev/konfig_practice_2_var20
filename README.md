# Визуализатор графа зависимостей (Java / Maven)

## 1. Общее описание
Инструмент для анализа и визуализации графа зависимостей пакетов
Java (Maven). Реализован на языке Python без использования пакетных
менеджеров и сторонних библиотек для получения зависимостей.
Программа загружает POM-файлы напрямую из репозитория Maven Central
(или локального тестового репозитория), разбирает XML-структуру,
строит граф зависимостей с помощью итеративного алгоритма DFS без
рекурсии, выявляет циклические зависимости, рассчитывает порядок
загрузки и формирует диаграммы на языке D2 с рендерингом в PNG,
а также текстовое ASCII-дерево.

Выполнено по дисциплине «Конфигурационное управление», вариант №20.

## 2. Описание функций и настроек
Приложение настраивается через опции командной строки:
- `--package`, `-p` (обязательный) — координаты Maven-пакета
  (`groupId:artifactId[:version]`) или имя пакета в тестовом режиме
  (заглавные латинские буквы: `A`, `B`, `C`).
- `--repo`, `-r` — URL-адрес Maven репозитория (по умолчанию
  `https://repo1.maven.org/maven2`) либо путь к файлу тестового
  репозитория.
- `--test-mode`, `-t` — флаг включения режима тестового репозитория.
- `--output`, `-o` — имя сохраняемого PNG-изображения (по умолчанию
  `graph.png`). Также автоматически создается соответствующий `.d2` файл.
- `--ascii-tree`, `-a` — флаг вывода дерева зависимостей в формате ASCII.

### Модули проекта:
- `src/config.py`:
  - `parse_arguments`: парсинг и валидация аргументов CLI.
  - `validate_config`: проверка корректности координат, URL и файлов.
  - `format_config_kv`: форматирование настроек в виде «ключ-значение».
- `src/maven.py`:
  - `parse_coordinate`: разбор строковых координат Maven.
  - `fetch_pom`: загрузка POM-файла по HTTP без сторонних библиотек.
  - `resolve_latest_version`: получение версии из maven-metadata.xml.
  - `extract_direct_dependencies`: извлечение compile/runtime зависимостей
    с подстановкой `${property}`.
- `src/graph.py`:
  - `build_graph_dfs`: нерекурсивный алгоритм DFS с явным стеком.
  - `_handle_neighbor`: трехцветная раскраска для выявления циклов.
  - `parse_test_repo_file`: синтаксический разбор файлов тестового графа.
  - `format_load_order`: расчет топологического порядка загрузки.
- `src/visualizer.py`:
  - `generate_d2_text`: генерация описания графа на языке D2.
  - `format_ascii_tree`: формирование иерархического ASCII-дерева.
  - `export_graph`: экспорт диаграммы D2 и вызов D2 CLI для сохранения PNG.

## 3. Команды для сборки проекта и запуска тестов
Проект не требует внешней сборки (интерпретируемый Python).

Запуск модульных тестов и проверок оформления:
```bash
python -m unittest discover tests
```

Запуск приложения через скрипты:
```bash
# Windows
run.bat --package org.slf4j:slf4j-simple:2.0.7 --ascii-tree

# Linux / macOS
./run.sh --package org.slf4j:slf4j-simple:2.0.7 --ascii-tree
```

## 4. Примеры использования

### Этап 1. Минимальный прототип с конфигурацией
Проверка вывода параметров в формате ключ-значение:
```bash
run.bat --package org.example:lib:1.0 --ascii-tree
```

### Этап 2. Сбор прямых зависимостей
```bash
run.bat --package com.google.guava:guava:31.1-jre
```

### Этап 3. Тестовый репозиторий и обход DFS без рекурсии
Демонстрация различных графов в тестовом режиме:
1. Линейный граф (`tests/data/linear.txt`):
```bash
run.bat --test-mode --repo tests/data/linear.txt --package A
```
2. Ромбовидный граф с ветвлением (`tests/data/branching.txt`):
```bash
run.bat --test-mode --repo tests/data/branching.txt --package A
```
3. Граф с циклической зависимостью (`tests/data/cycle.txt`):
```bash
run.bat --test-mode --repo tests/data/cycle.txt --package A
```

### Этап 4. Порядок загрузки зависимостей
Порядок загрузки формируется на этапе обратного хода DFS (post-order):
```bash
run.bat --test-mode --repo tests/data/branching.txt --package A
```
Вывод:
```text
Порядок загрузки зависимостей для A:
  1. D
  2. B
  3. C
  4. A
```

### Этап 5. Визуализация (D2, PNG, ASCII-дерево)
Демонстрация для трех пакетов:
1. `org.slf4j:slf4j-simple:2.0.7`:
```bash
run.bat --package org.slf4j:slf4j-simple:2.0.7 --ascii-tree --output slf4j.png
```
2. `com.google.code.gson:gson:2.10.1`:
```bash
run.bat --package com.google.code.gson:gson:2.10.1 --ascii-tree --output gson.png
```
3. `org.apache.commons:commons-text:1.10.0`:
```bash
run.bat --package org.apache.commons:commons-text:1.10.0 --ascii-tree --output text.png
```

## 5. Сравнение со штатными средствами (mvn dependency:tree)
При сравнении со штатным плагином `mvn dependency:tree`:
1. **Фильтрация областей видимости (scope)**:
   Штатный `mvn dependency:tree` по умолчанию выводит все области
   видимости (`test`, `provided`, `runtime`, `compile`). Наш инструмент
   фокусируется на производственных зависимостях (`compile`/`runtime`),
   исключая тестовые фреймворки (`junit`, `easymock`).
2. **Разрешение конфликтов (nearest wins)**:
   Maven разрешает версии по принципу кратчайшего пути от корня дерева.
   При наличии дубликатов Maven выводит пометку `omitted for conflict`.
3. **Обработка циклов**:
   В Maven циклические зависимости между проектами приводят к ошибке
   `CycleDetectedException` и аварийному завершению. Наш инструмент
   обнаруживает циклы в процессе DFS, помечает ребро как циклическое,
   выводит предупреждение и корректно строит граф и порядок загрузки.
