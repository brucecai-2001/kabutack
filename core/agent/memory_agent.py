import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import dashvector
import dashscope

from utils.log import logger
from utils.config import agent_config
from utils.func import get_time

from core.llm.model_factory import create_model
from core.prompt.prompts import build_Prompt_summary_conversations

class MemoAgent:
    """
    The memeory agent, be responsible for the memory retrieval and chat summary
    Use chromadb
    """

    def __init__(self) -> None:
        """
        init the memory agent
        init client and collections
        """
        self.db_client  = dashvector.Client(
            api_key = agent_config.get('dashvector.key'),
            endpoint = agent_config.get('dashvector.endpoint')
        )

        try:
            self.user_collection = self.db_client.get(agent_config.get('dashvector.collection'))
            user_collection_status = self.user_collection.stats()
            self.total_doc_num = user_collection_status.output.partitions['default'].total_doc_count

        except:
            # 捕获到异常说明collection不存在，进行创建
            print("Creating new collection")
            ret = self.user_collection.create(
                name=agent_config.get('dashvector.collection'),
                dimension=1536,
                metric='dotproduct',
                dtype=float,
                fields_schema={'date': str, 'memory': str},
                timeout=-1
            )
            if ret:
                print("Collection created successfully.")
            else:
                print("Failed to create collection.")

        self.llm = create_model(agent_config.get('task_llm.platform'), 
                                    agent_config.get('task_llm.model_name'),
                                    agent_config.get('task_llm.end_point'),
                                    agent_config.get('task_llm.api_key'))
    
    def shutdown(self):
        print("memory agent exit")
    
    
    def retrieval(self, user_query: str):
        """
        retrieval the related memory to the user query
        Args:
            user_query (str): user's current query
        Returns:
            (str): retrievaled memory  or none
        """

        # calculate the embedding of the query
        query_embedding = self._dashscope_embed_Text_v2(user_query) 

        # search the collection
        try:
            ret = self.user_collection.query(
                vector=query_embedding,
                topk = 1
            )

            # if distance(similarity) is less than 1.0, then it is a highly related document, return to the agent
            similarity_score = ret[0].score
            print(similarity_score)
            if similarity_score > 0.2:
                return ret[0].fields['memory']
            else:
                return "none"
        except Exception as e:
            raise RuntimeError(str(e))

    
    def summary_and_persistence(self, conversations: str):
        """
        summary the conversations by sending conversations to a LLMs
        Save the summarized conversations to the chromadb
        Args:
            conversations (str): _description_
        """
        # llm summaries the conversations
        summary_prompt = build_Prompt_summary_conversations(conversations=conversations)
        try:
            summary = self.llm.invoke(summary_prompt)
            logger.log("Memory persistence", summary)

        except Exception as e:
            logger.log("Error ", str(e))
            raise RuntimeError(str(e))

        # chunking the summaried conversations
        sentences = summary.split(".")

        # store in the db
        for s in sentences:
            if len(s) < 10:
                break
            
            time = get_time()
            memory_to_store = f'''{time}: {s}'''
            print(memory_to_store)

            document_embedding = self._dashscope_embed_Text_v2(memory_to_store)

            try:
                _ = self.user_collection.insert(
                    dashvector.Doc(
                        id = f'''{self.total_doc_num + 1}''',
                        vector= document_embedding,
                        fields={
                            "date" : time,
                            "memory" : memory_to_store
                        }
                    )
                )
            except Exception as e:
                print(str(e))

            self.total_doc_num = self.total_doc_num + 1

    def _dashscope_embed_Text_v2(self, text):
        """
        embedding the texts
        Args:
            text (str): query text

        Returns:
            embedding([float]): a vector
        """
        resp = dashscope.TextEmbedding.call(
                api_key= agent_config.get('dashscope.key'),
                model=dashscope.TextEmbedding.Models.text_embedding_v2,
                input= text)
        embedding = resp["output"]["embeddings"][0]["embedding"]
        return embedding
        
    