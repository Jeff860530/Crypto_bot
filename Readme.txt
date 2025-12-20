=== PROJECT STRUCTURE ===
crypto_bot/
    .gitignore                  => 設定 Git 版本控制應忽略的檔案與資料夾 (如敏感金鑰、虛擬環境)
    config.py                   => 集中管理 API 金鑰、策略參數、風險控制與系統設定
    main.py                     => 程式入口點，負責組裝服務、啟動迴圈與排程管理
    questions.json              => 儲存使用者提問內容與回答狀態的資料檔
    Readme.txt                  => 專案架構說明與開發文件
    requirements.txt            => 列出專案執行所需的 Python 套件清單

    scripts/
        export_context.py       => 開發輔助工具，將專案程式碼匯出為單一文字檔以便 AI Review

    services/
        email_service.py        => 封裝 SMTP 協定，負責發送 HTML 格式的郵件通知
        market_data_service.py  => 負責計算技術指標 (RSI, MA) 並生成市場分析摘要
        qa_service.py           => 管理問答流程，協調 AI 回答問題並更新處理狀態
        report_service.py       => 負責 Prompt Engineering，呼叫 AI 生成 HTML 分析報告
        trading_service.py      => 核心交易大腦，整合數據分析、策略判斷與觸發下單

    utils/
        data_loader.py          => 透過 CCXT 套件從交易所獲取 K 線數據 (OHLCV)
        executor.py             => 負責執行真實下單、模擬交易與倉位管理
        trade_logger.py         => 將所有交易動作與損益結果記錄至 JSON 檔案

==================================================