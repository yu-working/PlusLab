# PlusLab

> 一個基於測試Akasha-plus應用於查詢資料庫的工具，可以幫助使用者快速的開始進行測試。

- [更多關於Akasha-plus](https://pypi.org/project/akasha-plus/)

## 安裝
> 請務必依據你的專案來調整內容。

以下是將此專案安裝到您的電腦上的步驟。建議使用 Python 3.9.13 版本。

### 取得專案
```
pip install git+https://github.com/yu-working/PlusLab.git
```
## 設定

### 環境變數設定
將環境變數儲存於 `.env` 檔案中，並將該檔案放置於專案的根目錄下。

```env
## .env file
AZURE_API_KEY={your azure key}
AZURE_API_BASE={your Language API base url}
AZURE_API_TYPE=azure
AZURE_API_VERSION=2023-05-15
```
### config.json
將環境變數儲存於 `config.json` 檔案中，並將該檔案放置於專案的根目錄下。
```json
{
  "result_csv_path":"./result.csv",
  "question_model":"openai:gpt-4",
  "question_count": 1,
  "test_models":["openai:gpt-35-turbo","openai:gpt-4"],
  "test_count": 2,
  "types": ["function","agent"],
  "dataset_path": "./dataset"
}
```

| 欄位         | 說明 | 預設值 |
| ---                  | ---------------------------- | ---    |
| `"result_csv_path"`   | 測試結果儲存位置與檔案名稱     | `"./result.csv"` |
| `"question_model"`    | 出題語言模型                  | `"openai:gpt-4"`|
| `"question_count"`    | 問題數                       | `1`|
| `"test_model"`        | 測試模型                     | `["openai:gpt-35-turbo","openai:gpt-4"]` |
| `"test_count"`        | 每題各組合測試次數            | `5`|
| `"function_or_agent"` | 使用function或是agent進行測試| `["function","agent"]`|

> **注意：請確保`.env`與`config.json`欄位名稱和欄位順序與上述格式一致。**

### 資料夾說明

- `config.json` - 測試設定檔
- `.env` - 環境變數設定檔
- `data` - 資料集放置處
    - `dataset.csv` - 測試資料集

### 移動到專案內

```bash
cd ./path/to/your/desired/folder
```

### 測試

```
# 測試所有模型
pluslab
```

## 使用

### 運行專案
```
# 測試所有模型
pluslab
```
可用指令參數
```
# --model : 輸入欲使用的模型，或是入`all`以全選，預設為openai:gpt-3.5-turbo
pluslab --model your-model

# --fa : 選擇使用function、agent，或是入`ALL`以全選，預設為function
pluslab --fa agent

# --question : 指定生成問題數目，預設為1個
pluslab --question 5

# --count : 指定單個組合的測試次數，預設為5次
pluslab --count 10
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
| 組合         | `test-model` + `type` |
| 提問ID       | 提問ID |
| 提問         | 由`question_model`生成的提問 |
| 預設答案      | 由`question_model`生成的回答 |
| 測試ID       | {組合臨時編號}{提問ID}{測試次數} |
| LLM回答      | 經過組合運算後輸出的答案 |
| 準確與否      | 透過語言模型判斷是否LLM回答準確度，若準確則顯示`1`，反之則顯示`0` |
| 耗時         | 每次運算過程中所用的時間 |
| token  | 提問過程中所消耗的累計令牌數量 |
| 備註          | - |

## 聯絡作者

你可以透過以下方式與我聯絡

- [E-mail : tsaiyuforwork@gmail.com]
