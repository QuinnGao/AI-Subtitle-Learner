from app.core.asr.asr_data import ASRData
from app.core.asr.chunked_asr import ChunkedASR
from app.core.asr.whisperx import WhisperXASR
from app.core.entities import TranscribeConfig, TranscribeModelEnum
from app.config import MODEL_PATH


def transcribe(audio_path: str, config: TranscribeConfig, callback=None) -> ASRData:
    """Transcribe audio file using specified configuration.

    Args:
        audio_path: Path to audio file
        config: Transcription configuration
        callback: Progress callback function(progress: int, message: str)

    Returns:
        ASRData: Transcription result data
    """

    def _default_callback(x, y):
        pass

    if callback is None:
        callback = _default_callback

    if config.transcribe_model is None:
        raise ValueError("Transcription model not set")

    # Create ASR instance based on model type
    asr = _create_asr_instance(audio_path, config)

    # Run transcription
    asr_data = asr.run(callback=callback)

    # Optimize subtitle timing if not using word timestamps
    if not config.need_word_time_stamp:
        asr_data.optimize_timing()

    return asr_data


def _create_asr_instance(audio_path: str, config: TranscribeConfig) -> ChunkedASR:
    """Create appropriate ASR instance based on configuration.

    Args:
        audio_path: Path to audio file
        config: Transcription configuration

    Returns:
        ChunkedASR: Chunked ASR instance ready to run
    """
    model_type = config.transcribe_model

    if model_type == TranscribeModelEnum.WHISPERX:
        return _create_whisperx_asr(audio_path, config)
    else:
        raise ValueError(f"Invalid transcription model: {model_type}")


def _create_whisperx_asr(audio_path: str, config: TranscribeConfig) -> ChunkedASR:
    """Create WhisperX ASR instance with chunking support."""
    # 默认使用 CPU
    device = config.whisperx_device or "cpu"
    compute_type = config.whisperx_compute_type or "float32"

    # 如果使用 CPU，确保 compute_type 为 float32
    if device == "cpu":
        compute_type = "float32"

    # 明确指定模型目录为 models/whisperx
    model_dir = str(MODEL_PATH / "whisperx")

    asr_kwargs = {
        "use_cache": True,
        "need_word_time_stamp": True,  # WhisperX 总是提供词级时间戳
        "language": config.transcribe_language,
        "model": config.whisperx_model or "large-v3",
        "device": device,
        "compute_type": compute_type,
        "batch_size": config.whisperx_batch_size or 16,
        "model_dir": model_dir,  # 明确指定为 models/whisperx
    }
    return ChunkedASR(
        asr_class=WhisperXASR,
        audio_path=audio_path,
        asr_kwargs=asr_kwargs,
        chunk_concurrency=1,  # 本地转录使用单线程
        chunk_length=60 * 20,  # 每块20分钟
    )


if __name__ == "__main__":
    # 示例用法
    # 创建配置
    config = TranscribeConfig(
        transcribe_model=TranscribeModelEnum.WHISPERX,
        transcribe_language="zh",
    )

    # 转录音频
    audio_file = "test.wav"

    def progress_callback(progress: int, message: str):
        print(f"Progress: {progress}%, Message: {message}")

    result = transcribe(audio_file, config, callback=progress_callback)
    print(result)
