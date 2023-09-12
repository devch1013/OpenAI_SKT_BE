from django.apps import AppConfig
from writer.openai_skt.models.llm.chain import KeywordsChain, DraftChain, TableChain
from writer.openai_skt.models.draft_generator import DraftGeneratorInstance
from writer.openai_skt.models.keywords_generator import KeywordsGeneratorInstance
from writer.openai_skt.models.table_generator import TableGeneratorInstance
from writer.openai_skt.models.qna_assistant import QnAInstance
from writer.openai_skt.tools.search_tool import SearchTool, SearchByURLTool
from writer.openai_skt.tools.database_tool import DatabaseTool
from writer.openai_skt.database import CustomEmbedChain


class DraftsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drafts"
    verbose = False
    table_template = "writer/openai_skt/models/templates/table_prompt_template.txt"
    keywords_template = "writer/openai_skt/models/templates/keywords_prompt_template.txt"
    draft_template = "writer/openai_skt/models/templates/draft_prompt_template.txt"
    unified_summary_chunk_template = (
        "writer/openai_skt/models/templates/unified_summary_chunk_prompt_template.txt"
    )
    with open(table_template) as f1:
        table_template = "".join(f1.readlines())
    with open(keywords_template) as f2:
        keywords_template = "".join(f2.readlines())
    with open(draft_template) as f3:
        draft_template = "".join(f3.readlines())
    with open(unified_summary_chunk_template) as f4:
        unified_summary_chunk_template = "".join(f4.readlines())
    table_chain = TableChain(
        verbose=verbose, input_variables=["purpose"], table_template=table_template
    )
    keywords_chain = KeywordsChain(
        verbose=verbose, input_variables=["purpose", "table"], keywords_template=keywords_template
    )
    draft_chain = DraftChain(
        verbose=verbose,
        input_variables=["purpose", "draft", "database", "single_table", "table"],
        draft_template=draft_template,
    )
    embedchain = CustomEmbedChain()
    search_by_url_tool = SearchByURLTool()
    search_tool = SearchTool(
        search_by_url_tool=search_by_url_tool,
        input_variables=["document", "question"],
        summary_chunk_template=unified_summary_chunk_template,
    )
    database_tool = DatabaseTool(
        input_variables=["document", "question"],
        summary_chunk_template=unified_summary_chunk_template,
    )
    

    table_generator_instance = TableGeneratorInstance(table_chain=table_chain)
    keywords_generator_instance = KeywordsGeneratorInstance(keywords_chain=keywords_chain)
    draft_generator_instance = DraftGeneratorInstance(draft_chain=draft_chain)
    qna_instance = QnAInstance(
        verbose=verbose,
        search_tool=search_tool,
        database_tool=database_tool,
        qna_prompt_path="writer/openai_skt/models/templates/qna_prompt_template.txt",
        summary_chunk_template=unified_summary_chunk_template,
        input_variables=["document", "question"],
    )

    instances = {
        "table_generator_instance": table_generator_instance,
        "keywords_generator_instance": keywords_generator_instance,
        "draft_generator_instance": draft_generator_instance,
        "qna_instance": qna_instance,
        "search_tool": search_tool,
        "embed_chain": embedchain,
    }
