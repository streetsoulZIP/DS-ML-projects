# Профессиональный архив опыта

Подробные карточки проектов, соревнований и хакатонов. Структурированный каталог компетенций и результатов — в [`portfolio/catalog.json`](portfolio/catalog.json).

## CV и геопространственный ML

### Kaggle Biohub: Cell Tracking During Development

Командное решение для 3D cell tracking и реконструкции lineage graph: 3D U-Net/DeepCenter для priors, TemporalUNet3D для межкадровых связей, candidate graph, lineage constraints и ILP. Вклад: интеграция detection/tracking-компонентов, настройка inference и графовых эвристик, проверка целостности lineage и сборка submission pipeline. **Результат по прежнему архиву: серебряная медаль Kaggle.** Отдельный собственный репозиторий подтверждает инфраструктурный вклад: воспроизводимый Kaggle runner, две успешные CPU-проверки запуска и получения артефактов, диагностика форматов Zarr/GEFF и систематизация reference notebooks. В его реестре экспериментов не зафиксированы обученная ML-модель или итоговая медаль; инфраструктурные проверки не следует путать с результатом команды. [Страница соревнования](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development).

### SUIM Underwater Semantic Segmentation

Локальный код: [`projects/underwater-segmentation`](projects/underwater-segmentation). Выполнены class-aware crops, балансировка, синхронные image-mask аугментации и combined Focal+Dice+IoU loss; сравнены DeepLabV3+ и U-Net. Лучший вариант DeepLabV3+ + EfficientNet-B6 достиг **mIoU 0.833, Dice 0.8702, PA 0.8663, mPA 0.8401** на локальной валидации.

### КосмоХакатон: Fires

Задача объединяет детекцию активного горения по VIIRS и сегментацию контура/степени повреждения по Sentinel-1/2, GIS и DEM. Применялись rule baseline, LightGBM, U-Net/Siamese U-Net, hard-crop mining и пространственная валидация. Вклад в команде: данные и EDA, baselines, моделирование, ансамблирование и интеграция inference через Docker/сервис. **Зафиксированный в репозитории командный private Score 0.8107** против 0.5486 у первого сабмита; median-excess AF показал F1 0.9272 на пространственной 5-fold OOF. Ранее в архиве указан private Score 0.8307, но в текущем журнале экспериментов он не найден; до дополнительного подтверждения это архивная оценка.

### КосмоХакатон: NDVI reconstruction

Восстановление пропусков NDVI в наблюдениях Sentinel-2, Landsat и MODIS с учётом sensor bias. Созданы признаки соседних измерений, сезона, климата, сенсора и погоды, использован spatial holdout и LightGBM. В [отчёте проекта](https://github.com/Niellari/KosmoHackathon/blob/main/REPORT.md) и [журнале экспериментов](https://github.com/Niellari/KosmoHackathon/blob/main/EXPERIMENTS.md) зафиксирован hidden test **RMSE 0.0736** для sensor_lightgbm v9 против 0.1024 у neighbor-mean baseline (−28.1%, 20 новых объектов, 2 323 цели). Ранее в архиве указано 0.0536 (−47.6%); это значение не подтверждается текущими файлами репозитория и сохранено отдельно.

### КосмоХакатон: HydroWatch

Change detection базовой/пиковой воды и новых зон наводнения по SAR/оптическим парам сцен. Сравнены Siamese ResNet18 и scene-specific boosting; применена event-level validation. Tuned boosting достиг **public Score 0.8943** на тех же известных reference-парах, на которых настраивался; на независимой проверке без scene-specific подстройки — 0.4646. Siamese ResNet18 encoder-decoder достиг Score 0.6665 при event-level validation и выбран в отчёте как более переносимый подход. Public Score не трактуется как оценка на неизвестных событиях.

## NLP, retrieval и LLM

### Multilingual Movie Retrieval

Локальный код: [`projects/multilingual-movie-retrieval`](projects/multilingual-movie-retrieval). BGE-M3 ранжирует описания фильмов по запросам на 10 языках; применены NLLB, pruning, distillation, triplet fine-tuning и int8 inference. **Test triplet loss 0.23**, уменьшение размера модели около 63%.

### Synthetic Movie Query Generation

Локальный код: [`projects/synthetic-movie-query-generation`](projects/synthetic-movie-query-generation). Mistral формирует структурированные описания, Qwen генерирует запросы, а последующая обработка добавляет опечатки. Получено около **70k запросов** и **6k описаний**.

### AI Finance Challenge: RAG-ассистент

Индивидуальный RAG pipeline: разбиение документов на чанки до 400 токенов, `text-embedding-3-small`, FAISS, Qwen3-Reranker-4B, генерация Mistral Small/Gemma 3, answer grading и regeneration. **Результат: выход в финал.**

### LLM-разметка товарных пар

Gemma/Qwen извлекают из описаний товарных карточек бренд, модель, размеры и комплектацию в JSON; Critic и Judge проверяют разметку. На 500 ручных парах agreement — **85.2%**, Judge self-consistency — **92.4%**, Critic veto precision — **89.7%**, JSON valid rate — **98.1%**.

### Альфа Старт: семантический поиск бизнес-сценариев

Прототип помощника начинающего предпринимателя, который выбирает заранее подготовленный ответ по сходству запроса и сценария, а не генерирует его. Реализованы RuBERT-tiny2 в формате ONNX INT8, masked mean pooling, L2-нормировка, предварительный расчёт векторов сценариев, cosine similarity и FastAPI. Личный вклад подтверждён собственными коммитами: переход на ONNX Runtime INT8, расширение базы с 44 до **224 сценариев**, реализация сервера и интерфейса. Последний коммит от 20 июля 2026 года. Число сценариев характеризует покрытие базы, а не качество классификации; измеренные latency и accuracy не представлены. Исходный код не переносился из приватного репозитория.

## Tabular ML, recommender systems и временные ряды

### Ozon E-CUP: product matching

Определение дубликатов товарных карточек по тексту, атрибутам, изображениям и OCR. Использованы NER, cross-attention и hard negatives. **Macro PR-AUC 0.769580845** на локальной Human validation (~73k строк), согласно прежнему архиву. Текущая командная документация также фиксирует bidirectional Nemotron Llama 1B, typed attribute fusion, взвешенные hard/soft labels и офлайн-сборку решения. Авторские [PR #2](https://github.com/NIKITA420240/Twin2Attr/pull/2) по обучению с synthetic hard negatives и [PR #3](https://github.com/NIKITA420240/Twin2Attr/pull/3) по бенчмаркам подтверждают конкретный личный вклад; оба PR открыты, поэтому их слияние не утверждается.

### Ozon E-CUP: LTV/GMV forecasting

Memory-efficient pipeline для ~250k клиентов: Parquet/Polars/PyArrow, rolling и decay aggregates, календарные признаки, memmap и LightGBM. **~1.67 RMSE в log1p(GMV)** при указанном в источнике ориентире лучшего решения ~1.64.

### Data Fest 2026, track 2

Multi-target классификация 41 бинарной цели на ~750k объектах и >2k признаках. Использованы экономная обработка Polars/PyArrow, Logistic Regression, CatBoost, XGBoost, LightGBM, MLP, feature selection и stacking. **Macro ROC-AUC около 0.83 на локальной проверке**; опубликованное решение остаётся в [отдельном репозитории](https://github.com/streetsoulZIP/Hackatons-and-ML-competions).

### Neftehack: технологические временные ряды

Командный проект нефтепереработки: объединение телеметрии, лабораторных и online-измерений через Parquet/as-of join, контроль доступности признаков без lookahead, CatBoost/LightGBM для динамики качества и контур оценки управляющих действий. На отложенном финальном периоде без lookahead: **normalized RMSE 0.061, MAPE 7.1%, R² 0.902**.

### Alfa Connectome 2026: прогноз движения цены

Командное соревнование по прогнозированию двух показателей будущего движения цены по последовательностям книги заявок и сделок. Метрика — Global Weighted Pearson. Подтверждённый личный вклад: разработка и проверка признаков, сравнительная оценка вариантов моделей. Согласно [официальному календарю](https://wundernn.io/docs/timeline), приём решений завершён 15 ноября 2026 года, а объявление победителей запланировано на 1 декабря. Итоговая оценка и место пока не указаны; частные технические детали, исходный код и промежуточные результаты не публикуются до подведения итогов.

## Другие локальные работы

См. [`projects/`](projects): прогноз спроса, энергоэффективность зданий, трудоустройство студентов, классификация русскоязычных новостей, спортивных изображений, отзывы DNS, fake news, NER, классификация тональности речи, Spotify recommendations и шахматное тестовое задание.

### Прогноз трудоустройства студентов

Бинарная классификация трудоустройства на Engineering Placements (~3k записей): адаптивное логарифмирование и масштабирование признаков, отбор информативных факторов, логистическая регрессия и ансамбль деревьев. **ROC-AUC 0.92, F1 0.88**. Кластеризация выходов модели выявила 5 стратегий трудоустройства (silhouette 0.41, ARI между запусками 0.85); профили проверены вручную.

### Spotify: тематическое моделирование и рекомендации

Обработан корпус из 57 651 текста песен: langdetect, перевод через googletrans, TF-IDF с 12k признаков, NMF на 20 тем и профилирование топ-10 исполнителей. Content-based рекомендации по topic vectors достигли **Recall@20 0.31** на отложенной выборке против 0.05 у случайного baseline; intra-list diversity — **0.38**.

### Вероятности шахматных ходов

Бинарный скоринг легальных ходов для FEN-позиции: AlphaZero-кодирование доски 12×8×8, гибрид ConvNeXt + Transformer (`Hybrid.pt`), XGBoost с Optuna и GPU-обучением чанками. **ROC-AUC 0.89** на отложенных парах `(fen, move)`; inference выполняется на CPU без шахматного движка.

### Тональность русскоязычных отзывов DNS

CNN с тремя Conv1D и BatchNorm для анализа отзывов: accuracy **0.95**, F1 **0.95**, ROC-AUC **0.97**.

### Детекция фейковых новостей WELFake

`Embedding(20k) → LSTM(150) → GlobalMaxPool`: accuracy **0.94** против 0.90 у TF-IDF + Logistic Regression baseline.

### NER на резюме

RoBERTa-base для token classification: entity-level F1 **0.76** по seqeval.

### Классификация эмоций в аудио CREMA-D

40 MFCC → LSTM(256), шесть классов эмоций: accuracy **0.66** при случайном baseline 0.167.
