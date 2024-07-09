import dashvector
import dashscope

from utils.config import agent_config


class ToolRetriever:
    """
    A dashvector client to retrieve the most related tool against user's query or task plan
    """
    def __init__(self, topk):
        self.topk = topk
        self.db_client  = dashvector.Client(
                    api_key = agent_config.get('dashvector.key'),
                    endpoint = agent_config.get('dashvector.endpoint')
        )
        try:
            self.tool_collection = self.__create_or_get_collection__(agent_config.get('dashvector.tool_collection'))
            tool_collection_status = self.tool_collection.stats()
            self.total_doc_num = tool_collection_status.output.partitions['default'].total_doc_count

        except Exception as e:
            print(e)

    def __create_or_get_collection__(self, collection_name: str):
        """
        get a collection, if it does not exist, create a new one

        Args:
            collection_name (str): collection name

        Raises:
            RuntimeError: _description_

        Returns:
            _type_: _description_
        """
        if not self.db_client.get(collection_name): 
            print("Creating new collection")
            ret = self.db_client.create(
                    name=collection_name,
                    dimension=1536,
                    metric='dotproduct',
                    dtype=float,
                    fields_schema={'tool_doc': str},
                    timeout=-1
            )
            if ret:
                print("Collection created successfully.")
            else:
                print("Failed to create collection.")
                raise RuntimeError(" Failed to create tool collection")
        return self.db_client.get(collection_name)


    def retrieve_tool(self, subplan: str) -> list:
        """
        Get a list of tool document related to the subplan

        Args:
            subplan (str): subplan from planner
            topk (int): filte the top k related tools

        Raises:
            RuntimeError: _description_

        Returns:
            list: a list of tool document
        """
        # calculate the embedding of the subplan
        resp = dashscope.TextEmbedding.call(
                    api_key= agent_config.get('dashscope.key'),
                    model=dashscope.TextEmbedding.Models.text_embedding_v2,
                    input= subplan)
        embedding = resp["output"]["embeddings"][0]["embedding"]

        # search the collection
        try:
            ret = self.tool_collection.query(
                vector=embedding,
                topk = self.topk
            )

            # if distance(similarity) is less than 1.0, then it is a highly related document, return to the agent
            tools_doc = []
            for i in range(len(ret)):
                tools_doc.append(ret[i].fields['tool_doc'])

            return tools_doc
        
        except Exception as e:
            raise RuntimeError(str(e))
        

    def save_docs(self, docs: list):
        """
        Save the tool documents to the vector db

        Args:
            docs (list): a list of tool document
        """
        for d in docs:
            resp = dashscope.TextEmbedding.call(
                    api_key= agent_config.get('dashscope.key'),
                    model=dashscope.TextEmbedding.Models.text_embedding_v2,
                    input= d)
            document_embedding = resp["output"]["embeddings"][0]["embedding"]

            try:
                _ = self.tool_collection.insert(
                    dashvector.Doc(
                        id = f'''{self.total_doc_num + 1}''',
                        vector= document_embedding,
                        fields={
                            "tool_doc" : d
                        }
                    )
                )
            except Exception as e:
                print(str(e))

            self.total_doc_num = self.total_doc_num + 1