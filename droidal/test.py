from google import genai
from google.genai import types

def transcribe_audio_with_gemini(api_key: str, audio_path: str, output_txt: str = "transcription.txt"):
    """
    Transcribes an audio file using Google Gemini API and saves the result to a text file.
    
    Requirements:
    - Install via: pip install google-genai
    - Set your API key via GOOGLE_API_KEY or pass it directly.
    """
    # Initialize the Gemini client
    client = genai.Client(api_key=api_key)

    # Upload audio file via Files API (recommended for files >20MB)
    audio_file = client.files.upload(file=audio_path)

    # Create a prompt asking for transcription
    prompt = "Generate a transcript of the speech."

    # Send transcription request
    response = client.models.generate_content(
        model="gemini-2.5-flash",  # you can also try "gemini-2.5-pro" or "gemini-2.0-flash"
        contents=[prompt, audio_file]
    )

    # Extract transcript text
    transcript_text = response.text

    # Save to a text file
    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(transcript_text)

    print(f"Transcription saved to: {output_txt}")

if __name__ == "__main__":
    import os
    your_api_key = os.getenv("AIzaSyDWcGlScX3MZ9xKC4SW4r4J1nsZh2G31bA") 
    transcribe_audio_with_gemini(your_api_key, r"C:\Users\Kaarthik.n\Downloads\harvard.wav", "transcription.txt")
