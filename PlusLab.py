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
@click.option('--question-count', 'question_count', help='Specify the number of questions you want to generate.')
@click.option('--test-model', 'test_model', help='Select a single model or all to include all models.')
@click.option('--test-count', 'test_count', help='Specify the number of tests you want to run.')
@click.option('--type', 'function_or_agent', help='Select function, agent, or all to determine the type of test.')
def main(question_model, question_count, test_model, test_count, function_or_agent):
    config = load_config('config.json')
    question_model = question_model or config.get("question_model")
    question_count = question_count or config.get("question_count")
    test_model = test_model or config.get("test_model")
    test_count = test_count or config.get("test_count")
    function_or_agent = function_or_agent or config.get("function_or_agent")
    result_csv_path = config.get("result_csv_path")
    id_q_a = generate_questions(question_model, question_count)
    _, _, table_name = create_or_update_table(csv_file)
    test(test_model, test_count, function_or_agent, ask, id_q_a, table_name, result_csv_path)
    
def test(test_model,test_count,function_or_agent,ask,id_q_a, table_name, result_csv_path):
    result_format_df = get_or_create_result_csv(result_csv_path)
    temp_tokens = token()
    for test_model in test_model:
        for fa in function_or_agent:
            ask += 1
            for key in id_q_a: #key[0] = QnA_id,key[1] = Q,key[2] = A
                for i in range(1, int(test_count)+1):  
                    # start time
                    start_time = time.time()
                    # get answer using an Agent or Function --------------------------------------------------------------------------------------------------------------
                    if fa == "function" :
                        answer = db_query_func(question=key[1], table_name=table_name, simplified_answer=True, connection_config=connection_config, model=test_model)
                    elif fa == "agent":
                        agent = akasha.test_agent(verbose=True, tools=[db_query_tool], model=test_model) 
                        question = f'''
                                我要查詢一個"SQLITE"資料庫 名為 "database.db", 裡面有一個table={table_name},
                                {key[1]}
                                '''
                                # let akasha agent to consider the rest of the process       
                        answer = agent(question, messages=[])

                    # end time
                    end_time = time.time()
                    execution_time = end_time - start_time
                    #token
                    now_tokens = token()
                    tokens = now_tokens - temp_tokens
                    #y/n
                    yn = yon(key, answer)
                    # data
                    data = {
                                '組合':test_model + " + " + fa,
                                '提問ID':f'Q{int(key[0])+1}',
                                '提問':key[1],
                                '預設答案':key[2],
                                '測試ID': ask*10000 + int(key[0])*100 + i,
                                'LLM回答': answer,
                                '準確與否': yn,
                                '耗時': execution_time,
                                'token': tokens,
                                '備註': "-",
                            }
                    temp_tokens = now_tokens
                    result_format_df = pd.concat([result_format_df, pd.DataFrame([data])], ignore_index=True).astype(object)
    result_format_df.to_csv('result.csv', index=False, header=False, encoding='utf-8-sig')

def generate_questions(question_model, question_count):
    dataset_df, columns, table_name = create_or_update_table(csv_file)
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
    with open('output.txt', 'r', encoding="ANSI") as f:
        question_content = f.read()
    model_obj = akasha.helper.handle_model("openai:gpt-3.5-turbo", False, 0.0)
    now_tokens = model_obj.get_num_tokens(question_content)
    return now_tokens

#Yes or no
def yon(key, answer):
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
  
def create_or_update_table(csv_file, database='database.db'):
    if not os.path.exists(csv_file):
        sys.exit()

    dataset_df = pd.read_csv(csv_file, encoding='utf-8-sig')
    columns = dataset_df.columns.tolist()
    table_name = csv_file.replace(".csv", "")  
    columns_with_types = ', '.join([f'"{col}" TEXT' for col in columns])
    table_schema = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_with_types});'

    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(table_schema)
    dataset_df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()
    return dataset_df, columns, table_name

config = load_config('config.json')
result_csv_path = config.get('result_csv_path')
get_or_create_result_csv(result_csv_path)

# dataset.csv
directory = '.'
csv_file = next((file for file in os.listdir(directory) if file.endswith('.csv')), None)
if csv_file:
    create_or_update_table(csv_file)
# set database connection
connection_config = set_connection_config(sql_type='SQLITE', database='database.db')
ask = 0
main()


