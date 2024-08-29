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
import random
import re

def load_config(config_file_path):
    with open(config_file_path, 'r', encoding='utf-8') as file:
        config = json.load(file)
    return config
    
def ensure_list(var):
    if not isinstance(var, list):
        return [var]
    return var

#click
@click.command()
@click.option('--question-model', 'question_model', help='Select a single model to generate your question.')
@click.option('--question-count', 'question_count', type=int, help='Specify the number of questions you want to generate.')
@click.option('--test-model', 'test_models', help='Select a single model to test.')
@click.option('--test-count', 'test_count', type=int, help='Specify the number of tests you want to run.')
@click.option('--type', 'types', help='Select function or agent to determine the type of test.')
def main(question_model, question_count, test_models, test_count, types):
    sys.stdout = open('output.txt', 'w', encoding='utf-8-sig')
    config = load_config('./config.json')
    ask = 0
    question_model = question_model or config.get("question_model")
    question_count = question_count or config.get("question_count")
    test_models = test_models or config.get("test_models")
    test_count = test_count or config.get("test_count")
    types = types or config.get("types")
    result_csv_path = config.get("result_csv_path")
    #ensure_list
    test_models = ensure_list(test_models)
    types = ensure_list(types)

    # dataset.csv
    dataset_path = config.get("dataset_path")
    files = os.listdir(dataset_path)
    if files:
        create_or_update_table(dataset_path, files)
    connection_config = set_database_connection()
    generate_data = generate_questions(dataset_path, files, question_model, question_count, connection_config)
    _, _, table_name = create_or_update_table(dataset_path, files)
    get_or_create_result_csv(result_csv_path)
    test(test_models, test_count, types, ask, generate_data, table_name, result_csv_path, connection_config)
    
def test(test_models, test_count, types, ask, generate_data, table_name, result_csv_path, connection_config):
    result_format_df = get_or_create_result_csv(result_csv_path)
    temp_tokens = token()
    results = []
    for test_model in test_models:
        for type in types:
            ask += 1
            for index, (id, content) in enumerate(generate_data.items()):
                for i in range(1, int(test_count)+1):
                    print(type)
                    id = id
                    question = content['question_sentence']
                    model_answer = content['result']
                    answer = None

                    # start time
                    start_time = time.time()
                    # get answer using an Agent or Function --------------------------------------------------------------------------------------------------------------
                    if type == "function" :
                        answer = db_query_func(question=question, table_name=table_name, simplified_answer=True, connection_config=connection_config, model=test_model)
                    elif type == "agent":
                        agent = akasha.test_agent(verbose=True, tools=[db_query_tool], model=test_model) 
                        question_prompt = f'''
                                我要查詢一個"SQLITE"資料庫 名為 "database.db", 裡面有一個table={table_name},
                                {question}
                                '''
                                # let akasha agent to consider the rest of the process       
                        answer = agent(question_prompt, messages=[])
                    else:
                        raise 'wrong type'

                    # end time
                    end_time = time.time()
                    execution_time = end_time - start_time
                    #token
                    now_tokens = token()
                    tokens = now_tokens - temp_tokens
                    #y/n
                    if answer is not None:
                        yn = verify_response(content, answer)
                    else:
                        raise "Answer generation failed."
                    # data
                    results.append({
                                '組合':test_model + " + " + type,
                                '提問ID':f'Q{int(id)}',
                                '提問':question,
                                '預設答案':model_answer,
                                '測試ID': ask*10000 + int(id)*100 + i,
                                'LLM回答': answer,
                                '準確與否': yn,
                                '耗時': execution_time,
                                'token': tokens,
                                '備註': "-",
                            })
                    temp_tokens = now_tokens
    result_format_df = pd.concat([result_format_df, pd.DataFrame(results)], ignore_index=True).astype(object)
    result_format_df.to_csv('result.csv', index=False, encoding='utf-8-sig')

def get_df(dataset_df):
    def check(col):
        return dataset_df[col].dtype == 'int64'
    return check

def question_template(question_type, columns, generate_data, table_name):
    question_sentence_list = []
    for index, (id, content) in enumerate(generate_data.items()):
        question_type = content["question_type"]
        col = content["col"]
        ans_data = content["result"]
        feature = content["feature"]
        string_col = columns.copy()
        string_col.remove(col)
        if question_type == 'select': #V
            df = pd.DataFrame(ans_data, columns=columns)
            for inx, row in df.iterrows(): 
                string = '\nand\n'.join([f"{col}={row[col]}" for col in string_col])
            question_sentence = f'請問資料表{table_name}中，符合下列條件:{string}的{col}為何?'
            question_sentence_list.append(question_sentence)
        elif question_type =='vs':
            question_sentence = f'請問資料表{table_name}中，{col}由大到小進行排序，第一名與第五名相差多少?'
            question_sentence_list.append(question_sentence)
        elif question_type == 'sum': #V
            question_sentence = f'請問資料表{table_name}中 ，{col}總和是多少？'
            question_sentence_list.append(question_sentence)
        elif question_type == 'order':
            question_sentence = f'請問資料表{table_name}中 ，依照{col}由大到小進行排序，前五名是哪些{feature}？'
            question_sentence_list.append(question_sentence)
    return question_sentence_list

def get_random_column_and_generate_sql(single_generate_data, table_name, columns, checked_colist):
    feature = []
    if single_generate_data["question_type"] == 'select':
        col = random.choice(columns)
        gen_sql = f'SELECT * FROM "{table_name}" LIMIT 1 OFFSET ABS(RANDOM()) % (SELECT COUNT(*) FROM "{table_name}");'
    elif single_generate_data["question_type"] == 'vs':
        col = random.choice(checked_colist)
        gen_sql = f'''SELECT 
                        (SELECT {col} FROM (SELECT {col}, ROW_NUMBER() OVER (ORDER BY {col} DESC) AS rank FROM {table_name}) 
                        AS ranked WHERE rank = 1) -
                        (SELECT {col} FROM (SELECT {col}, ROW_NUMBER() OVER (ORDER BY {col} DESC) AS rank FROM {table_name}) 
                        AS ranked WHERE rank = 5) AS {col}_difference;
                        '''
    elif single_generate_data["question_type"] == 'sum':
        col = random.choice(checked_colist)
        gen_sql = f'SELECT SUM({col}) AS total FROM "{table_name}";'
    elif single_generate_data["question_type"] == 'order':
        col = random.choice(checked_colist)
        string_col = columns.copy()
        string_col.remove(col)
        string_col_len = len(string_col)
        for i in range(string_col_len//2):
            feature_temp = random.choice(string_col)
            feature.append(feature_temp)
            string_col.remove(feature_temp)
            feature_str = ', '.join(feature)
        gen_sql = f'SELECT {feature_str} FROM "{table_name}" ORDER BY {col} DESC LIMIT 5;'
    else:
        raise ValueError('Invalid question_type')
    return gen_sql, col, feature

def get_query_result_from_sql(generate_data, database ='database.db'):
    result_list = []
    # 1. 連接到 SQLite 資料庫
    conn = sqlite3.connect(database)
    # 2. 創建一個游標對象
    cursor = conn.cursor()
    try:
        # 3. 執行查詢
        for index in generate_data:
            cursor.execute(generate_data[index]["gen_sql"])
            # 4. 獲取結果
            result = cursor.fetchall()
            # 輸出結果
            result_list.append(result)
    except sqlite3.Error as e:
        raise e
    finally:
        # 5. 關閉游標和連接
        cursor.close()
        conn.close()
    return result_list



def generate_questions(dataset_path, files, question_model, question_count, connection_config):
    dataset_df, columns, table_name = create_or_update_table(dataset_path, files)
    #new
    ak = akasha.Doc_QA(
        verbose=True,
        max_doc_len=15000,
        model=question_model,
    )
    # table_type
    table_type = ak.ask_self(prompt=f'這是一份資料表名稱為{table_name}，欄位名稱為{columns}，請判斷此資料表是否有適合進行加減運算的欄位，若有則輸出欄位名稱，若無則只可以輸出"0"', info=columns)
    # get colist from table_type
    colist=[]
    for column in columns:
            if column in table_type:
                colist.append(column)
    #choice random column and double check
    check = get_df(dataset_df)
    checked_colist = list(filter(check, colist)) 
    #get question_type from table_type(select or other)
    generate_data = {}
    for qtime in range(int(question_count)):
        id = qtime+1
        add_id(generate_data, id)
        if table_type == "0":
            question_type = 'select'
        else:
            question_types = ['sum','order','vs']
            question_type = random.choice(question_types)
        update_generate_data(generate_data, id, question_type)
        # get random column and generate sql
        gen_sql, col, feature = get_random_column_and_generate_sql(generate_data[id], table_name, columns, checked_colist)
        update_generate_data(generate_data, id, question_type, col, feature, gen_sql, result=None, question_sentence=None)
    # get all sql query result
    result_list = get_query_result_from_sql(generate_data)
    for k in range(1,id+1):
        update_generate_data(generate_data, k, result = result_list[k-1], question_type=None, col=None, feature=None, gen_sql=None, question_sentence=None)
    # get question from question template, columns and answer
    question_sentence_list = question_template(question_type, columns, generate_data, table_name)
    for k in range(1,id+1):
        update_generate_data(generate_data, k,  question_sentence = question_sentence_list[k-1], question_type=None, col=None, feature=None, gen_sql=None, result =None)
    return generate_data

'''#generate data format
generate_data = {
    "1": { #qtime
        "type": "sum",
        "col": "A",
        "SQL": "SELECT * FROM "{table_name}" ORDER BY RANDOM() LIMIT 2",
        "result": "這是答案的示例。",
        "question_sentence": "這是一個問題的示例？",
    },
    "2": {
        "type": "order",
        col": "time",
        "SQL": "SELECT * FROM "{table_name}" ORDER BY RANDOM() LIMIT 2",
        "result": "這是另一個答案的示例。",
        "question_sentence": "這是另一個問題的示例？",
    }
}
'''
def add_id(generate_data, id):
    generate_data[id] = {
        "question_type": None,
        "col": None,
        "feature":None,
        "gen_sql": None,
        "result": None,
        "question_sentence": None,
    }

def update_generate_data(generate_data, id, question_type=None, col=None, feature=None, gen_sql=None, result=None, question_sentence=None):
    if id in generate_data:
        if question_type is not None:
            generate_data[id]['question_type'] = question_type
        if col is not None:
            generate_data[id]['col'] = col
        if feature is not None:
            generate_data[id]['feature'] = feature
        if gen_sql is not None:
            generate_data[id]['gen_sql'] = gen_sql
        if result is not None:
            generate_data[id]['result'] = result
        if question_sentence is not None:
            generate_data[id]['question_sentence'] = question_sentence
    else:
        raise f"題號 {id} 不存在"



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

def verify_response(content, answer):
    ak = akasha.Doc_QA(
        verbose=True,
        max_doc_len=15000,
        model="openai:gpt-4",
    )
    ma = content['result']
    data = f'測試輸出:"{answer}"、標準答案:"{ma}"'
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
        raise "can't find dataset path"
        sys.exit()
    for file in files:
        path = f"{dataset_path}/{file}"
        try:
            dataset_df = pd.read_csv(path, encoding='ANSI', on_bad_lines='warn')
        except UnicodeDecodeError:
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
