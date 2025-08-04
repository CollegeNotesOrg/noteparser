"""Audio and video transcription capabilities."""

import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess
import speech_recognition as sr
from moviepy.editor import VideoFileClip
import logging

logger = logging.getLogger(__name__)


class AudioTranscriber:
    """Handles audio and video transcription using speech recognition."""
    
    AUDIO_FORMATS = {'.mp3', '.wav', '.m4a'}
    VIDEO_FORMATS = {'.mp4', '.mov', '.avi'}
    
    def __init__(self, use_google_api: bool = True):
        """Initialize the audio transcriber.
        
        Args:
            use_google_api: Whether to use Google Speech Recognition API
        """
        self.recognizer = sr.Recognizer()
        self.use_google_api = use_google_api
        
    def transcribe(self, file_path: Path) -> Dict[str, Any]:
        """Transcribe audio or video file to text.
        
        Args:
            file_path: Path to audio/video file
            
        Returns:
            Dictionary with transcription results and metadata
        """
        file_path = Path(file_path)
        
        if file_path.suffix.lower() in self.VIDEO_FORMATS:
            return self._transcribe_video(file_path)
        elif file_path.suffix.lower() in self.AUDIO_FORMATS:
            return self._transcribe_audio(file_path)
        else:
            raise ValueError(f"Unsupported format: {file_path.suffix}")
            
    def _transcribe_video(self, video_path: Path) -> Dict[str, Any]:
        """Extract audio from video and transcribe.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Transcription results with metadata
        """
        try:
            # Extract audio from video
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                video = VideoFileClip(str(video_path))
                audio = video.audio
                audio.write_audiofile(temp_audio.name, verbose=False, logger=None)
                video.close()
                audio.close()
                
                # Transcribe extracted audio
                result = self._transcribe_audio(Path(temp_audio.name))
                
                # Clean up temporary file
                os.unlink(temp_audio.name)
                
                # Add video metadata
                result['source_type'] = 'video'
                result['original_format'] = video_path.suffix
                
                return result
                
        except Exception as e:
            logger.error(f"Video transcription failed: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'error': str(e),
                'source_type': 'video'
            }
            
    def _transcribe_audio(self, audio_path: Path) -> Dict[str, Any]:
        """Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcription results with metadata
        """
        try:
            with sr.AudioFile(str(audio_path)) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source)
                audio_data = self.recognizer.record(source)
                
            # Perform transcription
            if self.use_google_api:
                text = self.recognizer.recognize_google(audio_data)
                confidence = 0.9  # Google API doesn't return confidence
            else:
                # Use offline recognition (requires additional setup)
                text = self.recognizer.recognize_sphinx(audio_data)
                confidence = 0.7
                
            return {
                'text': text,
                'confidence': confidence,
                'source_type': 'audio',
                'original_format': audio_path.suffix,
                'duration': self._get_audio_duration(audio_path)
            }
            
        except sr.UnknownValueError:
            return {
                'text': '',
                'confidence': 0.0,
                'error': 'Speech recognition could not understand audio',
                'source_type': 'audio'
            }
        except sr.RequestError as e:
            return {
                'text': '',
                'confidence': 0.0,
                'error': f'Could not request results from speech recognition service: {e}',
                'source_type': 'audio'
            }
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'error': str(e),
                'source_type': 'audio'
            }
            
    def _get_audio_duration(self, audio_path: Path) -> Optional[float]:
        """Get duration of audio file in seconds.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds or None if unavailable
        """
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', str(audio_path)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception:
            pass
            
        return None
        
    def format_transcription_markdown(self, transcription: Dict[str, Any], title: str = None) -> str:
        """Format transcription results as markdown.
        
        Args:
            transcription: Transcription results dictionary
            title: Optional title for the document
            
        Returns:
            Formatted markdown content
        """
        lines = []
        
        if title:
            lines.append(f"# {title}")
            lines.append("")
            
        # Add metadata
        lines.append("## Transcription Metadata")
        lines.append(f"- **Source Type**: {transcription.get('source_type', 'unknown')}")
        lines.append(f"- **Format**: {transcription.get('original_format', 'unknown')}")
        lines.append(f"- **Confidence**: {transcription.get('confidence', 0.0):.1%}")
        
        if 'duration' in transcription and transcription['duration']:
            duration = transcription['duration']
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            lines.append(f"- **Duration**: {minutes}:{seconds:02d}")
            
        if 'error' in transcription:
            lines.append(f"- **Error**: {transcription['error']}")
            
        lines.append("")
        
        # Add transcribed content
        lines.append("## Transcribed Content")
        lines.append("")
        
        text = transcription.get('text', '')
        if text:
            # Split into paragraphs for better readability
            paragraphs = text.split('. ')
            for i, paragraph in enumerate(paragraphs):
                if paragraph.strip():
                    lines.append(paragraph.strip() + ('.' if i < len(paragraphs) - 1 else ''))
                    lines.append("")
        else:
            lines.append("*No transcription available*")
            
        return '\n'.join(lines)