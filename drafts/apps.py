from django.apps import AppConfig
from writer.openai_skt.models.llm.chain import ImageGenerationChain
from writer.openai_skt.models.draft_generator import DraftGeneratorInstance
from writer.openai_skt.models.keywords_generator import KeywordsGeneratorInstance
from writer.openai_skt.models.table_generator import TableGeneratorInstance
from writer.openai_skt.models.qna_assistant import QnAInstance
from writer.openai_skt.models.draft_edit_assistant import DraftEditInstance
from writer.openai_skt.tools.search_tool import SearchTool, SearchByURLTool
from writer.openai_skt.api.dalle_api import DalleAPI
from writer.openai_skt.database import CustomEmbedChain

class DraftsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drafts"
    verbose = False

    embedchain = CustomEmbedChain()
    search_by_url_tool = SearchByURLTool()
    search_tool = SearchTool(search_by_url_tool=search_by_url_tool)    

    table_generator_instance = TableGeneratorInstance(verbose=verbose)
    keywords_generator_instance = KeywordsGeneratorInstance(verbose=verbose)
    draft_generator_instance = DraftGeneratorInstance(verbose=verbose)
    qna_instance = QnAInstance(verbose=verbose)
    draft_edit_instance = DraftEditInstance(verbose=verbose)

    instances = {
        "table_generator_instance": table_generator_instance,
        "keywords_generator_instance": keywords_generator_instance,
        "draft_generator_instance": draft_generator_instance,
        "qna_instance": qna_instance,
        "draft_edit_instance": draft_edit_instance,
        "search_tool": search_tool,
        "embed_chain": embedchain,
    }
    
    image_generation_chain = ImageGenerationChain(verbose=verbose)
    dalle = DalleAPI()