import sys
sys.path.append('/home/ubuntu/draft/writer/openai_skt')
### Set OpenAI key 
import os
import configparser

config = configparser.ConfigParser()
config.read('/home/ubuntu/draft/writer/.secrets.ini')
OPENAI_API_KEY = config['OPENAI']['OPENAI_API_KEY']
YOUTUBE_KEY = config['YOUTUBE']['YOUTUBE_API_KEY']
NAVER_CLIENT_ID = config['NAVER']['NAVER_CLIENT_ID']
NAVER_CLIENT_SECRET = config['NAVER']['NAVER_CLIENT_SECRET']
GOOGLE_SEARCH_KEY = config['GOOGLE']['GOOGLE_API_KEY']
CSE_ID = config['GOOGLE']['CSE_ID']
SERPAPI_API_KEY = config['SERPAPI']['SERPAPI_API_KEY']


os.environ.update({'OPENAI_API_KEY': OPENAI_API_KEY})
os.environ.update({'YOUTUBE_KEY': YOUTUBE_KEY})
os.environ.update({'NAVER_CLIENT_ID': NAVER_CLIENT_ID})
os.environ.update({'NAVER_CLIENT_SECRET': NAVER_CLIENT_SECRET})
os.environ.update({'GOOGLE_SEARCH_KEY': GOOGLE_SEARCH_KEY})
os.environ.update({'CSE_ID': CSE_ID})
os.environ.update({'SERPAPI_API_KEY': SERPAPI_API_KEY})


# import multiprocessing
# multiprocessing.set_start_method('spawn', force=True)
import os
# from database import DataBase, CustomEmbedChain
# from multiprocessing import Process, current_process, Manager
from tqdm import tqdm

# def process_files(sub_files):
#     embedchain = CustomEmbedChain()
#     database_thread = DataBase(files=[], embed_chain=embedchain)
#     print(f"Processing in process {current_process().name}")
#     database_thread.add_files(sub_files)

# if __name__ == '__main__':
#     files = os.listdir('/home/ubuntu/data/kostat/files')
#     pdf_files = [os.path.join("/home/ubuntu/data/kostat/files", f) for f in files if f.endswith('.pdf')]
#     print(len(pdf_files))

#     # Divide the files into 5 chunks
#     chunk_size = len(pdf_files) // 3
#     chunks = [pdf_files[i:i + chunk_size] for i in range(0, len(pdf_files), chunk_size)]

#     # Use Manager to manage the shared counter

#     processes = []
#     for chunk in chunks:
#         sub_files_input = [(f, 'pdf_file') for f in chunk]
#         p = Process(target=process_files, args=(sub_files_input,))
#         processes.append(p)
#         p.start()

#     # Wait for all processes to complete
#     for p in processes:
#         p.join()

    # embedchain_thread = CustomEmbedChain()
    # database_thread = DataBase(files=[], embed_chain=embedchain_thread)
    # db_ids = list(database_thread.embed_chain.db.get([], {'data_source_type': 'kostat'}))
    # a = database_thread.embed_chain.db.collection.get(db_ids, include=["documents", "metadatas"])
    # b = set()
    # for i in a['metadatas']:
    #     b.add(i['url'])
    # print(len(b))

import os
from database import DataBase, CustomEmbedChain
from tqdm import tqdm

    
embedchain = CustomEmbedChain()
database_thread = DataBase(files=[], embed_chain=embedchain)
print(f"Processing files")
# database_thread.add('https://platform.openai.com/account/api-keys', 'web_page')

# files = os.listdir('/home/ubuntu/data/data/files')[:100]
# pdf_files = [os.path.join("/home/ubuntu/data/data/files", f) for f in files if f.endswith('.pdf')]

# files = os.listdir('/home/ubuntu/data/kostat/files')
# pdf_files = [os.path.join("/home/ubuntu/data/kostat/files", f) for f in files if f.endswith('.pdf')]

# Divide the files into 3 chunks (as per the original code)

pdf_files = ["/home/ubuntu/draft/audrey_files/source_files/558/382.pdf"]
sub_files_input = [(f, 'pdf_file') for f in  pdf_files]
database_thread.add_files(sub_files_input)