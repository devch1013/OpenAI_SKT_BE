from django.apps import AppConfig
from writer.openai_skt.models.llm.chain import KeywordsChain, DraftChain, TableChain
from writer.openai_skt.models.draft_generator import DraftGeneratorInstance
from writer.openai_skt.models.keywords_generator import KeywordsGeneratorInstance
from writer.openai_skt.models.table_generator import TableGeneratorInstance
from writer.openai_skt.tools.search_tool import SearchTool


class DraftsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drafts"
    verbose = False
    table_template = "writer/openai_skt/models/templates/table_prompt_template.txt"
    keywords_template = "writer/openai_skt/models/templates/keywords_prompt_template.txt"
    draft_template = "writer/openai_skt/models/templates/draft_prompt_template.txt"
    with open(table_template) as f1:
        table_template = "".join(f1.readlines())
    with open(keywords_template) as f2:
        keywords_template = "".join(f2.readlines())
    with open(draft_template) as f3:
        draft_template = "".join(f3.readlines())
    table_chain = TableChain(
        verbose=verbose, input_variables=["purpose"], table_template=table_template
    )
    keywords_chain = KeywordsChain(
        verbose=verbose, input_variables=["purpose", "table"], keywords_template=keywords_template
    )
    draft_chain = DraftChain(
        verbose=verbose, input_variables=["purpose", "draft", "database", "single_table", "table"], draft_template=draft_template
    )

    table_generator_instance = TableGeneratorInstance(table_chain=table_chain)
    keywords_generator_instance = KeywordsGeneratorInstance(keywords_chain=keywords_chain)
    draft_generator_instance = DraftGeneratorInstance(draft_chain=draft_chain)
    search_tool = SearchTool()
    instances = {
        "table_generator_instance": table_generator_instance,
        "keywords_generator_instance": keywords_generator_instance,
        "draft_generator_instance": draft_generator_instance,
        "search_tool": search_tool,
    }
