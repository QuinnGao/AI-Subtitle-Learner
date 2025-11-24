"""
字典查询相关路由
"""

from fastapi import APIRouter, HTTPException

from app.schemas.subtitle import (
    DictionaryQueryRequest,
    DictionaryQueryResponse,
)
from app.services.dictionary_service import DictionaryService
from app.core.utils.logger import setup_logger

router = APIRouter()
dictionary_service = DictionaryService()
logger = setup_logger("dictionary_router")


@router.post("/dictionary/query", response_model=DictionaryQueryResponse)
async def query_dictionary(request: DictionaryQueryRequest):
    """查询单词的词典信息

    Args:
        request: 词典查询请求，包含单词文本、平假名、罗马字、词性等信息

    Returns:
        词典查询响应，包含单词的详细词典信息
    """
    logger.info(f"收到词典查询请求: word={request.word}")
    try:
        result = dictionary_service.query_word(
            word=request.word,
            furigana=request.furigana,
            romaji=request.romaji,
            part_of_speech=request.part_of_speech,
        )
        logger.info(f"成功查询单词: {request.word}")
        return DictionaryQueryResponse(**result)
    except Exception as e:
        logger.error(
            f"查询词典失败: word={request.word}, error={str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"查询词典失败: {str(e)}")
