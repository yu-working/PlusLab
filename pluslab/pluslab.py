import time
import pandas as pd
import sqlite3
from akasha_plus.agents.tools import set_connection_config, db_query_func
import akasha
from akasha_plus.agents.tools import db_query_tool
import os
from datetime import datetime
import sys
import click
import json

def load_config(config_file_path):
    with open(config_file_path, 'r', encoding='utf-8') as file:
        config = json.load(file)
    return config

#click
@click.command()
@click.option('--question-model', 'question_model', help='Select a single model to generate your question.')
@click.option('--question-count', 'question_count', type=int, help='Specify the number of questions you want to generate.')
@click.option('--test-model', 'test_models', help='Select a single model to test.')
@click.option('--test-count', 'test_count', type=int, help='Specify the number of tests you want to run.')
@click.option('--type', 'types', help='Select function or agent to determine the type of test.')
def main(question_model, question_count, test_models, test_count, types):
    sys.stdout = open('output.txt', 'w')
    config = load_config('./config.json')
    ask = 0
    question_model = question_model or config.get("question_model")
    question_count = question_count or config.get("question_count")
    test_models = [test_models] or config.get("test_models")
    test_count = test_count or config.get("test_count")
    types = [types] or config.get("types")
    result_csv_path = config.get("result_csv_path")

    # dataset.csv
    dataset_path = config.get("dataset_path")
    files = os.listdir(dataset_path)
    if files:
        create_or_update_table(dataset_path, files)
    connection_config = set_database_connection()
    id_q_a = generate_questions(dataset_path, files, question_model, question_count, connection_config)
    _, _, table_name = create_or_update_table(dataset_path, files)
    get_or_create_result_csv(result_csv_path)
    test(test_models, test_count, types, ask, id_q_a, table_name, result_csv_path, connection_config)
    
def test(test_models, test_count, types, ask, id_q_a, table_name, result_csv_path, connection_config):
    result_format_df = get_or_create_result_csv(result_csv_path)
    temp_tokens = token()
    results = []
    for test_model in test_models:
        for type in types:
            ask += 1
            for key in id_q_a: #key[0] = QnA_id,key[1] = Q,key[2] = A
                for i in range(1, int(test_count)+1):  
                    answer = None
                    # start time
                    start_time = time.time()
                    # get answer using an Agent or Function --------------------------------------------------------------------------------------------------------------
                    if type == "function" :
                        answer = db_query_func(question=key[1], table_name=table_name, simplified_answer=True, connection_config=connection_config, model=test_model)
                    elif type == "agent":
                        agent = akasha.test_agent(verbose=True, tools=[db_query_tool], model=test_model) 
                        question = f'''
                                我要查詢一個"SQLITE"資料庫 名為 "database.db", 裡面有一個table={table_name},
                                {key[1]}
                                '''
                                # let akasha agent to consider the rest of the process       
                        answer = agent(question, messages=[])
                    else:
                        print('wrong type')

                    # end time
                    end_time = time.time()
                    execution_time = end_time - start_time
                    #token
                    now_tokens = token()
                    tokens = now_tokens - temp_tokens
                    #y/n
                    if answer is not None:
                        yn = verify_response(key, answer)
                    else:
                        print("Answer generation failed.")
                    # data
                    results.append({
                                '組合':test_model + " + " + type,
                                '提問ID':f'Q{int(key[0])+1}',
                                '提問':key[1],
                                '預設答案':key[2],
                                '測試ID': ask*10000 + int(key[0])*100 + i,
                                'LLM回答': answer,
                                '準確與否': yn,
                                '耗時': execution_time,
                                'token': tokens,
                                '備註': "-",
                            })
                    temp_tokens = now_tokens
    result_format_df = pd.concat([result_format_df, pd.DataFrame(results)], ignore_index=True).astype(object)
    result_format_df.to_csv('result.csv', index=False, encoding='utf-8-sig')

def generate_questions(dataset_path, files, question_model, question_count, connection_config):
    dataset_df, columns, table_name = create_or_update_table(dataset_path, files)
    row_titles = dataset_df.iloc[:, 0].tolist()  # `iloc` 用來選擇行列
    data = columns + row_titles
    ak = akasha.Doc_QA(
        verbose=True,
        max_doc_len=15000,
        model=question_model,
    )
    id_q_a = []
    for qtime in range(int(question_count)):
        q_response = ak.ask_self(prompt=f"這是一份table名為{table_name}，以此為基礎幫我產出一個問題，不可與{id_q_a}中的相同", info=data)
        model_answer = db_query_func(question=q_response, table_name=table_name, simplified_answer=True, connection_config=connection_config, model=question_model)
        id_q_a.append([qtime, q_response,model_answer])
    return id_q_a

def token():
    try:
        with open('output.txt', 'r', encoding='ANSI') as f:
            question_content = f.read()
    except UnicodeDecodeError:
        with open('output.txt', 'r', encoding="utf-8") as f:
            question_content = f.read()
    
    model_obj = akasha.helper.handle_model("openai:gpt-3.5-turbo", False, 0.0)
    now_tokens = model_obj.get_num_tokens(question_content)
    return now_tokens

#Yes or no
def verify_response(key, answer):
    ak = akasha.Doc_QA(
        verbose=True,
        max_doc_len=15000,
        model="openai:gpt-4",
    )
    data = f'測試輸出:"{key[2]}"、標準答案:"{answer}"'
    #yn = ak.ask_self(prompt=f"根據{data}，判斷測試輸出與標準答案是否極為相似，回答判斷結果與原因。", info = data)
    yn = ak.ask_self(prompt=f"根據{data}，判斷測試輸出與標準答案是否極為相似，給予值0或是1，嚴禁出現數字以外的回覆。", info = data)
    return yn

def get_or_create_result_csv(result_csv_path):
    if os.path.exists(result_csv_path):
        result_format_df = pd.read_csv(result_csv_path, encoding='utf-8-sig')
    else:
        result_format = {
            '組合': [],
            '提問ID': [],
            '提問': [],
            '預設答案': [],
            '測試ID': [],
            'LLM回答': [],
            '準確與否': [],
            '耗時': [],
            'token': [],
            '備註': [],
        }
        result_format_df = pd.DataFrame(result_format)
        result_format_df.to_csv(result_csv_path, index=False, encoding='utf-8-sig')
    return result_format_df
  
def create_or_update_table(dataset_path, files, database='database.db'):
    if not os.path.exists(dataset_path):
        print("can't find dataset path")
        sys.exit()
    for file in files:
        path = f"{dataset_path}/{file}"
        dataset_df = pd.read_csv(path, encoding='utf-8-sig', on_bad_lines='warn')
        columns = dataset_df.columns.tolist()
        table_name = file.replace(".csv", "")  
        columns_with_types = ', '.join([f'"{col}" TEXT' for col in columns])
        table_schema = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_with_types});'

        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        cursor.execute(table_schema)
        dataset_df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.commit()
        conn.close()
    return dataset_df, columns, table_name

def set_database_connection():
    connection_config = set_connection_config(sql_type='SQLITE', database='database.db')
    return connection_config

if __name__ == '__main__':
    main()
