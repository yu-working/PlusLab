# PlusLab

> 一個基於測試Akasha-plus應用於查詢資料庫的工具，可以幫助使用者快速的開始進行測試。

- [更多關於Akasha-plus](https://pypi.org/project/akasha-plus/)

## 安裝

> 請務必依據你的專案來調整內容。

以下是將此專案安裝到您的電腦上的步驟。建議使用 Python 3.9.13 版本。

### 取得專案

下載`PlusLab.zip`

### 解壓縮至目標位置

### 檔案說明

- `config.json` - 測試設定檔
- `.env` - 環境變數設定檔
- `PlusLab.py` - 測試程式
- `dataset.csv` - 查詢用資料集
- `README.md` - 專案說明文件

### 相依套件安裝
```
pip install akasha-plus
pip install pandas
```

### 環境變數設定
將環境變數儲存於 `.env` 檔案中，並將該檔案放置於專案的根目錄下。

```env
## .env file
AZURE_API_KEY={your azure key}
AZURE_API_BASE={your Language API base url}
AZURE_API_TYPE=azure
AZURE_API_VERSION=2023-05-15
```

> **注意：請確保欄位名稱和欄位順序與上述格式完全一致。**

### 移動到專案內

```bash
cd ./path/to/your/desired/folder
```

### 測試

```
# 快速進行所有模型測試
python PlusLab.py > output.txt
```

## 使用
### config.json
可根據使用者需求調整多項參數，包含:
| 欄位         | 說明 | 預設值 |
| ---                  | ---------------------------- | ---    |
| `"result_csv_path"`   | 測試結果儲存位置與檔案名稱     | `"./result.csv"` |
| `"question_model"`    | 出題語言模型                  | `"openai:gpt-4"`|
| `"question_count"`    | 問題數                       | `1`|
| `"test_model"`        | 測試模型                     | `["openai:gpt-35-turbo","openai:gpt-4"]` |
| `"test_count"`        | 每題各組合測試次數            | `5`|
| `"function_or_agent"` | 使用function或是agent進行測試| `["function","agent"]`|
### 運行專案
```
# 快速進行所有模型測試
python PlusLab.py > output.txt
```
可用指令參數
```
# --model : 輸入欲使用的模型，或是入`all`以全選，預設為openai:gpt-3.5-turbo
python test.py > output.txt --model your-model

# --fa : 選擇使用function、agent，或是入`ALL`以全選，預設為function
python test.py > output.txt --fa agent

# --question : 指定生成問題數目，預設為1個
python test.py > output.txt --question 5

# --count : 指定單個組合的測試次數，預設為5次
python test.py > output.txt --count 10
```

輸入指令後，自動生成問題與預設答案並進行測試，測試完成後，你可以在當前目錄中的 `result.csv` 文件中查看結果。

### 測試結果

測試結束後，將會在當前目錄生成三個文件。

 - `database.db` : 資料庫文件，包含與資料集同名的資料表。
 - `output.txt` : 保存執行過程中的所有輸出，用於檢查生成的 SQL 語法是否符合需求。
 - `result.csv` : 測試結果。

result.csv欄位如下:

 > **欄位說明**

| 欄位         | 說明 |
| ------------ | ----- |
| 組合         | Function/Agent + openai:gpt-4/openai:gpt-3.5-turbo |
| 提問ID       | QnA.csv的欄位ID |
| 提問         | QnA.csv的欄位question |
| 預設答案      | QnA.csv的欄位Answer |
| 測試ID       | {組合臨時編號}{提問ID}{測試次數} |
| LLM回答      | 經過組合運算後輸出的答案 |
| 準確與否      | 透過語言模型判斷是否LLM回答與預設答案是否相同或相似 |
| 耗時         | 每次運算過程中所用的時間 |
| token  | 提問過程中所消耗的累計令牌數量 |
| 備註          | - |

## 聯絡作者

你可以透過以下方式與我聯絡

- [E-mail : tsaiyuforwork@gmail.com]
