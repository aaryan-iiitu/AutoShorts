import os
from models.domain import Script, ScriptSegment
from services.caption_service import SRTGenerator

def test_srt_generation(tmp_path):
    output_path = os.path.join(tmp_path, "captions.srt")
    
    script = Script(
        topic="Test",
        segments=[
            ScriptSegment(text="Hello world.", duration=2.5),
            ScriptSegment(text="Subscribe for more.", duration=1.75)
        ]
    )
    
    generator = SRTGenerator()
    generator.generate_captions(script, output_path)
    
    assert os.path.exists(output_path)
    
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Check block 1
    assert "1\n00:00:00,000 --> 00:00:02,500\nHello world.\n" in content
    
    # Check block 2
    assert "2\n00:00:02,500 --> 00:00:04,250\nSubscribe for more.\n" in content
