# AutoShorts AI

AutoShorts AI is an automated YouTube Shorts generator. It generates topics, creates a script, produces Text to Speech audio, fetches background visuals and renders a complete vertical video.

## Features
- AI Topic and Script Generation
- Edge TTS Narration
- Automated Video Rendering with FFmpeg
- Zero Cost Architecture
- Fallback visual systems

## Architecture

The project relies on external visual providers (Pexels and Unsplash) for stock footage. The intended visual architecture is:

**Pexels (Videos) → Unsplash (Images) → Local Fallback**

### Local Visual Fallback

In highly restrictive network environments or when API quotas are exceeded, external visual providers might fail. To guarantee that rendering always completes successfully, this repository includes a **local fallback system**. 

A subtle animated background (`assets/video/fallback.mp4`) exists specifically to serve as this local fallback. If external providers are unavailable, the pipeline will gracefully fall back to this video. The renderer automatically loops the fallback visual to perfectly match the narration duration, ensuring you always get a completed output.

If you ever need to re-generate or modify this fallback visual, you can run the included Python script:
```bash
python scripts/generate_fallback.py
```
This will locally generate a fresh 60 second animated gradient background using Pillow and FFmpeg without any external dependencies.
